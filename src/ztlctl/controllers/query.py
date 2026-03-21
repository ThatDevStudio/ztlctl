"""QueryController — orchestration wrapper for QueryService."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ztlctl.controllers.base import BaseController

if TYPE_CHECKING:
    from ztlctl.services.result import ServiceResult


class QueryController(BaseController):
    """Thin wrapper over QueryService. All methods return ServiceResult."""

    def count_items(self, *, include_archived: bool = False) -> ServiceResult:
        """Return total indexed item count."""
        from ztlctl.services.query import QueryService

        kwargs: dict[str, Any] = {"include_archived": include_archived}

        def _invoke(kw: dict[str, Any]) -> ServiceResult:
            return QueryService(self._vault).count_items(include_archived=kw["include_archived"])

        return self._run_action("count_items", kwargs, _invoke)

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

        kwargs: dict[str, Any] = {
            "query": query,
            "content_type": content_type,
            "tag": tag,
            "space": space,
            "rank_by": rank_by,
            "limit": limit,
        }

        def _invoke(kw: dict[str, Any]) -> ServiceResult:
            return QueryService(self._vault).search(
                kw["query"],
                content_type=kw["content_type"],
                tag=kw["tag"],
                space=kw["space"],
                rank_by=kw["rank_by"],
                limit=kw["limit"],
            )

        return self._run_action("search", kwargs, _invoke)

    def get(self, content_id: str) -> ServiceResult:
        """Retrieve a single content item by ID."""
        from ztlctl.services.query import QueryService

        kwargs: dict[str, Any] = {"content_id": content_id}

        def _invoke(kw: dict[str, Any]) -> ServiceResult:
            return QueryService(self._vault).get(kw["content_id"])

        return self._run_action("get", kwargs, _invoke)

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

        kwargs: dict[str, Any] = {
            "content_type": content_type,
            "status": status,
            "tag": tag,
            "topic": topic,
            "subtype": subtype,
            "maturity": maturity,
            "space": space,
            "since": since,
            "include_archived": include_archived,
            "sort": sort,
            "limit": limit,
        }

        def _invoke(kw: dict[str, Any]) -> ServiceResult:
            return QueryService(self._vault).list_items(
                content_type=kw["content_type"],
                status=kw["status"],
                tag=kw["tag"],
                topic=kw["topic"],
                subtype=kw["subtype"],
                maturity=kw["maturity"],
                space=kw["space"],
                since=kw["since"],
                include_archived=kw["include_archived"],
                sort=kw["sort"],
                limit=kw["limit"],
            )

        return self._run_action("list_items", kwargs, _invoke)

    def work_queue(self, *, space: str | None = None) -> ServiceResult:
        """Return prioritized task list using scoring formula."""
        from ztlctl.services.query import QueryService

        kwargs: dict[str, Any] = {"space": space}

        def _invoke(kw: dict[str, Any]) -> ServiceResult:
            return QueryService(self._vault).work_queue(space=kw["space"])

        return self._run_action("work_queue", kwargs, _invoke)

    def list_tags(self, *, prefix: str | None = None, limit: int = 100) -> ServiceResult:
        """List active tags with usage counts."""
        from ztlctl.services.query import QueryService

        kwargs: dict[str, Any] = {"prefix": prefix, "limit": limit}

        def _invoke(kw: dict[str, Any]) -> ServiceResult:
            return QueryService(self._vault).list_tags(prefix=kw["prefix"], limit=kw["limit"])

        return self._run_action("list_tags", kwargs, _invoke)

    def decision_support(
        self,
        *,
        topic: str | None = None,
        space: str | None = None,
    ) -> ServiceResult:
        """Aggregate notes, decisions, and references for a topic."""
        from ztlctl.services.query import QueryService

        kwargs: dict[str, Any] = {"topic": topic, "space": space}

        def _invoke(kw: dict[str, Any]) -> ServiceResult:
            return QueryService(self._vault).decision_support(
                topic=kw["topic"], space=kw["space"]
            )

        return self._run_action("decision_support", kwargs, _invoke)

    def topic_packet(
        self,
        topic: str,
        *,
        mode: str = "learn",
        budget: int = 4000,
    ) -> ServiceResult:
        """Build a topic packet without requiring an active session."""
        from ztlctl.services.query import QueryService

        kwargs: dict[str, Any] = {"topic": topic, "mode": mode, "budget": budget}

        def _invoke(kw: dict[str, Any]) -> ServiceResult:
            return QueryService(self._vault).topic_packet(
                kw["topic"], mode=kw["mode"], budget=kw["budget"]
            )

        return self._run_action("topic_packet", kwargs, _invoke)

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

        kwargs: dict[str, Any] = {
            "topic": topic,
            "target": target,
            "mode": mode,
            "budget": budget,
        }

        def _invoke(kw: dict[str, Any]) -> ServiceResult:
            return QueryService(self._vault).draft_from_topic(
                kw["topic"],
                target=kw["target"],
                mode=kw["mode"],
                budget=kw["budget"],
            )

        return self._run_action("draft_from_topic", kwargs, _invoke)

    def vault_review(self, *, top: int = 10, stale_days: int = 7) -> ServiceResult:
        """Aggregate a review-ready snapshot of vault health and structure."""
        from ztlctl.services.query import QueryService

        kwargs: dict[str, Any] = {"top": top, "stale_days": stale_days}

        def _invoke(kw: dict[str, Any]) -> ServiceResult:
            return QueryService(self._vault).vault_review(
                top=kw["top"], stale_days=kw["stale_days"]
            )

        return self._run_action("vault_review", kwargs, _invoke)
