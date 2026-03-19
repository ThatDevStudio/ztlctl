"""VectorController — orchestration wrapper for VectorService."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ztlctl.controllers.base import BaseController

if TYPE_CHECKING:
    from ztlctl.services.result import ServiceResult


class VectorController(BaseController):
    """Thin wrapper over VectorService. All methods return ServiceResult."""

    def reindex_all(self) -> ServiceResult:
        """Re-embed all non-archived nodes."""
        from ztlctl.services.vector import VectorService

        return VectorService(self._vault).reindex_all()
