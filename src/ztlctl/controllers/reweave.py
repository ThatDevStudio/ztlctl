"""ReweaveController — orchestration wrapper for ReweaveService."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

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

        kwargs: dict[str, Any] = {
            "content_id": content_id,
            "dry_run": dry_run,
            "min_score_override": min_score_override,
        }

        def _invoke(kw: dict[str, Any]) -> ServiceResult:
            return ReweaveService(self._vault).reweave(
                content_id=kw["content_id"],
                dry_run=kw["dry_run"],
                min_score_override=kw["min_score_override"],
            )

        return self._run_action("reweave", kwargs, _invoke)

    def prune(
        self,
        *,
        content_id: str | None = None,
        dry_run: bool = False,
    ) -> ServiceResult:
        """Remove stale links that score below threshold."""
        from ztlctl.services.reweave import ReweaveService

        kwargs: dict[str, Any] = {"content_id": content_id, "dry_run": dry_run}

        def _invoke(kw: dict[str, Any]) -> ServiceResult:
            return ReweaveService(self._vault).prune(
                content_id=kw["content_id"],
                dry_run=kw["dry_run"],
            )

        return self._run_action("prune", kwargs, _invoke)

    def undo(self, *, reweave_id: int | None = None) -> ServiceResult:
        """Reverse a reweave operation via audit trail."""
        from ztlctl.services.reweave import ReweaveService

        kwargs: dict[str, Any] = {"reweave_id": reweave_id}

        def _invoke(kw: dict[str, Any]) -> ServiceResult:
            return ReweaveService(self._vault).undo(reweave_id=kw["reweave_id"])

        return self._run_action("undo", kwargs, _invoke)
