"""Tests for local directory plugin discovery in PluginManager."""

from __future__ import annotations

from pathlib import Path

import pluggy

from ztlctl.plugins.manager import PluginManager

hookimpl = pluggy.HookimplMarker("ztlctl")

# -- Plugin source code used in tests ------------------------------------------

_VALID_PLUGIN_SRC = """\
import pluggy

hookimpl = pluggy.HookimplMarker("ztlctl")


class LocalTestPlugin:
    \"\"\"A minimal local plugin for testing.\"\"\"

    @hookimpl
    def post_check(self, issues_found: int, issues_fixed: int) -> None:
        pass
"""

_INIT_PLUGIN_SRC = """\
import pluggy

hookimpl = pluggy.HookimplMarker("ztlctl")

calls: list[dict] = []


class InitCapturePlugin:
    \"\"\"Captures post_init calls for verification.\"\"\"

    @hookimpl
    def post_init(self, vault_name: str, client: str, tone: str) -> None:
        calls.append({"vault_name": vault_name, "client": client, "tone": tone})
"""

_SYNTAX_ERROR_SRC = """\
def broken(
    # missing closing paren and colon
"""

_NO_HOOKS_SRC = """\
class PlainClass:
    \"\"\"A class with no hookimpl-decorated methods.\"\"\"
    def hello(self) -> str:
        return "world"
"""


class TestLocalDiscovery:
    """Tests for PluginManager._discover_local and friends."""

    def test_discovers_local_plugin(self, tmp_path: Path) -> None:
        """A .py file with a valid hookimpl class is discovered and registered."""
        plugin_file = tmp_path / "myplugin.py"
        plugin_file.write_text(_VALID_PLUGIN_SRC, encoding="utf-8")

        pm = PluginManager()
        pm.discover_and_load(local_dir=tmp_path)

        names = pm.list_plugin_names()
        assert "ztlctl_local_plugin_myplugin" in names

    def test_skips_bad_plugin_gracefully(self, tmp_path: Path) -> None:
        """A .py file with a SyntaxError is logged and skipped, no crash."""
        bad_file = tmp_path / "broken.py"
        bad_file.write_text(_SYNTAX_ERROR_SRC, encoding="utf-8")

        pm = PluginManager()
        # Must not raise
        names = pm.discover_and_load(local_dir=tmp_path)

        # The broken plugin should NOT appear in registered plugins
        assert all("broken" not in n for n in names)

    def test_no_local_dir_is_noop(self) -> None:
        """Passing local_dir=None does not error."""
        pm = PluginManager()
        names = pm.discover_and_load(local_dir=None)
        # Should complete without error; is_loaded should be True
        assert pm.is_loaded is True
        assert isinstance(names, list)

    def test_nonexistent_dir_is_noop(self, tmp_path: Path) -> None:
        """Passing a path that does not exist does not error."""
        nonexistent = tmp_path / "does_not_exist"

        pm = PluginManager()
        names = pm.discover_and_load(local_dir=nonexistent)
        assert pm.is_loaded is True
        assert isinstance(names, list)

    def test_local_plugin_hooks_fire(self, tmp_path: Path) -> None:
        """A local plugin that implements post_init receives hook calls."""
        plugin_file = tmp_path / "initplugin.py"
        plugin_file.write_text(_INIT_PLUGIN_SRC, encoding="utf-8")

        # Use _discover_local directly to avoid loading entry-point plugins
        # (e.g. GitPlugin) whose hooks would also fire on post_init.
        pm = PluginManager()
        pm._discover_local(tmp_path)

        # Fire the hook
        pm.hook.post_init(vault_name="testvault", client="obsidian", tone="formal")

        # Verify the plugin's module-level `calls` list was populated
        import sys

        mod = sys.modules["ztlctl_local_plugin_initplugin"]
        assert len(mod.calls) == 1  # type: ignore[attr-defined]
        assert mod.calls[0]["vault_name"] == "testvault"  # type: ignore[attr-defined]

    def test_skips_underscore_prefixed_files(self, tmp_path: Path) -> None:
        """Files starting with _ are not loaded."""
        helper = tmp_path / "_helpers.py"
        helper.write_text(_VALID_PLUGIN_SRC, encoding="utf-8")

        pm = PluginManager()
        pm.discover_and_load(local_dir=tmp_path)

        names = pm.list_plugin_names()
        assert all("_helpers" not in n for n in names)

    def test_skips_classes_without_hookimpls(self, tmp_path: Path) -> None:
        """A class without @hookimpl methods is not registered."""
        plain_file = tmp_path / "plain.py"
        plain_file.write_text(_NO_HOOKS_SRC, encoding="utf-8")

        pm = PluginManager()
        pm.discover_and_load(local_dir=tmp_path)

        names = pm.list_plugin_names()
        assert all("plain" not in n for n in names)

    def test_has_hook_impls_positive(self) -> None:
        """_has_hook_impls returns True for a class with @hookimpl."""

        class _WithHook:
            @hookimpl
            def post_check(self, issues_found: int, issues_fixed: int) -> None:
                pass

        assert PluginManager._has_hook_impls(_WithHook) is True

    def test_has_hook_impls_negative(self) -> None:
        """_has_hook_impls returns False for a plain class."""

        class _NoHook:
            def some_method(self) -> None:
                pass

        assert PluginManager._has_hook_impls(_NoHook) is False
