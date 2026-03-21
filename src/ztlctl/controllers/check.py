"""CheckController — orchestration wrapper for CheckService."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ztlctl.controllers.base import BaseController

if TYPE_CHECKING:
    from ztlctl.services.result import ServiceResult


class CheckController(BaseController):
    """Thin wrapper over CheckService. All methods return ServiceResult."""

    def check(self, *, min_severity: str = "warning") -> ServiceResult:
        """Report integrity issues without modifying anything."""
        from ztlctl.services.check import CheckService
        from ztlctl.services.result import ServiceError, ServiceResult

        kwargs: dict[str, Any] = {"min_severity": min_severity}

        kwargs, rejection = self._dispatch_pre_action("check", kwargs)
        if rejection is not None:
            return ServiceResult(
                ok=False,
                op="check",
                error=ServiceError(
                    code="ACTION_REJECTED",
                    message=rejection.reason,
                    detail=rejection.detail,
                    recovery=f"Action rejected by plugin: {rejection.reason}",
                ),
            )

        result = CheckService(self._vault).check(min_severity=kwargs["min_severity"])
        return result

    def fix(self, *, level: str = "safe") -> ServiceResult:
        """Automatically repair issues. Level: 'safe' or 'aggressive'."""
        from ztlctl.services.check import CheckService
        from ztlctl.services.result import ServiceError, ServiceResult

        kwargs: dict[str, Any] = {"level": level}

        kwargs, rejection = self._dispatch_pre_action("fix", kwargs)
        if rejection is not None:
            return ServiceResult(
                ok=False,
                op="fix",
                error=ServiceError(
                    code="ACTION_REJECTED",
                    message=rejection.reason,
                    detail=rejection.detail,
                    recovery=f"Action rejected by plugin: {rejection.reason}",
                ),
            )

        result = CheckService(self._vault).fix(level=kwargs["level"])
        return result

    def rebuild(self) -> ServiceResult:
        """Full DB rebuild from filesystem (files are truth)."""
        from ztlctl.services.check import CheckService
        from ztlctl.services.result import ServiceError, ServiceResult

        kwargs: dict[str, Any] = {}

        kwargs, rejection = self._dispatch_pre_action("rebuild", kwargs)
        if rejection is not None:
            return ServiceResult(
                ok=False,
                op="rebuild",
                error=ServiceError(
                    code="ACTION_REJECTED",
                    message=rejection.reason,
                    detail=rejection.detail,
                    recovery=f"Action rejected by plugin: {rejection.reason}",
                ),
            )

        result = CheckService(self._vault).rebuild()
        return result

    def rollback(self) -> ServiceResult:
        """Restore DB from latest backup."""
        from ztlctl.services.check import CheckService
        from ztlctl.services.result import ServiceError, ServiceResult

        kwargs: dict[str, Any] = {}

        kwargs, rejection = self._dispatch_pre_action("rollback", kwargs)
        if rejection is not None:
            return ServiceResult(
                ok=False,
                op="rollback",
                error=ServiceError(
                    code="ACTION_REJECTED",
                    message=rejection.reason,
                    detail=rejection.detail,
                    recovery=f"Action rejected by plugin: {rejection.reason}",
                ),
            )

        result = CheckService(self._vault).rollback()
        return result
