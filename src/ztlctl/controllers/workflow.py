"""WorkflowController — orchestration wrapper for WorkflowService."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from ztlctl.controllers.base import BaseController

if TYPE_CHECKING:
    from ztlctl.services.result import ServiceResult
    from ztlctl.services.workflow import WorkflowAssetClient, WorkflowChoices


class WorkflowController(BaseController):
    """Thin wrapper over WorkflowService (static methods).

    WorkflowService uses static methods that operate on vault_root: Path
    rather than on a Vault instance. This controller extends BaseController
    for consistency but passes vault_root explicitly.
    """

    def init_workflow(
        self,
        vault_root: Path,
        choices: WorkflowChoices,
        *,
        force_trust: bool = False,
    ) -> ServiceResult:
        """Initialize Copier-backed workflow scaffolding for a vault."""
        from ztlctl.services.result import ServiceError, ServiceResult
        from ztlctl.services.workflow import WorkflowService

        kwargs: dict[str, Any] = {
            "vault_root": vault_root,
            "choices": choices,
            "force_trust": force_trust,
        }

        kwargs, rejection = self._dispatch_pre_action("init_workflow", kwargs)
        if rejection is not None:
            return ServiceResult(
                ok=False,
                op="init_workflow",
                error=ServiceError(
                    code="ACTION_REJECTED",
                    message=rejection.reason,
                    detail=rejection.detail,
                    recovery=f"Action rejected by plugin: {rejection.reason}",
                ),
            )

        result = WorkflowService.init_workflow(
            kwargs["vault_root"], kwargs["choices"], force_trust=kwargs["force_trust"]
        )

        self._dispatch_post_action("init_workflow", kwargs, result)
        return result

    def update_workflow(
        self,
        vault_root: Path,
        *,
        choices: WorkflowChoices | None = None,
        force_trust: bool = False,
    ) -> ServiceResult:
        """Update workflow scaffolding using stored answers plus optional overrides."""
        from ztlctl.services.result import ServiceError, ServiceResult
        from ztlctl.services.workflow import WorkflowService

        kwargs: dict[str, Any] = {
            "vault_root": vault_root,
            "choices": choices,
            "force_trust": force_trust,
        }

        kwargs, rejection = self._dispatch_pre_action("update_workflow", kwargs)
        if rejection is not None:
            return ServiceResult(
                ok=False,
                op="update_workflow",
                error=ServiceError(
                    code="ACTION_REJECTED",
                    message=rejection.reason,
                    detail=rejection.detail,
                    recovery=f"Action rejected by plugin: {rejection.reason}",
                ),
            )

        result = WorkflowService.update_workflow(
            kwargs["vault_root"],
            choices=kwargs["choices"],
            force_trust=kwargs["force_trust"],
        )

        self._dispatch_post_action("update_workflow", kwargs, result)
        return result

    def export_assets(
        self,
        vault_root: Path,
        *,
        client: WorkflowAssetClient = "both",
    ) -> ServiceResult:
        """Render portable client workflow assets into a vault."""
        from ztlctl.services.result import ServiceError, ServiceResult
        from ztlctl.services.workflow import WorkflowService

        kwargs: dict[str, Any] = {"vault_root": vault_root, "client": client}

        kwargs, rejection = self._dispatch_pre_action("export_assets", kwargs)
        if rejection is not None:
            return ServiceResult(
                ok=False,
                op="export_assets",
                error=ServiceError(
                    code="ACTION_REJECTED",
                    message=rejection.reason,
                    detail=rejection.detail,
                    recovery=f"Action rejected by plugin: {rejection.reason}",
                ),
            )

        result = WorkflowService.export_assets(kwargs["vault_root"], client=kwargs["client"])

        self._dispatch_post_action("export_assets", kwargs, result)
        return result

    def validate_assets(
        self,
        vault_root: Path,
        *,
        client: WorkflowAssetClient = "both",
    ) -> ServiceResult:
        """Validate the packaged workflow spec and generated client assets."""
        from ztlctl.services.result import ServiceError, ServiceResult
        from ztlctl.services.workflow import WorkflowService

        kwargs: dict[str, Any] = {"vault_root": vault_root, "client": client}

        kwargs, rejection = self._dispatch_pre_action("validate_assets", kwargs)
        if rejection is not None:
            return ServiceResult(
                ok=False,
                op="validate_assets",
                error=ServiceError(
                    code="ACTION_REJECTED",
                    message=rejection.reason,
                    detail=rejection.detail,
                    recovery=f"Action rejected by plugin: {rejection.reason}",
                ),
            )

        result = WorkflowService.validate_assets(kwargs["vault_root"], client=kwargs["client"])

        self._dispatch_post_action("validate_assets", kwargs, result)
        return result

    def read_answers(self, vault_root: Path) -> WorkflowChoices | None:
        """Read the stored workflow answers file if present."""
        from ztlctl.services.workflow import WorkflowService

        return WorkflowService.read_answers(vault_root)

    def profile_choices(self, vault_root: Path) -> list[str]:
        """Return installed profile ids visible to a vault-scoped workflow command."""
        from ztlctl.services.workflow import WorkflowService

        return WorkflowService.profile_choices(vault_root)

    def default_choices(self, *, profile: str | None = None) -> Any:
        """Return the default workflow selection set."""
        from ztlctl.services.workflow import WorkflowService

        if profile is not None:
            return WorkflowService.default_choices(profile=profile)
        return WorkflowService.default_choices()
