"""CheckController — orchestration wrapper for CheckService."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ztlctl.controllers.base import BaseController

if TYPE_CHECKING:
    from ztlctl.services.result import ServiceResult


class CheckController(BaseController):
    """Thin wrapper over CheckService. All methods return ServiceResult."""

    def check(self, *, min_severity: str = "warning") -> ServiceResult:
        """Report integrity issues without modifying anything."""
        from ztlctl.services.check import CheckService

        return CheckService(self._vault).check(min_severity=min_severity)

    def fix(self, *, level: str = "safe") -> ServiceResult:
        """Automatically repair issues. Level: 'safe' or 'aggressive'."""
        from ztlctl.services.check import CheckService

        return CheckService(self._vault).fix(level=level)

    def rebuild(self) -> ServiceResult:
        """Full DB rebuild from filesystem (files are truth)."""
        from ztlctl.services.check import CheckService

        return CheckService(self._vault).rebuild()

    def rollback(self) -> ServiceResult:
        """Restore DB from latest backup."""
        from ztlctl.services.check import CheckService

        return CheckService(self._vault).rollback()
