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
        from ztlctl.services.result import ServiceError, ServiceResult

        kwargs: dict[str, Any] = {"include_archived": include_archived}

        kwargs, rejection = self._dispatch_pre_action("count_items", kwargs)
        if rejection is not None:
            return ServiceResult(
                ok=False,
                op="count_items",
                error=ServiceError(
                    code="ACTION_REJECTED",
                    message=rejection.reason,
                    detail=rejection.detail,
                    recovery=f"Action rejected by plugin: {rejection.reason}",
                ),
            )

        result = QueryService(self._vault).count_items(include_archived=kwargs["include_archived"])

        self._dispatch_post_action("count_items", kwargs, result)
        return result

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
        from ztlctl.services.result import ServiceError, ServiceResult

        kwargs: dict[str, Any] = {
            "query": query,
            "content_type": content_type,
            "tag": tag,
            "space": space,
            "rank_by": rank_by,
            "limit": limit,
        }

        kwargs, rejection = self._dispatch_pre_action("search", kwargs)
        if rejection is not None:
            return ServiceResult(
                ok=False,
                op="search",
                error=ServiceError(
                    code="ACTION_REJECTED",
                    message=rejection.reason,
                    detail=rejection.detail,
                    recovery=f"Action rejected by plugin: {rejection.reason}",
                ),
            )

        result = QueryService(self._vault).search(
            kwargs["query"],
            content_type=kwargs["content_type"],
            tag=kwargs["tag"],
            space=kwargs["space"],
            rank_by=kwargs["rank_by"],
            limit=kwargs["limit"],
        )

        self._dispatch_post_action("search", kwargs, result)
        return result

    def get(self, content_id: str) -> ServiceResult:
        """Retrieve a single content item by ID."""
        from ztlctl.services.query import QueryService
        from ztlctl.services.result import ServiceError, ServiceResult

        kwargs: dict[str, Any] = {"content_id": content_id}

        kwargs, rejection = self._dispatch_pre_action("get", kwargs)
        if rejection is not None:
            return ServiceResult(
                ok=False,
                op="get",
                error=ServiceError(
                    code="ACTION_REJECTED",
                    message=rejection.reason,
                    detail=rejection.detail,
                    recovery=f"Action rejected by plugin: {rejection.reason}",
                ),
            )

        result = QueryService(self._vault).get(kwargs["content_id"])

        self._dispatch_post_action("get", kwargs, result)
        return result

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
        from ztlctl.services.result import ServiceError, ServiceResult

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

        kwargs, rejection = self._dispatch_pre_action("list_items", kwargs)
        if rejection is not None:
            return ServiceResult(
                ok=False,
                op="list_items",
                error=ServiceError(
                    code="ACTION_REJECTED",
                    message=rejection.reason,
                    detail=rejection.detail,
                    recovery=f"Action rejected by plugin: {rejection.reason}",
                ),
            )

        result = QueryService(self._vault).list_items(
            content_type=kwargs["content_type"],
            status=kwargs["status"],
            tag=kwargs["tag"],
            topic=kwargs["topic"],
            subtype=kwargs["subtype"],
            maturity=kwargs["maturity"],
            space=kwargs["space"],
            since=kwargs["since"],
            include_archived=kwargs["include_archived"],
            sort=kwargs["sort"],
            limit=kwargs["limit"],
        )

        self._dispatch_post_action("list_items", kwargs, result)
        return result

    def work_queue(self, *, space: str | None = None) -> ServiceResult:
        """Return prioritized task list using scoring formula."""
        from ztlctl.services.query import QueryService
        from ztlctl.services.result import ServiceError, ServiceResult

        kwargs: dict[str, Any] = {"space": space}

        kwargs, rejection = self._dispatch_pre_action("work_queue", kwargs)
        if rejection is not None:
            return ServiceResult(
                ok=False,
                op="work_queue",
                error=ServiceError(
                    code="ACTION_REJECTED",
                    message=rejection.reason,
                    detail=rejection.detail,
                    recovery=f"Action rejected by plugin: {rejection.reason}",
                ),
            )

        result = QueryService(self._vault).work_queue(space=kwargs["space"])

        self._dispatch_post_action("work_queue", kwargs, result)
        return result

    def list_tags(self, *, prefix: str | None = None, limit: int = 100) -> ServiceResult:
        """List active tags with usage counts."""
        from ztlctl.services.query import QueryService
        from ztlctl.services.result import ServiceError, ServiceResult

        kwargs: dict[str, Any] = {"prefix": prefix, "limit": limit}

        kwargs, rejection = self._dispatch_pre_action("list_tags", kwargs)
        if rejection is not None:
            return ServiceResult(
                ok=False,
                op="list_tags",
                error=ServiceError(
                    code="ACTION_REJECTED",
                    message=rejection.reason,
                    detail=rejection.detail,
                    recovery=f"Action rejected by plugin: {rejection.reason}",
                ),
            )

        result = QueryService(self._vault).list_tags(prefix=kwargs["prefix"], limit=kwargs["limit"])

        self._dispatch_post_action("list_tags", kwargs, result)
        return result

    def decision_support(
        self,
        *,
        topic: str | None = None,
        space: str | None = None,
    ) -> ServiceResult:
        """Aggregate notes, decisions, and references for a topic."""
        from ztlctl.services.query import QueryService
        from ztlctl.services.result import ServiceError, ServiceResult

        kwargs: dict[str, Any] = {"topic": topic, "space": space}

        kwargs, rejection = self._dispatch_pre_action("decision_support", kwargs)
        if rejection is not None:
            return ServiceResult(
                ok=False,
                op="decision_support",
                error=ServiceError(
                    code="ACTION_REJECTED",
                    message=rejection.reason,
                    detail=rejection.detail,
                    recovery=f"Action rejected by plugin: {rejection.reason}",
                ),
            )

        result = QueryService(self._vault).decision_support(
            topic=kwargs["topic"], space=kwargs["space"]
        )

        self._dispatch_post_action("decision_support", kwargs, result)
        return result

    def topic_packet(
        self,
        topic: str,
        *,
        mode: str = "learn",
        budget: int = 4000,
    ) -> ServiceResult:
        """Build a topic packet without requiring an active session."""
        from ztlctl.services.query import QueryService
        from ztlctl.services.result import ServiceError, ServiceResult

        kwargs: dict[str, Any] = {"topic": topic, "mode": mode, "budget": budget}

        kwargs, rejection = self._dispatch_pre_action("topic_packet", kwargs)
        if rejection is not None:
            return ServiceResult(
                ok=False,
                op="topic_packet",
                error=ServiceError(
                    code="ACTION_REJECTED",
                    message=rejection.reason,
                    detail=rejection.detail,
                    recovery=f"Action rejected by plugin: {rejection.reason}",
                ),
            )

        result = QueryService(self._vault).topic_packet(
            kwargs["topic"], mode=kwargs["mode"], budget=kwargs["budget"]
        )

        self._dispatch_post_action("topic_packet", kwargs, result)
        return result

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
        from ztlctl.services.result import ServiceError, ServiceResult

        kwargs: dict[str, Any] = {
            "topic": topic,
            "target": target,
            "mode": mode,
            "budget": budget,
        }

        kwargs, rejection = self._dispatch_pre_action("draft_from_topic", kwargs)
        if rejection is not None:
            return ServiceResult(
                ok=False,
                op="draft_from_topic",
                error=ServiceError(
                    code="ACTION_REJECTED",
                    message=rejection.reason,
                    detail=rejection.detail,
                    recovery=f"Action rejected by plugin: {rejection.reason}",
                ),
            )

        result = QueryService(self._vault).draft_from_topic(
            kwargs["topic"],
            target=kwargs["target"],
            mode=kwargs["mode"],
            budget=kwargs["budget"],
        )

        self._dispatch_post_action("draft_from_topic", kwargs, result)
        return result

    def vault_review(self, *, top: int = 10, stale_days: int = 7) -> ServiceResult:
        """Aggregate a review-ready snapshot of vault health and structure."""
        from ztlctl.services.query import QueryService
        from ztlctl.services.result import ServiceError, ServiceResult

        kwargs: dict[str, Any] = {"top": top, "stale_days": stale_days}

        kwargs, rejection = self._dispatch_pre_action("vault_review", kwargs)
        if rejection is not None:
            return ServiceResult(
                ok=False,
                op="vault_review",
                error=ServiceError(
                    code="ACTION_REJECTED",
                    message=rejection.reason,
                    detail=rejection.detail,
                    recovery=f"Action rejected by plugin: {rejection.reason}",
                ),
            )

        result = QueryService(self._vault).vault_review(
            top=kwargs["top"], stale_days=kwargs["stale_days"]
        )

        self._dispatch_post_action("vault_review", kwargs, result)
        return result
