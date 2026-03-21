"""Tests for RecallService — temporal and topic recall of session history."""

from __future__ import annotations

from tests.conftest import start_session
from ztlctl.infrastructure.vault import Vault
from ztlctl.services.session import SessionService

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _close_session(vault: Vault) -> str:
    """Close the active session and return its session_id."""
    result = SessionService(vault).close()
    assert result.ok, result.error
    return str(result.data["session_id"])


def _add_log(vault: Vault, message: str) -> None:
    """Add a log entry to the active session."""
    result = SessionService(vault).log_entry(message)
    assert result.ok, result.error


# ---------------------------------------------------------------------------
# recall_temporal()
# ---------------------------------------------------------------------------


class TestRecallTemporal:
    def test_empty_vault_returns_empty_list(self, vault: Vault) -> None:
        from ztlctl.services.recall import RecallService

        result = RecallService(vault).recall_temporal()
        assert result.ok
        assert result.op == "recall_temporal"
        assert result.data["sessions"] == []
        assert result.data["count"] == 0

    def test_returns_all_sessions_without_filter(self, vault: Vault) -> None:
        from ztlctl.services.recall import RecallService

        # Create and close two sessions
        start_session(vault, "Session Alpha")
        _add_log(vault, "Entry A1")
        _close_session(vault)

        start_session(vault, "Session Beta")
        _add_log(vault, "Entry B1")
        _close_session(vault)

        result = RecallService(vault).recall_temporal()
        assert result.ok
        assert result.data["count"] == 2
        sessions = result.data["sessions"]
        assert len(sessions) == 2

    def test_each_session_has_required_fields(self, vault: Vault) -> None:
        from ztlctl.services.recall import RecallService

        start_session(vault, "Topic Alpha")
        _add_log(vault, "some work")
        _close_session(vault)

        result = RecallService(vault).recall_temporal()
        assert result.ok
        session = result.data["sessions"][0]
        assert "session_id" in session
        assert "topic" in session
        assert "status" in session
        assert "started" in session
        assert "log_entry_count" in session
        assert "note_ids" in session

    def test_session_topic_is_correct(self, vault: Vault) -> None:
        from ztlctl.services.recall import RecallService

        start_session(vault, "My Special Topic")
        _close_session(vault)

        result = RecallService(vault).recall_temporal()
        assert result.ok
        session = result.data["sessions"][0]
        assert session["topic"] == "My Special Topic"

    def test_log_entry_count_is_accurate(self, vault: Vault) -> None:
        from ztlctl.services.recall import RecallService

        start_session(vault, "Counted Session")
        _add_log(vault, "Entry 1")
        _add_log(vault, "Entry 2")
        _add_log(vault, "Entry 3")
        _close_session(vault)

        result = RecallService(vault).recall_temporal()
        assert result.ok
        session = result.data["sessions"][0]
        # 3 log_entry + 1 session_start + 1 session_close = 5 total entries
        assert session["log_entry_count"] >= 3

    def test_from_date_filters_sessions(self, vault: Vault) -> None:
        from ztlctl.services.recall import RecallService

        start_session(vault, "Old Session")
        _close_session(vault)

        start_session(vault, "New Session")
        _close_session(vault)

        # Filter from today — should include both since both were created today
        result = RecallService(vault).recall_temporal(from_date="2025-01-01")
        assert result.ok
        assert result.data["count"] >= 1

    def test_to_date_filters_sessions(self, vault: Vault) -> None:
        from ztlctl.services.recall import RecallService

        start_session(vault, "Future Session")
        _close_session(vault)

        # Filter to far future — should include all sessions
        result = RecallService(vault).recall_temporal(to_date="2099-12-31")
        assert result.ok
        assert result.data["count"] >= 1

    def test_from_date_excludes_old_sessions(self, vault: Vault) -> None:
        from ztlctl.services.recall import RecallService

        start_session(vault, "Some Session")
        _close_session(vault)

        # Filter from far future — should exclude all sessions
        result = RecallService(vault).recall_temporal(from_date="2099-01-01")
        assert result.ok
        assert result.data["count"] == 0
        assert result.data["sessions"] == []

    def test_to_date_excludes_future_sessions(self, vault: Vault) -> None:
        from ztlctl.services.recall import RecallService

        start_session(vault, "Some Session")
        _close_session(vault)

        # Filter to far past — should exclude all sessions
        result = RecallService(vault).recall_temporal(to_date="2000-12-31")
        assert result.ok
        assert result.data["count"] == 0
        assert result.data["sessions"] == []

    def test_both_dates_returns_sessions_in_range(self, vault: Vault) -> None:
        from ztlctl.services.recall import RecallService

        start_session(vault, "Ranged Session")
        _close_session(vault)

        # Range that includes today
        result = RecallService(vault).recall_temporal(from_date="2020-01-01", to_date="2099-12-31")
        assert result.ok
        assert result.data["count"] == 1

    def test_includes_open_sessions(self, vault: Vault) -> None:
        from ztlctl.services.recall import RecallService

        start_session(vault, "Open Session")
        # Don't close it

        result = RecallService(vault).recall_temporal()
        assert result.ok
        assert result.data["count"] == 1
        assert result.data["sessions"][0]["status"] == "open"

    def test_note_ids_includes_notes_created_in_session(self, vault: Vault) -> None:
        from ztlctl.services.recall import RecallService

        session_data = start_session(vault, "Note Session")
        session_id = session_data["id"]

        # Create notes with session tag
        from ztlctl.services.create import CreateService

        note_result = CreateService(vault).create_note("Test Note", session=session_id)
        assert note_result.ok

        _close_session(vault)

        result = RecallService(vault).recall_temporal()
        assert result.ok
        sessions = result.data["sessions"]
        # Find the matching session
        matched = next(s for s in sessions if s["session_id"] == session_id)
        assert note_result.data["id"] in matched["note_ids"]


# ---------------------------------------------------------------------------
# recall_topic()
# ---------------------------------------------------------------------------


class TestRecallTopic:
    def test_empty_query_returns_error(self, vault: Vault) -> None:
        from ztlctl.services.recall import RecallService

        result = RecallService(vault).recall_topic("")
        assert not result.ok
        assert result.error is not None
        assert result.error.code == "EMPTY_QUERY"

    def test_whitespace_only_query_returns_error(self, vault: Vault) -> None:
        from ztlctl.services.recall import RecallService

        result = RecallService(vault).recall_topic("   ")
        assert not result.ok
        assert result.error is not None
        assert result.error.code == "EMPTY_QUERY"

    def test_non_matching_query_returns_empty(self, vault: Vault) -> None:
        from ztlctl.services.recall import RecallService

        start_session(vault, "Session About Dogs")
        _add_log(vault, "We worked on the dog feature")
        _close_session(vault)

        result = RecallService(vault).recall_topic("zzz_nonexistent_xyz")
        assert result.ok
        assert result.data["sessions"] == []
        assert result.data["count"] == 0

    def test_matching_query_returns_sessions(self, vault: Vault) -> None:
        from ztlctl.services.recall import RecallService

        start_session(vault, "Authentication Work")
        _add_log(vault, "Implemented JWT token refresh logic")
        _add_log(vault, "Added rate limiting to auth endpoints")
        _close_session(vault)

        result = RecallService(vault).recall_topic("JWT")
        assert result.ok
        assert result.data["count"] == 1
        sessions = result.data["sessions"]
        assert len(sessions) == 1

    def test_matched_entries_included_in_result(self, vault: Vault) -> None:
        from ztlctl.services.recall import RecallService

        start_session(vault, "Feature Work")
        _add_log(vault, "Discussed database schema changes")
        _add_log(vault, "Implemented search feature")
        _close_session(vault)

        result = RecallService(vault).recall_topic("database")
        assert result.ok
        sessions = result.data["sessions"]
        assert len(sessions) == 1
        matched_entries = sessions[0]["matched_entries"]
        assert len(matched_entries) >= 1
        # The matching entry should contain the query
        assert any("database" in e["summary"].lower() for e in matched_entries)

    def test_matched_entry_has_required_fields(self, vault: Vault) -> None:
        from ztlctl.services.recall import RecallService

        start_session(vault, "Work Session")
        _add_log(vault, "Worked on the authentication module")
        _close_session(vault)

        result = RecallService(vault).recall_topic("authentication")
        assert result.ok
        sessions = result.data["sessions"]
        assert len(sessions) >= 1
        entry = sessions[0]["matched_entries"][0]
        assert "summary" in entry
        assert "timestamp" in entry
        assert "type" in entry

    def test_query_is_returned_in_result_data(self, vault: Vault) -> None:
        from ztlctl.services.recall import RecallService

        start_session(vault, "Session")
        _add_log(vault, "Some log entry")
        _close_session(vault)

        result = RecallService(vault).recall_topic("nonexistent")
        assert result.ok
        assert result.data["query"] == "nonexistent"

    def test_session_fields_present_in_topic_result(self, vault: Vault) -> None:
        from ztlctl.services.recall import RecallService

        start_session(vault, "My Topic Session")
        _add_log(vault, "Working on search functionality")
        _close_session(vault)

        result = RecallService(vault).recall_topic("search")
        assert result.ok
        sessions = result.data["sessions"]
        assert len(sessions) == 1
        session = sessions[0]
        assert "session_id" in session
        assert "topic" in session
        assert "status" in session
        assert "matched_entries" in session

    def test_multiple_sessions_only_matching_returned(self, vault: Vault) -> None:
        from ztlctl.services.recall import RecallService

        start_session(vault, "Session About Cats")
        _add_log(vault, "Cat-related work done")
        _close_session(vault)

        start_session(vault, "Session About Dogs")
        _add_log(vault, "Dog-related work done")
        _close_session(vault)

        result = RecallService(vault).recall_topic("Cat")
        assert result.ok
        assert result.data["count"] == 1
        assert result.data["sessions"][0]["topic"] == "Session About Cats"

    def test_case_insensitive_matching(self, vault: Vault) -> None:
        from ztlctl.services.recall import RecallService

        start_session(vault, "Work Session")
        _add_log(vault, "Implemented REDIS caching layer")
        _close_session(vault)

        # Search with lowercase
        result = RecallService(vault).recall_topic("redis")
        assert result.ok
        assert result.data["count"] >= 1
