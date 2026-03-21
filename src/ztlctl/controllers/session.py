"""SessionController — orchestration wrapper for SessionService."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ztlctl.controllers.base import BaseController

if TYPE_CHECKING:
    from ztlctl.services.result import ServiceResult


class SessionController(BaseController):
    """Thin wrapper over SessionService. All methods return ServiceResult."""

    def start(self, topic: str) -> ServiceResult:
        """Start a new session, returning the LOG-NNNN id."""
        from ztlctl.services.session import SessionService

        kwargs: dict[str, Any] = {"topic": topic}

        def _invoke(kw: dict[str, Any]) -> ServiceResult:
            return SessionService(self._vault).start(kw["topic"])

        return self._run_action("start", kwargs, _invoke)

    def close(self, *, summary: str | None = None) -> ServiceResult:
        """Close the active session with enrichment pipeline."""
        from ztlctl.services.session import SessionService

        kwargs: dict[str, Any] = {"summary": summary}

        def _invoke(kw: dict[str, Any]) -> ServiceResult:
            return SessionService(self._vault).close(summary=kw["summary"])

        return self._run_action("close", kwargs, _invoke)

    def reopen(self, session_id: str) -> ServiceResult:
        """Reopen a previously closed session."""
        from ztlctl.services.session import SessionService

        kwargs: dict[str, Any] = {"session_id": session_id}

        def _invoke(kw: dict[str, Any]) -> ServiceResult:
            return SessionService(self._vault).reopen(kw["session_id"])

        return self._run_action("reopen", kwargs, _invoke)

    def status(self) -> ServiceResult:
        """Return the active session summary, if any."""
        from ztlctl.services.session import SessionService

        kwargs: dict[str, Any] = {}

        def _invoke(kw: dict[str, Any]) -> ServiceResult:
            return SessionService(self._vault).status()

        return self._run_action("status", kwargs, _invoke)

    def log_entry(
        self,
        message: str,
        *,
        pin: bool = False,
        cost: int = 0,
        detail: str | None = None,
        entry_type: str = "log_entry",
        subtype: str | None = None,
        references: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ServiceResult:
        """Append a log entry to the active session."""
        from ztlctl.services.session import SessionService

        kwargs: dict[str, Any] = {
            "message": message,
            "pin": pin,
            "cost": cost,
            "detail": detail,
            "entry_type": entry_type,
            "subtype": subtype,
            "references": references,
            "metadata": metadata,
        }

        def _invoke(kw: dict[str, Any]) -> ServiceResult:
            return SessionService(self._vault).log_entry(
                kw["message"],
                pin=kw["pin"],
                cost=kw["cost"],
                detail=kw["detail"],
                entry_type=kw["entry_type"],
                subtype=kw["subtype"],
                references=kw["references"],
                metadata=kw["metadata"],
            )

        return self._run_action("log_entry", kwargs, _invoke)

    def cost(self, *, report: int | None = None) -> ServiceResult:
        """Query or report accumulated token cost for the active session."""
        from ztlctl.services.session import SessionService

        kwargs: dict[str, Any] = {"report": report}

        def _invoke(kw: dict[str, Any]) -> ServiceResult:
            return SessionService(self._vault).cost(report=kw["report"])

        return self._run_action("cost", kwargs, _invoke)

    def context(
        self,
        *,
        topic: str | None = None,
        budget: int = 8000,
        ignore_checkpoints: bool = False,
    ) -> ServiceResult:
        """Build token-budgeted agent context payload."""
        from ztlctl.services.session import SessionService

        kwargs: dict[str, Any] = {
            "topic": topic,
            "budget": budget,
            "ignore_checkpoints": ignore_checkpoints,
        }

        def _invoke(kw: dict[str, Any]) -> ServiceResult:
            return SessionService(self._vault).context(
                topic=kw["topic"],
                budget=kw["budget"],
                ignore_checkpoints=kw["ignore_checkpoints"],
            )

        return self._run_action("context", kwargs, _invoke)

    def brief(self) -> ServiceResult:
        """Quick orientation (delegates to ContextAssembler)."""
        from ztlctl.services.session import SessionService

        kwargs: dict[str, Any] = {}

        def _invoke(kw: dict[str, Any]) -> ServiceResult:
            return SessionService(self._vault).brief()

        return self._run_action("brief", kwargs, _invoke)

    def extract_decision(self, session_id: str, *, title: str | None = None) -> ServiceResult:
        """Extract a decision note from a session log's pinned/decision entries."""
        from ztlctl.services.session import SessionService

        kwargs: dict[str, Any] = {"session_id": session_id, "title": title}

        def _invoke(kw: dict[str, Any]) -> ServiceResult:
            return SessionService(self._vault).extract_decision(kw["session_id"], title=kw["title"])

        return self._run_action("extract_decision", kwargs, _invoke)
