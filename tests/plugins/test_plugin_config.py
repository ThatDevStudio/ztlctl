"""Tests for PluginManager version checking, config injection, and BaseController dispatch."""

from __future__ import annotations

import logging
from typing import Any
from unittest.mock import MagicMock

import pluggy
import pytest
from pydantic import BaseModel

from ztlctl.config.models import PluginsConfig
from ztlctl.plugins import PLUGIN_API_VERSION
from ztlctl.plugins.contracts import ActionRejection
from ztlctl.plugins.manager import PluginManager

hookimpl = pluggy.HookimplMarker("ztlctl")


# ---------------------------------------------------------------------------
# PluginsConfig extra=allow tests
# ---------------------------------------------------------------------------


class TestPluginsConfigExtra:
    def test_plugins_config_extra_allow(self) -> None:
        """PluginsConfig accepts arbitrary extra keys for plugin sections."""
        cfg = PluginsConfig(git={"enabled": True}, myplugin={"key": "val"})  # type: ignore[call-arg]
        assert cfg.model_extra is not None
        assert "myplugin" in cfg.model_extra

    def test_get_plugin_config_exists(self) -> None:
        """get_plugin_config returns the config dict for a known plugin."""
        cfg = PluginsConfig(git={"enabled": True}, myplugin={"key": "val"})  # type: ignore[call-arg]
        result = cfg.get_plugin_config("myplugin")
        assert result == {"key": "val"}

    def test_get_plugin_config_missing(self) -> None:
        """get_plugin_config returns empty dict for unknown plugins."""
        cfg = PluginsConfig()
        result = cfg.get_plugin_config("nonexistent")
        assert result == {}

    def test_get_plugin_config_no_extra(self) -> None:
        """get_plugin_config with no model_extra still returns empty dict."""
        cfg = PluginsConfig()
        assert cfg.get_plugin_config("anything") == {}


# ---------------------------------------------------------------------------
# PluginManager version checking
# ---------------------------------------------------------------------------


class TestVersionCheckInDiscover:
    def test_version_check_rejects_too_new(self, caplog: pytest.LogCaptureFixture) -> None:
        """A plugin with API version too new is skipped with a warning."""

        class FuturePlugin:
            PLUGIN_API_VERSION = 99

            @hookimpl
            def post_action(self, action_name: str, kwargs: dict[str, Any], result: Any) -> None:
                pass

        pm = PluginManager()
        with caplog.at_level(logging.WARNING, logger="ztlctl.plugins.manager"):
            pm.register_plugin(FuturePlugin(), name="future-plugin")

        # Plugin should not be in the loaded plugins (was unregistered)
        assert "future-plugin" not in pm.list_plugin_names()

    def test_version_check_warns_on_deprecated(self, caplog: pytest.LogCaptureFixture) -> None:
        """A plugin with a deprecated-but-supported API version loads with a warning."""

        class OldPlugin:
            PLUGIN_API_VERSION = 0

            @hookimpl
            def post_action(self, action_name: str, kwargs: dict[str, Any], result: Any) -> None:
                pass

        pm = PluginManager()
        with caplog.at_level(logging.WARNING, logger="ztlctl.plugins.manager"):
            pm.register_plugin(OldPlugin(), name="old-plugin")

        # Plugin SHOULD be registered (deprecated but within window)
        assert "old-plugin" in pm.list_plugin_names()
        # Should have a warning in the log
        warning_messages = [r.message for r in caplog.records if r.levelno == logging.WARNING]
        assert any("consider updating" in msg for msg in warning_messages)

    def test_version_check_compatible_loads_clean(self, caplog: pytest.LogCaptureFixture) -> None:
        """A plugin with the current API version loads without warnings."""

        class CurrentPlugin:
            PLUGIN_API_VERSION = PLUGIN_API_VERSION

            @hookimpl
            def post_action(self, action_name: str, kwargs: dict[str, Any], result: Any) -> None:
                pass

        pm = PluginManager()
        with caplog.at_level(logging.WARNING, logger="ztlctl.plugins.manager"):
            pm.register_plugin(CurrentPlugin(), name="current-plugin")

        assert "current-plugin" in pm.list_plugin_names()
        # No version-related warnings
        version_warnings = [
            r.message
            for r in caplog.records
            if r.levelno == logging.WARNING and "version" in r.message.lower()
        ]
        assert len(version_warnings) == 0


# ---------------------------------------------------------------------------
# Plugin config injection
# ---------------------------------------------------------------------------


class TestConfigInjection:
    def test_config_injected_with_schema(self) -> None:
        """A plugin with get_config_schema gets its config validated and passed to initialize."""

        class MyPluginConfig(BaseModel):
            api_key: str
            timeout: int = 30

        injected: list[BaseModel | None] = []

        class MyPlugin:
            @hookimpl
            def get_config_schema(self) -> type[BaseModel] | None:
                return MyPluginConfig

            @hookimpl
            def initialize(self, config: BaseModel | None) -> None:
                injected.append(config)

        pm = PluginManager()
        pm.register_plugin(MyPlugin(), name="myplugin")

        # Build a settings mock with the plugin config
        mock_settings = MagicMock()
        mock_settings.plugins = PluginsConfig(  # type: ignore[call-arg]
            myplugin={"api_key": "test-key", "timeout": 10}
        )

        pm.inject_configs(mock_settings)

        assert len(injected) == 1
        assert isinstance(injected[0], MyPluginConfig)
        assert injected[0].api_key == "test-key"  # type: ignore[union-attr]
        assert injected[0].timeout == 10  # type: ignore[union-attr]

    def test_invalid_config_rejected(self, caplog: pytest.LogCaptureFixture) -> None:
        """A plugin with invalid config gets initialize(config=None) and a warning is logged."""

        class StrictConfig(BaseModel):
            required_field: str  # required — no default

        injected: list[BaseModel | None] = []

        class StrictPlugin:
            @hookimpl
            def get_config_schema(self) -> type[BaseModel] | None:
                return StrictConfig

            @hookimpl
            def initialize(self, config: BaseModel | None) -> None:
                injected.append(config)

        pm = PluginManager()
        pm.register_plugin(StrictPlugin(), name="strictplugin")

        mock_settings = MagicMock()
        mock_settings.plugins = PluginsConfig(  # type: ignore[call-arg]
            strictplugin={"wrong_field": "value"}  # missing required_field
        )

        with caplog.at_level(logging.WARNING, logger="ztlctl.plugins.manager"):
            pm.inject_configs(mock_settings)

        # initialize should be called with None because config was invalid
        assert len(injected) == 1
        assert injected[0] is None
        # Warning should be logged
        assert any(
            "strictplugin" in r.message and "config" in r.message.lower()
            for r in caplog.records
            if r.levelno == logging.WARNING
        )

    def test_no_schema_no_initialize(self) -> None:
        """A plugin without get_config_schema or initialize is skipped cleanly."""
        called: list[bool] = []

        class SimplePlugin:
            @hookimpl
            def post_action(self, action_name: str, kwargs: dict[str, Any], result: Any) -> None:
                called.append(True)

        pm = PluginManager()
        pm.register_plugin(SimplePlugin(), name="simpleplugin")

        mock_settings = MagicMock()
        mock_settings.plugins = PluginsConfig()

        # Should not raise
        pm.inject_configs(mock_settings)
        assert called == []  # No side effects

    def test_inject_configs_no_config_section(self) -> None:
        """A plugin with schema but no TOML section gets initialize(config=None)."""

        class SomeConfig(BaseModel):
            optional_val: str = "default"

        injected: list[BaseModel | None] = []

        class SomePlugin:
            @hookimpl
            def get_config_schema(self) -> type[BaseModel] | None:
                return SomeConfig

            @hookimpl
            def initialize(self, config: BaseModel | None) -> None:
                injected.append(config)

        pm = PluginManager()
        pm.register_plugin(SomePlugin(), name="someplugin")

        mock_settings = MagicMock()
        mock_settings.plugins = PluginsConfig()  # no someplugin section

        pm.inject_configs(mock_settings)

        # With no config section, initialize is called with None
        assert len(injected) == 1
        assert injected[0] is None


# ---------------------------------------------------------------------------
# BaseController dispatch methods
# ---------------------------------------------------------------------------


class TestBaseControllerDispatch:
    def _make_vault_with_pm(self, pm: PluginManager | None = None) -> MagicMock:
        """Build a mock Vault with an optional PluginManager."""
        mock_vault = MagicMock()
        mock_vault.plugin_manager = pm
        return mock_vault

    def test_dispatch_pre_action_no_pm(self) -> None:
        """_dispatch_pre_action returns original kwargs + None rejection when no plugin manager."""
        from ztlctl.controllers.base import BaseController

        vault = self._make_vault_with_pm(None)
        controller = BaseController(vault)
        original_kwargs = {"title": "test"}

        result_kwargs, rejection = controller._dispatch_pre_action("create", original_kwargs)

        assert result_kwargs is original_kwargs
        assert rejection is None

    def test_dispatch_pre_action_rejection(self) -> None:
        """_dispatch_pre_action returns (original_kwargs, ActionRejection) when plugin rejects."""
        from ztlctl.controllers.base import BaseController

        pm = PluginManager()

        class RejectingPlugin:
            @hookimpl
            def pre_action(self, action_name: str, kwargs: dict[str, Any]) -> Any:
                return ActionRejection(reason="blocked")

        pm.register_plugin(RejectingPlugin(), name="rejecter")

        vault = self._make_vault_with_pm(pm)
        controller = BaseController(vault)

        _result_kwargs, rejection = controller._dispatch_pre_action("create", {"title": "test"})

        assert isinstance(rejection, ActionRejection)
        assert rejection.reason == "blocked"

    def test_dispatch_pre_action_modified_kwargs(self) -> None:
        """_dispatch_pre_action returns modified kwargs when plugin modifies them."""
        from ztlctl.controllers.base import BaseController

        pm = PluginManager()

        class ModifyingPlugin:
            @hookimpl
            def pre_action(self, action_name: str, kwargs: dict[str, Any]) -> Any:
                return {**kwargs, "title": "modified"}

        pm.register_plugin(ModifyingPlugin(), name="modifier")

        vault = self._make_vault_with_pm(pm)
        controller = BaseController(vault)

        result_kwargs, rejection = controller._dispatch_pre_action("create", {"title": "original"})

        assert result_kwargs["title"] == "modified"
        assert rejection is None

    def test_dispatch_pre_action_none_passthrough(self) -> None:
        """_dispatch_pre_action returns original kwargs when plugin returns None."""
        from ztlctl.controllers.base import BaseController

        pm = PluginManager()

        class PassPlugin:
            @hookimpl
            def pre_action(self, action_name: str, kwargs: dict[str, Any]) -> Any:
                return None

        pm.register_plugin(PassPlugin(), name="passer")

        vault = self._make_vault_with_pm(pm)
        controller = BaseController(vault)
        original_kwargs = {"title": "test"}

        result_kwargs, rejection = controller._dispatch_pre_action("create", original_kwargs)

        assert result_kwargs is original_kwargs
        assert rejection is None

    def test_dispatch_post_action_no_pm(self) -> None:
        """_dispatch_post_action is a no-op when no plugin manager."""
        from ztlctl.controllers.base import BaseController

        vault = self._make_vault_with_pm(None)
        controller = BaseController(vault)

        # Should not raise
        controller._dispatch_post_action("create", {"title": "test"}, result=None)

    def test_dispatch_post_action_fires(self) -> None:
        """_dispatch_post_action invokes post_action on all plugins."""
        from ztlctl.controllers.base import BaseController

        pm = PluginManager()
        received: list[dict[str, Any]] = []

        class ObserverPlugin:
            @hookimpl
            def post_action(self, action_name: str, kwargs: dict[str, Any], result: Any) -> None:
                received.append({"action_name": action_name, "result": result})

        pm.register_plugin(ObserverPlugin(), name="observer")

        vault = self._make_vault_with_pm(pm)
        controller = BaseController(vault)
        sentinel = object()

        controller._dispatch_post_action("create", {"title": "test"}, result=sentinel)

        assert len(received) == 1
        assert received[0]["action_name"] == "create"
        assert received[0]["result"] is sentinel

    def test_dispatch_pre_action_exception_returns_originals(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """_dispatch_pre_action returns original kwargs + None on exception."""
        from ztlctl.controllers.base import BaseController

        pm = PluginManager()

        class BrokenPlugin:
            @hookimpl
            def pre_action(self, action_name: str, kwargs: dict[str, Any]) -> Any:
                raise RuntimeError("plugin exploded")

        pm.register_plugin(BrokenPlugin(), name="broken")

        vault = self._make_vault_with_pm(pm)
        controller = BaseController(vault)
        original_kwargs = {"title": "test"}

        with caplog.at_level(logging.DEBUG):
            result_kwargs, rejection = controller._dispatch_pre_action("create", original_kwargs)

        assert result_kwargs is original_kwargs
        assert rejection is None
