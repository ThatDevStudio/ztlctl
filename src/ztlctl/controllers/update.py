"""UpdateController — orchestration wrapper for UpdateService."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ztlctl.controllers.base import BaseController

if TYPE_CHECKING:
    from ztlctl.services.result import ServiceResult


class UpdateController(BaseController):
    """Thin wrapper over UpdateService. All methods return ServiceResult."""

    def update(self, content_id: str, *, changes: dict[str, Any]) -> ServiceResult:
        """Update a content item via the five-stage pipeline."""
        from ztlctl.services.update import UpdateService

        return UpdateService(self._vault).update(content_id, changes=changes)

    def archive(self, content_id: str) -> ServiceResult:
        """Archive a content item (soft delete, preserves edges)."""
        from ztlctl.services.update import UpdateService

        return UpdateService(self._vault).archive(content_id)

    def supersede(self, old_id: str, new_id: str) -> ServiceResult:
        """Supersede a decision with a new one."""
        from ztlctl.services.update import UpdateService

        return UpdateService(self._vault).supersede(old_id, new_id)
