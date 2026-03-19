"""UpgradeController — orchestration wrapper for UpgradeService."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ztlctl.controllers.base import BaseController

if TYPE_CHECKING:
    from ztlctl.services.result import ServiceResult


class UpgradeController(BaseController):
    """Thin wrapper over UpgradeService. All methods return ServiceResult."""

    def check_pending(self) -> ServiceResult:
        """List pending migrations without applying."""
        from ztlctl.services.upgrade import UpgradeService

        return UpgradeService(self._vault).check_pending()

    def apply(self) -> ServiceResult:
        """BACKUP → MIGRATE → VALIDATE → REPORT pipeline."""
        from ztlctl.services.upgrade import UpgradeService

        return UpgradeService(self._vault).apply()

    def stamp_current(self) -> ServiceResult:
        """Stamp DB as at current head (for freshly created DBs)."""
        from ztlctl.services.upgrade import UpgradeService

        return UpgradeService(self._vault).stamp_current()
