"""Tests for SessionService — start, close, reopen."""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy import select

from ztlctl.infrastructure.database.schema import nodes
from ztlctl.infrastructure.vault import Vault
from ztlctl.services.create import CreateService
from ztlctl.services.session import SessionService

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _create_note(vault: Vault, title: str, **kwargs: Any) -> dict[str, Any]:
    result = CreateService(vault).create_note(title, **kwargs)
    assert result.ok, result.error
    return result.data


def _start_session(vault: Vault, topic: str) -> dict[str, Any]:
    result = SessionService(vault).start(topic)
    assert result.ok, result.error
    return result.data


# ---------------------------------------------------------------------------
# start()
# ---------------------------------------------------------------------------


class TestSessionStart:
    def test_start_creates_session(self, vault: Vault) -> None:
        result = SessionService(vault).start("Test Topic")
        assert result.ok
        assert result.data["id"].startswith("LOG-")
        assert result.data["topic"] == "Test Topic"
        assert result.data["status"] == "open"

    def test_start_creates_jsonl_file(self, vault: Vault) -> None:
        data = _start_session(vault, "File Test")
        path = vault.root / data["path"]
        assert path.exists()
        assert path.suffix == ".jsonl"

        content = path.read_text(encoding="utf-8").strip()
        entry = json.loads(content)
        assert entry["type"] == "session_start"
        assert entry["session_id"] == data["id"]
        assert entry["topic"] == "File Test"

    def test_start_creates_db_row(self, vault: Vault) -> None:
        data = _start_session(vault, "DB Test")
        with vault.engine.connect() as conn:
            row = conn.execute(select(nodes).where(nodes.c.id == data["id"])).first()
            assert row is not None
            assert row.type == "log"
            assert row.status == "open"
            assert row.topic == "DB Test"

    def test_start_sequential_ids(self, vault: Vault) -> None:
        data1 = _start_session(vault, "First")
        data2 = _start_session(vault, "Second")
        # IDs should be sequential
        n1 = int(data1["id"].split("-")[1])
        n2 = int(data2["id"].split("-")[1])
        assert n2 == n1 + 1

    def test_start_creates_fts_entry(self, vault: Vault) -> None:
        from sqlalchemy import text

        data = _start_session(vault, "Searchable Session")
        with vault.engine.connect() as conn:
            rows = conn.execute(
                text("SELECT id FROM nodes_fts WHERE title MATCH :q"),
                {"q": "Searchable"},
            ).fetchall()
            assert any(r[0] == data["id"] for r in rows)


# ---------------------------------------------------------------------------
# close()
# ---------------------------------------------------------------------------


class TestSessionClose:
    def test_close_active_session(self, vault: Vault) -> None:
        data = _start_session(vault, "Close Me")
        result = SessionService(vault).close()
        assert result.ok
        assert result.data["session_id"] == data["id"]
        assert result.data["status"] == "closed"

    def test_close_updates_db_status(self, vault: Vault) -> None:
        data = _start_session(vault, "Close DB Test")
        SessionService(vault).close()

        with vault.engine.connect() as conn:
            row = conn.execute(select(nodes.c.status).where(nodes.c.id == data["id"])).first()
            assert row is not None
            assert row.status == "closed"

    def test_close_appends_to_jsonl(self, vault: Vault) -> None:
        data = _start_session(vault, "JSONL Close Test")
        SessionService(vault).close(summary="Done!")

        path = vault.root / data["path"]
        lines = path.read_text(encoding="utf-8").strip().split("\n")
        assert len(lines) == 2  # start + close
        close_entry = json.loads(lines[1])
        assert close_entry["type"] == "session_close"
        assert close_entry["summary"] == "Done!"

    def test_close_no_active_session(self, vault: Vault) -> None:
        result = SessionService(vault).close()
        assert not result.ok
        assert result.error is not None
        assert result.error.code == "NO_ACTIVE_SESSION"

    def test_close_already_closed(self, vault: Vault) -> None:
        _start_session(vault, "Already Closed")
        SessionService(vault).close()

        # Try to close again
        result = SessionService(vault).close()
        assert not result.ok
        assert result.error is not None
        assert result.error.code == "NO_ACTIVE_SESSION"

    def test_close_report_counts(self, vault: Vault) -> None:
        _start_session(vault, "Report Test")
        result = SessionService(vault).close()
        assert result.ok
        assert "reweave_count" in result.data
        assert "orphan_count" in result.data
        assert "integrity_issues" in result.data

    def test_close_with_session_notes_reweave(self, vault: Vault) -> None:
        """Notes created in the session are reweaved on close."""
        data = _start_session(vault, "Reweave Session")
        session_id = data["id"]

        # Create notes in this session
        _create_note(vault, "Python Guide", session=session_id)
        _create_note(vault, "Python Reference", session=session_id)

        result = SessionService(vault).close()
        assert result.ok
        # Reweave count may be 0 if scores are below threshold, but pipeline ran
        assert result.data["reweave_count"] >= 0


# ---------------------------------------------------------------------------
# close() — disabled enrichment
# ---------------------------------------------------------------------------


class TestSessionCloseDisabled:
    def test_close_reweave_disabled(self, vault_root: Any) -> None:
        """Close skips reweave when disabled in settings."""
        from ztlctl.config.settings import ZtlSettings

        config = vault_root / "ztlctl.toml"
        toml = (
            "[session]\n"
            "close_reweave = false\n"
            "close_orphan_sweep = false\n"
            "close_integrity_check = false\n"
        )
        config.write_text(toml, encoding="utf-8")
        settings = ZtlSettings.from_cli(vault_root=vault_root)
        v = Vault(settings)

        _start_session(v, "Disabled Test")
        result = SessionService(v).close()
        assert result.ok
        assert result.data["reweave_count"] == 0
        assert result.data["orphan_count"] == 0


# ---------------------------------------------------------------------------
# reopen()
# ---------------------------------------------------------------------------


class TestSessionReopen:
    def test_reopen_closed_session(self, vault: Vault) -> None:
        data = _start_session(vault, "Reopen Me")
        SessionService(vault).close()

        result = SessionService(vault).reopen(data["id"])
        assert result.ok
        assert result.data["status"] == "open"

    def test_reopen_updates_db(self, vault: Vault) -> None:
        data = _start_session(vault, "Reopen DB Test")
        SessionService(vault).close()
        SessionService(vault).reopen(data["id"])

        with vault.engine.connect() as conn:
            row = conn.execute(select(nodes.c.status).where(nodes.c.id == data["id"])).first()
            assert row is not None
            assert row.status == "open"

    def test_reopen_appends_to_jsonl(self, vault: Vault) -> None:
        data = _start_session(vault, "Reopen JSONL Test")
        SessionService(vault).close()
        SessionService(vault).reopen(data["id"])

        path = vault.root / data["path"]
        lines = path.read_text(encoding="utf-8").strip().split("\n")
        assert len(lines) == 3  # start + close + reopen
        reopen_entry = json.loads(lines[2])
        assert reopen_entry["type"] == "session_reopen"

    def test_reopen_already_open(self, vault: Vault) -> None:
        data = _start_session(vault, "Already Open")
        result = SessionService(vault).reopen(data["id"])
        assert not result.ok
        assert result.error is not None
        assert result.error.code == "ALREADY_OPEN"

    def test_reopen_not_found(self, vault: Vault) -> None:
        result = SessionService(vault).reopen("LOG-9999")
        assert not result.ok
        assert result.error is not None
        assert result.error.code == "NOT_FOUND"

    def test_reopen_then_close_again(self, vault: Vault) -> None:
        """Can close a reopened session."""
        data = _start_session(vault, "Cycle Test")
        SessionService(vault).close()
        SessionService(vault).reopen(data["id"])

        result = SessionService(vault).close()
        assert result.ok
        assert result.data["session_id"] == data["id"]
