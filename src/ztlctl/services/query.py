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
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ztlctl.domain.content import parse_frontmatter
from ztlctl.infrastructure.repositories import QueryRepository
from ztlctl.services.base import BaseService
from ztlctl.services.contracts import (
    ListItemsResultData,
    ListTagsResultData,
    SearchResultData,
    TopicDraftData,
    TopicPacketData,
    VaultReviewResultData,
    dump_validated,
)
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
_MATURITY_SCORES: dict[str, float] = {"seed": 0.4, "budding": 0.7, "evergreen": 1.0}


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

    @staticmethod
    def _list_item_from_row(row: dict[str, Any]) -> dict[str, Any]:
        """Normalize a repository row to the list-item payload shape."""
        return {
            "id": row["id"],
            "title": row["title"],
            "type": row["type"],
            "subtype": row.get("subtype"),
            "maturity": row.get("maturity"),
            "status": row["status"],
            "path": row["path"],
            "topic": row.get("topic"),
            "created": row["created"],
            "modified": row["modified"],
        }

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
                "hybrid" (BM25 + cosine weighted merge), "review" (topic review
                prioritization), or "garden" (enrichment prioritization).
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
        use_review_rank = rank_by == "review"
        use_garden_rank = rank_by == "garden"
        needs_rerank = (
            use_time_decay or use_graph_rank or use_hybrid or use_review_rank or use_garden_rank
        )
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
                                    "maturity": r.get("maturity"),
                                    "status": r["status"],
                                    "path": r["path"],
                                    "topic": r.get("topic"),
                                    "created": r["created"],
                                    "modified": r["modified"],
                                    "score": round(similarity, 4),
                                }
                            )

                annotated_items = self._annotate_search_items(items, mode="semantic")
                result_kwargs: dict[str, Any] = {
                    "ok": True,
                    "op": "search",
                    "data": dump_validated(
                        SearchResultData,
                        {"query": query, "count": len(annotated_items), "items": annotated_items},
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
                "maturity": row.get("maturity"),
                "status": row["status"],
                "path": row["path"],
                "topic": row.get("topic"),
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
                    items, merge_warnings = self._merge_hybrid_results(items, vec_results, w, limit)
                    warnings.extend(merge_warnings)
        elif use_review_rank:
            items = self._apply_enrichment_rank(items, mode="review", limit=limit)
        elif use_garden_rank:
            items = self._apply_enrichment_rank(items, mode="garden", limit=limit)

        # Round scores for final output and strip pagerank from response
        for item in items:
            item["score"] = round(item["score"], 4)
            item.pop("pagerank", None)

        items = self._annotate_search_items(items, mode=rank_by)

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
    def _hybrid_score_map(
        fts_items: list[dict[str, Any]],
        vec_results: list[dict[str, Any]],
        semantic_weight: float,
    ) -> dict[str, float]:
        """Compute merged hybrid scores for FTS and vector results."""
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
        return merged

    @staticmethod
    def _merge_hybrid_scores(
        fts_items: list[dict[str, Any]],
        vec_results: list[dict[str, Any]],
        semantic_weight: float,
        limit: int,
    ) -> list[dict[str, Any]]:
        """Merge FTS5 BM25 and vector cosine scores for existing FTS hits only."""
        merged = QueryService._hybrid_score_map(fts_items, vec_results, semantic_weight)
        result: list[dict[str, Any]] = []
        for item in fts_items:
            updated = item.copy()
            updated["score"] = merged.get(item["id"], 0.0)
            result.append(updated)
        result.sort(key=lambda candidate: candidate["score"], reverse=True)
        return result[:limit]

    def _merge_hybrid_results(
        self,
        fts_items: list[dict[str, Any]],
        vec_results: list[dict[str, Any]],
        semantic_weight: float,
        limit: int,
    ) -> tuple[list[dict[str, Any]], list[str]]:
        """Merge FTS and vector scores, including vector-only hits with metadata."""
        merged = self._hybrid_score_map(fts_items, vec_results, semantic_weight)
        fts_map = {item["id"]: item for item in fts_items}
        result: list[dict[str, Any]] = []
        warnings: list[str] = []
        vec_only_ids = [nid for nid in merged if nid not in fts_map]
        meta_map = self._repo.get_nodes_metadata(vec_only_ids) if vec_only_ids else {}
        for nid, score in sorted(merged.items(), key=lambda x: x[1], reverse=True):
            if nid in fts_map:
                item = fts_map[nid].copy()
                item["score"] = score
                result.append(item)
                continue

            meta = meta_map.get(nid)
            if meta is None:
                warnings.append(f"Skipping semantic-only hit without metadata: {nid}")
                continue
            result.append(
                {
                    "id": meta["id"],
                    "title": meta["title"],
                    "type": meta["type"],
                    "subtype": meta["subtype"],
                    "maturity": meta.get("maturity"),
                    "status": meta["status"],
                    "path": meta["path"],
                    "topic": meta.get("topic"),
                    "created": meta["created"],
                    "modified": meta["modified"],
                    "score": score,
                }
            )

        return result[:limit], warnings

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

    def _apply_enrichment_rank(
        self,
        items: list[dict[str, Any]],
        *,
        mode: str,
        limit: int,
    ) -> list[dict[str, Any]]:
        """Re-rank items for review or garden-oriented workflows."""
        if not items:
            return []

        signals = self._build_enrichment_signals(items)
        raw_scores = [abs(float(item.get("score", 0.0))) for item in items]
        raw_max = max(raw_scores) or 1.0

        for item in items:
            item_id = str(item.get("id", ""))
            signal = signals.get(item_id, {})
            lexical = abs(float(item.get("score", 0.0))) / raw_max
            staleness = float(signal.get("staleness", 0.0))
            graph_gap = float(signal.get("graph_gap", 0.0))
            bridge_value = float(signal.get("bridge_value", 0.0))
            provenance_support = float(signal.get("provenance_support", 0.0))
            maturity = float(signal.get("maturity_score", 0.0))

            if mode == "review":
                item["score"] = (
                    0.35 * lexical + 0.30 * staleness + 0.20 * graph_gap + 0.15 * bridge_value
                )
            else:
                item["score"] = (
                    0.30 * lexical
                    + 0.25 * provenance_support
                    + 0.20 * maturity
                    + 0.15 * bridge_value
                    + 0.10 * staleness
                )

        items.sort(key=lambda candidate: candidate["score"], reverse=True)
        return items[:limit]

    def _annotate_search_items(
        self,
        items: list[dict[str, Any]],
        *,
        mode: str,
    ) -> list[dict[str, Any]]:
        """Attach reusable ranking explanations to search-like result rows."""
        if not items:
            return []

        signals = self._build_enrichment_signals(items)
        annotated: list[dict[str, Any]] = []
        for item in items:
            updated = item.copy()
            updated["ranking"] = self._ranking_explanation_for_item(updated, mode, signals)
            annotated.append(updated)
        return annotated

    def _build_enrichment_signals(self, items: list[dict[str, Any]]) -> dict[str, dict[str, float]]:
        """Collect normalized enrichment signals for ranked items."""
        node_ids = [str(item.get("id", "")) for item in items if item.get("id")]
        repo_signals = self._repo.get_node_signal_rows(node_ids)

        features_map: dict[str, dict[str, float]] = {}
        for item in items:
            item_id = str(item.get("id", ""))
            path = item.get("path")
            file_features = self._content_features(path) if isinstance(path, str) else {}
            signal_row = repo_signals.get(item_id, {})
            outgoing = float(signal_row.get("outgoing_count", 0.0) or 0.0)
            incoming = float(signal_row.get("incoming_count", 0.0) or 0.0)
            total_edges = outgoing + incoming
            age_days = self._age_days(item.get("modified"))
            staleness = min(age_days / 30.0, 1.0)
            graph_gap = 1.0 / (1.0 + total_edges)
            bridge_value = min((total_edges / 6.0), 1.0)
            provenance_support = min(
                (
                    float(file_features.get("provenance_count", 0.0))
                    + float(file_features.get("excerpt_count", 0.0))
                    + float(file_features.get("key_point_count", 0.0))
                )
                / 6.0,
                1.0,
            )
            maturity_name = (
                str(item.get("maturity") or signal_row.get("maturity") or "").strip().lower()
            )
            maturity_score = _MATURITY_SCORES.get(maturity_name, 0.0)
            features_map[item_id] = {
                "age_days": age_days,
                "staleness": staleness,
                "graph_gap": graph_gap,
                "bridge_value": bridge_value,
                "provenance_support": provenance_support,
                "maturity_score": maturity_score,
                "provenance_count": float(file_features.get("provenance_count", 0.0)),
                "excerpt_count": float(file_features.get("excerpt_count", 0.0)),
                "key_point_count": float(file_features.get("key_point_count", 0.0)),
            }
        return features_map

    def _ranking_explanation_for_item(
        self,
        item: dict[str, Any],
        mode: str,
        signals: dict[str, dict[str, float]],
    ) -> dict[str, Any]:
        """Render a compact explanation payload for a ranked item."""
        item_id = str(item.get("id", ""))
        signal = signals.get(item_id, {})
        reasons: list[str] = []
        signal_values = {
            "score": round(float(item.get("score", 0.0)), 4),
            "staleness": round(float(signal.get("staleness", 0.0)), 4),
            "graph_gap": round(float(signal.get("graph_gap", 0.0)), 4),
            "bridge_value": round(float(signal.get("bridge_value", 0.0)), 4),
            "provenance_support": round(float(signal.get("provenance_support", 0.0)), 4),
            "maturity_score": round(float(signal.get("maturity_score", 0.0)), 4),
        }

        if mode in {"relevance", "semantic", "hybrid"}:
            reasons.append("Strong query match.")
        if mode == "recency":
            reasons.append("Recent activity boosted this result.")
        if mode == "graph":
            reasons.append("Graph centrality boosted this result.")
        if mode == "review":
            if signal_values["staleness"] >= 0.4:
                reasons.append("Item is stale enough to review.")
            if signal_values["graph_gap"] >= 0.3:
                reasons.append("Sparse graph context makes this a review candidate.")
        if mode == "garden":
            if signal_values["provenance_support"] >= 0.3:
                reasons.append("Source-backed evidence makes this useful for enrichment.")
            if signal_values["maturity_score"] > 0.0:
                reasons.append("Garden maturity increases enrichment value.")
        if signal_values["bridge_value"] >= 0.5:
            reasons.append("Graph position suggests bridging potential.")
        if not reasons:
            reasons.append("Selected by ranking heuristics.")

        return {"mode": mode, "reasons": reasons, "signals": signal_values}

    @staticmethod
    def _section_map(markdown: str) -> dict[str, str]:
        """Split markdown into second-level sections."""
        sections: dict[str, list[str]] = {}
        current: str | None = None
        for line in markdown.splitlines():
            if line.startswith("## "):
                current = line[3:].strip()
                sections.setdefault(current, [])
                continue
            if current is not None:
                sections[current].append(line)
        return {name: "\n".join(lines).strip() for name, lines in sections.items()}

    def _content_features(self, relative_path: str) -> dict[str, float]:
        """Extract lightweight enrichment features from a markdown file."""
        path = self._vault.root / Path(relative_path)
        if not path.is_file():
            return {}

        try:
            raw = path.read_text(encoding="utf-8")
            frontmatter, body = parse_frontmatter(raw)
        except Exception:
            return {}

        sections = self._section_map(body)
        key_points = frontmatter.get("key_points", [])
        if not isinstance(key_points, list):
            key_points = []
        if not key_points:
            key_points = [
                line.strip().lstrip("- ").strip()
                for line in sections.get("Key Points", "").splitlines()
                if line.strip().startswith("-")
            ]
        provenance_lines = [
            line
            for line in sections.get("Provenance", "").splitlines()
            if line.strip().startswith("-")
        ]
        excerpt_lines = [
            line
            for line in sections.get("Excerpts", "").splitlines()
            if line.strip().startswith(">")
        ]
        return {
            "provenance_count": float(len(provenance_lines)),
            "excerpt_count": float(len(excerpt_lines)),
            "key_point_count": float(len(key_points)),
        }

    @staticmethod
    def _age_days(timestamp: Any) -> float:
        """Compute age in days from an ISO timestamp-like value."""
        if timestamp is None:
            return 0.0
        try:
            dt = datetime.fromisoformat(str(timestamp))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=UTC)
        except ValueError:
            return 0.0
        return max((datetime.now(UTC) - dt).total_seconds() / 86400, 0.0)

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
        frontmatter: dict[str, Any] = {}
        file_path = self._vault.root / str(row["path"])
        if file_path.exists():
            content = file_path.read_text(encoding="utf-8")
            frontmatter, body = parse_frontmatter(content)

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
            "source_kind": frontmatter.get("source_kind"),
            "modalities": frontmatter.get("modalities", []),
            "capture_agent": frontmatter.get("capture_agent"),
            "capture_method": frontmatter.get("capture_method"),
            "citations": frontmatter.get("citations", []),
            "artifacts": frontmatter.get("artifacts", []),
            "source_bundle_path": frontmatter.get("source_bundle_path"),
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

        items = [self._list_item_from_row(r) for r in rows]

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

    @traced
    def list_tags(self, *, prefix: str | None = None, limit: int = 100) -> ServiceResult:
        """List active tags with usage counts."""
        rows = self._repo.list_tags_rows(prefix=prefix, limit=limit)
        items = [
            {
                "tag": row["tag"],
                "count": int(row["count"]),
                "domain": row["domain"],
                "scope": row["scope"],
            }
            for row in rows
        ]
        return ServiceResult(
            ok=True,
            op="list_tags",
            data=dump_validated(ListTagsResultData, {"count": len(items), "items": items}),
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

    @traced
    def topic_packet(
        self,
        topic: str,
        *,
        mode: str = "learn",
        budget: int = 4000,
    ) -> ServiceResult:
        """Build a topic packet without requiring an active session."""
        if mode not in {"learn", "review", "decision"}:
            return ServiceResult(
                ok=False,
                op="topic_packet",
                error=ServiceError(
                    code="VALIDATION_FAILED",
                    message=f"Unsupported topic packet mode: {mode}",
                ),
            )

        from ztlctl.services.context import ContextAssembler

        result = ContextAssembler(self._vault).build_topic_packet(topic, mode=mode, budget=budget)
        if not result.ok:
            return result
        return ServiceResult(
            ok=True,
            op="topic_packet",
            data=dump_validated(TopicPacketData, result.data),
            warnings=result.warnings,
        )

    @traced
    def draft_from_topic(
        self,
        topic: str,
        *,
        target: str = "note",
        mode: str = "learn",
        budget: int = 4000,
    ) -> ServiceResult:
        """Generate a draft note/task/decision from a topic packet."""
        if target not in {"note", "task", "decision"}:
            return ServiceResult(
                ok=False,
                op="draft_from_topic",
                error=ServiceError(
                    code="VALIDATION_FAILED",
                    message=f"Unsupported draft target: {target}",
                ),
            )

        packet_result = self.topic_packet(topic, mode=mode, budget=budget)
        if not packet_result.ok:
            return packet_result

        packet = packet_result.data
        source_items = [
            *packet.get("references", []),
            *packet.get("notes", []),
            *packet.get("decisions", []),
        ]
        unique_sources: list[dict[str, Any]] = []
        seen: set[str] = set()
        for item in source_items:
            item_id = str(item.get("id", ""))
            if not item_id or item_id in seen:
                continue
            seen.add(item_id)
            unique_sources.append(
                {
                    "id": item_id,
                    "title": str(item.get("title", item_id)),
                    "type": str(item.get("type", "note")),
                    "path": item.get("path"),
                }
            )

        title, body = self._draft_body(topic, target=target, mode=mode, packet=packet)
        return ServiceResult(
            ok=True,
            op="draft_from_topic",
            data=dump_validated(
                TopicDraftData,
                {
                    "topic": topic,
                    "mode": mode,
                    "target": target,
                    "title": title,
                    "body": body,
                    "sources": unique_sources[:8],
                    "packet": packet,
                },
            ),
            warnings=packet_result.warnings,
        )

    @staticmethod
    def _draft_body(
        topic: str,
        *,
        target: str,
        mode: str,
        packet: dict[str, Any],
    ) -> tuple[str, str]:
        """Build a simple structured draft from a topic packet."""
        evidence = packet.get("evidence", [])[:5]
        actions = packet.get("suggested_actions", [])[:5]
        notes = packet.get("notes", [])[:5]
        decisions = packet.get("decisions", [])[:5]

        if target == "task":
            title = f"Review {topic}"
            lines = [
                f"# {title}",
                "",
                "## Why",
                f"- Review packet mode: {mode}",
            ]
            if actions:
                lines.extend(["", "## Actions"])
                for action in actions:
                    lines.append(f"- {action['title']}: {action['rationale']}")
            if evidence:
                lines.extend(["", "## Evidence"])
                for item in evidence:
                    lines.append(f"- {item['title']}: {item['text']}")
            return title, "\n".join(lines).strip() + "\n"

        if target == "decision":
            title = f"Decision: {topic}"
            lines = [
                f"# {title}",
                "",
                "## Context",
                f"- Topic packet mode: {mode}",
            ]
            if evidence:
                lines.append("- Evidence available from packet references and notes.")
            lines.extend(
                [
                    "",
                    "## Choice",
                    "- TODO: record the preferred option.",
                    "",
                    "## Rationale",
                ]
            )
            for item in evidence[:3]:
                lines.append(f"- {item['title']}: {item['text']}")
            lines.extend(
                [
                    "",
                    "## Alternatives",
                    "- TODO: document alternatives.",
                    "",
                    "## Consequences",
                    "- TODO: document likely consequences.",
                ]
            )
            return title, "\n".join(lines).strip() + "\n"

        title = f"{topic.title()} synthesis"
        lines = [
            f"# {title}",
            "",
            "## Summary",
            f"- Topic packet mode: {mode}",
        ]
        for item in notes[:3]:
            lines.append(f"- {item['title']}")
        lines.extend(["", "## Evidence"])
        if evidence:
            for item in evidence:
                lines.append(f"- {item['title']}: {item['text']}")
        else:
            lines.append("- No evidence excerpts captured yet.")
        if decisions:
            lines.extend(["", "## Related Decisions"])
            for item in decisions[:3]:
                lines.append(f"- {item['title']}")
        if actions:
            lines.extend(["", "## Next Actions"])
            for action in actions:
                lines.append(f"- {action['title']}: {action['rationale']}")
        return title, "\n".join(lines).strip() + "\n"

    @traced
    def vault_review(self, *, top: int = 10, stale_days: int = 7) -> ServiceResult:
        """Aggregate a review-ready snapshot of vault health and structure."""
        from datetime import UTC, timedelta

        from ztlctl.services.graph import GraphService

        recent_result = self.list_items(sort="recency", limit=top)
        recent_items = recent_result.data.get("items", []) if recent_result.ok else []

        work_result = self.work_queue()
        work_items = work_result.data.get("items", []) if work_result.ok else []

        theme_result = GraphService(self._vault).themes()
        themes = theme_result.data.get("communities", []) if theme_result.ok else []

        gaps_result = GraphService(self._vault).gaps(top=top)
        gaps = gaps_result.data.get("items", []) if gaps_result.ok else []

        bridges_result = GraphService(self._vault).bridges(top=top)
        bridges = bridges_result.data.get("items", []) if bridges_result.ok else []

        rank_result = GraphService(self._vault).rank(top=top)
        important_items = rank_result.data.get("items", []) if rank_result.ok else []

        cutoff_iso = (datetime.now(UTC) - timedelta(days=stale_days)).date().isoformat()
        stale_rows = self._repo.stale_seed_rows(cutoff_iso=cutoff_iso, limit=top)
        orphan_rows = self._repo.orphan_note_rows(limit=top)

        overview = {
            "vault_name": self._vault.settings.vault.name,
            "counts": self._repo.type_counts(),
            "total": self._repo.count_items(),
            "recent": recent_items,
        }

        payload = dump_validated(
            VaultReviewResultData,
            {
                "overview": overview,
                "recent": recent_items,
                "work_queue": work_items,
                "themes": themes,
                "gaps": gaps,
                "bridges": bridges,
                "important_items": important_items,
                "stale_seeds": [self._list_item_from_row(row) for row in stale_rows],
                "orphan_notes": [self._list_item_from_row(row) for row in orphan_rows],
            },
        )

        warnings = [
            *recent_result.warnings,
            *work_result.warnings,
            *theme_result.warnings,
            *gaps_result.warnings,
            *bridges_result.warnings,
            *rank_result.warnings,
        ]
        return ServiceResult(ok=True, op="vault_review", data=payload, warnings=warnings)
