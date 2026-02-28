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
from typing import TYPE_CHECKING, Any

from ztlctl.domain.content import parse_frontmatter
from ztlctl.infrastructure.repositories import QueryRepository
from ztlctl.services.base import BaseService
from ztlctl.services.contracts import ListItemsResultData, SearchResultData, dump_validated
from ztlctl.services.result import ServiceError, ServiceResult
from ztlctl.services.telemetry import traced

if TYPE_CHECKING:
    from ztlctl.infrastructure.vault import Vault

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

    def __init__(self, vault: Vault) -> None:
        """Initialize service with read repository."""
        super().__init__(vault)
        self._repo = QueryRepository(vault.engine)

    # ------------------------------------------------------------------
    # count_items — total items in index
    # ------------------------------------------------------------------

    @traced
    def count_items(self, *, include_archived: bool = False) -> ServiceResult:
        """Return total indexed item count."""
        count = self._repo.count_items(include_archived=include_archived)
        return ServiceResult(ok=True, op="count_items", data={"count": count})

    # ------------------------------------------------------------------
    # search — FTS5 full-text search
    # ------------------------------------------------------------------

    def _get_vector_service(self) -> Any:
        """Lazy-create VectorService for semantic search."""
        from ztlctl.services.vector import VectorService

        return VectorService(self._vault)

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
                "graph" (BM25*PageRank), "semantic" (vector cosine similarity),
                or "hybrid" (BM25 + cosine weighted merge).
            limit: Maximum results to return.
        """
        if not query.strip():
            return ServiceResult(
                ok=False,
                op="search",
                error=ServiceError(code="EMPTY_QUERY", message="Search query cannot be empty"),
            )

        # Recency/graph/hybrid modes: fetch more candidates for Python-side re-ranking
        use_time_decay = rank_by == "recency"
        use_graph_rank = rank_by == "graph"
        use_semantic = rank_by == "semantic"
        use_hybrid = rank_by == "hybrid"
        needs_rerank = use_time_decay or use_graph_rank or use_hybrid
        fetch_limit = min(limit * 3, 1000) if needs_rerank else limit

        warnings: list[str] = []

        # --- Pure semantic: skip FTS5, use vector search only ---
        if use_semantic:
            vec_svc = self._get_vector_service()
            if not vec_svc.is_available():
                warnings.append("Semantic search unavailable — falling back to FTS5")
                # Fall through: run FTS5 below
            else:
                vec_results: list[dict[str, Any]] = vec_svc.search_similar(query, limit=limit)
                items: list[dict[str, Any]] = []
                if vec_results:
                    node_ids = [r["node_id"] for r in vec_results]
                    meta_map = self._repo.get_nodes_metadata(node_ids)

                    for vr in vec_results:
                        nid = vr["node_id"]
                        if nid in meta_map:
                            r = meta_map[nid]
                            similarity = 1.0 - vr["distance"] / 2.0
                            items.append(
                                {
                                    "id": r["id"],
                                    "title": r["title"],
                                    "type": r["type"],
                                    "subtype": r["subtype"],
                                    "status": r["status"],
                                    "path": r["path"],
                                    "created": r["created"],
                                    "modified": r["modified"],
                                    "score": round(similarity, 4),
                                }
                            )

                result_kwargs: dict[str, Any] = {
                    "ok": True,
                    "op": "search",
                    "data": dump_validated(
                        SearchResultData,
                        {"query": query, "count": len(items), "items": items},
                    ),
                }
                if warnings:
                    result_kwargs["warnings"] = warnings
                return ServiceResult(**result_kwargs)

        # --- FTS5 query (used by relevance, recency, graph, hybrid, and fallback) ---
        rows = self._repo.search_fts_rows(
            query,
            content_type=content_type,
            tag=tag,
            space=space,
            limit=fetch_limit,
        )
        items = [
            {
                "id": row["id"],
                "title": row["title"],
                "type": row["type"],
                "subtype": row["subtype"],
                "status": row["status"],
                "path": row["path"],
                "created": row["created"],
                "modified": row["modified"],
                "pagerank": float(row.get("pagerank") or 0.0),
                "score": float(row["score"]),
            }
            for row in rows
        ]

        if use_time_decay:
            half_life = self._vault.settings.search.half_life_days
            items = self._apply_time_decay(items, half_life=half_life, limit=limit)
        elif use_graph_rank:
            items, warnings = self._apply_graph_rank(items, limit=limit)
        elif use_hybrid:
            vec_svc = self._get_vector_service()
            if not vec_svc.is_available():
                warnings.append("Semantic search unavailable — using FTS5 only")
            else:
                vec_results = vec_svc.search_similar(query, limit=fetch_limit)
                if vec_results:
                    w = self._vault.settings.search.semantic_weight
                    items = self._merge_hybrid_scores(items, vec_results, w, limit)

        # Round scores for final output and strip pagerank from response
        for item in items:
            item["score"] = round(item["score"], 4)
            item.pop("pagerank", None)

        result_kwargs = {
            "ok": True,
            "op": "search",
            "data": dump_validated(
                SearchResultData,
                {"query": query, "count": len(items), "items": items},
            ),
        }
        if warnings:
            result_kwargs["warnings"] = warnings
        return ServiceResult(**result_kwargs)

    @staticmethod
    def _merge_hybrid_scores(
        fts_items: list[dict[str, Any]],
        vec_results: list[dict[str, Any]],
        semantic_weight: float,
        limit: int,
    ) -> list[dict[str, Any]]:
        """Merge FTS5 BM25 and vector cosine scores with min-max normalization."""
        # Convert BM25 scores to positive (FTS5 BM25 is negative)
        bm25_scores = {item["id"]: abs(item["score"]) for item in fts_items}

        # Convert cosine distances to similarities
        vec_scores = {r["node_id"]: 1.0 - r["distance"] / 2.0 for r in vec_results}

        # Min-max normalize BM25 scores
        bm25_vals = list(bm25_scores.values())
        bm25_min = min(bm25_vals) if bm25_vals else 0.0
        bm25_max = max(bm25_vals) if bm25_vals else 1.0
        bm25_range = bm25_max - bm25_min or 1.0

        # Min-max normalize vector scores
        vec_vals = list(vec_scores.values())
        vec_min = min(vec_vals) if vec_vals else 0.0
        vec_max = max(vec_vals) if vec_vals else 1.0
        vec_range = vec_max - vec_min or 1.0

        # Merge: all IDs from both sets
        all_ids = set(bm25_scores.keys()) | set(vec_scores.keys())
        merged: dict[str, float] = {}
        for nid in all_ids:
            bm25_norm = (
                (bm25_scores.get(nid, 0.0) - bm25_min) / bm25_range if nid in bm25_scores else 0.0
            )
            vec_norm = (
                (vec_scores.get(nid, 0.0) - vec_min) / vec_range if nid in vec_scores else 0.0
            )
            merged[nid] = (1.0 - semantic_weight) * bm25_norm + semantic_weight * vec_norm

        # Re-rank FTS items by merged score, adding any vector-only results
        fts_map = {item["id"]: item for item in fts_items}
        result: list[dict[str, Any]] = []
        for nid, score in sorted(merged.items(), key=lambda x: x[1], reverse=True):
            if nid in fts_map:
                item = fts_map[nid].copy()
                item["score"] = score
                result.append(item)
            # Vector-only results need metadata — skip them for now
            # (they'd need a DB join like semantic mode does)

        return result[:limit]

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
        row = self._repo.get_node(content_id)
        if row is None:
            return ServiceResult(
                ok=False,
                op="get",
                error=ServiceError(
                    code="NOT_FOUND",
                    message=f"No content found with ID '{content_id}'",
                ),
            )

        item_tags = self._repo.get_node_tags(content_id)
        links_out = self._repo.get_outgoing_links(content_id)
        links_in = self._repo.get_incoming_links(content_id)

        # Read file body
        body = ""
        file_path = self._vault.root / str(row["path"])
        if file_path.exists():
            content = file_path.read_text(encoding="utf-8")
            _, body = parse_frontmatter(content)

        data: dict[str, Any] = {
            "id": row["id"],
            "title": row["title"],
            "type": row["type"],
            "subtype": row["subtype"],
            "status": row["status"],
            "maturity": row["maturity"],
            "path": row["path"],
            "topic": row["topic"],
            "session": row["session"],
            "created": row["created"],
            "modified": row["modified"],
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
        rows = self._repo.list_items_rows(
            content_type=content_type,
            status=status,
            tag=tag,
            topic=topic,
            subtype=subtype,
            maturity=maturity,
            space=space,
            since=since,
            include_archived=include_archived,
            sort=sort,
            limit=limit,
        )

        items = [
            {
                "id": r["id"],
                "title": r["title"],
                "type": r["type"],
                "subtype": r["subtype"],
                "maturity": r["maturity"],
                "status": r["status"],
                "path": r["path"],
                "topic": r["topic"],
                "created": r["created"],
                "modified": r["modified"],
            }
            for r in rows
        ]

        if sort == "priority":
            return self._apply_priority_sort(items, limit=limit)

        return ServiceResult(
            ok=True,
            op="list_items",
            data=dump_validated(ListItemsResultData, {"count": len(items), "items": items}),
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
            data=dump_validated(ListItemsResultData, {"count": len(items), "items": items}),
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
        rows = self._repo.work_queue_rows(space=space)

        tasks: list[dict[str, Any]] = []
        warnings: list[str] = []
        for row in rows:
            # Parse frontmatter to get priority/impact/effort
            priority = "medium"
            impact = "medium"
            effort = "medium"

            file_path = self._vault.root / str(row["path"])
            if file_path.exists():
                content = file_path.read_text(encoding="utf-8")
                fm, _ = parse_frontmatter(content)
                priority = str(fm.get("priority", "medium"))
                impact = str(fm.get("impact", "medium"))
                effort = str(fm.get("effort", "medium"))
            else:
                warnings.append(f"Task file missing for {row['id']}: {row['path']}")

            p_score = _PRIORITY_SCORES.get(priority, 2.0)
            i_score = _IMPACT_SCORES.get(impact, 2.0)
            e_score = _EFFORT_SCORES.get(effort, 2.0)
            score = p_score * 2 + i_score * 1.5 + (4 - e_score)

            tasks.append(
                {
                    "id": row["id"],
                    "title": row["title"],
                    "status": row["status"],
                    "path": row["path"],
                    "priority": priority,
                    "impact": impact,
                    "effort": effort,
                    "score": round(score, 2),
                    "created": row["created"],
                    "modified": row["modified"],
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
        rows = self._repo.decision_support_rows(topic=topic, space=space)

        decisions: list[dict[str, Any]] = []
        notes_list: list[dict[str, Any]] = []
        references: list[dict[str, Any]] = []

        for r in rows:
            item: dict[str, Any] = {
                "id": r["id"],
                "title": r["title"],
                "type": r["type"],
                "subtype": r["subtype"],
                "status": r["status"],
                "path": r["path"],
                "topic": r["topic"],
                "created": r["created"],
                "modified": r["modified"],
            }

            if r["subtype"] == "decision":
                decisions.append(item)
            elif r["type"] == "reference":
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
