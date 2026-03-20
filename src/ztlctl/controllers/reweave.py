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
        from ztlctl.services.result import ServiceError, ServiceResult
        from ztlctl.services.reweave import ReweaveService

        kwargs: dict[str, Any] = {
            "content_id": content_id,
            "dry_run": dry_run,
            "min_score_override": min_score_override,
        }

        kwargs, rejection = self._dispatch_pre_action("reweave", kwargs)
        if rejection is not None:
            return ServiceResult(
                ok=False,
                op="reweave",
                error=ServiceError(
                    code="ACTION_REJECTED",
                    message=rejection.reason,
                    detail=rejection.detail,
                    recovery=f"Action rejected by plugin: {rejection.reason}",
                ),
            )

        result = ReweaveService(self._vault).reweave(
            content_id=kwargs["content_id"],
            dry_run=kwargs["dry_run"],
            min_score_override=kwargs["min_score_override"],
        )

        self._dispatch_post_action("reweave", kwargs, result)
        return result

    def prune(
        self,
        *,
        content_id: str | None = None,
        dry_run: bool = False,
    ) -> ServiceResult:
        """Remove stale links that score below threshold."""
        from ztlctl.services.result import ServiceError, ServiceResult
        from ztlctl.services.reweave import ReweaveService

        kwargs: dict[str, Any] = {"content_id": content_id, "dry_run": dry_run}

        kwargs, rejection = self._dispatch_pre_action("prune", kwargs)
        if rejection is not None:
            return ServiceResult(
                ok=False,
                op="prune",
                error=ServiceError(
                    code="ACTION_REJECTED",
                    message=rejection.reason,
                    detail=rejection.detail,
                    recovery=f"Action rejected by plugin: {rejection.reason}",
                ),
            )

        result = ReweaveService(self._vault).prune(
            content_id=kwargs["content_id"],
            dry_run=kwargs["dry_run"],
        )

        self._dispatch_post_action("prune", kwargs, result)
        return result

    def undo(self, *, reweave_id: int | None = None) -> ServiceResult:
        """Reverse a reweave operation via audit trail."""
        from ztlctl.services.result import ServiceError, ServiceResult
        from ztlctl.services.reweave import ReweaveService

        kwargs: dict[str, Any] = {"reweave_id": reweave_id}

        kwargs, rejection = self._dispatch_pre_action("undo", kwargs)
        if rejection is not None:
            return ServiceResult(
                ok=False,
                op="undo",
                error=ServiceError(
                    code="ACTION_REJECTED",
                    message=rejection.reason,
                    detail=rejection.detail,
                    recovery=f"Action rejected by plugin: {rejection.reason}",
                ),
            )

        result = ReweaveService(self._vault).undo(reweave_id=kwargs["reweave_id"])

        self._dispatch_post_action("undo", kwargs, result)
        return result
