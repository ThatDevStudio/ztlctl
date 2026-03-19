"""Tests for NoteTypeDefinition and NoteTypeRegistry."""

from __future__ import annotations

import pytest
from ztlctl.domain.registry import (
    NoteTypeDefinition,
    NoteTypeRegistry,
    get_note_type_registry,
)

from ztlctl.domain.content import (
    ContentModel,
    DecisionModel,
    KnowledgeModel,
    NoteModel,
    ReferenceModel,
    TaskModel,
)
from ztlctl.domain.lifecycle import (
    DECISION_TRANSITIONS,
    LOG_TRANSITIONS,
    NOTE_TRANSITIONS,
    REFERENCE_TRANSITIONS,
    TASK_TRANSITIONS,
)

# ---------------------------------------------------------------------------
# NoteTypeDefinition
# ---------------------------------------------------------------------------


class TestNoteTypeDefinition:
    def test_required_fields(self) -> None:
        """NoteTypeDefinition can be created with required fields."""
        ntd = NoteTypeDefinition(
            name="note",
            content_type="note",
            model_cls=NoteModel,
            transitions=NOTE_TRANSITIONS,
            template_name="note.md.j2",
        )
        assert ntd.name == "note"
        assert ntd.content_type == "note"
        assert ntd.model_cls is NoteModel
        assert ntd.transitions == NOTE_TRANSITIONS
        assert ntd.template_name == "note.md.j2"

    def test_default_fields(self) -> None:
        """Optional fields have sensible defaults."""
        ntd = NoteTypeDefinition(
            name="note",
            content_type="note",
            model_cls=NoteModel,
            transitions=NOTE_TRANSITIONS,
            template_name="note.md.j2",
        )
        assert ntd.required_sections == []
        assert ntd.initial_status == ""
        assert ntd.is_subtype is False
        assert ntd.parent_type is None

    def test_frozen(self) -> None:
        """NoteTypeDefinition is immutable (frozen dataclass)."""
        ntd = NoteTypeDefinition(
            name="note",
            content_type="note",
            model_cls=NoteModel,
            transitions=NOTE_TRANSITIONS,
            template_name="note.md.j2",
        )
        with pytest.raises((TypeError, AttributeError)):
            ntd.name = "changed"  # type: ignore[misc]

    def test_subtype_fields(self) -> None:
        """Subtypes can set is_subtype=True and parent_type."""
        ntd = NoteTypeDefinition(
            name="decision",
            content_type="note",
            model_cls=DecisionModel,
            transitions=DECISION_TRANSITIONS,
            template_name="decision.md.j2",
            required_sections=["Context", "Choice", "Rationale", "Alternatives", "Consequences"],
            initial_status="proposed",
            is_subtype=True,
            parent_type="note",
        )
        assert ntd.is_subtype is True
        assert ntd.parent_type == "note"
        assert ntd.initial_status == "proposed"
        assert "Context" in ntd.required_sections


# ---------------------------------------------------------------------------
# NoteTypeRegistry
# ---------------------------------------------------------------------------


class TestNoteTypeRegistry:
    def test_register_and_get(self) -> None:
        """register() stores NoteTypeDefinition; get() retrieves by name."""
        registry = NoteTypeRegistry()
        ntd = NoteTypeDefinition(
            name="note",
            content_type="note",
            model_cls=NoteModel,
            transitions=NOTE_TRANSITIONS,
            template_name="note.md.j2",
        )
        registry.register(ntd)
        assert registry.get("note") is ntd

    def test_get_unknown_raises_key_error(self) -> None:
        """get() raises KeyError for unregistered names."""
        registry = NoteTypeRegistry()
        with pytest.raises(KeyError):
            registry.get("nonexistent")

    def test_register_duplicate_raises_value_error(self) -> None:
        """Registering a name already registered raises ValueError."""
        registry = NoteTypeRegistry()
        ntd = NoteTypeDefinition(
            name="note",
            content_type="note",
            model_cls=NoteModel,
            transitions=NOTE_TRANSITIONS,
            template_name="note.md.j2",
        )
        registry.register(ntd)
        with pytest.raises(ValueError, match="already registered"):
            registry.register(ntd)

    def test_register_subtype_without_parent_raises(self) -> None:
        """Subtype with parent_type=None raises ValueError on register."""
        registry = NoteTypeRegistry()
        ntd = NoteTypeDefinition(
            name="knowledge",
            content_type="note",
            model_cls=KnowledgeModel,
            transitions=NOTE_TRANSITIONS,
            template_name="knowledge.md.j2",
            is_subtype=True,
            parent_type=None,  # missing parent
        )
        with pytest.raises(ValueError, match="parent_type"):
            registry.register(ntd)

    def test_register_invalid_transitions_raises(self) -> None:
        """Transition map with unreachable target states raises ValueError."""
        registry = NoteTypeRegistry()
        bad_transitions: dict[str, list[str]] = {
            "open": ["in_progress"],
            # "in_progress" is a target but not a key — unreachable!
        }
        ntd = NoteTypeDefinition(
            name="bad",
            content_type="task",
            model_cls=TaskModel,
            transitions=bad_transitions,
            template_name="task.md.j2",
        )
        with pytest.raises(ValueError, match="in_progress"):
            registry.register(ntd)

    def test_list_types_returns_all(self) -> None:
        """list_types() with no filter returns all registered types."""
        registry = NoteTypeRegistry()
        note_ntd = NoteTypeDefinition(
            name="note",
            content_type="note",
            model_cls=NoteModel,
            transitions=NOTE_TRANSITIONS,
            template_name="note.md.j2",
        )
        ref_ntd = NoteTypeDefinition(
            name="reference",
            content_type="reference",
            model_cls=ReferenceModel,
            transitions=REFERENCE_TRANSITIONS,
            template_name="reference.md.j2",
        )
        registry.register(note_ntd)
        registry.register(ref_ntd)
        all_types = registry.list_types()
        assert len(all_types) == 2
        names = {t.name for t in all_types}
        assert names == {"note", "reference"}

    def test_list_types_filters_by_content_type(self) -> None:
        """list_types(content_type=...) filters results."""
        registry = NoteTypeRegistry()
        note_ntd = NoteTypeDefinition(
            name="note",
            content_type="note",
            model_cls=NoteModel,
            transitions=NOTE_TRANSITIONS,
            template_name="note.md.j2",
        )
        ref_ntd = NoteTypeDefinition(
            name="reference",
            content_type="reference",
            model_cls=ReferenceModel,
            transitions=REFERENCE_TRANSITIONS,
            template_name="reference.md.j2",
        )
        registry.register(note_ntd)
        registry.register(ref_ntd)
        note_types = registry.list_types(content_type="note")
        assert len(note_types) == 1
        assert note_types[0].name == "note"

    def test_register_custom_type_succeeds(self) -> None:
        """Plugin-contributed NoteTypeDefinitions can be registered."""
        registry = NoteTypeRegistry()
        custom_transitions: dict[str, list[str]] = {
            "draft": ["published"],
            "published": [],
        }
        custom_ntd = NoteTypeDefinition(
            name="custom_note",
            content_type="note",
            model_cls=NoteModel,
            transitions=custom_transitions,
            template_name="note.md.j2",
        )
        registry.register(custom_ntd)
        assert registry.get("custom_note").name == "custom_note"


# ---------------------------------------------------------------------------
# get_note_type_registry() — built-in registrations
# ---------------------------------------------------------------------------


class TestGetNoteTypeRegistry:
    def test_returns_singleton(self) -> None:
        """get_note_type_registry() returns the same instance each time."""
        r1 = get_note_type_registry()
        r2 = get_note_type_registry()
        assert r1 is r2

    def test_all_nine_types_registered(self) -> None:
        """Singleton has all 9 built-in types registered."""
        registry = get_note_type_registry()
        all_types = registry.list_types()
        names = {t.name for t in all_types}
        expected = {
            "note",
            "knowledge",
            "decision",
            "reference",
            "article",
            "tool",
            "spec",
            "task",
            "log",
        }
        assert names == expected

    def test_builtin_note_type(self) -> None:
        """Built-in 'note' type has expected fields."""
        registry = get_note_type_registry()
        ntd = registry.get("note")
        assert ntd.content_type == "note"
        assert ntd.model_cls is NoteModel
        assert ntd.transitions == NOTE_TRANSITIONS
        assert ntd.template_name == "note.md.j2"
        assert ntd.is_subtype is False
        assert ntd.parent_type is None

    def test_builtin_decision_type(self) -> None:
        """Built-in 'decision' type has custom transitions and sections."""
        registry = get_note_type_registry()
        ntd = registry.get("decision")
        assert ntd.content_type == "note"
        assert ntd.model_cls is DecisionModel
        assert ntd.transitions == DECISION_TRANSITIONS
        assert ntd.template_name == "decision.md.j2"
        assert ntd.is_subtype is True
        assert ntd.parent_type == "note"
        assert ntd.required_sections == [
            "Context",
            "Choice",
            "Rationale",
            "Alternatives",
            "Consequences",
        ]
        assert ntd.initial_status == "proposed"

    def test_builtin_knowledge_type(self) -> None:
        """Built-in 'knowledge' type inherits NOTE_TRANSITIONS."""
        registry = get_note_type_registry()
        ntd = registry.get("knowledge")
        assert ntd.is_subtype is True
        assert ntd.parent_type == "note"
        assert ntd.transitions == NOTE_TRANSITIONS
        assert ntd.template_name == "knowledge.md.j2"

    def test_builtin_article_type(self) -> None:
        """Built-in 'article' type is reference subtype with parent transitions."""
        registry = get_note_type_registry()
        ntd = registry.get("article")
        assert ntd.content_type == "reference"
        assert ntd.is_subtype is True
        assert ntd.parent_type == "reference"
        assert ntd.transitions == REFERENCE_TRANSITIONS
        assert ntd.template_name == "reference.md.j2"

    def test_builtin_log_type(self) -> None:
        """Built-in 'log' type uses LOG_TRANSITIONS with no template."""
        registry = get_note_type_registry()
        ntd = registry.get("log")
        assert ntd.content_type == "log"
        assert ntd.transitions == LOG_TRANSITIONS
        assert ntd.template_name == ""
        assert ntd.model_cls is ContentModel

    def test_builtin_task_type(self) -> None:
        """Built-in 'task' type uses TASK_TRANSITIONS."""
        registry = get_note_type_registry()
        ntd = registry.get("task")
        assert ntd.content_type == "task"
        assert ntd.model_cls is TaskModel
        assert ntd.transitions == TASK_TRANSITIONS
        assert ntd.template_name == "task.md.j2"
        assert ntd.is_subtype is False

    def test_builtin_tool_and_spec_are_reference_subtypes(self) -> None:
        """tool and spec are reference subtypes with REFERENCE_TRANSITIONS."""
        registry = get_note_type_registry()
        for name in ("tool", "spec"):
            ntd = registry.get(name)
            assert ntd.content_type == "reference"
            assert ntd.is_subtype is True
            assert ntd.parent_type == "reference"
            assert ntd.transitions == REFERENCE_TRANSITIONS

    def test_list_note_content_types(self) -> None:
        """list_types(content_type='note') returns note, knowledge, decision."""
        registry = get_note_type_registry()
        note_types = registry.list_types(content_type="note")
        names = {t.name for t in note_types}
        assert names == {"note", "knowledge", "decision"}

    def test_list_reference_content_types(self) -> None:
        """list_types(content_type='reference') returns reference, article, tool, spec."""
        registry = get_note_type_registry()
        ref_types = registry.list_types(content_type="reference")
        names = {t.name for t in ref_types}
        assert names == {"reference", "article", "tool", "spec"}
