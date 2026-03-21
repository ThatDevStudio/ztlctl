"""Tests for ActionEvent domain model."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from ztlctl.domain.events import ActionEvent


class TestActionEventDefaults:
    def test_minimal_valid_event(self) -> None:
        event = ActionEvent(action_name="create_note", payload={"id": "x", "type": "note"})
        assert event.action_name == "create_note"
        assert event.payload == {"id": "x", "type": "note"}

    def test_side_effect_defaults_to_write(self) -> None:
        event = ActionEvent(action_name="create_note", payload={})
        assert event.side_effect == "write"

    def test_warnings_defaults_to_empty_list(self) -> None:
        event = ActionEvent(action_name="create_note", payload={})
        assert event.warnings == []

    def test_result_defaults_to_none(self) -> None:
        event = ActionEvent(action_name="create_note", payload={})
        assert event.result is None


class TestActionEventValidation:
    def test_side_effect_write_is_valid(self) -> None:
        event = ActionEvent(action_name="create_note", side_effect="write", payload={})
        assert event.side_effect == "write"

    def test_side_effect_read_is_valid(self) -> None:
        event = ActionEvent(action_name="query_notes", side_effect="read", payload={})
        assert event.side_effect == "read"

    def test_side_effect_invalid_raises(self) -> None:
        with pytest.raises(ValidationError):
            ActionEvent(action_name="create_note", side_effect="invalid", payload={})  # type: ignore[arg-type]

    def test_full_event_with_all_fields(self) -> None:
        event = ActionEvent(
            action_name="create_note",
            side_effect="write",
            payload={"id": "x", "type": "note"},
            warnings=["missing tag"],
            result={"ok": True},
        )
        assert event.warnings == ["missing tag"]
        assert event.result == {"ok": True}


class TestActionEventFrozen:
    def test_frozen_prevents_assignment(self) -> None:
        event = ActionEvent(action_name="create_note", payload={})
        with pytest.raises(Exception):
            event.action_name = "changed"  # type: ignore[misc]

    def test_frozen_prevents_payload_reassignment(self) -> None:
        event = ActionEvent(action_name="create_note", payload={})
        with pytest.raises(Exception):
            event.payload = {"new": "value"}  # type: ignore[misc]


class TestActionEventSerialization:
    def test_model_dump_json_produces_valid_json(self) -> None:
        import json

        event = ActionEvent(
            action_name="create_note",
            payload={"id": "x", "type": "note"},
        )
        json_str = event.model_dump_json()
        # Must not raise
        parsed = json.loads(json_str)
        assert parsed["action_name"] == "create_note"
        assert parsed["side_effect"] == "write"
        assert parsed["warnings"] == []
        assert parsed["result"] is None
