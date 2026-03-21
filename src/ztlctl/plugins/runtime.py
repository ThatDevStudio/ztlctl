"""Centralized PluginManager factory — single coherent runtime owner (ARCH-08)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ztlctl.plugins.manager import PluginManager

_cache: dict[tuple[Path | None, bool], PluginManager] = {}


def get_plugin_manager(
    *,
    local_dir: Path | None = None,
    include_entrypoints: bool = True,
    settings: Any = None,
    cache: bool = True,
) -> PluginManager:
    """Return a discovered PluginManager, creating one if needed for this scope.

    Args:
        local_dir: Path to local plugins directory (e.g., vault_root / ".ztlctl" / "plugins").
        include_entrypoints: Whether to load setuptools entry-point plugins.
        settings: If provided, calls inject_configs(settings) on the PM.
            Config injection runs on every call even for cached instances,
            since settings may differ between invocations.
        cache: Whether to store and retrieve the PM from the module-level cache.
            Set to False when the caller will mutate the PM (e.g., register
            vault-instance-specific built-in plugins) to prevent stale instances
            from being returned on subsequent calls.

    Returns:
        A fully discovered PluginManager instance.
    """
    key = (local_dir, include_entrypoints)
    pm = _cache.get(key) if cache else None
    if pm is None:
        pm = PluginManager()
        pm.discover_and_load(local_dir=local_dir, include_entrypoints=include_entrypoints)
        if cache:
            _cache[key] = pm
    if settings is not None:
        pm.inject_configs(settings)
    return pm


def reset_plugin_manager_cache() -> None:
    """Clear the PM cache. Used in test teardown."""
    _cache.clear()
