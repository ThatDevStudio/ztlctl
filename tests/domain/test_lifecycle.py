"""Tests for lifecycle status enums and transitions."""

import pytest

from ztlctl.domain.lifecycle import (
    DECISION_TRANSITIONS,
    GARDEN_TRANSITIONS,
    LOG_TRANSITIONS,
    NOTE_TRANSITIONS,
    TASK_TRANSITIONS,
    DecisionStatus,
    GardenMaturity,
    NoteStatus,
    ReferenceStatus,
    TaskStatus,
    is_valid_transition,
)


class TestNoteStatus:
    def test_members(self) -> None:
        assert set(NoteStatus) == {
            NoteStatus.DRAFT,
            NoteStatus.LINKED,
            NoteStatus.CONNECTED,
        }

    def test_transitions(self) -> None:
        assert is_valid_transition("draft", "linked", NOTE_TRANSITIONS)
        assert is_valid_transition("linked", "connected", NOTE_TRANSITIONS)
        assert not is_valid_transition("draft", "connected", NOTE_TRANSITIONS)
        assert not is_valid_transition("connected", "draft", NOTE_TRANSITIONS)


class TestTaskStatus:
    def test_members(self) -> None:
        assert {s.value for s in TaskStatus} == {
            "inbox",
            "active",
            "blocked",
            "done",
            "dropped",
        }

    def test_transitions(self) -> None:
        assert is_valid_transition("inbox", "active", TASK_TRANSITIONS)
        assert is_valid_transition("inbox", "dropped", TASK_TRANSITIONS)
        assert is_valid_transition("active", "blocked", TASK_TRANSITIONS)
        assert is_valid_transition("active", "done", TASK_TRANSITIONS)
        assert not is_valid_transition("done", "active", TASK_TRANSITIONS)
        assert not is_valid_transition("dropped", "inbox", TASK_TRANSITIONS)


class TestDecisionStatus:
    def test_members(self) -> None:
        assert {s.value for s in DecisionStatus} == {
            "proposed",
            "accepted",
            "superseded",
        }

    def test_immutability_path(self) -> None:
        """Decisions follow proposed -> accepted -> superseded only."""
        assert is_valid_transition("proposed", "accepted", DECISION_TRANSITIONS)
        assert is_valid_transition("accepted", "superseded", DECISION_TRANSITIONS)
        assert not is_valid_transition("accepted", "proposed", DECISION_TRANSITIONS)
        assert not is_valid_transition("superseded", "accepted", DECISION_TRANSITIONS)


class TestLogStatus:
    def test_reopenable(self) -> None:
        """Logs can be reopened: closed -> open."""
        assert is_valid_transition("open", "closed", LOG_TRANSITIONS)
        assert is_valid_transition("closed", "open", LOG_TRANSITIONS)


class TestReferenceStatus:
    def test_members(self) -> None:
        assert {s.value for s in ReferenceStatus} == {"captured", "annotated"}


class TestGardenMaturity:
    def test_members(self) -> None:
        assert {s.value for s in GardenMaturity} == {"seed", "budding", "evergreen"}

    def test_transitions(self) -> None:
        assert is_valid_transition("seed", "budding", GARDEN_TRANSITIONS)
        assert is_valid_transition("budding", "evergreen", GARDEN_TRANSITIONS)
        assert not is_valid_transition("seed", "evergreen", GARDEN_TRANSITIONS)
        assert not is_valid_transition("evergreen", "seed", GARDEN_TRANSITIONS)


class TestInvalidTransition:
    def test_unknown_status(self) -> None:
        """Unknown current status returns False."""
        assert not is_valid_transition("nonexistent", "draft", NOTE_TRANSITIONS)

    @pytest.mark.parametrize(
        "current,target,transitions",
        [
            ("draft", "draft", NOTE_TRANSITIONS),
            ("inbox", "inbox", TASK_TRANSITIONS),
            ("seed", "seed", GARDEN_TRANSITIONS),
        ],
    )
    def test_self_transition_disallowed(
        self, current: str, target: str, transitions: dict[str, list[str]]
    ) -> None:
        """Self-transitions are not allowed."""
        assert not is_valid_transition(current, target, transitions)
