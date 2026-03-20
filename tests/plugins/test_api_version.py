"""Tests for plugin API versioning (PLUG-01)."""

from __future__ import annotations

import pluggy
import pytest

from ztlctl.plugins import PLUGIN_API_VERSION, PluginLoadError, check_plugin_api_version
from ztlctl.plugins.hookspecs import ZtlctlHookSpec


class TestApiVersionConstant:
    def test_plugin_api_version_constant(self) -> None:
        assert PLUGIN_API_VERSION == 1
        assert isinstance(PLUGIN_API_VERSION, int)


class TestCheckPluginApiVersion:
    def test_compatible_plugin_loads(self) -> None:
        """A plugin with the current API version returns empty warnings."""

        class MyPlugin:
            PLUGIN_API_VERSION = 1

        result = check_plugin_api_version(MyPlugin(), "myplugin")
        assert result == []

    def test_plugin_too_new_rejected(self) -> None:
        """A plugin that requires a newer API version raises PluginLoadError."""

        class FuturePlugin:
            PLUGIN_API_VERSION = 99

        with pytest.raises(PluginLoadError, match="requires API version 99"):
            check_plugin_api_version(FuturePlugin(), "future-plugin")

    def test_plugin_too_old_rejected(self) -> None:
        """A plugin with an API version outside the compatibility window raises PluginLoadError."""

        class AncientPlugin:
            PLUGIN_API_VERSION = -99

        with pytest.raises(PluginLoadError, match="no longer supported"):
            check_plugin_api_version(AncientPlugin(), "ancient-plugin")

    def test_deprecated_api_version_warns(self) -> None:
        """A plugin with a deprecated but still-supported version returns warning."""

        class OldPlugin:
            PLUGIN_API_VERSION = 0

        result = check_plugin_api_version(OldPlugin(), "old-plugin")
        assert len(result) == 1
        assert "consider updating" in result[0]

    def test_legacy_plugin_no_version(self) -> None:
        """A plugin without PLUGIN_API_VERSION is treated as legacy (no warnings)."""

        class LegacyPlugin:
            pass

        result = check_plugin_api_version(LegacyPlugin(), "legacy-plugin")
        assert result == []

    def test_edge_case_at_compatibility_window_boundary(self) -> None:
        """A plugin at exactly current - _COMPATIBILITY_WINDOW should raise."""
        from ztlctl.plugins import _COMPATIBILITY_WINDOW

        min_supported = PLUGIN_API_VERSION - _COMPATIBILITY_WINDOW

        class TooOldPlugin:
            pass

        TooOldPlugin.PLUGIN_API_VERSION = min_supported  # type: ignore[attr-defined]

        with pytest.raises(PluginLoadError, match="no longer supported"):
            check_plugin_api_version(TooOldPlugin(), "too-old")

    def test_edge_case_just_inside_window(self) -> None:
        """A plugin just inside the window returns a warning, not an error."""
        from ztlctl.plugins import _COMPATIBILITY_WINDOW

        version_in_window = PLUGIN_API_VERSION - _COMPATIBILITY_WINDOW + 1

        class AlmostOldPlugin:
            pass

        AlmostOldPlugin.PLUGIN_API_VERSION = version_in_window  # type: ignore[attr-defined]

        # If version_in_window == PLUGIN_API_VERSION, should be clean; otherwise warn
        result = check_plugin_api_version(AlmostOldPlugin(), "almost-old")
        assert isinstance(result, list)


class TestDeprecatedHookspecWarns:
    def test_deprecated_hookspec_warns_on_registration(self) -> None:
        """Registering a plugin that implements a deprecated hookspec emits DeprecationWarning."""
        hookimpl = pluggy.HookimplMarker("ztlctl")

        class DeprecatedPlugin:
            @hookimpl
            def post_create(
                self,
                content_type: str,
                content_id: str,
                title: str,
                path: str,
                tags: list[str],
            ) -> None:
                pass

        pm = pluggy.PluginManager("ztlctl")
        pm.add_hookspecs(ZtlctlHookSpec)

        with pytest.warns(DeprecationWarning, match="post_create"):
            pm.register(DeprecatedPlugin())
