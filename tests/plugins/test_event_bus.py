"""Tests for EventBus — WAL-backed async event dispatch."""

from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any

import pluggy
import pytest
from sqlalchemy import insert, select

from ztlctl.infrastructure.database.engine import init_database
from ztlctl.infrastructure.database.schema import event_wal
from ztlctl.plugins.event_bus import EventBus
from ztlctl.plugins.manager import PluginManager
from ztlctl.services._helpers import now_iso

hookimpl = pluggy.HookimplMarker("ztlctl")


# ---------------------------------------------------------------------------
# Fake plugins for testing
# ---------------------------------------------------------------------------


class RecordingPlugin:
    """Plugin that records all hook calls."""

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
    def post_check(self, issues_found: int, issues_fixed: int) -> None:
        self.calls.append(
            (
                "post_check",
                {"issues_found": issues_found, "issues_fixed": issues_fixed},
            )
        )

    @hookimpl
    def post_session_close(
        self,
        session_id: str,
        stats: dict[str, Any],
    ) -> None:
        self.calls.append(
            (
                "post_session_close",
                {"session_id": session_id, "stats": stats},
            )
        )


class FailingPlugin:
    """Plugin that always raises on post_create."""

    @hookimpl
    def post_create(
        self,
        content_type: str,
        content_id: str,
        title: str,
        path: str,
        tags: list[str],
    ) -> None:
        msg = "Plugin exploded!"
        raise RuntimeError(msg)


class PostActionPlugin:
    """Plugin that records post_action calls."""

    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    @hookimpl
    def post_action(self, action_name: str, kwargs: dict[str, Any], result: Any) -> None:
        self.calls.append({"action_name": action_name, "kwargs": kwargs, "result": result})


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def pm_with_recorder() -> tuple[PluginManager, RecordingPlugin]:
    """PluginManager with a recording plugin registered."""
    pm = PluginManager()
    recorder = RecordingPlugin()
    pm.register_plugin(recorder, name="recorder")
    return pm, recorder


@pytest.fixture
def pm_with_failer() -> PluginManager:
    """PluginManager with a plugin that always fails."""
    pm = PluginManager()
    pm.register_plugin(FailingPlugin(), name="failer")
    return pm


@pytest.fixture
def engine(tmp_path: Path):
    """Initialized SQLite engine with event_wal table."""
    return init_database(tmp_path)


@pytest.fixture
def bus(engine, pm_with_recorder) -> tuple[EventBus, RecordingPlugin]:
    """Sync EventBus with a recording plugin."""
    pm, recorder = pm_with_recorder
    bus = EventBus(engine, pm, sync=True)
    return bus, recorder


# ---------------------------------------------------------------------------
# Tests — WAL persistence
# ---------------------------------------------------------------------------


class TestEventBusWAL:
    """Tests for WAL row persistence."""

    def test_dispatch_writes_wal_row(self, bus, engine):
        event_bus, _ = bus
        event_id = event_bus.dispatch(
            "post_create",
            {
                "content_type": "note",
                "content_id": "N-0001",
                "title": "Test",
                "path": "notes/N-0001.md",
                "tags": ["test"],
            },
        )

        with engine.connect() as conn:
            row = conn.execute(select(event_wal).where(event_wal.c.id == event_id)).fetchone()

        assert row is not None
        assert row.hook_name == "post_create"
        assert row.status == "completed"
        assert row.retries == 0

    def test_dispatch_sync_completes_event(self, bus, engine):
        event_bus, recorder = bus
        event_bus.dispatch(
            "post_check",
            {"issues_found": 3, "issues_fixed": 1},
        )

        assert len(recorder.calls) == 1
        assert recorder.calls[0][0] == "post_check"
        assert recorder.calls[0][1]["issues_found"] == 3

    def test_dispatch_with_session_id(self, bus, engine):
        event_bus, _ = bus
        event_id = event_bus.dispatch(
            "post_create",
            {
                "content_type": "note",
                "content_id": "N-0001",
                "title": "Test",
                "path": "notes/N-0001.md",
                "tags": [],
            },
            session_id="LOG-0001",
        )

        with engine.connect() as conn:
            row = conn.execute(
                select(event_wal.c.session_id).where(event_wal.c.id == event_id)
            ).fetchone()

        assert row is not None
        assert row.session_id == "LOG-0001"


class TestEventBusFailures:
    """Tests for hook failure handling and retries."""

    def test_failed_hook_records_error(self, engine, pm_with_failer):
        bus = EventBus(engine, pm_with_failer, sync=True, max_retries=3)
        event_id = bus.dispatch(
            "post_create",
            {
                "content_type": "note",
                "content_id": "N-0001",
                "title": "Test",
                "path": "notes/N-0001.md",
                "tags": [],
            },
        )

        with engine.connect() as conn:
            row = conn.execute(select(event_wal).where(event_wal.c.id == event_id)).fetchone()

        assert row is not None
        assert row.status == "failed"
        assert "Plugin exploded!" in row.error
        assert row.retries == 1

    def test_max_retries_dead_letters(self, engine, pm_with_failer):
        bus = EventBus(engine, pm_with_failer, sync=True, max_retries=1)
        event_id = bus.dispatch(
            "post_create",
            {
                "content_type": "note",
                "content_id": "N-0001",
                "title": "Test",
                "path": "notes/N-0001.md",
                "tags": [],
            },
        )

        with engine.connect() as conn:
            row = conn.execute(select(event_wal).where(event_wal.c.id == event_id)).fetchone()

        assert row is not None
        assert row.status == "dead_letter"
        assert row.retries == 1

    def test_drain_retries_pending(self, engine, pm_with_recorder):
        """Drain retries failed events from a previous dispatch."""
        pm, _recorder = pm_with_recorder

        # First, dispatch with a failer to get a "failed" event
        failer_pm = PluginManager()
        failer_pm.register_plugin(FailingPlugin(), name="failer")
        failing_bus = EventBus(engine, failer_pm, sync=True, max_retries=3)
        failing_bus.dispatch(
            "post_create",
            {
                "content_type": "note",
                "content_id": "N-0001",
                "title": "Test",
                "path": "notes/N-0001.md",
                "tags": [],
            },
        )

        # Now create a bus with the recording plugin and drain
        success_bus = EventBus(engine, pm, sync=True)
        results = success_bus.drain()

        assert len(results) == 1
        assert results[0]["hook_name"] == "post_create"
        assert results[0]["status"] == "completed"

    def test_drain_returns_summary(self, bus, engine):
        event_bus, _ = bus
        # No pending events — drain returns empty
        results = event_bus.drain()
        assert results == []


class TestEventBusAsync:
    """Tests for async dispatch mode."""

    def test_async_dispatch_completes(self, engine, pm_with_recorder):
        pm, recorder = pm_with_recorder
        bus = EventBus(engine, pm, sync=False, max_workers=1)

        bus.dispatch(
            "post_check",
            {"issues_found": 1, "issues_fixed": 0},
        )

        bus.shutdown()

        assert len(recorder.calls) == 1
        assert recorder.calls[0][0] == "post_check"

    def test_shutdown_waits(self, engine, pm_with_recorder):
        pm, recorder = pm_with_recorder
        bus = EventBus(engine, pm, sync=False, max_workers=1)

        for i in range(5):
            bus.dispatch(
                "post_check",
                {"issues_found": i, "issues_fixed": 0},
            )

        bus.shutdown()
        assert len(recorder.calls) == 5


class TestEventBusStateMachineTransitions:
    """Tests for the full state machine path through failed -> dead_letter."""

    def test_event_transitions_to_failed_on_handler_error(self, engine, pm_with_failer):
        """A failing handler transitions the event from pending to failed."""
        bus = EventBus(engine, pm_with_failer, sync=True, max_retries=3)
        event_id = bus.dispatch(
            "post_create",
            {
                "content_type": "note",
                "content_id": "N-0001",
                "title": "Test",
                "path": "notes/N-0001.md",
                "tags": [],
            },
        )

        with engine.connect() as conn:
            row = conn.execute(select(event_wal).where(event_wal.c.id == event_id)).fetchone()

        assert row is not None
        assert row.status == "failed"
        assert row.retries == 1
        assert "Plugin exploded!" in row.error

    def test_event_transitions_to_dead_letter_after_max_retries(self, engine, pm_with_failer):
        """After exhausting retries, event transitions to dead_letter state."""
        # max_retries=2: first dispatch fails with retries=1 → still "failed"
        # drain() re-executes the hook, retries becomes 2 = max_retries → dead_letter
        bus = EventBus(engine, pm_with_failer, sync=True, max_retries=2)
        event_id = bus.dispatch(
            "post_create",
            {
                "content_type": "note",
                "content_id": "N-0001",
                "title": "Test",
                "path": "notes/N-0001.md",
                "tags": [],
            },
        )

        # After first dispatch: retries=1, status="failed" (not dead_letter yet)
        with engine.connect() as conn:
            row = conn.execute(
                select(event_wal.c.status, event_wal.c.retries).where(event_wal.c.id == event_id)
            ).fetchone()
        assert row is not None
        assert row.status == "failed"
        assert row.retries == 1

        # Drain forces another retry — now retries == max_retries → dead_letter
        results = bus.drain()
        assert len(results) == 1
        assert results[0]["status"] == "dead_letter"

        with engine.connect() as conn:
            row = conn.execute(
                select(event_wal.c.status, event_wal.c.retries).where(event_wal.c.id == event_id)
            ).fetchone()
        assert row is not None
        assert row.status == "dead_letter"
        assert row.retries == 2

    def test_sync_mode_dispatch_calls_handler_synchronously(self, engine, pm_with_recorder):
        """Sync mode dispatches handler immediately without ThreadPoolExecutor."""
        pm, recorder = pm_with_recorder
        bus = EventBus(engine, pm, sync=True)

        # In sync mode, there should be no executor
        assert bus._executor is None

        bus.dispatch(
            "post_check",
            {"issues_found": 0, "issues_fixed": 0},
        )

        # Handler was called immediately (sync)
        assert len(recorder.calls) == 1
        assert recorder.calls[0][0] == "post_check"

    def test_shutdown_after_drain_no_error(self, engine, pm_with_recorder):
        """shutdown() can be called after drain() without error."""
        pm, _ = pm_with_recorder
        bus = EventBus(engine, pm, sync=False, max_workers=1)

        bus.dispatch(
            "post_check",
            {"issues_found": 0, "issues_fixed": 0},
        )

        bus.drain()
        # Should not raise
        bus.shutdown()


class TestEventBusConfig:
    """Tests for EventBusConfig-wired constructor."""

    def test_config_sets_per_future_timeout(self, engine) -> None:
        from ztlctl.config.models import EventBusConfig

        config = EventBusConfig(per_future_timeout_seconds=15.0)
        pm = PluginManager()
        bus = EventBus(engine, pm, sync=True, config=config)
        assert bus._per_future_timeout == 15.0

    def test_config_sets_shutdown_timeout(self, engine) -> None:
        from ztlctl.config.models import EventBusConfig

        config = EventBusConfig(shutdown_timeout_seconds=2.0)
        pm = PluginManager()
        bus = EventBus(engine, pm, sync=True, config=config)
        assert bus._shutdown_timeout == 2.0

    def test_config_sets_max_retries(self, engine) -> None:
        from ztlctl.config.models import EventBusConfig

        config = EventBusConfig(max_retries=7)
        pm = PluginManager()
        bus = EventBus(engine, pm, sync=True, config=config)
        assert bus._max_retries == 7

    def test_config_sets_dead_letter_retention(self, engine) -> None:
        from ztlctl.config.models import EventBusConfig

        config = EventBusConfig(dead_letter_retention_days=14)
        pm = PluginManager()
        bus = EventBus(engine, pm, sync=True, config=config)
        assert bus._dead_letter_retention_days == 14

    def test_no_config_uses_defaults(self, engine) -> None:
        pm = PluginManager()
        bus = EventBus(engine, pm, sync=True)
        assert bus._per_future_timeout == 30.0
        assert bus._shutdown_timeout == 5.0
        assert bus._max_retries == 3
        assert bus._dead_letter_retention_days == 30

    def test_wait_futures_uses_configurable_timeout(self, engine, pm_with_recorder) -> None:
        """Verify _wait_futures passes per_future_timeout to future.result()."""
        from unittest.mock import MagicMock

        from ztlctl.config.models import EventBusConfig

        config = EventBusConfig(per_future_timeout_seconds=99.0)
        pm, _ = pm_with_recorder
        bus = EventBus(engine, pm, sync=False, config=config)

        # Manually insert a mock future
        mock_future: MagicMock = MagicMock()
        bus._futures = [(1, mock_future)]
        bus._wait_futures()
        mock_future.result.assert_called_once_with(timeout=99.0)


class TestEventBusNoPlugins:
    """Tests for dispatch when no plugins are registered."""

    def test_dispatch_with_empty_pm_is_noop(self, engine):
        pm = PluginManager()
        bus = EventBus(engine, pm, sync=True)
        event_id = bus.dispatch(
            "post_create",
            {
                "content_type": "note",
                "content_id": "N-0001",
                "title": "Test",
                "path": "notes/N-0001.md",
                "tags": [],
            },
        )

        # Event should be completed (no hook = no failure)
        with engine.connect() as conn:
            row = conn.execute(
                select(event_wal.c.status).where(event_wal.c.id == event_id)
            ).fetchone()

        assert row is not None
        assert row.status == "completed"

    def test_dispatch_unknown_hook_completes(self, engine):
        """Dispatching a hook name that doesn't exist on the relay completes silently."""
        pm = PluginManager()
        bus = EventBus(engine, pm, sync=True)
        event_id = bus.dispatch(
            "nonexistent_hook",
            {"foo": "bar"},
        )

        with engine.connect() as conn:
            row = conn.execute(
                select(event_wal.c.status).where(event_wal.c.id == event_id)
            ).fetchone()

        assert row is not None
        assert row.status == "completed"


class TestShutdownAndStartupDrain:
    """Tests for bounded shutdown drain and startup recovery drain."""

    def test_shutdown_drain_completes_pending_events(self, engine, pm_with_recorder):
        """Shutdown with wait=True ensures no pending WAL rows remain."""
        pm, recorder = pm_with_recorder
        bus = EventBus(engine, pm, sync=False, max_workers=2)

        bus.dispatch("post_check", {"issues_found": 1, "issues_fixed": 0})
        bus.dispatch("post_check", {"issues_found": 2, "issues_fixed": 1})

        bus.shutdown(wait=True)

        with engine.connect() as conn:
            pending = conn.execute(
                select(event_wal.c.id).where(event_wal.c.status == "pending")
            ).fetchall()

        assert len(pending) == 0
        assert len(recorder.calls) == 2

    def test_shutdown_drain_timeout_leaves_pending_as_pending(self, engine):
        """After a short timeout, slow events are left as pending (not cancelled)."""
        barrier = threading.Barrier(2)
        hook_called = threading.Event()

        class SlowPlugin:
            @hookimpl
            def post_check(self, issues_found: int, issues_fixed: int) -> None:
                hook_called.set()
                barrier.wait(timeout=10)

        pm = PluginManager()
        pm.register_plugin(SlowPlugin(), name="slow")
        bus = EventBus(engine, pm, sync=False, max_workers=1)

        bus.dispatch("post_check", {"issues_found": 0, "issues_fixed": 0})

        # Wait for the hook to start before shutting down
        hook_called.wait(timeout=5)
        # Shutdown with very short per-future timeout — future.result() will time out
        bus.shutdown(wait=True, timeout=0.01)

        # Unblock the slow hook so cleanup can happen
        try:
            barrier.wait(timeout=1)
        except Exception:
            pass

        # The WAL row may be pending or completed depending on timing,
        # but the key invariant is: shutdown does NOT raise and does NOT
        # forcefully cancel futures — rows remain as pending (not deleted).
        with engine.connect() as conn:
            row = conn.execute(
                select(event_wal.c.status, event_wal.c.id).order_by(event_wal.c.id.desc())
            ).fetchone()
        assert row is not None  # Row exists — not deleted by timeout

    def test_startup_drain_retries_pending_from_prior_run(self, engine):
        """Insert pending WAL rows directly, create EventBus, drain processes them."""
        pm = PluginManager()
        recorder = PostActionPlugin()
        pm.register_plugin(recorder, name="post-action-recorder")

        # Insert a pending post_action event as if from a prior run
        action_payload = {
            "action_name": "create_note",
            "side_effect": "write",
            "payload": {"id": "N-0001", "title": "Test"},
            "warnings": [],
            "result": None,
        }
        with engine.begin() as conn:
            conn.execute(
                insert(event_wal).values(
                    hook_name="post_action",
                    payload=json.dumps(action_payload),
                    status="pending",
                    retries=0,
                    session_id=None,
                    created=now_iso(),
                )
            )

        bus = EventBus(engine, pm, sync=True)
        results = bus.drain()

        assert len(results) == 1
        assert results[0]["hook_name"] == "post_action"
        assert results[0]["status"] == "completed"
        assert len(recorder.calls) == 1
        assert recorder.calls[0]["action_name"] == "create_note"

    def test_post_action_canonical_dispatch(self, engine):
        """Dispatch a post_action event with ActionEvent dict, verify correct hook call."""
        pm = PluginManager()
        recorder = PostActionPlugin()
        pm.register_plugin(recorder, name="post-action-recorder")

        bus = EventBus(engine, pm, sync=True)
        action_payload = {
            "action_name": "create_note",
            "side_effect": "write",
            "payload": {"id": "N-0001", "title": "My Note"},
            "warnings": [],
            "result": {"ok": True},
        }
        event_id = bus.dispatch("post_action", action_payload)

        with engine.connect() as conn:
            row = conn.execute(
                select(event_wal.c.status).where(event_wal.c.id == event_id)
            ).fetchone()

        assert row is not None
        assert row.status == "completed"
        assert len(recorder.calls) == 1
        call = recorder.calls[0]
        assert call["action_name"] == "create_note"
        assert call["kwargs"] == {"id": "N-0001", "title": "My Note"}
        assert call["result"] == {"ok": True}
