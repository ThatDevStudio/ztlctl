"""Read-oriented repository for query and context workflows."""

from __future__ import annotations

from typing import Any

from sqlalchemy import func, select, text
from sqlalchemy.engine import Engine

from ztlctl.infrastructure.database.schema import edges, node_tags, nodes


class QueryRepository:
    """Encapsulates SQL for read-side query operations."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def count_items(self, *, include_archived: bool = False) -> int:
        """Count indexed nodes."""
        stmt = select(func.count(nodes.c.id))
        if not include_archived:
            stmt = stmt.where(nodes.c.archived == 0)

        with self._engine.connect() as conn:
            return int(conn.execute(stmt).scalar_one() or 0)

    def get_nodes_metadata(self, node_ids: list[str]) -> dict[str, dict[str, Any]]:
        """Fetch metadata rows for a set of node ids."""
        if not node_ids:
            return {}

        stmt = select(
            nodes.c.id,
            nodes.c.title,
            nodes.c.type,
            nodes.c.subtype,
            nodes.c.status,
            nodes.c.path,
            nodes.c.created,
            nodes.c.modified,
        ).where(nodes.c.id.in_(node_ids), nodes.c.archived == 0)

        with self._engine.connect() as conn:
            rows = conn.execute(stmt).mappings().all()

        return {str(row["id"]): dict(row) for row in rows}

    def search_fts_rows(
        self,
        query: str,
        *,
        content_type: str | None = None,
        tag: str | None = None,
        space: str | None = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """Execute FTS5 search query and return row dicts."""
        sql = """
            SELECT n.id, n.title, n.type, n.subtype, n.status, n.path,
                   n.created, n.modified, n.pagerank, bm25(nodes_fts) AS score
            FROM nodes_fts AS fts
            JOIN nodes AS n ON fts.id = n.id
            WHERE nodes_fts MATCH :query
              AND n.archived = 0
        """
        params: dict[str, Any] = {"query": query, "limit": limit}

        if content_type:
            sql += " AND n.type = :content_type"
            params["content_type"] = content_type
        if tag:
            sql += " AND n.id IN (SELECT node_id FROM node_tags WHERE tag = :tag)"
            params["tag"] = tag
        if space:
            sql += " AND n.path LIKE :space_prefix"
            params["space_prefix"] = f"{space}/%"

        sql += " ORDER BY bm25(nodes_fts) LIMIT :limit"

        with self._engine.connect() as conn:
            rows = conn.execute(text(sql), params).mappings().all()
        return [dict(row) for row in rows]

    def get_node(self, content_id: str) -> dict[str, Any] | None:
        """Fetch one node row by id."""
        stmt = select(nodes).where(nodes.c.id == content_id)
        with self._engine.connect() as conn:
            row = conn.execute(stmt).mappings().first()
        return dict(row) if row is not None else None

    def get_node_tags(self, content_id: str) -> list[str]:
        """Fetch tags attached to a node."""
        stmt = select(node_tags.c.tag).where(node_tags.c.node_id == content_id)
        with self._engine.connect() as conn:
            rows = conn.execute(stmt).fetchall()
        return [str(row.tag) for row in rows]

    def get_outgoing_links(self, content_id: str) -> list[dict[str, str]]:
        """Fetch outgoing edge links for a node."""
        stmt = select(edges.c.target_id, edges.c.edge_type).where(edges.c.source_id == content_id)
        with self._engine.connect() as conn:
            rows = conn.execute(stmt).fetchall()
        return [{"id": str(row.target_id), "edge_type": str(row.edge_type)} for row in rows]

    def get_incoming_links(self, content_id: str) -> list[dict[str, str]]:
        """Fetch incoming edge links for a node."""
        stmt = select(edges.c.source_id, edges.c.edge_type).where(edges.c.target_id == content_id)
        with self._engine.connect() as conn:
            rows = conn.execute(stmt).fetchall()
        return [{"id": str(row.source_id), "edge_type": str(row.edge_type)} for row in rows]

    def list_items_rows(
        self,
        *,
        content_type: str | None = None,
        status: str | None = None,
        tag: str | None = None,
        topic: str | None = None,
        subtype: str | None = None,
        maturity: str | None = None,
        space: str | None = None,
        since: str | None = None,
        include_archived: bool = False,
        sort: str = "recency",
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """List node rows with filters and sort."""
        stmt = select(
            nodes.c.id,
            nodes.c.title,
            nodes.c.type,
            nodes.c.subtype,
            nodes.c.maturity,
            nodes.c.status,
            nodes.c.path,
            nodes.c.topic,
            nodes.c.created,
            nodes.c.modified,
        )

        if not include_archived:
            stmt = stmt.where(nodes.c.archived == 0)
        if content_type:
            stmt = stmt.where(nodes.c.type == content_type)
        if status:
            stmt = stmt.where(nodes.c.status == status)
        if topic:
            stmt = stmt.where(nodes.c.topic == topic)
        if tag:
            stmt = stmt.where(
                nodes.c.id.in_(select(node_tags.c.node_id).where(node_tags.c.tag == tag))
            )
        if subtype:
            stmt = stmt.where(nodes.c.subtype == subtype)
        if maturity:
            stmt = stmt.where(nodes.c.maturity == maturity)
        if since:
            stmt = stmt.where(nodes.c.modified >= since)
        if space:
            stmt = stmt.where(nodes.c.path.like(f"{space}/%"))

        if sort == "title":
            stmt = stmt.order_by(nodes.c.title)
        elif sort == "type":
            stmt = stmt.order_by(nodes.c.type, nodes.c.modified.desc())
        else:  # recency and priority pre-sort
            stmt = stmt.order_by(nodes.c.modified.desc())

        if sort != "priority":
            stmt = stmt.limit(limit)

        with self._engine.connect() as conn:
            rows = conn.execute(stmt).mappings().all()
        return [dict(row) for row in rows]

    def work_queue_rows(self, *, space: str | None = None) -> list[dict[str, Any]]:
        """Fetch task candidates for work queue scoring."""
        stmt = (
            select(
                nodes.c.id,
                nodes.c.title,
                nodes.c.status,
                nodes.c.path,
                nodes.c.created,
                nodes.c.modified,
            )
            .where(nodes.c.type == "task")
            .where(nodes.c.status.in_(["inbox", "active", "blocked"]))
            .where(nodes.c.archived == 0)
        )
        if space:
            stmt = stmt.where(nodes.c.path.like(f"{space}/%"))

        with self._engine.connect() as conn:
            rows = conn.execute(stmt).mappings().all()
        return [dict(row) for row in rows]

    def decision_support_rows(
        self,
        *,
        topic: str | None = None,
        space: str | None = None,
    ) -> list[dict[str, Any]]:
        """Fetch note/reference rows for decision-support partitioning."""
        stmt = select(
            nodes.c.id,
            nodes.c.title,
            nodes.c.type,
            nodes.c.subtype,
            nodes.c.status,
            nodes.c.path,
            nodes.c.topic,
            nodes.c.created,
            nodes.c.modified,
        ).where(
            nodes.c.archived == 0,
            nodes.c.type.in_(["note", "reference"]),
        )

        if topic:
            stmt = stmt.where(nodes.c.topic == topic)
        if space:
            stmt = stmt.where(nodes.c.path.like(f"{space}/%"))

        stmt = stmt.order_by(nodes.c.modified.desc())

        with self._engine.connect() as conn:
            rows = conn.execute(stmt).mappings().all()
        return [dict(row) for row in rows]
