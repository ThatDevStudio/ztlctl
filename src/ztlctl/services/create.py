"""CreateService — content creation pipeline.

Pipeline: VALIDATE → GENERATE → PERSIST → INDEX → EVENT → REWEAVE → VECTOR INDEX → RESPOND
(DESIGN.md Section 4)
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlalchemy import insert, select

if TYPE_CHECKING:
    from sqlalchemy import Connection

from ztlctl.domain.content import get_content_model
from ztlctl.domain.ids import TYPE_PREFIXES, generate_content_hash
from ztlctl.infrastructure.database.counters import next_sequential_id
from ztlctl.infrastructure.database.schema import nodes
from ztlctl.services._helpers import today_iso
from ztlctl.services.base import BaseService
from ztlctl.services.result import ServiceError, ServiceResult
from ztlctl.services.telemetry import trace_span, traced


class CreateService(BaseService):
    """Handles content creation for all types."""

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @traced
    def create_note(
        self,
        title: str,
        *,
        subtype: str | None = None,
        tags: list[str] | None = None,
        topic: str | None = None,
        session: str | None = None,
        maturity: str | None = None,
    ) -> ServiceResult:
        """Create a new note (plain, knowledge, or decision subtype)."""
        return self._create_content(
            content_type="note",
            title=title,
            subtype=subtype,
            tags=tags,
            topic=topic,
            session=session,
            maturity=maturity,
        )

    @traced
    def create_reference(
        self,
        title: str,
        *,
        url: str | None = None,
        subtype: str | None = None,
        tags: list[str] | None = None,
        topic: str | None = None,
        session: str | None = None,
    ) -> ServiceResult:
        """Create a new reference to an external source."""
        return self._create_content(
            content_type="reference",
            title=title,
            subtype=subtype,
            tags=tags,
            topic=topic,
            session=session,
            url=url,
        )

    @traced
    def create_task(
        self,
        title: str,
        *,
        priority: str = "medium",
        impact: str = "medium",
        effort: str = "medium",
        tags: list[str] | None = None,
        session: str | None = None,
    ) -> ServiceResult:
        """Create a new task with priority/impact/effort matrix."""
        return self._create_content(
            content_type="task",
            title=title,
            tags=tags,
            session=session,
            priority=priority,
            impact=impact,
            effort=effort,
        )

    @traced
    def create_batch(
        self,
        items: list[dict[str, object]],
        *,
        partial: bool = False,
    ) -> ServiceResult:
        """Create multiple items. All-or-nothing unless *partial* is True."""
        results: list[dict[str, Any]] = []
        errors: list[dict[str, Any]] = []

        for i, item in enumerate(items):
            content_type = str(item.get("type", "note"))
            title = str(item.get("title", ""))
            kwargs: dict[str, Any] = {k: v for k, v in item.items() if k not in ("type", "title")}
            result = self._create_content(content_type=content_type, title=title, **kwargs)
            if result.ok:
                results.append(result.data)
            else:
                errors.append({"index": i, "error": result.error.message if result.error else ""})
                if not partial:
                    return ServiceResult(
                        ok=False,
                        op="create_batch",
                        error=ServiceError(
                            code="BATCH_FAILED",
                            message=f"Item {i} failed: {errors[-1]['error']}",
                        ),
                        data={"created": results, "errors": errors},
                    )

        all_ok = len(errors) == 0
        return ServiceResult(
            ok=all_ok,
            op="create_batch",
            data={"created": results, "errors": errors},
            error=ServiceError(
                code="BATCH_PARTIAL",
                message=f"{len(errors)} of {len(items)} items failed",
            )
            if not all_ok
            else None,
        )

    # ------------------------------------------------------------------
    # Six-stage pipeline (private)
    # ------------------------------------------------------------------

    def _create_content(
        self,
        *,
        content_type: str,
        title: str,
        subtype: str | None = None,
        tags: list[str] | None = None,
        topic: str | None = None,
        session: str | None = None,
        **extra: Any,
    ) -> ServiceResult:
        """Shared creation pipeline.

        VALIDATE → GENERATE → PERSIST → INDEX → EVENT → REWEAVE → VECTOR INDEX → RESPOND
        """
        op = f"create_{content_type}"
        warnings: list[str] = []
        tags = tags or []
        today = today_iso()

        # ── VALIDATE ──────────────────────────────────────────────
        with trace_span("validate"):
            try:
                model_cls = get_content_model(content_type, subtype)
            except KeyError:
                return ServiceResult(
                    ok=False,
                    op=op,
                    error=ServiceError(
                        code="UNKNOWN_TYPE",
                        message=f"Unknown content type: {content_type!r} / subtype: {subtype!r}",
                    ),
                )

            initial_status = self._initial_status(content_type, subtype)
            validate_data: dict[str, Any] = {
                "title": title,
                "status": initial_status,
                "tags": tags,
                **extra,
            }
            vr = model_cls.validate_create(validate_data)
            if not vr.valid:
                return ServiceResult(
                    ok=False,
                    op=op,
                    error=ServiceError(code="VALIDATION_FAILED", message="; ".join(vr.errors)),
                )
            warnings.extend(vr.warnings)

            # Warn on tags missing domain/scope format
            for tag in tags:
                if "/" not in tag:
                    warnings.append(
                        f"Tag '{tag}' missing domain/scope format (e.g. 'domain/scope')"
                    )

        # ── GENERATE → PERSIST → INDEX (inside transaction) ───────
        with self._vault.transaction() as txn:
            # GENERATE
            with trace_span("generate"):
                content_id = self._generate_id(txn.conn, content_type, title)
                if content_id is None:
                    return ServiceResult(
                        ok=False,
                        op=op,
                        error=ServiceError(
                            code="UNKNOWN_TYPE",
                            message=f"No ID prefix for content type: {content_type!r}",
                        ),
                    )

                # Check for ID collision
                existing = txn.conn.execute(
                    select(nodes.c.id).where(nodes.c.id == content_id)
                ).first()
                if existing is not None:
                    return ServiceResult(
                        ok=False,
                        op=op,
                        error=ServiceError(
                            code="ID_COLLISION",
                            message=f"Content with ID '{content_id}' already exists",
                        ),
                    )

            with trace_span("persist"):
                # Build model attributes
                model_data: dict[str, Any] = {
                    "id": content_id,
                    "type": content_type,
                    "status": initial_status,
                    "title": title,
                    "created": today,
                    "modified": today,
                }
                if subtype:
                    model_data["subtype"] = subtype
                if tags:
                    model_data["tags"] = tags
                if topic:
                    model_data["topic"] = topic
                if session:
                    model_data["session"] = session
                model_data.update(extra)

                model = model_cls.model_validate(model_data)
                body = model.write_body(**extra)
                fm = model.to_frontmatter()

                # PERSIST
                path = txn.resolve_path(content_type, content_id, topic=topic)
                txn.write_content(path, fm, body)

            # INDEX
            with trace_span("index"):
                rel_path = str(path.relative_to(self._vault.root))
                node_row: dict[str, Any] = {
                    "id": content_id,
                    "title": title,
                    "type": content_type,
                    "subtype": subtype,
                    "status": initial_status,
                    "path": rel_path,
                    "created": today,
                    "modified": today,
                }
                if topic:
                    node_row["topic"] = topic
                if session:
                    node_row["session"] = session
                maturity = extra.get("maturity")
                if maturity:
                    node_row["maturity"] = maturity
                txn.conn.execute(insert(nodes).values(**node_row))

                # FTS5 index
                txn.upsert_fts(content_id, title, body)

                # Tags
                txn.index_tags(content_id, tags, today)

                # Links (frontmatter + body wikilinks)
                fm_links = fm.get("links", {})
                if isinstance(fm_links, dict):
                    txn.index_links(content_id, fm_links, body, today)

        # ── EVENT ─────────────────────────────────────────────────
        with trace_span("dispatch_event"):
            self._dispatch_event(
                "post_create",
                {
                    "content_type": content_type,
                    "content_id": content_id,
                    "title": title,
                    "path": rel_path,
                    "tags": tags,
                },
                warnings,
            )

        # ── REWEAVE ──────────────────────────────────────────────
        if not self._vault.settings.no_reweave and content_type in ("note", "reference"):
            with trace_span("post_create_reweave"):
                from ztlctl.services.reweave import ReweaveService

                try:
                    rw = ReweaveService(self._vault).reweave(content_id=content_id)
                except Exception as exc:
                    warnings.append(f"Auto-reweave skipped: {exc}")
                else:
                    if rw.ok:
                        count = rw.data.get("count", 0)
                        if count > 0:
                            warnings.append(f"Auto-reweave: {count} link(s) added")
                    else:
                        msg = rw.error.message if rw.error else "unknown"
                        warnings.append(f"Auto-reweave skipped: {msg}")

        # ── VECTOR INDEX ─────────────────────────────────────────
        if self._vault.settings.search.semantic_enabled:
            with trace_span("vector_index"):
                try:
                    from ztlctl.services.vector import VectorService

                    vec_svc = VectorService(self._vault)
                    if vec_svc.is_available():
                        vec_svc.index_node(content_id, f"{title} {body}")
                except Exception as exc:
                    warnings.append(f"Vector indexing skipped: {exc}")

        # ── RESPOND ───────────────────────────────────────────────
        return ServiceResult(
            ok=True,
            op=op,
            data={
                "id": content_id,
                "path": rel_path,
                "title": title,
                "type": content_type,
            },
            warnings=warnings,
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _initial_status(content_type: str, subtype: str | None = None) -> str:
        """Determine the correct initial status for a content type."""
        if subtype == "decision":
            return "proposed"
        return {
            "note": "draft",
            "reference": "captured",
            "task": "inbox",
            "log": "open",
        }.get(content_type, "draft")

    @staticmethod
    def _generate_id(conn: Connection, content_type: str, title: str) -> str | None:
        """Generate the appropriate ID for the content type.

        Returns None if the content type has no registered ID prefix.
        """
        prefix = TYPE_PREFIXES.get(content_type)
        if prefix is None:
            return None

        if content_type in ("log", "task"):
            return next_sequential_id(conn, prefix)
        return generate_content_hash(title, prefix)
