"""Machine status and garden maturity lifecycle models.

Dual lifecycle from DESIGN.md Section 2:
- Machine lifecycle: computed/enforced by the tool (status transitions).
- Garden lifecycle: advisory, human-driven via Obsidian (maturity).

Machine status is always computed from structural properties, never
set directly by CLI command.
"""

from __future__ import annotations

from enum import StrEnum

# --- Machine status enums (per content type) ---


class NoteStatus(StrEnum):
    """Machine status for notes, based on link count thresholds."""

    DRAFT = "draft"
    LINKED = "linked"
    CONNECTED = "connected"


class ReferenceStatus(StrEnum):
    """Machine status for references."""

    CAPTURED = "captured"
    ANNOTATED = "annotated"


class LogStatus(StrEnum):
    """Machine status for session logs."""

    OPEN = "open"
    CLOSED = "closed"


class TaskStatus(StrEnum):
    """Machine status for tasks."""

    INBOX = "inbox"
    ACTIVE = "active"
    BLOCKED = "blocked"
    DONE = "done"
    DROPPED = "dropped"


class DecisionStatus(StrEnum):
    """Status for decision-subtype notes."""

    PROPOSED = "proposed"
    ACCEPTED = "accepted"
    SUPERSEDED = "superseded"


# --- Garden maturity (advisory, human-driven) ---


class GardenMaturity(StrEnum):
    """Garden lifecycle maturity levels for notes."""

    SEED = "seed"
    BUDDING = "budding"
    EVERGREEN = "evergreen"


# --- Transition maps ---

NOTE_TRANSITIONS: dict[str, list[str]] = {
    "draft": ["linked"],
    "linked": ["connected"],
    "connected": [],
}

REFERENCE_TRANSITIONS: dict[str, list[str]] = {
    "captured": ["annotated"],
    "annotated": [],
}

LOG_TRANSITIONS: dict[str, list[str]] = {
    "open": ["closed"],
    "closed": ["open"],  # reopenable
}

TASK_TRANSITIONS: dict[str, list[str]] = {
    "inbox": ["active", "dropped"],
    "active": ["blocked", "done", "dropped"],
    "blocked": ["active", "dropped"],
    "done": [],
    "dropped": [],
}

DECISION_TRANSITIONS: dict[str, list[str]] = {
    "proposed": ["accepted"],
    "accepted": ["superseded"],
    "superseded": [],
}

GARDEN_TRANSITIONS: dict[str, list[str]] = {
    "seed": ["budding"],
    "budding": ["evergreen"],
    "evergreen": [],
}


# --- Note status thresholds (outgoing link count) ---

NOTE_LINKED_THRESHOLD = 1  # outgoing links required for "linked"
NOTE_CONNECTED_THRESHOLD = 3  # outgoing links required for "connected"


def is_valid_transition(
    current: str,
    target: str,
    transitions: dict[str, list[str]],
) -> bool:
    """Check if transitioning from *current* to *target* is allowed."""
    allowed = transitions.get(current, [])
    return target in allowed


def compute_note_status(outgoing_link_count: int) -> str:
    """Compute note status from outgoing link count.

    Returns the highest status the note qualifies for based on
    link count thresholds.
    """
    if outgoing_link_count >= NOTE_CONNECTED_THRESHOLD:
        return str(NoteStatus.CONNECTED)
    if outgoing_link_count >= NOTE_LINKED_THRESHOLD:
        return str(NoteStatus.LINKED)
    return str(NoteStatus.DRAFT)
