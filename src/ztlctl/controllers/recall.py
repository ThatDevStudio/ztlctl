"""RecallController — orchestration wrapper for RecallService."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ztlctl.controllers.base import BaseController

if TYPE_CHECKING:
    from ztlctl.services.result import ServiceResult


class RecallController(BaseController):
    """Thin wrapper over RecallService. All methods return ServiceResult."""

    def recall_temporal(
        self,
        *,
        from_date: str | None = None,
        to_date: str | None = None,
    ) -> ServiceResult:
        """Return sessions filtered by date range with per-session summaries."""
        from ztlctl.services.recall import RecallService

        kwargs: dict[str, Any] = {"from_date": from_date, "to_date": to_date}

        def _invoke(kw: dict[str, Any]) -> ServiceResult:
            return RecallService(self._vault).recall_temporal(
                from_date=kw["from_date"],
                to_date=kw["to_date"],
            )

        return self._run_action("recall_temporal", kwargs, _invoke)

    def recall_topic(self, query: str) -> ServiceResult:
        """Return sessions whose log entries match a text query."""
        from ztlctl.services.recall import RecallService

        kwargs: dict[str, Any] = {"query": query}

        def _invoke(kw: dict[str, Any]) -> ServiceResult:
            return RecallService(self._vault).recall_topic(kw["query"])

        return self._run_action("recall_topic", kwargs, _invoke)

    def recall_topology(self, *, limit: int = 10) -> ServiceResult:
        """Return most-connected notes across sessions (stub for Plan 02)."""
        from ztlctl.services.recall import RecallService

        kwargs: dict[str, Any] = {"limit": limit}

        def _invoke(kw: dict[str, Any]) -> ServiceResult:
            return RecallService(self._vault).recall_topology(limit=kw["limit"])

        return self._run_action("recall_topology", kwargs, _invoke)
