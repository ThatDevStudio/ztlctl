"""ReweaveController — orchestration wrapper for ReweaveService."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ztlctl.controllers.base import BaseController

if TYPE_CHECKING:
    from ztlctl.services.result import ServiceResult


class ReweaveController(BaseController):
    """Thin wrapper over ReweaveService. All methods return ServiceResult."""

    def reweave(
        self,
        *,
        content_id: str | None = None,
        dry_run: bool = False,
        min_score_override: float | None = None,
    ) -> ServiceResult:
        """Run reweave on a specific item or the latest creation."""
        from ztlctl.services.reweave import ReweaveService

        return ReweaveService(self._vault).reweave(
            content_id=content_id,
            dry_run=dry_run,
            min_score_override=min_score_override,
        )

    def prune(
        self,
        *,
        content_id: str | None = None,
        dry_run: bool = False,
    ) -> ServiceResult:
        """Remove stale links that score below threshold."""
        from ztlctl.services.reweave import ReweaveService

        return ReweaveService(self._vault).prune(
            content_id=content_id,
            dry_run=dry_run,
        )

    def undo(self, *, reweave_id: int | None = None) -> ServiceResult:
        """Reverse a reweave operation via audit trail."""
        from ztlctl.services.reweave import ReweaveService

        return ReweaveService(self._vault).undo(reweave_id=reweave_id)
