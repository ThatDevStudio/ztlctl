"""Plugin discovery and loading.

Discovery: entry_points (pip-installed) via pluggy setuptools entrypoints.
Capabilities: lifecycle hooks, CLI commands, MCP tools/resources.
"""

from __future__ import annotations

import logging

import pluggy

from ztlctl.plugins.hookspecs import ZtlctlHookSpec

PROJECT_NAME = "ztlctl"

logger = logging.getLogger(__name__)


class PluginManager:
    """Manages plugin discovery, loading, and hook dispatch."""

    def __init__(self) -> None:
        self._pm = pluggy.PluginManager(PROJECT_NAME)
        self._pm.add_hookspecs(ZtlctlHookSpec)
        self._loaded: bool = False

    def discover_and_load(self) -> list[str]:
        """Discover plugins from entry points.

        Uses pluggy's native setuptools entry_point discovery for the
        ``ztlctl.plugins`` group. Returns a list of loaded plugin names.
        """
        self._pm.load_setuptools_entrypoints("ztlctl.plugins")
        self._loaded = True
        return self.list_plugin_names()

    def register_plugin(self, plugin: object, name: str | None = None) -> None:
        """Register a plugin instance directly (e.g. built-in plugins)."""
        resolved_name = name or plugin.__class__.__name__
        self._pm.register(plugin, name=resolved_name)
        logger.debug("Registered plugin: %s", resolved_name)

    def unregister(self, plugin: object) -> None:
        """Unregister a plugin instance."""
        self._pm.unregister(plugin)

    @property
    def is_loaded(self) -> bool:
        """Whether discover_and_load() has been called."""
        return self._loaded

    @property
    def hook(self) -> pluggy.HookRelay:
        """Access the hook relay for dispatching events."""
        return self._pm.hook

    def get_plugins(self) -> list[object]:
        """Return all registered plugins."""
        return list(self._pm.get_plugins())

    def list_plugin_names(self) -> list[str]:
        """Return names of all registered plugins."""
        return [self._pm.get_name(p) or p.__class__.__name__ for p in self._pm.get_plugins()]
