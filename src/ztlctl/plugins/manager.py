"""Plugin discovery and loading.

Discovery: entry_points (pip-installed) + .ztlctl/plugins/ (local).
Capabilities: lifecycle hooks, CLI commands, MCP tools/resources.
"""

from __future__ import annotations

import pluggy

from ztlctl.plugins.hookspecs import ZtlctlHookSpec

PROJECT_NAME = "ztlctl"


class PluginManager:
    """Manages plugin discovery, loading, and hook dispatch."""

    def __init__(self) -> None:
        self._pm = pluggy.PluginManager(PROJECT_NAME)
        self._pm.add_hookspecs(ZtlctlHookSpec)

    def discover_and_load(self) -> None:
        """Discover plugins from entry points and local directory."""
        # Implementation deferred to plugin system feature
        raise NotImplementedError

    @property
    def hook(self) -> pluggy.HookRelay:
        """Access the hook relay for dispatching events."""
        return self._pm.hook
