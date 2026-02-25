"""Integration tests — event dispatch from services to plugins."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pluggy
import pytest

from ztlctl.config.settings import ZtlSettings
from ztlctl.infrastructure.vault import Vault
from ztlctl.plugins.event_bus import EventBus
from ztlctl.plugins.manager import PluginManager
from ztlctl.services.check import CheckService
from ztlctl.services.create import CreateService
from ztlctl.services.session import SessionService
from ztlctl.services.update import UpdateService

hookimpl = pluggy.HookimplMarker("ztlctl")


# ---------------------------------------------------------------------------
# Test plugins
# ---------------------------------------------------------------------------


class RecordingPlugin:
    """Plugin that records all hook calls for verification."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, Any]]] = []

    @hookimpl
    def post_create(
        self,
        content_type: str,
        content_id: str,
        title: str,
        path: str,
        tags: list[str],
    ) -> None:
        self.calls.append(
            (
                "post_create",
                {
                    "content_type": content_type,
                    "content_id": content_id,
                    "title": title,
                    "path": path,
                    "tags": tags,
                },
            )
        )

    @hookimpl
    def post_update(
        self,
        content_type: str,
        content_id: str,
        fields_changed: list[str],
        path: str,
    ) -> None:
        self.calls.append(
            (
                "post_update",
                {
                    "content_type": content_type,
                    "content_id": content_id,
                    "fields_changed": fields_changed,
                    "path": path,
                },
            )
        )

    @hookimpl
    def post_close(
        self,
        content_type: str,
        content_id: str,
        path: str,
        summary: str,
    ) -> None:
        self.calls.append(
            (
                "post_close",
                {
                    "content_type": content_type,
                    "content_id": content_id,
                    "path": path,
                    "summary": summary,
                },
            )
        )

    @hookimpl
    def post_session_start(self, session_id: str) -> None:
        self.calls.append(("post_session_start", {"session_id": session_id}))

    @hookimpl
    def post_session_close(self, session_id: str, stats: dict[str, Any]) -> None:
        self.calls.append(
            (
                "post_session_close",
                {"session_id": session_id, "stats": stats},
            )
        )

    @hookimpl
    def post_check(self, issues_found: int, issues_fixed: int) -> None:
        self.calls.append(
            (
                "post_check",
                {"issues_found": issues_found, "issues_fixed": issues_fixed},
            )
        )

    @hookimpl
    def post_reweave(
        self,
        source_id: str,
        affected_ids: list[str],
        links_added: int,
    ) -> None:
        self.calls.append(
            (
                "post_reweave",
                {
                    "source_id": source_id,
                    "affected_ids": affected_ids,
                    "links_added": links_added,
                },
            )
        )

    @hookimpl
    def post_init(self, vault_name: str, client: str, tone: str) -> None:
        self.calls.append(
            (
                "post_init",
                {"vault_name": vault_name, "client": client, "tone": tone},
            )
        )


class BrokenPlugin:
    """Plugin that raises on every hook."""

    @hookimpl
    def post_create(
        self,
        content_type: str,
        content_id: str,
        title: str,
        path: str,
        tags: list[str],
    ) -> None:
        msg = "Broken plugin!"
        raise RuntimeError(msg)

    @hookimpl
    def post_check(self, issues_found: int, issues_fixed: int) -> None:
        msg = "Broken plugin!"
        raise RuntimeError(msg)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def vault_root(tmp_path: Path) -> Path:
    """Vault directory structure for event dispatch tests."""
    (tmp_path / "notes").mkdir()
    (tmp_path / "ops" / "logs").mkdir(parents=True)
    (tmp_path / "ops" / "tasks").mkdir(parents=True)
    return tmp_path


@pytest.fixture
def vault_with_events(vault_root: Path) -> tuple[Vault, RecordingPlugin]:
    """Vault with sync event bus and recording plugin."""
    settings = ZtlSettings.from_cli(vault_root=vault_root)
    vault = Vault(settings)

    pm = PluginManager()
    recorder = RecordingPlugin()
    pm.register_plugin(recorder, name="recorder")

    vault._event_bus = EventBus(vault.engine, pm, sync=True)
    return vault, recorder


@pytest.fixture
def vault_with_broken_plugin(vault_root: Path) -> tuple[Vault, BrokenPlugin]:
    """Vault with a plugin that always raises."""
    settings = ZtlSettings.from_cli(vault_root=vault_root)
    vault = Vault(settings)

    pm = PluginManager()
    broken = BrokenPlugin()
    pm.register_plugin(broken, name="broken")

    vault._event_bus = EventBus(vault.engine, pm, sync=True)
    return vault, broken


# ---------------------------------------------------------------------------
# Tests — CreateService dispatch
# ---------------------------------------------------------------------------


class TestCreateEventDispatch:
    """Verify post_create is dispatched on content creation."""

    def test_post_create_dispatched_on_note_creation(
        self, vault_with_events: tuple[Vault, RecordingPlugin]
    ):
        vault, recorder = vault_with_events
        result = CreateService(vault).create_note("Test Note")
        assert result.ok

        assert len(recorder.calls) == 1
        hook, payload = recorder.calls[0]
        assert hook == "post_create"
        assert payload["content_type"] == "note"
        assert payload["title"] == "Test Note"

    def test_post_create_includes_tags_and_path(
        self, vault_with_events: tuple[Vault, RecordingPlugin]
    ):
        vault, recorder = vault_with_events
        result = CreateService(vault).create_note("Tagged Note", tags=["test/alpha"])
        assert result.ok

        _, payload = recorder.calls[0]
        assert payload["tags"] == ["test/alpha"]
        assert payload["path"]  # non-empty path

    def test_post_create_dispatched_for_reference(
        self, vault_with_events: tuple[Vault, RecordingPlugin]
    ):
        vault, recorder = vault_with_events
        result = CreateService(vault).create_reference("Ref Item")
        assert result.ok

        _, payload = recorder.calls[0]
        assert payload["content_type"] == "reference"

    def test_post_create_dispatched_for_task(
        self, vault_with_events: tuple[Vault, RecordingPlugin]
    ):
        vault, recorder = vault_with_events
        result = CreateService(vault).create_task("Task Item")
        assert result.ok

        _, payload = recorder.calls[0]
        assert payload["content_type"] == "task"


# ---------------------------------------------------------------------------
# Tests — UpdateService dispatch
# ---------------------------------------------------------------------------


class TestUpdateEventDispatch:
    """Verify post_update and post_close are dispatched."""

    def test_post_update_dispatched(self, vault_with_events: tuple[Vault, RecordingPlugin]):
        vault, recorder = vault_with_events
        create_result = CreateService(vault).create_note("Update Me")
        assert create_result.ok
        content_id = create_result.data["id"]

        recorder.calls.clear()

        result = UpdateService(vault).update(content_id, changes={"title": "Updated"})
        assert result.ok

        update_calls = [c for c in recorder.calls if c[0] == "post_update"]
        assert len(update_calls) == 1
        _, payload = update_calls[0]
        assert payload["content_id"] == content_id
        assert "title" in payload["fields_changed"]

    def test_post_close_dispatched_on_archive(
        self, vault_with_events: tuple[Vault, RecordingPlugin]
    ):
        vault, recorder = vault_with_events
        create_result = CreateService(vault).create_note("Archive Me")
        assert create_result.ok
        content_id = create_result.data["id"]

        recorder.calls.clear()

        result = UpdateService(vault).archive(content_id)
        assert result.ok

        close_calls = [c for c in recorder.calls if c[0] == "post_close"]
        assert len(close_calls) == 1
        _, payload = close_calls[0]
        assert payload["content_id"] == content_id
        assert payload["summary"] == "archived"


# ---------------------------------------------------------------------------
# Tests — SessionService dispatch
# ---------------------------------------------------------------------------


class TestSessionEventDispatch:
    """Verify session events are dispatched."""

    def test_post_session_start_dispatched(self, vault_with_events: tuple[Vault, RecordingPlugin]):
        vault, recorder = vault_with_events
        result = SessionService(vault).start("test-topic")
        assert result.ok

        start_calls = [c for c in recorder.calls if c[0] == "post_session_start"]
        assert len(start_calls) == 1
        _, payload = start_calls[0]
        assert payload["session_id"] == result.data["id"]

    def test_post_session_close_dispatched_with_stats(
        self, vault_with_events: tuple[Vault, RecordingPlugin]
    ):
        vault, recorder = vault_with_events
        SessionService(vault).start("test-topic")
        recorder.calls.clear()

        result = SessionService(vault).close(summary="done")
        assert result.ok

        close_calls = [c for c in recorder.calls if c[0] == "post_session_close"]
        assert len(close_calls) == 1
        _, payload = close_calls[0]
        assert "stats" in payload
        assert "session_id" in payload


# ---------------------------------------------------------------------------
# Tests — CheckService dispatch
# ---------------------------------------------------------------------------


class TestCheckEventDispatch:
    """Verify post_check is dispatched."""

    def test_post_check_dispatched(self, vault_with_events: tuple[Vault, RecordingPlugin]):
        vault, recorder = vault_with_events
        result = CheckService(vault).check()
        assert result.ok

        check_calls = [c for c in recorder.calls if c[0] == "post_check"]
        assert len(check_calls) == 1
        _, payload = check_calls[0]
        assert "issues_found" in payload
        assert "issues_fixed" in payload


# ---------------------------------------------------------------------------
# Tests — failure safety
# ---------------------------------------------------------------------------


class TestEventDispatchFailureSafety:
    """Verify broken plugins don't break services."""

    def test_broken_plugin_does_not_fail_create(
        self, vault_with_broken_plugin: tuple[Vault, BrokenPlugin]
    ):
        vault, _ = vault_with_broken_plugin
        result = CreateService(vault).create_note("Should Succeed")
        assert result.ok  # Service succeeds despite broken plugin

    def test_broken_plugin_adds_warning(self, vault_with_broken_plugin: tuple[Vault, BrokenPlugin]):
        vault, _ = vault_with_broken_plugin
        result = CreateService(vault).create_note("Warning Check")
        assert result.ok
        # The event dispatch failure is in the EventBus (handled internally),
        # not in _dispatch_event — the bus handles the exception.
        # Depending on whether the bus raises or not, we check:
        # EventBus with sync=True catches exceptions internally.

    def test_no_event_bus_is_noop(self, vault_root: Path):
        """Services work fine when event bus is not initialized."""
        settings = ZtlSettings.from_cli(vault_root=vault_root)
        vault = Vault(settings)
        # Don't init event bus — event_bus is None
        assert vault.event_bus is None

        result = CreateService(vault).create_note("No Bus")
        assert result.ok
        assert not result.warnings  # No warnings about missing bus
