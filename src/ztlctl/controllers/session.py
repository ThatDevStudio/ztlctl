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
        from ztlctl.services.result import ServiceError, ServiceResult
        from ztlctl.services.session import SessionService

        kwargs: dict[str, Any] = {"topic": topic}

        kwargs, rejection = self._dispatch_pre_action("start", kwargs)
        if rejection is not None:
            return ServiceResult(
                ok=False,
                op="start",
                error=ServiceError(
                    code="ACTION_REJECTED",
                    message=rejection.reason,
                    detail=rejection.detail,
                    recovery=f"Action rejected by plugin: {rejection.reason}",
                ),
            )

        result = SessionService(self._vault).start(kwargs["topic"])
        return result

    def close(self, *, summary: str | None = None) -> ServiceResult:
        """Close the active session with enrichment pipeline."""
        from ztlctl.services.result import ServiceError, ServiceResult
        from ztlctl.services.session import SessionService

        kwargs: dict[str, Any] = {"summary": summary}

        kwargs, rejection = self._dispatch_pre_action("close", kwargs)
        if rejection is not None:
            return ServiceResult(
                ok=False,
                op="close",
                error=ServiceError(
                    code="ACTION_REJECTED",
                    message=rejection.reason,
                    detail=rejection.detail,
                    recovery=f"Action rejected by plugin: {rejection.reason}",
                ),
            )

        result = SessionService(self._vault).close(summary=kwargs["summary"])
        return result

    def reopen(self, session_id: str) -> ServiceResult:
        """Reopen a previously closed session."""
        from ztlctl.services.result import ServiceError, ServiceResult
        from ztlctl.services.session import SessionService

        kwargs: dict[str, Any] = {"session_id": session_id}

        kwargs, rejection = self._dispatch_pre_action("reopen", kwargs)
        if rejection is not None:
            return ServiceResult(
                ok=False,
                op="reopen",
                error=ServiceError(
                    code="ACTION_REJECTED",
                    message=rejection.reason,
                    detail=rejection.detail,
                    recovery=f"Action rejected by plugin: {rejection.reason}",
                ),
            )

        result = SessionService(self._vault).reopen(kwargs["session_id"])
        return result

    def status(self) -> ServiceResult:
        """Return the active session summary, if any."""
        from ztlctl.services.result import ServiceError, ServiceResult
        from ztlctl.services.session import SessionService

        kwargs: dict[str, Any] = {}

        kwargs, rejection = self._dispatch_pre_action("status", kwargs)
        if rejection is not None:
            return ServiceResult(
                ok=False,
                op="status",
                error=ServiceError(
                    code="ACTION_REJECTED",
                    message=rejection.reason,
                    detail=rejection.detail,
                    recovery=f"Action rejected by plugin: {rejection.reason}",
                ),
            )

        result = SessionService(self._vault).status()
        return result

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
        from ztlctl.services.result import ServiceError, ServiceResult
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

        kwargs, rejection = self._dispatch_pre_action("log_entry", kwargs)
        if rejection is not None:
            return ServiceResult(
                ok=False,
                op="log_entry",
                error=ServiceError(
                    code="ACTION_REJECTED",
                    message=rejection.reason,
                    detail=rejection.detail,
                    recovery=f"Action rejected by plugin: {rejection.reason}",
                ),
            )

        result = SessionService(self._vault).log_entry(
            kwargs["message"],
            pin=kwargs["pin"],
            cost=kwargs["cost"],
            detail=kwargs["detail"],
            entry_type=kwargs["entry_type"],
            subtype=kwargs["subtype"],
            references=kwargs["references"],
            metadata=kwargs["metadata"],
        )
        return result

    def cost(self, *, report: int | None = None) -> ServiceResult:
        """Query or report accumulated token cost for the active session."""
        from ztlctl.services.result import ServiceError, ServiceResult
        from ztlctl.services.session import SessionService

        kwargs: dict[str, Any] = {"report": report}

        kwargs, rejection = self._dispatch_pre_action("cost", kwargs)
        if rejection is not None:
            return ServiceResult(
                ok=False,
                op="cost",
                error=ServiceError(
                    code="ACTION_REJECTED",
                    message=rejection.reason,
                    detail=rejection.detail,
                    recovery=f"Action rejected by plugin: {rejection.reason}",
                ),
            )

        result = SessionService(self._vault).cost(report=kwargs["report"])
        return result

    def context(
        self,
        *,
        topic: str | None = None,
        budget: int = 8000,
        ignore_checkpoints: bool = False,
    ) -> ServiceResult:
        """Build token-budgeted agent context payload."""
        from ztlctl.services.result import ServiceError, ServiceResult
        from ztlctl.services.session import SessionService

        kwargs: dict[str, Any] = {
            "topic": topic,
            "budget": budget,
            "ignore_checkpoints": ignore_checkpoints,
        }

        kwargs, rejection = self._dispatch_pre_action("context", kwargs)
        if rejection is not None:
            return ServiceResult(
                ok=False,
                op="context",
                error=ServiceError(
                    code="ACTION_REJECTED",
                    message=rejection.reason,
                    detail=rejection.detail,
                    recovery=f"Action rejected by plugin: {rejection.reason}",
                ),
            )

        result = SessionService(self._vault).context(
            topic=kwargs["topic"],
            budget=kwargs["budget"],
            ignore_checkpoints=kwargs["ignore_checkpoints"],
        )
        return result

    def brief(self) -> ServiceResult:
        """Quick orientation (delegates to ContextAssembler)."""
        from ztlctl.services.result import ServiceError, ServiceResult
        from ztlctl.services.session import SessionService

        kwargs: dict[str, Any] = {}

        kwargs, rejection = self._dispatch_pre_action("brief", kwargs)
        if rejection is not None:
            return ServiceResult(
                ok=False,
                op="brief",
                error=ServiceError(
                    code="ACTION_REJECTED",
                    message=rejection.reason,
                    detail=rejection.detail,
                    recovery=f"Action rejected by plugin: {rejection.reason}",
                ),
            )

        result = SessionService(self._vault).brief()
        return result

    def extract_decision(self, session_id: str, *, title: str | None = None) -> ServiceResult:
        """Extract a decision note from a session log's pinned/decision entries."""
        from ztlctl.services.result import ServiceError, ServiceResult
        from ztlctl.services.session import SessionService

        kwargs: dict[str, Any] = {"session_id": session_id, "title": title}

        kwargs, rejection = self._dispatch_pre_action("extract_decision", kwargs)
        if rejection is not None:
            return ServiceResult(
                ok=False,
                op="extract_decision",
                error=ServiceError(
                    code="ACTION_REJECTED",
                    message=rejection.reason,
                    detail=rejection.detail,
                    recovery=f"Action rejected by plugin: {rejection.reason}",
                ),
            )

        result = SessionService(self._vault).extract_decision(
            kwargs["session_id"], title=kwargs["title"]
        )
        return result
