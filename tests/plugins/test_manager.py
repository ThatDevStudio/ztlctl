"""Tests for PluginManager — discovery, registration, and hook relay."""

from __future__ import annotations

import pluggy
import pytest

from ztlctl.domain.content import CONTENT_REGISTRY, NoteModel, get_content_model
from ztlctl.plugins.manager import PluginManager

hookimpl = pluggy.HookimplMarker("ztlctl")


class _DummyPlugin:
    """Minimal plugin for registration tests."""

    @hookimpl
    def post_check(self, issues_found: int, issues_fixed: int) -> None:
        pass


class _CustomSubtypeModel(NoteModel):
    _subtype_name = "plugin_note"


class _ContentModelPlugin:
    @hookimpl
    def register_content_models(self) -> dict[str, type[NoteModel]]:
        return {"plugin_note": _CustomSubtypeModel}


class _ConflictingContentModelPlugin:
    @hookimpl
    def register_content_models(self) -> dict[str, type[NoteModel]]:
        return {"decision": _CustomSubtypeModel}


class TestPluginManager:
    """Tests for the PluginManager class."""

    def test_hook_relay_accessible(self):
        pm = PluginManager()
        assert hasattr(pm.hook, "post_create")
        assert hasattr(pm.hook, "post_session_close")

    def test_register_plugin(self):
        pm = PluginManager()
        plugin = _DummyPlugin()
        pm.register_plugin(plugin, name="dummy")
        assert "dummy" in pm.list_plugin_names()

    def test_register_plugin_default_name(self):
        pm = PluginManager()
        plugin = _DummyPlugin()
        pm.register_plugin(plugin)
        assert "_DummyPlugin" in pm.list_plugin_names()

    def test_unregister_plugin(self):
        pm = PluginManager()
        plugin = _DummyPlugin()
        pm.register_plugin(plugin, name="dummy")
        pm.unregister(plugin)
        assert "dummy" not in pm.list_plugin_names()

    def test_discover_loads_entry_points(self):
        """Discover loads at least the built-in git plugin (package is editable-installed)."""
        pm = PluginManager()
        names = pm.discover_and_load()
        assert pm.is_loaded is True
        # At minimum, the git plugin entry point should be found
        assert any("git" in n.lower() or "Git" in n for n in names)

    def test_is_loaded_false_before_discover(self):
        pm = PluginManager()
        assert pm.is_loaded is False

    def test_get_plugins_returns_registered(self):
        pm = PluginManager()
        plugin = _DummyPlugin()
        pm.register_plugin(plugin, name="test")
        plugins = pm.get_plugins()
        assert plugin in plugins

    @pytest.mark.parametrize(
        "hook_name",
        [
            "post_create",
            "post_update",
            "post_close",
            "post_reweave",
            "post_session_start",
            "post_session_close",
            "post_check",
            "post_init",
            "register_content_models",
        ],
    )
    def test_all_hookspecs_registered(self, hook_name: str):
        """All lifecycle and setup hookspecs should be available on the hook relay."""
        pm = PluginManager()
        assert hasattr(pm.hook, hook_name)

    def test_discover_registers_plugin_content_models(self) -> None:
        pm = PluginManager()
        original_registry = CONTENT_REGISTRY.copy()
        pm.register_plugin(_ContentModelPlugin(), name="content-models")

        try:
            pm.discover_and_load(local_dir=None)
            assert get_content_model("note", "plugin_note") is _CustomSubtypeModel
        finally:
            CONTENT_REGISTRY.clear()
            CONTENT_REGISTRY.update(original_registry)

    def test_conflicting_plugin_content_models_warn_and_skip(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        pm = PluginManager()
        original_registry = CONTENT_REGISTRY.copy()
        pm.register_plugin(_ConflictingContentModelPlugin(), name="conflicting-models")

        try:
            with caplog.at_level("WARNING"):
                pm.discover_and_load(local_dir=None)
            assert get_content_model("note", "decision").__name__ == "DecisionModel"
            assert "Skipping content model registration" in caplog.text
        finally:
            CONTENT_REGISTRY.clear()
            CONTENT_REGISTRY.update(original_registry)

    def test_register_plugin_after_load_registers_content_models(self) -> None:
        pm = PluginManager()
        original_registry = CONTENT_REGISTRY.copy()

        try:
            pm.discover_and_load(local_dir=None)
            pm.register_plugin(_ContentModelPlugin(), name="runtime-content-models")
            assert get_content_model("note", "plugin_note") is _CustomSubtypeModel
        finally:
            CONTENT_REGISTRY.clear()
            CONTENT_REGISTRY.update(original_registry)
