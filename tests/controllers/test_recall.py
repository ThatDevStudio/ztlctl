"""Tests for RecallController — smoke tests for temporal, topic, and topology recall."""

from __future__ import annotations

from tests.conftest import start_session
from ztlctl.controllers.recall import RecallController
from ztlctl.infrastructure.vault import Vault
from ztlctl.services.session import SessionService

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _close_session(vault: Vault) -> None:
    """Close the active session."""
    result = SessionService(vault).close()
    assert result.ok, result.error


def _add_log(vault: Vault, message: str) -> None:
    """Add a log entry to the active session."""
    result = SessionService(vault).log_entry(message)
    assert result.ok, result.error


# ---------------------------------------------------------------------------
# RecallController smoke tests
# ---------------------------------------------------------------------------


class TestRecallController:
    def test_recall_temporal_empty_vault(self, vault: Vault) -> None:
        result = RecallController(vault).recall_temporal()
        assert result.ok
        assert result.data["count"] == 0
        assert result.data["sessions"] == []

    def test_recall_temporal_with_sessions(self, vault: Vault) -> None:
        start_session(vault, "Session A")
        _add_log(vault, "Did some work")
        _close_session(vault)

        result = RecallController(vault).recall_temporal()
        assert result.ok
        assert result.data["count"] == 1
        sessions = result.data["sessions"]
        assert len(sessions) == 1
        assert sessions[0]["topic"] == "Session A"

    def test_recall_temporal_with_date_filter(self, vault: Vault) -> None:
        start_session(vault, "Recent Session")
        _close_session(vault)

        # Should include the session created today
        result = RecallController(vault).recall_temporal(
            from_date="2020-01-01", to_date="2099-12-31"
        )
        assert result.ok
        assert result.data["count"] == 1

    def test_recall_topic_matching(self, vault: Vault) -> None:
        start_session(vault, "Bug Fix Session")
        _add_log(vault, "Fixed a critical authentication bug in login flow")
        _close_session(vault)

        result = RecallController(vault).recall_topic("authentication")
        assert result.ok
        assert result.data["count"] == 1
        assert result.data["query"] == "authentication"
        sessions = result.data["sessions"]
        assert len(sessions) == 1
        assert sessions[0]["topic"] == "Bug Fix Session"

    def test_recall_topic_no_match(self, vault: Vault) -> None:
        start_session(vault, "Some Session")
        _add_log(vault, "Worked on unrelated things")
        _close_session(vault)

        result = RecallController(vault).recall_topic("zzz_xyz_nonexistent")
        assert result.ok
        assert result.data["count"] == 0

    def test_recall_topic_empty_query_returns_error(self, vault: Vault) -> None:
        result = RecallController(vault).recall_topic("")
        assert not result.ok
        assert result.error is not None
        assert result.error.code == "EMPTY_QUERY"

    def test_recall_topology_stub_returns_ok(self, vault: Vault) -> None:
        result = RecallController(vault).recall_topology()
        assert result.ok
        assert "nodes" in result.data

    def test_recall_topology_respects_limit_param(self, vault: Vault) -> None:
        result = RecallController(vault).recall_topology(limit=5)
        assert result.ok
        assert result.data["limit"] == 5
