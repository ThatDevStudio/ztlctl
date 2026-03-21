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

        kwargs: dict[str, Any] = {
            "path": path,
            "name": name,
            "profile": profile,
            "client": client,
            "tone": tone,
            "topics": topics,
            "no_workflow": no_workflow,
        }

        def _invoke(kw: dict[str, Any]) -> ServiceResult:
            return InitService.init_vault(
                kw["path"],
                name=kw["name"],
                profile=kw["profile"],
                client=kw["client"],
                tone=kw["tone"],
                topics=kw["topics"],
                no_workflow=kw["no_workflow"],
            )

        return self._run_action("init_vault", kwargs, _invoke)

    def regenerate_self(self) -> ServiceResult:
        """Re-render self/ files from current vault settings."""
        from ztlctl.services.init import InitService

        kwargs: dict[str, Any] = {}

        def _invoke(kw: dict[str, Any]) -> ServiceResult:
            return InitService.regenerate_self(self._vault)

        return self._run_action("regenerate_self", kwargs, _invoke)

    def check_staleness(self) -> ServiceResult:
        """Compare ztlctl.toml mtime vs self/*.md mtimes."""
        from ztlctl.services.init import InitService

        kwargs: dict[str, Any] = {}

        def _invoke(kw: dict[str, Any]) -> ServiceResult:
            return InitService.check_staleness(self._vault)

        return self._run_action("check_staleness", kwargs, _invoke)
