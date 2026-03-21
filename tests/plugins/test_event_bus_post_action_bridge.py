"""Tests asserting the EventBus post_action bridge has been removed (ARCH-05).

After Phase 15, services emit post_action directly via _dispatch_post_action_event.
The bridge in EventBus._execute_hook that used to fire post_action for per-event
hooks would cause duplicate delivery. These tests verify that dispatch of a
per-event hook (post_create, post_update, etc.) does NOT trigger post_action.

Legacy per-event hooks themselves still fire for backward compatibility with
plugins that implement them directly.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pluggy
import pytest

from ztlctl.config.settings import ZtlSettings
from ztlctl.infrastructure.vault import Vault
from ztlctl.plugins.event_bus import EventBus
from ztlctl.plugins.hookspecs import ZtlctlHookSpec

_hookimpl = pluggy.HookimplMarker("ztlctl")


# ---------------------------------------------------------------------------
# Helper: build a minimal PluginManager with post_action support
# ---------------------------------------------------------------------------


class _RecordingPlugin:
    """Mock plugin that records post_action calls.

    The hookimpl marker is applied at class definition time so pluggy can find
    the attribute on the unbound function object.
    """

    post_action_calls: list[dict[str, Any]]
    post_create_calls: list[dict[str, Any]]

    def __init__(self) -> None:
        self.post_action_calls = []
        self.post_create_calls = []

    @_hookimpl
    def post_action(self, action_name: str, kwargs: dict[str, Any], result: Any) -> None:
        self.post_action_calls.append(
            {"action_name": action_name, "kwargs": kwargs, "result": result}
        )

    @_hookimpl
    def post_create(
        self,
        content_type: str,
        content_id: str,
        title: str,
        path: str,
        tags: list[str],
    ) -> None:
        self.post_create_calls.append(
            {
                "content_type": content_type,
                "content_id": content_id,
                "title": title,
                "path": path,
                "tags": tags,
            }
        )


def _make_plugin_manager(recording_plugin: _RecordingPlugin) -> Any:
    """Build a minimal pluggy PluginManager with ZtlctlHookSpec and the recording plugin."""
    pm = pluggy.PluginManager("ztlctl")
    pm.add_hookspecs(ZtlctlHookSpec)
    pm.register(recording_plugin)
    return pm


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def vault_with_bus(vault_root: Any) -> Vault:
    """Vault with sync EventBus."""
    v = Vault(ZtlSettings.from_cli(vault_root=vault_root))
    v.init_event_bus(sync=True)
    return v


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestEventBusBridgeRemoved:
    """Per-event hooks must NOT fire post_action after ARCH-05 bridge removal."""

    def _make_bus(self, vault: Vault, plugin: _RecordingPlugin) -> EventBus:
        pm = _make_plugin_manager(plugin)
        return EventBus(vault.engine, pm, sync=True)

    def test_post_create_does_not_trigger_post_action(self, vault_with_bus: Vault) -> None:
        """dispatch('post_create') must NOT fire post_action — no bridge."""
        plugin = _RecordingPlugin()
        bus = self._make_bus(vault_with_bus, plugin)

        payload = {
            "content_type": "note",
            "content_id": "N-0001",
            "title": "Test",
            "path": "notes/test.md",
            "tags": [],
        }
        bus.dispatch("post_create", payload)

        assert len(plugin.post_action_calls) == 0

    def test_post_update_does_not_trigger_post_action(self, vault_with_bus: Vault) -> None:
        """dispatch('post_update') must NOT fire post_action — no bridge."""
        plugin = _RecordingPlugin()
        bus = self._make_bus(vault_with_bus, plugin)

        payload = {
            "content_type": "note",
            "content_id": "N-0001",
            "fields_changed": ["title"],
            "path": "notes/test.md",
        }
        bus.dispatch("post_update", payload)

        assert len(plugin.post_action_calls) == 0

    def test_non_lifecycle_hook_does_not_trigger_post_action(self, vault_with_bus: Vault) -> None:
        """Hooks not mapped to any action do NOT trigger post_action (unchanged behavior)."""
        plugin = _RecordingPlugin()
        bus = self._make_bus(vault_with_bus, plugin)

        # "register_content_models" is not a lifecycle hook
        bus.dispatch("register_content_models", {})

        assert len(plugin.post_action_calls) == 0

    def test_per_event_hook_still_fires_normally(self, vault_with_bus: Vault) -> None:
        """dispatch('post_create') still fires the post_create per-event hook itself."""
        plugin = _RecordingPlugin()
        bus = self._make_bus(vault_with_bus, plugin)

        payload = {
            "content_type": "note",
            "content_id": "N-0001",
            "title": "Test",
            "path": "notes/test.md",
            "tags": [],
        }
        bus.dispatch("post_create", payload)

        # The per-event hook fires, post_action does not
        assert len(plugin.post_create_calls) == 1
        assert plugin.post_create_calls[0]["content_id"] == "N-0001"
        assert len(plugin.post_action_calls) == 0

    def test_post_action_dispatch_still_works(self, vault_with_bus: Vault) -> None:
        """Explicit dispatch('post_action') still fires post_action hook."""
        plugin = _RecordingPlugin()
        bus = self._make_bus(vault_with_bus, plugin)

        # Services emit post_action directly with ActionEvent payload structure
        payload = {
            "action_name": "create_note",
            "payload": {"content_id": "N-0001", "title": "Test"},
            "result": None,
        }
        bus.dispatch("post_action", payload)

        assert len(plugin.post_action_calls) == 1
        call = plugin.post_action_calls[0]
        assert call["action_name"] == "create_note"
