"""UpdateService — content modification, archive, and supersession.

Pipeline: VALIDATE → APPLY → PROPAGATE → INDEX → RESPOND
(DESIGN.md Section 4)
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import delete, select

from ztlctl.domain.content import get_content_model
from ztlctl.domain.lifecycle import (
    DECISION_TRANSITIONS,
    NOTE_TRANSITIONS,
    REFERENCE_TRANSITIONS,
    TASK_TRANSITIONS,
    compute_note_status,
)
from ztlctl.infrastructure.database.schema import edges, node_tags, nodes
from ztlctl.services._helpers import today_iso
from ztlctl.services.base import BaseService
from ztlctl.services.result import ServiceError, ServiceResult
from ztlctl.services.telemetry import traced

# Map content type to transition map
_TRANSITION_MAPS: dict[str, dict[str, list[str]]] = {
    "note": NOTE_TRANSITIONS,
    "reference": REFERENCE_TRANSITIONS,
    "task": TASK_TRANSITIONS,
}


class UpdateService(BaseService):
    """Handles content modification, archiving, and supersession."""

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @traced
    def update(self, content_id: str, *, changes: dict[str, Any]) -> ServiceResult:
        """Update a content item via the five-stage pipeline.

        VALIDATE → APPLY → PROPAGATE → INDEX → RESPOND
        """
        op = "update"
        warnings: list[str] = []
        today = today_iso()

        with self._vault.transaction() as txn:
            # ── VALIDATE ─────────────────────────────────────────
            node_row = txn.conn.execute(select(nodes).where(nodes.c.id == content_id)).first()
            if node_row is None:
                return ServiceResult(
                    ok=False,
                    op=op,
                    error=ServiceError(
                        code="NOT_FOUND",
                        message=f"No content found with ID: {content_id}",
                    ),
                )

            content_type = node_row.type
            subtype = node_row.subtype
            file_path = self._vault.root / node_row.path

            try:
                model_cls = get_content_model(content_type, subtype)
            except KeyError:
                return ServiceResult(
                    ok=False,
                    op=op,
                    error=ServiceError(
                        code="UNKNOWN_TYPE",
                        message=f"Unknown type: {content_type!r} / subtype: {subtype!r}",
                    ),
                )

            # Read current file (files are truth)
            fm, body = txn.read_content(file_path)

            # Validate update against business rules
            vr = model_cls.validate_update(fm, changes)
            if not vr.valid:
                return ServiceResult(
                    ok=False,
                    op=op,
                    error=ServiceError(
                        code="VALIDATION_FAILED",
                        message="; ".join(vr.errors),
                    ),
                )
            warnings.extend(vr.warnings)

            # Validate status transition if status is being changed
            if "status" in changes:
                new_status = str(changes["status"])
                current_status = str(fm.get("status", ""))
                transition_map = _get_transition_map(content_type, subtype)
                if transition_map is not None:
                    allowed = transition_map.get(current_status, [])
                    if new_status not in allowed:
                        return ServiceResult(
                            ok=False,
                            op=op,
                            error=ServiceError(
                                code="INVALID_TRANSITION",
                                message=(
                                    f"Invalid status transition: "
                                    f"{current_status} -> {new_status}. "
                                    f"Allowed: {allowed}"
                                ),
                            ),
                        )

            # ── APPLY ────────────────────────────────────────────
            fields_changed: list[str] = []

            # Garden note protection: don't modify body if maturity is set
            maturity = fm.get("maturity")
            body_change = changes.pop("body", None)
            if body_change is not None and maturity is None:
                body = str(body_change)
                fields_changed.append("body")
            elif body_change is not None and maturity is not None:
                warnings.append(f"Body change rejected: garden note (maturity={maturity})")

            # Merge frontmatter changes
            for key, value in changes.items():
                if key in ("id", "type", "created"):
                    # Immutable fields
                    warnings.append(f"Cannot change immutable field: {key}")
                    continue
                fm[key] = value
                fields_changed.append(key)

            fm["modified"] = today

            # Write back
            txn.write_content(file_path, fm, body)

            # ── PROPAGATE ────────────────────────────────────────
            # Recompute note status from link count
            if content_type == "note" and subtype != "decision":
                outgoing = txn.conn.execute(
                    select(edges.c.target_id).where(edges.c.source_id == content_id)
                ).fetchall()
                computed_status = compute_note_status(len(outgoing))
                current_fm_status = str(fm.get("status", "draft"))
                if computed_status != current_fm_status:
                    fm["status"] = computed_status
                    fm["modified"] = today
                    txn.write_content(file_path, fm, body)

            # ── INDEX ────────────────────────────────────────────
            # Update nodes row
            update_cols: dict[str, Any] = {
                "title": str(fm.get("title", node_row.title)),
                "status": str(fm.get("status", node_row.status)),
                "modified": today,
            }
            if "subtype" in fm:
                update_cols["subtype"] = fm["subtype"]
            if "topic" in fm:
                update_cols["topic"] = fm["topic"]
            if "maturity" in fm:
                update_cols["maturity"] = fm["maturity"]
            if "session" in fm:
                update_cols["session"] = fm["session"]
            # Store aliases as JSON
            aliases = fm.get("aliases")
            if aliases and isinstance(aliases, list):
                import json

                update_cols["aliases"] = json.dumps(aliases)

            txn.conn.execute(nodes.update().where(nodes.c.id == content_id).values(**update_cols))

            # FTS5
            txn.upsert_fts(content_id, str(fm.get("title", "")), body)

            # Re-sync tags if changed
            if "tags" in changes:
                txn.conn.execute(delete(node_tags).where(node_tags.c.node_id == content_id))
                new_tags = fm.get("tags", [])
                if isinstance(new_tags, list):
                    txn.index_tags(content_id, new_tags, today)

            # Re-index edges if links changed
            if "links" in changes:
                txn.conn.execute(delete(edges).where(edges.c.source_id == content_id))
                fm_links = fm.get("links", {})
                if isinstance(fm_links, dict):
                    txn.index_links(content_id, fm_links, body, today)

        # ── EVENT ────────────────────────────────────────────
        self._dispatch_event(
            "post_update",
            {
                "content_type": content_type,
                "content_id": content_id,
                "fields_changed": fields_changed,
                "path": node_row.path,
            },
            warnings,
        )

        # ── RESPOND ──────────────────────────────────────────
        return ServiceResult(
            ok=True,
            op=op,
            data={
                "id": content_id,
                "path": node_row.path,
                "fields_changed": fields_changed,
                "status": str(fm.get("status", "")),
            },
            warnings=warnings,
        )

    @traced
    def archive(self, content_id: str) -> ServiceResult:
        """Archive a content item (soft delete, preserves edges)."""
        today = today_iso()

        with self._vault.transaction() as txn:
            node_row = txn.conn.execute(
                select(nodes.c.id, nodes.c.path, nodes.c.type).where(nodes.c.id == content_id)
            ).first()
            if node_row is None:
                return ServiceResult(
                    ok=False,
                    op="archive",
                    error=ServiceError(
                        code="NOT_FOUND",
                        message=f"No content found with ID: {content_id}",
                    ),
                )

            file_path = self._vault.root / node_row.path
            fm, body = txn.read_content(file_path)

            # Set archived in frontmatter and write back
            fm["archived"] = True
            fm["modified"] = today
            txn.write_content(file_path, fm, body)

            # Update DB
            txn.conn.execute(
                nodes.update().where(nodes.c.id == content_id).values(archived=1, modified=today)
            )

        # Dispatch post_close event
        warnings: list[str] = []
        self._dispatch_event(
            "post_close",
            {
                "content_type": node_row.type,
                "content_id": content_id,
                "path": node_row.path,
                "summary": "archived",
            },
            warnings,
        )

        return ServiceResult(
            ok=True,
            op="archive",
            data={"id": content_id, "path": node_row.path},
            warnings=warnings,
        )

    @traced
    def supersede(self, old_id: str, new_id: str) -> ServiceResult:
        """Supersede a decision with a new one."""
        return self.update(
            old_id,
            changes={"status": "superseded", "superseded_by": new_id},
        )


def _get_transition_map(content_type: str, subtype: str | None) -> dict[str, list[str]] | None:
    """Get the transition map for a content type/subtype."""
    if subtype == "decision":
        return DECISION_TRANSITIONS
    return _TRANSITION_MAPS.get(content_type)
