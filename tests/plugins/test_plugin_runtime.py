"""Tests for the centralized PluginManager factory (ARCH-08)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ztlctl.plugins.runtime import get_plugin_manager, reset_plugin_manager_cache


@pytest.fixture(autouse=True)
def clear_cache() -> None:
    """Reset the PM cache before and after each test."""
    reset_plugin_manager_cache()
    yield
    reset_plugin_manager_cache()


def test_get_plugin_manager_returns_loaded_instance() -> None:
    """get_plugin_manager() returns a PluginManager with is_loaded=True."""
    pm = get_plugin_manager()
    assert pm.is_loaded is True


def test_get_plugin_manager_caches_by_scope() -> None:
    """Repeated calls with the same scope return the same PM instance."""
    pm1 = get_plugin_manager()
    pm2 = get_plugin_manager()
    assert pm1 is pm2


def test_get_plugin_manager_different_scope_different_instance() -> None:
    """Different scopes (local_dir differs) produce different PM instances."""
    pm_none = get_plugin_manager(local_dir=None)
    pm_tmp = get_plugin_manager(local_dir=Path("/tmp"))
    assert pm_none is not pm_tmp


def test_reset_clears_cache() -> None:
    """reset_plugin_manager_cache() causes a new PM instance to be created."""
    pm1 = get_plugin_manager()
    reset_plugin_manager_cache()
    pm2 = get_plugin_manager()
    assert pm1 is not pm2


def test_inject_configs_called_when_settings_provided() -> None:
    """inject_configs(settings) is called on the PM when settings is provided."""
    settings = MagicMock()
    with patch("ztlctl.plugins.runtime.PluginManager") as mock_pm_cls:
        mock_pm = MagicMock()
        mock_pm.is_loaded = True
        mock_pm_cls.return_value = mock_pm

        result = get_plugin_manager(settings=settings)

    mock_pm.inject_configs.assert_called_once_with(settings)
    assert result is mock_pm


def test_inject_configs_not_called_when_settings_none() -> None:
    """inject_configs is NOT called when settings=None (default)."""
    with patch("ztlctl.plugins.runtime.PluginManager") as mock_pm_cls:
        mock_pm = MagicMock()
        mock_pm.is_loaded = True
        mock_pm_cls.return_value = mock_pm

        get_plugin_manager()

    mock_pm.inject_configs.assert_not_called()


def test_cache_false_returns_fresh_instance() -> None:
    """cache=False always creates a new PM instance even for the same scope."""
    pm1 = get_plugin_manager(cache=False)
    pm2 = get_plugin_manager(cache=False)
    assert pm1 is not pm2


def test_cache_false_does_not_populate_cache() -> None:
    """cache=False does not store the PM in the module-level cache."""
    pm_uncached = get_plugin_manager(cache=False)
    # Now call with cache=True (default) — should create a new (different) instance
    pm_cached = get_plugin_manager()
    assert pm_uncached is not pm_cached


def test_inject_configs_called_on_cached_instance() -> None:
    """inject_configs is called on the cached PM when settings is provided on repeat call."""
    settings = MagicMock()

    with patch("ztlctl.plugins.runtime.PluginManager") as mock_pm_cls:
        mock_pm = MagicMock()
        mock_pm.is_loaded = True
        mock_pm_cls.return_value = mock_pm

        # First call — creates PM and stores in cache
        get_plugin_manager()
        # Second call — uses cached PM, calls inject_configs
        get_plugin_manager(settings=settings)

    # PluginManager should only have been instantiated once
    assert mock_pm_cls.call_count == 1
    # inject_configs called once (second call had settings)
    mock_pm.inject_configs.assert_called_once_with(settings)
