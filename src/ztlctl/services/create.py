"""CreateService — five-stage content creation pipeline.

Pipeline: VALIDATE → GENERATE → PERSIST → INDEX → RESPOND
(DESIGN.md Section 4)
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlalchemy import insert, select, text

if TYPE_CHECKING:
    from sqlalchemy import Connection

from ztlctl.domain.content import get_content_model
from ztlctl.domain.ids import TYPE_PREFIXES, generate_content_hash
from ztlctl.domain.links import extract_frontmatter_links, extract_wikilinks
from ztlctl.infrastructure.database.counters import next_sequential_id
from ztlctl.infrastructure.database.schema import edges, node_tags, nodes, tags_registry
from ztlctl.services._helpers import parse_tag_parts, today_iso
from ztlctl.services.base import BaseService
from ztlctl.services.result import ServiceError, ServiceResult


class CreateService(BaseService):
    """Handles content creation for all types."""

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

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
    # Five-stage pipeline (private)
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
        """Shared pipeline: VALIDATE → GENERATE → PERSIST → INDEX → RESPOND."""
        op = f"create_{content_type}"
        warnings: list[str] = []
        tags = tags or []
        today = today_iso()

        # ── VALIDATE ──────────────────────────────────────────────
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
                warnings.append(f"Tag '{tag}' missing domain/scope format (e.g. 'domain/scope')")

        # ── GENERATE → PERSIST → INDEX (inside transaction) ───────
        with self._vault.transaction() as txn:
            # GENERATE
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
            existing = txn.conn.execute(select(nodes.c.id).where(nodes.c.id == content_id)).first()
            if existing is not None:
                return ServiceResult(
                    ok=False,
                    op=op,
                    error=ServiceError(
                        code="ID_COLLISION",
                        message=f"Content with ID '{content_id}' already exists",
                    ),
                )

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
            txn.conn.execute(
                text("INSERT INTO nodes_fts(id, title, body) VALUES (:id, :title, :body)"),
                {"id": content_id, "title": title, "body": body},
            )

            # Tags
            self._index_tags(txn.conn, content_id, tags, today)

            # Links (frontmatter + body wikilinks)
            fm_links = fm.get("links", {})
            if isinstance(fm_links, dict):
                self._index_links(txn.conn, content_id, fm_links, body, today)

        # ── EVENT ─────────────────────────────────────────────────
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

    @staticmethod
    def _index_tags(conn: Connection, content_id: str, tags: list[str], today: str) -> None:
        """Register tags and link them to the content node."""
        for tag in tags:
            domain, scope = parse_tag_parts(tag)

            # Upsert tag into registry (ignore if already exists)
            existing_tag = conn.execute(
                select(tags_registry.c.tag).where(tags_registry.c.tag == tag)
            ).first()
            if existing_tag is None:
                conn.execute(
                    insert(tags_registry).values(tag=tag, domain=domain, scope=scope, created=today)
                )

            conn.execute(insert(node_tags).values(node_id=content_id, tag=tag))

    @staticmethod
    def _index_links(
        conn: Connection,
        source_id: str,
        fm_links: dict[str, list[str]],
        body: str,
        today: str,
    ) -> None:
        """Extract and index links from frontmatter and body wikilinks."""
        # Frontmatter typed links
        for link in extract_frontmatter_links(fm_links):
            # Only index if target exists
            target = conn.execute(select(nodes.c.id).where(nodes.c.id == link.target_id)).first()
            if target is not None:
                conn.execute(
                    insert(edges).values(
                        source_id=source_id,
                        target_id=link.target_id,
                        edge_type=link.edge_type,
                        source_layer="frontmatter",
                        weight=1.0,
                        created=today,
                    )
                )

        # Body wikilinks
        for wlink in extract_wikilinks(body):
            resolved_id = _resolve_wikilink(conn, wlink.raw)
            if resolved_id is not None:
                # Avoid duplicate edges
                exists = conn.execute(
                    select(edges.c.source_id).where(
                        edges.c.source_id == source_id,
                        edges.c.target_id == resolved_id,
                        edges.c.edge_type == "relates",
                    )
                ).first()
                if exists is None:
                    conn.execute(
                        insert(edges).values(
                            source_id=source_id,
                            target_id=resolved_id,
                            edge_type="relates",
                            source_layer="body",
                            weight=1.0,
                            created=today,
                        )
                    )


def _resolve_wikilink(conn: Connection, raw: str) -> str | None:
    """Resolve a wikilink target to a node ID.

    Resolution order (DESIGN.md Section 3):
    1. Exact title match
    2. Alias match (JSON array in nodes.aliases via json_each)
    3. Direct ID match
    """
    # 1. Title match
    row = conn.execute(select(nodes.c.id).where(nodes.c.title == raw)).first()
    if row is not None:
        return str(row.id)

    # 2. Alias match (JSON array in nodes.aliases)
    alias_row = conn.execute(
        text("SELECT nodes.id FROM nodes, json_each(nodes.aliases) WHERE json_each.value = :raw"),
        {"raw": raw},
    ).first()
    if alias_row is not None:
        return str(alias_row.id)

    # 3. Direct ID match (covers [[ztl_abc12345]] style)
    row = conn.execute(select(nodes.c.id).where(nodes.c.id == raw)).first()
    if row is not None:
        return str(row.id)

    return None
