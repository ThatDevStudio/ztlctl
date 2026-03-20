"""VectorController — orchestration wrapper for VectorService."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ztlctl.controllers.base import BaseController

if TYPE_CHECKING:
    from ztlctl.services.result import ServiceResult


class VectorController(BaseController):
    """Thin wrapper over VectorService. All methods return ServiceResult."""

    def status(self) -> ServiceResult:
        """Check semantic search availability and index status."""
        from ztlctl.services.result import ServiceResult
        from ztlctl.services.vector import VectorService

        svc = VectorService(self._vault)
        available = svc.is_available()
        data: dict[str, object] = {"available": available}
        if available:
            data["message"] = "Semantic search is available"
        else:
            data["message"] = (
                "Semantic search unavailable — install sqlite-vec and sentence-transformers"
            )
        return ServiceResult(ok=True, op="vector_status", data=data)

    def reindex_all(self) -> ServiceResult:
        """Re-embed all non-archived nodes."""
        from ztlctl.services.vector import VectorService

        return VectorService(self._vault).reindex_all()
