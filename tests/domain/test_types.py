"""Tests for domain type enums."""

from ztlctl.domain.types import ContentType, NoteSubtype, RefSubtype, Space


class TestContentType:
    def test_members(self) -> None:
        assert set(ContentType) == {
            ContentType.NOTE,
            ContentType.REFERENCE,
            ContentType.LOG,
            ContentType.TASK,
        }

    def test_values(self) -> None:
        assert ContentType.NOTE.value == "note"
        assert ContentType.REFERENCE.value == "reference"
        assert ContentType.LOG.value == "log"
        assert ContentType.TASK.value == "task"

    def test_str_enum(self) -> None:
        assert ContentType.NOTE == "note"
        assert isinstance(ContentType.NOTE, str)


class TestNoteSubtype:
    def test_members(self) -> None:
        assert set(NoteSubtype) == {NoteSubtype.DECISION, NoteSubtype.KNOWLEDGE}

    def test_values(self) -> None:
        assert NoteSubtype.DECISION.value == "decision"
        assert NoteSubtype.KNOWLEDGE.value == "knowledge"


class TestRefSubtype:
    def test_members(self) -> None:
        assert set(RefSubtype) == {RefSubtype.ARTICLE, RefSubtype.TOOL, RefSubtype.SPEC}


class TestSpace:
    def test_members(self) -> None:
        assert set(Space) == {Space.SELF, Space.NOTES, Space.OPS}

    def test_values(self) -> None:
        assert Space.SELF.value == "self"
        assert Space.NOTES.value == "notes"
        assert Space.OPS.value == "ops"
