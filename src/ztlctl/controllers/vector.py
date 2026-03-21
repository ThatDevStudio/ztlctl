"""VectorController — orchestration wrapper for VectorService."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ztlctl.controllers.base import BaseController

if TYPE_CHECKING:
    from ztlctl.services.result import ServiceResult


class VectorController(BaseController):
    """Thin wrapper over VectorService. All methods return ServiceResult."""

    def status(self) -> ServiceResult:
        """Check semantic search availability and index status."""
        from ztlctl.services.result import ServiceError, ServiceResult
        from ztlctl.services.vector import VectorService

        kwargs: dict[str, Any] = {}

        kwargs, rejection = self._dispatch_pre_action("vector_status", kwargs)
        if rejection is not None:
            return ServiceResult(
                ok=False,
                op="vector_status",
                error=ServiceError(
                    code="ACTION_REJECTED",
                    message=rejection.reason,
                    detail=rejection.detail,
                    recovery=f"Action rejected by plugin: {rejection.reason}",
                ),
            )

        svc = VectorService(self._vault)
        available = svc.is_available()
        data: dict[str, object] = {"available": available}
        if available:
            data["message"] = "Semantic search is available"
        else:
            data["message"] = (
                "Semantic search unavailable — install sqlite-vec and sentence-transformers"
            )
        result = ServiceResult(ok=True, op="vector_status", data=data)
        return result

    def reindex_all(self) -> ServiceResult:
        """Re-embed all non-archived nodes."""
        from ztlctl.services.result import ServiceError, ServiceResult
        from ztlctl.services.vector import VectorService

        kwargs: dict[str, Any] = {}

        kwargs, rejection = self._dispatch_pre_action("reindex_all", kwargs)
        if rejection is not None:
            return ServiceResult(
                ok=False,
                op="reindex_all",
                error=ServiceError(
                    code="ACTION_REJECTED",
                    message=rejection.reason,
                    detail=rejection.detail,
                    recovery=f"Action rejected by plugin: {rejection.reason}",
                ),
            )

        result = VectorService(self._vault).reindex_all()
        return result
