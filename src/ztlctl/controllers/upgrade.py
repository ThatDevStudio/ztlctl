"""UpgradeController — orchestration wrapper for UpgradeService."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ztlctl.controllers.base import BaseController

if TYPE_CHECKING:
    from ztlctl.services.result import ServiceResult


class UpgradeController(BaseController):
    """Thin wrapper over UpgradeService. All methods return ServiceResult."""

    def check_pending(self) -> ServiceResult:
        """List pending migrations without applying."""
        from ztlctl.services.result import ServiceError, ServiceResult
        from ztlctl.services.upgrade import UpgradeService

        kwargs: dict[str, Any] = {}

        kwargs, rejection = self._dispatch_pre_action("check_pending", kwargs)
        if rejection is not None:
            return ServiceResult(
                ok=False,
                op="check_pending",
                error=ServiceError(
                    code="ACTION_REJECTED",
                    message=rejection.reason,
                    detail=rejection.detail,
                    recovery=f"Action rejected by plugin: {rejection.reason}",
                ),
            )

        result = UpgradeService(self._vault).check_pending()
        return result

    def apply(self) -> ServiceResult:
        """BACKUP → MIGRATE → VALIDATE → REPORT pipeline."""
        from ztlctl.services.result import ServiceError, ServiceResult
        from ztlctl.services.upgrade import UpgradeService

        kwargs: dict[str, Any] = {}

        kwargs, rejection = self._dispatch_pre_action("apply", kwargs)
        if rejection is not None:
            return ServiceResult(
                ok=False,
                op="apply",
                error=ServiceError(
                    code="ACTION_REJECTED",
                    message=rejection.reason,
                    detail=rejection.detail,
                    recovery=f"Action rejected by plugin: {rejection.reason}",
                ),
            )

        result = UpgradeService(self._vault).apply()
        return result

    def stamp_current(self) -> ServiceResult:
        """Stamp DB as at current head (for freshly created DBs)."""
        from ztlctl.services.result import ServiceError, ServiceResult
        from ztlctl.services.upgrade import UpgradeService

        kwargs: dict[str, Any] = {}

        kwargs, rejection = self._dispatch_pre_action("stamp_current", kwargs)
        if rejection is not None:
            return ServiceResult(
                ok=False,
                op="stamp_current",
                error=ServiceError(
                    code="ACTION_REJECTED",
                    message=rejection.reason,
                    detail=rejection.detail,
                    recovery=f"Action rejected by plugin: {rejection.reason}",
                ),
            )

        result = UpgradeService(self._vault).stamp_current()
        return result
