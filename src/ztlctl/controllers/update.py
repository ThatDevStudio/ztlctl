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
        from ztlctl.services.result import ServiceError, ServiceResult
        from ztlctl.services.update import UpdateService

        kwargs: dict[str, Any] = {"content_id": content_id, "changes": changes}

        kwargs, rejection = self._dispatch_pre_action("update", kwargs)
        if rejection is not None:
            return ServiceResult(
                ok=False,
                op="update",
                error=ServiceError(
                    code="ACTION_REJECTED",
                    message=rejection.reason,
                    detail=rejection.detail,
                    recovery=f"Action rejected by plugin: {rejection.reason}",
                ),
            )

        result = UpdateService(self._vault).update(kwargs["content_id"], changes=kwargs["changes"])

        self._dispatch_post_action("update", kwargs, result)
        return result

    def archive(self, content_id: str) -> ServiceResult:
        """Archive a content item (soft delete, preserves edges)."""
        from ztlctl.services.result import ServiceError, ServiceResult
        from ztlctl.services.update import UpdateService

        kwargs: dict[str, Any] = {"content_id": content_id}

        kwargs, rejection = self._dispatch_pre_action("archive", kwargs)
        if rejection is not None:
            return ServiceResult(
                ok=False,
                op="archive",
                error=ServiceError(
                    code="ACTION_REJECTED",
                    message=rejection.reason,
                    detail=rejection.detail,
                    recovery=f"Action rejected by plugin: {rejection.reason}",
                ),
            )

        result = UpdateService(self._vault).archive(kwargs["content_id"])

        self._dispatch_post_action("archive", kwargs, result)
        return result

    def supersede(self, old_id: str, new_id: str) -> ServiceResult:
        """Supersede a decision with a new one."""
        from ztlctl.services.result import ServiceError, ServiceResult
        from ztlctl.services.update import UpdateService

        kwargs: dict[str, Any] = {"old_id": old_id, "new_id": new_id}

        kwargs, rejection = self._dispatch_pre_action("supersede", kwargs)
        if rejection is not None:
            return ServiceResult(
                ok=False,
                op="supersede",
                error=ServiceError(
                    code="ACTION_REJECTED",
                    message=rejection.reason,
                    detail=rejection.detail,
                    recovery=f"Action rejected by plugin: {rejection.reason}",
                ),
            )

        result = UpdateService(self._vault).supersede(kwargs["old_id"], kwargs["new_id"])

        self._dispatch_post_action("supersede", kwargs, result)
        return result
