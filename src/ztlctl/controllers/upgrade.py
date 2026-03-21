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
        from ztlctl.services.upgrade import UpgradeService

        kwargs: dict[str, Any] = {}

        def _invoke(kw: dict[str, Any]) -> ServiceResult:
            return UpgradeService(self._vault).check_pending()

        return self._run_action("check_pending", kwargs, _invoke)

    def apply(self) -> ServiceResult:
        """BACKUP → MIGRATE → VALIDATE → REPORT pipeline."""
        from ztlctl.services.upgrade import UpgradeService

        kwargs: dict[str, Any] = {}

        def _invoke(kw: dict[str, Any]) -> ServiceResult:
            return UpgradeService(self._vault).apply()

        return self._run_action("apply", kwargs, _invoke)

    def stamp_current(self) -> ServiceResult:
        """Stamp DB as at current head (for freshly created DBs)."""
        from ztlctl.services.upgrade import UpgradeService

        kwargs: dict[str, Any] = {}

        def _invoke(kw: dict[str, Any]) -> ServiceResult:
            return UpgradeService(self._vault).stamp_current()

        return self._run_action("stamp_current", kwargs, _invoke)
