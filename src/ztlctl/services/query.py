"""QueryService — structured retrieval and search.

Three surfaces: search, list/get, and agent-oriented queries.
(DESIGN.md Section 8)
"""

from __future__ import annotations

from ztlctl.services.result import ServiceResult


class QueryService:
    """Handles search, retrieval, and agent context queries."""

    def search(
        self,
        query: str,
        *,
        content_type: str | None = None,
        tag: str | None = None,
        rank_by: str = "relevance",
        limit: int = 20,
    ) -> ServiceResult:
        """Full-text search via FTS5 BM25."""
        raise NotImplementedError

    def get(self, content_id: str) -> ServiceResult:
        """Retrieve a single content item by ID."""
        raise NotImplementedError

    def list_items(
        self,
        *,
        content_type: str | None = None,
        status: str | None = None,
        tag: str | None = None,
        topic: str | None = None,
        sort: str = "recency",
        limit: int = 20,
    ) -> ServiceResult:
        """List content items with filters."""
        raise NotImplementedError

    def work_queue(self) -> ServiceResult:
        """Return prioritized task list using scoring formula."""
        raise NotImplementedError

    def decision_support(self, *, topic: str | None = None) -> ServiceResult:
        """Aggregate notes, decisions, and references for a topic."""
        raise NotImplementedError
