"""Content types and classification enums.

These enums define the four content types, note/reference subtypes,
and the three vault spaces from DESIGN.md Section 2.
"""

from __future__ import annotations

from enum import StrEnum


class ContentType(StrEnum):
    """Primary content types in the vault."""

    NOTE = "note"
    REFERENCE = "reference"
    LOG = "log"
    TASK = "task"


class NoteSubtype(StrEnum):
    """Subtypes for notes with specific lifecycle rules."""

    DECISION = "decision"
    KNOWLEDGE = "knowledge"


class RefSubtype(StrEnum):
    """Classification subtypes for references (no lifecycle enforcement)."""

    ARTICLE = "article"
    TOOL = "tool"
    SPEC = "spec"


class Space(StrEnum):
    """Vault directory spaces."""

    SELF = "self"
    NOTES = "notes"
    OPS = "ops"
