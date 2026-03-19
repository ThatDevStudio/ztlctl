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
    ) -> ServiceResult:
        """Initialize Copier-backed workflow scaffolding for a vault."""
        from ztlctl.services.workflow import WorkflowService

        return WorkflowService.init_workflow(vault_root, choices)

    def update_workflow(
        self,
        vault_root: Path,
        *,
        choices: WorkflowChoices | None = None,
    ) -> ServiceResult:
        """Update workflow scaffolding using stored answers plus optional overrides."""
        from ztlctl.services.workflow import WorkflowService

        return WorkflowService.update_workflow(vault_root, choices=choices)

    def export_assets(
        self,
        vault_root: Path,
        *,
        client: WorkflowAssetClient = "both",
    ) -> ServiceResult:
        """Render portable client workflow assets into a vault."""
        from ztlctl.services.workflow import WorkflowService

        return WorkflowService.export_assets(vault_root, client=client)

    def validate_assets(
        self,
        vault_root: Path,
        *,
        client: WorkflowAssetClient = "both",
    ) -> ServiceResult:
        """Validate the packaged workflow spec and generated client assets."""
        from ztlctl.services.workflow import WorkflowService

        return WorkflowService.validate_assets(vault_root, client=client)

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
