"""QueryService — structured retrieval and search.

Five read-only surfaces using engine.connect() (no transaction overhead):
- search: FTS5 full-text search with BM25 ranking
- get: Single-item retrieval with tags, body, and graph neighbors
- list_items: Filtered listing with multiple sort modes
- work_queue: Scored task queue for prioritization
- decision_support: Aggregated context for decision-making

(DESIGN.md Section 8)
"""

from __future__ import annotations

import math
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select, text

from ztlctl.domain.content import parse_frontmatter
from ztlctl.infrastructure.database.schema import edges, node_tags, nodes
from ztlctl.services.base import BaseService
from ztlctl.services.result import ServiceError, ServiceResult
from ztlctl.services.telemetry import traced

# Priority/impact/effort scoring weights for work_queue
_PRIORITY_SCORES: dict[str, float] = {
    "critical": 4.0,
    "high": 3.0,
    "medium": 2.0,
    "low": 1.0,
}
_IMPACT_SCORES: dict[str, float] = {"high": 3.0, "medium": 2.0, "low": 1.0}
_EFFORT_SCORES: dict[str, float] = {"high": 3.0, "medium": 2.0, "low": 1.0}


class QueryService(BaseService):
    """Handles search, retrieval, and agent context queries."""

    # ------------------------------------------------------------------
    # search — FTS5 full-text search
    # ------------------------------------------------------------------

    @traced
    def search(
        self,
        query: str,
        *,
        content_type: str | None = None,
        tag: str | None = None,
        space: str | None = None,
        rank_by: str = "relevance",
        limit: int = 20,
    ) -> ServiceResult:
        """Full-text search via FTS5 BM25.

        Args:
            query: FTS5 search expression.
            content_type: Filter to a specific type (note, reference, task).
            tag: Filter to items with this tag.
            space: Filter by vault space (notes, ops, self).
            rank_by: Sort mode — "relevance" (BM25), "recency" (BM25*decay),
                or "graph" (BM25*PageRank).
            limit: Maximum results to return.
        """
        if not query.strip():
            return ServiceResult(
                ok=False,
                op="search",
                error=ServiceError(code="EMPTY_QUERY", message="Search query cannot be empty"),
            )

        # Recency/graph modes: fetch more candidates for Python-side re-ranking
        use_time_decay = rank_by == "recency"
        use_graph_rank = rank_by == "graph"
        needs_rerank = use_time_decay or use_graph_rank
        fetch_limit = min(limit * 3, 1000) if needs_rerank else limit

        # Always order by BM25 for the SQL fetch
        order_clause = "bm25(nodes_fts)"

        sql = """
            SELECT n.id, n.title, n.type, n.subtype, n.status, n.path,
                   n.created, n.modified, n.pagerank, bm25(nodes_fts) AS score
            FROM nodes_fts AS fts
            JOIN nodes AS n ON fts.id = n.id
            WHERE nodes_fts MATCH :query
              AND n.archived = 0
        """

        params: dict[str, Any] = {"query": query, "limit": fetch_limit}

        if content_type:
            sql += " AND n.type = :content_type"
            params["content_type"] = content_type

        if tag:
            sql += " AND n.id IN (SELECT node_id FROM node_tags WHERE tag = :tag)"
            params["tag"] = tag

        if space:
            sql += " AND n.path LIKE :space_prefix"
            params["space_prefix"] = f"{space}/%"

        sql += f" ORDER BY {order_clause} LIMIT :limit"

        with self._vault.engine.connect() as conn:
            rows = conn.execute(text(sql), params).fetchall()

        items = [
            {
                "id": r.id,
                "title": r.title,
                "type": r.type,
                "subtype": r.subtype,
                "status": r.status,
                "path": r.path,
                "created": r.created,
                "modified": r.modified,
                "pagerank": float(r.pagerank or 0.0),
                "score": float(r.score),
            }
            for r in rows
        ]

        warnings: list[str] = []

        if use_time_decay:
            half_life = self._vault.settings.search.half_life_days
            items = self._apply_time_decay(items, half_life=half_life, limit=limit)
        elif use_graph_rank:
            items, warnings = self._apply_graph_rank(items, limit=limit)

        # Round scores for final output and strip pagerank from response
        for item in items:
            item["score"] = round(item["score"], 4)
            item.pop("pagerank", None)

        result_kwargs: dict[str, Any] = {
            "ok": True,
            "op": "search",
            "data": {"query": query, "count": len(items), "items": items},
        }
        if warnings:
            result_kwargs["warnings"] = warnings
        return ServiceResult(**result_kwargs)

    def _apply_time_decay(
        self,
        items: list[dict[str, Any]],
        *,
        half_life: float,
        limit: int,
    ) -> list[dict[str, Any]]:
        """Re-rank search results by BM25 x time-decay.

        Combined score = abs(bm25) * exp(-age_days * ln(2) / half_life).
        BM25 scores are negative in FTS5 (more negative = more relevant),
        so we negate them to get positive relevance before applying decay.
        """
        now = datetime.now(UTC)
        decay_constant = math.log(2) / half_life

        for item in items:
            # Parse modified timestamp to compute age in days
            modified_str = item["modified"]
            try:
                modified_dt = datetime.fromisoformat(modified_str)
                if modified_dt.tzinfo is None:
                    modified_dt = modified_dt.replace(tzinfo=UTC)
                age_days = max((now - modified_dt).total_seconds() / 86400, 0.0)
            except (ValueError, TypeError):
                age_days = 0.0

            bm25_positive = abs(item["score"])
            decay_factor = math.exp(-age_days * decay_constant)
            item["score"] = round(bm25_positive * decay_factor, 4)

        items.sort(key=lambda x: x["score"], reverse=True)
        return items[:limit]

    def _apply_graph_rank(
        self,
        items: list[dict[str, Any]],
        *,
        limit: int,
    ) -> tuple[list[dict[str, Any]], list[str]]:
        """Re-rank search results by BM25 x PageRank.

        Combined score = abs(bm25) * pagerank.
        Falls back to pure BM25 if all pagerank values are 0.0.
        """
        warnings: list[str] = []

        all_zero = all(item.get("pagerank", 0.0) == 0.0 for item in items)
        if all_zero and items:
            warnings.append(
                "All pagerank values are 0.0 — run 'ztlctl graph materialize' first. "
                "Falling back to BM25 ranking."
            )
            # Fall back to pure BM25: negate to positive, sort desc
            for item in items:
                item["score"] = abs(item["score"])
            items.sort(key=lambda x: x["score"], reverse=True)
            return items[:limit], warnings

        for item in items:
            bm25_positive = abs(item["score"])
            pr = item.get("pagerank", 0.0)
            item["score"] = round(bm25_positive * pr, 4)

        items.sort(key=lambda x: x["score"], reverse=True)
        return items[:limit], warnings

    # ------------------------------------------------------------------
    # get — single item retrieval
    # ------------------------------------------------------------------

    @traced
    def get(self, content_id: str) -> ServiceResult:
        """Retrieve a single content item by ID.

        Returns the node metadata, tags, file body, and graph neighbors
        (outgoing and incoming links).
        """
        with self._vault.engine.connect() as conn:
            row = conn.execute(select(nodes).where(nodes.c.id == content_id)).first()
            if row is None:
                return ServiceResult(
                    ok=False,
                    op="get",
                    error=ServiceError(
                        code="NOT_FOUND",
                        message=f"No content found with ID '{content_id}'",
                    ),
                )

            # Tags
            tag_rows = conn.execute(
                select(node_tags.c.tag).where(node_tags.c.node_id == content_id)
            ).fetchall()
            item_tags = [t.tag for t in tag_rows]

            # Outgoing links
            out_rows = conn.execute(
                select(edges.c.target_id, edges.c.edge_type).where(edges.c.source_id == content_id)
            ).fetchall()
            links_out = [{"id": e.target_id, "edge_type": e.edge_type} for e in out_rows]

            # Incoming links
            in_rows = conn.execute(
                select(edges.c.source_id, edges.c.edge_type).where(edges.c.target_id == content_id)
            ).fetchall()
            links_in = [{"id": e.source_id, "edge_type": e.edge_type} for e in in_rows]

        # Read file body
        body = ""
        file_path = self._vault.root / row.path
        if file_path.exists():
            content = file_path.read_text(encoding="utf-8")
            _, body = parse_frontmatter(content)

        data: dict[str, Any] = {
            "id": row.id,
            "title": row.title,
            "type": row.type,
            "subtype": row.subtype,
            "status": row.status,
            "path": row.path,
            "topic": row.topic,
            "session": row.session,
            "created": row.created,
            "modified": row.modified,
            "tags": item_tags,
            "body": body,
            "links_out": links_out,
            "links_in": links_in,
        }

        return ServiceResult(ok=True, op="get", data=data)

    # ------------------------------------------------------------------
    # list_items — filtered listing
    # ------------------------------------------------------------------

    @traced
    def list_items(
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
    ) -> ServiceResult:
        """List content items with filters.

        Args:
            content_type: Filter by type (note, reference, task).
            status: Filter by status.
            tag: Filter by tag.
            topic: Filter by topic.
            subtype: Filter by subtype (e.g. decision).
            maturity: Filter by garden maturity (seed/budding/evergreen).
            space: Filter by vault space (notes, ops, self).
            since: Include items modified on or after this ISO date.
            include_archived: If True, include archived items.
            sort: Sort mode — "recency", "title", "type", or "priority".
            limit: Maximum results.
        """
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

        # Sort — priority sort fetches all rows for in-Python scoring
        if sort == "priority":
            pass
        elif sort == "title":
            stmt = stmt.order_by(nodes.c.title)
        elif sort == "type":
            stmt = stmt.order_by(nodes.c.type, nodes.c.modified.desc())
        else:  # recency (default)
            stmt = stmt.order_by(nodes.c.modified.desc())

        if sort != "priority":
            stmt = stmt.limit(limit)

        with self._vault.engine.connect() as conn:
            rows = conn.execute(stmt).fetchall()

        items = [
            {
                "id": r.id,
                "title": r.title,
                "type": r.type,
                "subtype": r.subtype,
                "maturity": r.maturity,
                "status": r.status,
                "path": r.path,
                "topic": r.topic,
                "created": r.created,
                "modified": r.modified,
            }
            for r in rows
        ]

        if sort == "priority":
            return self._apply_priority_sort(items, limit=limit)

        return ServiceResult(
            ok=True,
            op="list_items",
            data={"count": len(items), "items": items},
        )

    def _apply_priority_sort(
        self,
        items: list[dict[str, Any]],
        *,
        limit: int,
    ) -> ServiceResult:
        """Score items by priority and return sorted, limited results."""
        warnings: list[str] = []
        for item in items:
            if item["type"] == "task":
                file_path = self._vault.root / item["path"]
                priority, impact, effort = "medium", "medium", "medium"
                if file_path.exists():
                    content = file_path.read_text(encoding="utf-8")
                    fm, _ = parse_frontmatter(content)
                    priority = str(fm.get("priority", "medium"))
                    impact = str(fm.get("impact", "medium"))
                    effort = str(fm.get("effort", "medium"))
                else:
                    warnings.append(f"File missing for {item['id']}: {item['path']}")
                p = _PRIORITY_SCORES.get(priority, 2.0)
                i = _IMPACT_SCORES.get(impact, 2.0)
                e = _EFFORT_SCORES.get(effort, 2.0)
                item["score"] = round(p * 2 + i * 1.5 + (4 - e), 2)
            else:
                item["score"] = 0.0

        items.sort(key=lambda x: x["score"], reverse=True)
        items = items[:limit]

        return ServiceResult(
            ok=True,
            op="list_items",
            data={"count": len(items), "items": items},
            warnings=warnings,
        )

    # ------------------------------------------------------------------
    # work_queue — scored task prioritization
    # ------------------------------------------------------------------

    @traced
    def work_queue(self, *, space: str | None = None) -> ServiceResult:
        """Return prioritized task list using scoring formula.

        Score = priority*2 + impact*1.5 + (4 - effort).
        Only includes tasks in actionable statuses (inbox, active, blocked).

        Args:
            space: Filter by vault space (notes, ops, self).
        """
        with self._vault.engine.connect() as conn:
            # Read file content to extract priority/impact/effort from frontmatter
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
            rows = conn.execute(stmt).fetchall()

        tasks: list[dict[str, Any]] = []
        warnings: list[str] = []
        for row in rows:
            # Parse frontmatter to get priority/impact/effort
            priority = "medium"
            impact = "medium"
            effort = "medium"

            file_path = self._vault.root / row.path
            if file_path.exists():
                content = file_path.read_text(encoding="utf-8")
                fm, _ = parse_frontmatter(content)
                priority = str(fm.get("priority", "medium"))
                impact = str(fm.get("impact", "medium"))
                effort = str(fm.get("effort", "medium"))
            else:
                warnings.append(f"Task file missing for {row.id}: {row.path}")

            p_score = _PRIORITY_SCORES.get(priority, 2.0)
            i_score = _IMPACT_SCORES.get(impact, 2.0)
            e_score = _EFFORT_SCORES.get(effort, 2.0)
            score = p_score * 2 + i_score * 1.5 + (4 - e_score)

            tasks.append(
                {
                    "id": row.id,
                    "title": row.title,
                    "status": row.status,
                    "path": row.path,
                    "priority": priority,
                    "impact": impact,
                    "effort": effort,
                    "score": round(score, 2),
                    "created": row.created,
                    "modified": row.modified,
                }
            )

        # Sort by score descending (highest priority first)
        tasks.sort(key=lambda t: t["score"], reverse=True)

        return ServiceResult(
            ok=True,
            op="work_queue",
            data={"count": len(tasks), "items": tasks},
            warnings=warnings,
        )

    # ------------------------------------------------------------------
    # decision_support — aggregated decision context
    # ------------------------------------------------------------------

    @traced
    def decision_support(
        self, *, topic: str | None = None, space: str | None = None
    ) -> ServiceResult:
        """Aggregate notes, decisions, and references for a topic.

        Partitions relevant content into decisions, notes, and references
        to provide comprehensive context for decision-making.

        Args:
            topic: Filter by topic.
            space: Filter by vault space (notes, ops, self).
        """
        base_stmt = select(
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
            base_stmt = base_stmt.where(nodes.c.topic == topic)
        if space:
            base_stmt = base_stmt.where(nodes.c.path.like(f"{space}/%"))

        base_stmt = base_stmt.order_by(nodes.c.modified.desc())

        with self._vault.engine.connect() as conn:
            rows = conn.execute(base_stmt).fetchall()

        decisions: list[dict[str, Any]] = []
        notes_list: list[dict[str, Any]] = []
        references: list[dict[str, Any]] = []

        for r in rows:
            item: dict[str, Any] = {
                "id": r.id,
                "title": r.title,
                "type": r.type,
                "subtype": r.subtype,
                "status": r.status,
                "path": r.path,
                "topic": r.topic,
                "created": r.created,
                "modified": r.modified,
            }

            if r.subtype == "decision":
                decisions.append(item)
            elif r.type == "reference":
                references.append(item)
            else:
                notes_list.append(item)

        return ServiceResult(
            ok=True,
            op="decision_support",
            data={
                "topic": topic,
                "decisions": decisions,
                "notes": notes_list,
                "references": references,
                "counts": {
                    "decisions": len(decisions),
                    "notes": len(notes_list),
                    "references": len(references),
                },
            },
        )
