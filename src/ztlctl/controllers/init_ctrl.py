"""InitController — orchestration wrapper for InitService.

Named init_ctrl.py to avoid shadowing the __init__.py module.
InitService uses static methods that operate on a vault_root Path (init_vault)
or accept a Vault instance directly (regenerate_self, check_staleness).
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from ztlctl.controllers.base import BaseController

if TYPE_CHECKING:
    from ztlctl.services.result import ServiceResult


class InitController(BaseController):
    """Thin wrapper over InitService (static methods).

    init_vault takes an explicit vault_root; regenerate_self and check_staleness
    use self._vault from BaseController.
    """

    def init_vault(
        self,
        path: Path,
        *,
        name: str,
        profile: str | None = None,
        client: str | None = None,
        tone: str = "research-partner",
        topics: list[str] | None = None,
        no_workflow: bool = False,
    ) -> ServiceResult:
        """Create a new ztlctl vault at path."""
        from ztlctl.services.init import InitService
        from ztlctl.services.result import ServiceError, ServiceResult

        kwargs: dict[str, Any] = {
            "path": path,
            "name": name,
            "profile": profile,
            "client": client,
            "tone": tone,
            "topics": topics,
            "no_workflow": no_workflow,
        }

        kwargs, rejection = self._dispatch_pre_action("init_vault", kwargs)
        if rejection is not None:
            return ServiceResult(
                ok=False,
                op="init_vault",
                error=ServiceError(
                    code="ACTION_REJECTED",
                    message=rejection.reason,
                    detail=rejection.detail,
                    recovery=f"Action rejected by plugin: {rejection.reason}",
                ),
            )

        result = InitService.init_vault(
            kwargs["path"],
            name=kwargs["name"],
            profile=kwargs["profile"],
            client=kwargs["client"],
            tone=kwargs["tone"],
            topics=kwargs["topics"],
            no_workflow=kwargs["no_workflow"],
        )
        return result

    def regenerate_self(self) -> ServiceResult:
        """Re-render self/ files from current vault settings."""
        from ztlctl.services.init import InitService
        from ztlctl.services.result import ServiceError, ServiceResult

        kwargs: dict[str, Any] = {}

        kwargs, rejection = self._dispatch_pre_action("regenerate_self", kwargs)
        if rejection is not None:
            return ServiceResult(
                ok=False,
                op="regenerate_self",
                error=ServiceError(
                    code="ACTION_REJECTED",
                    message=rejection.reason,
                    detail=rejection.detail,
                    recovery=f"Action rejected by plugin: {rejection.reason}",
                ),
            )

        result = InitService.regenerate_self(self._vault)
        return result

    def check_staleness(self) -> ServiceResult:
        """Compare ztlctl.toml mtime vs self/*.md mtimes."""
        from ztlctl.services.init import InitService
        from ztlctl.services.result import ServiceError, ServiceResult

        kwargs: dict[str, Any] = {}

        kwargs, rejection = self._dispatch_pre_action("check_staleness", kwargs)
        if rejection is not None:
            return ServiceResult(
                ok=False,
                op="check_staleness",
                error=ServiceError(
                    code="ACTION_REJECTED",
                    message=rejection.reason,
                    detail=rejection.detail,
                    recovery=f"Action rejected by plugin: {rejection.reason}",
                ),
            )

        result = InitService.check_staleness(self._vault)
        return result
