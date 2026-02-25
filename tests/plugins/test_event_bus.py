"""Tests for EventBus — WAL-backed async event dispatch."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pluggy
import pytest
from sqlalchemy import select

from ztlctl.infrastructure.database.engine import init_database
from ztlctl.infrastructure.database.schema import event_wal
from ztlctl.plugins.event_bus import EventBus
from ztlctl.plugins.manager import PluginManager

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
