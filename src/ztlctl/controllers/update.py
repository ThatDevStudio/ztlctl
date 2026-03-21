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

        kwargs: dict[str, Any] = {"content_id": content_id, "changes": changes}

        def _invoke(kw: dict[str, Any]) -> ServiceResult:
            return UpdateService(self._vault).update(kw["content_id"], changes=kw["changes"])

        return self._run_action("update", kwargs, _invoke)

    def archive(self, content_id: str) -> ServiceResult:
        """Archive a content item (soft delete, preserves edges)."""
        from ztlctl.services.update import UpdateService

        kwargs: dict[str, Any] = {"content_id": content_id}

        def _invoke(kw: dict[str, Any]) -> ServiceResult:
            return UpdateService(self._vault).archive(kw["content_id"])

        return self._run_action("archive", kwargs, _invoke)

    def supersede(self, old_id: str, new_id: str) -> ServiceResult:
        """Supersede a decision with a new one."""
        from ztlctl.services.update import UpdateService

        kwargs: dict[str, Any] = {"old_id": old_id, "new_id": new_id}

        def _invoke(kw: dict[str, Any]) -> ServiceResult:
            return UpdateService(self._vault).supersede(kw["old_id"], kw["new_id"])

        return self._run_action("supersede", kwargs, _invoke)
