"""Tests for the EventBus post_action bridge.

The bridge fires post_action for migrated plugins when the service layer
dispatches legacy per-event hooks (post_create, post_update, etc.) via
EventBus._execute_hook.
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

    def __init__(self) -> None:
        self.post_action_calls = []

    @_hookimpl
    def post_action(self, action_name: str, kwargs: dict[str, Any], result: Any) -> None:
        self.post_action_calls.append(
            {"action_name": action_name, "kwargs": kwargs, "result": result}
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


class TestEventBusPostActionBridge:
    """EventBus._execute_hook bridges lifecycle events to post_action."""

    def _make_bus(self, vault: Vault, plugin: _RecordingPlugin) -> EventBus:
        pm = _make_plugin_manager(plugin)
        return EventBus(vault.engine, pm, sync=True)

    def test_post_create_bridges_to_post_action_create_note(self, vault_with_bus: Vault) -> None:
        """post_create event with content_type=note -> post_action(create_note)."""
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

        assert len(plugin.post_action_calls) == 1
        call = plugin.post_action_calls[0]
        assert call["action_name"] == "create_note"
        assert call["kwargs"] == payload
        assert call["result"] is None

    def test_post_create_bridges_to_post_action_create_reference(
        self, vault_with_bus: Vault
    ) -> None:
        """post_create with content_type=reference -> post_action(create_reference)."""
        plugin = _RecordingPlugin()
        bus = self._make_bus(vault_with_bus, plugin)

        payload = {
            "content_type": "reference",
            "content_id": "R-0001",
            "title": "Ref",
            "path": "notes/ref.md",
            "tags": [],
        }
        bus.dispatch("post_create", payload)

        assert len(plugin.post_action_calls) == 1
        assert plugin.post_action_calls[0]["action_name"] == "create_reference"

    def test_post_create_bridges_to_post_action_create_task(self, vault_with_bus: Vault) -> None:
        """post_create with content_type=task -> post_action(create_task)."""
        plugin = _RecordingPlugin()
        bus = self._make_bus(vault_with_bus, plugin)

        payload = {
            "content_type": "task",
            "content_id": "TASK-0001",
            "title": "Task",
            "path": "ops/tasks/TASK-0001.md",
            "tags": [],
        }
        bus.dispatch("post_create", payload)

        assert len(plugin.post_action_calls) == 1
        assert plugin.post_action_calls[0]["action_name"] == "create_task"

    def test_post_update_bridges_to_post_action_update(self, vault_with_bus: Vault) -> None:
        """post_update event -> post_action(update)."""
        plugin = _RecordingPlugin()
        bus = self._make_bus(vault_with_bus, plugin)

        payload = {
            "content_type": "note",
            "content_id": "N-0001",
            "fields_changed": ["title"],
            "path": "notes/test.md",
        }
        bus.dispatch("post_update", payload)

        assert len(plugin.post_action_calls) == 1
        assert plugin.post_action_calls[0]["action_name"] == "update"

    def test_post_session_close_bridges(self, vault_with_bus: Vault) -> None:
        """post_session_close event -> post_action(session_close)."""
        plugin = _RecordingPlugin()
        bus = self._make_bus(vault_with_bus, plugin)

        payload = {
            "session_id": "LOG-0001",
            "stats": {"created": 1, "updated": 0},
        }
        bus.dispatch("post_session_close", payload)

        assert len(plugin.post_action_calls) == 1
        assert plugin.post_action_calls[0]["action_name"] == "session_close"

    def test_post_reweave_bridges(self, vault_with_bus: Vault) -> None:
        """post_reweave event -> post_action(reweave)."""
        plugin = _RecordingPlugin()
        bus = self._make_bus(vault_with_bus, plugin)

        payload = {"source_id": "N-0001", "affected_ids": ["N-0002"], "links_added": 1}
        bus.dispatch("post_reweave", payload)

        assert len(plugin.post_action_calls) == 1
        assert plugin.post_action_calls[0]["action_name"] == "reweave"

    def test_post_check_bridges(self, vault_with_bus: Vault) -> None:
        """post_check event -> post_action(check)."""
        plugin = _RecordingPlugin()
        bus = self._make_bus(vault_with_bus, plugin)

        payload = {"issues_found": 2, "issues_fixed": 1}
        bus.dispatch("post_check", payload)

        assert len(plugin.post_action_calls) == 1
        assert plugin.post_action_calls[0]["action_name"] == "check"

    def test_post_init_bridges(self, vault_with_bus: Vault) -> None:
        """post_init event -> post_action(init)."""
        plugin = _RecordingPlugin()
        bus = self._make_bus(vault_with_bus, plugin)

        payload = {"vault_name": "my-vault", "client": "obsidian", "tone": "research-partner"}
        bus.dispatch("post_init", payload)

        assert len(plugin.post_action_calls) == 1
        assert plugin.post_action_calls[0]["action_name"] == "init"

    def test_non_lifecycle_hook_does_not_trigger_post_action(self, vault_with_bus: Vault) -> None:
        """Hooks not in _HOOK_TO_ACTION do NOT trigger post_action."""
        plugin = _RecordingPlugin()
        bus = self._make_bus(vault_with_bus, plugin)

        # "register_content_models" is not a lifecycle hook
        bus.dispatch("register_content_models", {})

        assert len(plugin.post_action_calls) == 0

    def test_bridge_result_is_always_none(self, vault_with_bus: Vault) -> None:
        """The bridge always passes result=None to post_action."""
        plugin = _RecordingPlugin()
        bus = self._make_bus(vault_with_bus, plugin)

        bus.dispatch("post_update", {"content_id": "N-0001", "path": "notes/test.md"})

        assert plugin.post_action_calls[0]["result"] is None

    def test_bridge_error_does_not_break_per_event_completion(self, vault_with_bus: Vault) -> None:
        """If post_action raises, the per-event WAL entry still completes."""
        from sqlalchemy import select

        from ztlctl.infrastructure.database.schema import event_wal

        pm = MagicMock()
        # Make per-event hook succeed (return normally)
        pm.hook.post_create = MagicMock()
        # Make post_action hook raise
        pm.hook.post_action = MagicMock(side_effect=RuntimeError("bridge error"))

        bus = EventBus(vault_with_bus.engine, pm, sync=True)
        payload = {
            "content_type": "note",
            "content_id": "N-0001",
            "title": "Test",
            "path": "notes/test.md",
            "tags": [],
        }
        event_id = bus.dispatch("post_create", payload)

        # WAL event should be completed despite bridge error
        with vault_with_bus.engine.connect() as conn:
            status = conn.execute(
                select(event_wal.c.status).where(event_wal.c.id == event_id)
            ).scalar_one()
        assert status == "completed"

    def test_bridge_with_no_post_action_hookspec_no_error(self, vault_with_bus: Vault) -> None:
        """If PluginManager has no post_action, bridge degrades gracefully."""
        pm = pluggy.PluginManager("ztlctl")
        # Do NOT add ZtlctlHookSpec — no post_action attribute on pm.hook

        bus = EventBus(vault_with_bus.engine, pm, sync=True)
        # Should not raise
        bus.dispatch("post_update", {"content_id": "N-0001", "path": "notes/test.md"})
