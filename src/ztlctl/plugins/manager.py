"""Plugin discovery and loading.

Discovery: entry_points (pip-installed) via pluggy setuptools entrypoints,
plus local directory discovery from ``.ztlctl/plugins/``.
Capabilities: lifecycle hooks, CLI commands, MCP tools/resources.
"""

from __future__ import annotations

import importlib.util
import inspect
import logging
import sys
from pathlib import Path

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

    def discover_and_load(self, *, local_dir: Path | None = None) -> list[str]:
        """Discover plugins from entry points and an optional local directory.

        Uses pluggy's native setuptools entry_point discovery for the
        ``ztlctl.plugins`` group, then scans *local_dir* (typically
        ``.ztlctl/plugins/``) for single-file Python plugins.

        Returns a list of loaded plugin names.
        """
        self._pm.load_setuptools_entrypoints("ztlctl.plugins")
        self._normalize_plugin_instances()
        if local_dir is not None:
            self._discover_local(local_dir)
        self._register_content_models()
        self._loaded = True
        return self.list_plugin_names()

    def register_plugin(self, plugin: object, name: str | None = None) -> None:
        """Register a plugin instance directly (e.g. built-in plugins)."""
        resolved_name = name or plugin.__class__.__name__
        self._pm.register(plugin, name=resolved_name)
        if self._loaded:
            self._register_plugin_content_models(plugin, resolved_name)
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

    # ------------------------------------------------------------------
    # Local directory discovery
    # ------------------------------------------------------------------

    def _discover_local(self, local_dir: Path) -> None:
        """Scan *local_dir* for single-file Python plugins.

        Each ``*.py`` file (excluding ``_``-prefixed names) is loaded as a
        module. Classes inside the module that carry pluggy hookimpl-decorated
        methods are instantiated and registered.

        Errors are logged as warnings but never raised — a broken local plugin
        must not prevent the rest of the system from starting.
        """
        if not local_dir.is_dir():
            return

        for py_file in sorted(local_dir.glob("*.py")):
            if py_file.name.startswith("_"):
                continue
            module_name = f"ztlctl_local_plugin_{py_file.stem}"
            try:
                spec = importlib.util.spec_from_file_location(module_name, py_file)
                if spec is None or spec.loader is None:
                    logger.warning("Could not create module spec for %s", py_file)
                    continue
                module = importlib.util.module_from_spec(spec)
                sys.modules[module_name] = module
                spec.loader.exec_module(module)
            except Exception:
                logger.warning("Failed to load local plugin %s", py_file, exc_info=True)
                # Clean up partial module registration
                sys.modules.pop(module_name, None)
                continue

            # Scan module for classes that have hookimpl-decorated methods
            for _attr_name, obj in inspect.getmembers(module, inspect.isclass):
                if obj.__module__ != module_name:
                    continue  # skip imported classes
                if not self._has_hook_impls(obj):
                    continue
                try:
                    instance = obj()
                    self.register_plugin(instance, name=module_name)
                    logger.debug(
                        "Loaded local plugin %s from %s",
                        obj.__name__,
                        py_file,
                    )
                except Exception:
                    logger.warning(
                        "Failed to instantiate plugin class %s from %s",
                        obj.__name__,
                        py_file,
                        exc_info=True,
                    )

    def _normalize_plugin_instances(self) -> None:
        """Replace registered plugin classes with instantiated objects.

        Entry-point loading may register a plugin class directly. Hook dispatch
        against class objects leaves ``self`` unbound and fails at runtime.
        """
        for plugin in list(self._pm.get_plugins()):
            if not inspect.isclass(plugin):
                continue
            if not self._has_hook_impls(plugin):
                continue

            plugin_name = self._pm.get_name(plugin) or plugin.__name__
            self._pm.unregister(plugin)

            try:
                instance = plugin()
            except Exception:
                logger.warning(
                    "Failed to instantiate entry-point plugin %s",
                    plugin_name,
                    exc_info=True,
                )
                continue

            self._pm.register(instance, name=plugin_name)
            logger.debug("Instantiated entry-point plugin: %s", plugin_name)

    def _register_content_models(self) -> None:
        """Load plugin-provided content subtype models into the domain registry."""
        for plugin in self._pm.get_plugins():
            plugin_name = self._pm.get_name(plugin) or plugin.__class__.__name__
            self._register_plugin_content_models(plugin, plugin_name)

    @staticmethod
    def _register_plugin_content_models(plugin: object, plugin_name: str) -> None:
        """Register content models exposed by a single plugin instance."""
        from ztlctl.domain.content import register_content_model

        hook = getattr(plugin, "register_content_models", None)
        if hook is None:
            return

        try:
            model_map = hook()
        except Exception:
            logger.warning(
                "Failed to collect content models from plugin %s",
                plugin_name,
                exc_info=True,
            )
            return

        if model_map is None:
            return
        if not isinstance(model_map, dict):
            logger.warning(
                "Plugin %s returned non-dict content model registrations",
                plugin_name,
            )
            return

        for subtype_name, model_cls in model_map.items():
            try:
                register_content_model(subtype_name, model_cls)
            except (TypeError, ValueError):
                logger.warning(
                    "Skipping content model registration %r from plugin %s",
                    subtype_name,
                    plugin_name,
                    exc_info=True,
                )

    @staticmethod
    def _has_hook_impls(cls: type) -> bool:
        """Check whether *cls* has any methods decorated with ``@hookimpl``.

        Pluggy's ``HookimplMarker("ztlctl")`` sets a ``ztlctl_impl``
        attribute on decorated methods.
        """
        for name in dir(cls):
            if name.startswith("_"):
                continue
            method = getattr(cls, name, None)
            if callable(method) and getattr(method, "ztlctl_impl", None):
                return True
        return False
