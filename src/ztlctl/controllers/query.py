"""QueryController — orchestration wrapper for QueryService."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ztlctl.controllers.base import BaseController

if TYPE_CHECKING:
    from ztlctl.services.result import ServiceResult


class QueryController(BaseController):
    """Thin wrapper over QueryService. All methods return ServiceResult."""

    def count_items(self, *, include_archived: bool = False) -> ServiceResult:
        """Return total indexed item count."""
        from ztlctl.services.query import QueryService

        return QueryService(self._vault).count_items(include_archived=include_archived)

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
        """Full-text search via FTS5 BM25."""
        from ztlctl.services.query import QueryService

        return QueryService(self._vault).search(
            query,
            content_type=content_type,
            tag=tag,
            space=space,
            rank_by=rank_by,
            limit=limit,
        )

    def get(self, content_id: str) -> ServiceResult:
        """Retrieve a single content item by ID."""
        from ztlctl.services.query import QueryService

        return QueryService(self._vault).get(content_id)

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
        """List content items with filters."""
        from ztlctl.services.query import QueryService

        return QueryService(self._vault).list_items(
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

    def work_queue(self, *, space: str | None = None) -> ServiceResult:
        """Return prioritized task list using scoring formula."""
        from ztlctl.services.query import QueryService

        return QueryService(self._vault).work_queue(space=space)

    def list_tags(self, *, prefix: str | None = None, limit: int = 100) -> ServiceResult:
        """List active tags with usage counts."""
        from ztlctl.services.query import QueryService

        return QueryService(self._vault).list_tags(prefix=prefix, limit=limit)

    def decision_support(
        self,
        *,
        topic: str | None = None,
        space: str | None = None,
    ) -> ServiceResult:
        """Aggregate notes, decisions, and references for a topic."""
        from ztlctl.services.query import QueryService

        return QueryService(self._vault).decision_support(topic=topic, space=space)

    def topic_packet(
        self,
        topic: str,
        *,
        mode: str = "learn",
        budget: int = 4000,
    ) -> ServiceResult:
        """Build a topic packet without requiring an active session."""
        from ztlctl.services.query import QueryService

        return QueryService(self._vault).topic_packet(topic, mode=mode, budget=budget)

    def draft_from_topic(
        self,
        topic: str,
        *,
        target: str = "note",
        mode: str = "learn",
        budget: int = 4000,
    ) -> ServiceResult:
        """Generate a draft note/task/decision from a topic packet."""
        from ztlctl.services.query import QueryService

        return QueryService(self._vault).draft_from_topic(
            topic, target=target, mode=mode, budget=budget
        )

    def vault_review(self, *, top: int = 10, stale_days: int = 7) -> ServiceResult:
        """Aggregate a review-ready snapshot of vault health and structure."""
        from ztlctl.services.query import QueryService

        return QueryService(self._vault).vault_review(top=top, stale_days=stale_days)
