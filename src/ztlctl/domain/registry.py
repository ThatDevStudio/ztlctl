"""NoteTypeDefinition and NoteTypeRegistry — canonical type registry.

NoteTypeDefinition is a frozen dataclass that captures all metadata for
a note type (content type, model class, transition map, template, etc.).

NoteTypeRegistry stores NoteTypeDefinitions and validates integrity on
registration.  A module-level singleton ``_REGISTRY`` is pre-populated
with all 9 built-in types; ``get_note_type_registry()`` exposes it.

Plugin authors register custom types via ``get_note_type_registry().register()``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

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

if TYPE_CHECKING:
    pass


# ---------------------------------------------------------------------------
# NoteTypeDefinition
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class NoteTypeDefinition:
    """Metadata descriptor for a note type (built-in or plugin-contributed).

    Fields
    ------
    name
        Unique registry key (e.g. ``"note"``, ``"decision"``).
    content_type
        Parent content type (``"note"``, ``"reference"``, ``"task"``,
        ``"log"``).
    model_cls
        The Pydantic model class for this type.
    transitions
        Status transition map embedded inline (source of truth for this
        type's lifecycle).
    template_name
        Jinja2 template filename (empty string for DB-only types like
        ``"log"``).
    required_sections
        Markdown body sections required during validation.
    initial_status
        Initial status on creation.  Empty string means "use first key of
        transitions at runtime."
    is_subtype
        ``True`` for decision, knowledge, article, tool, spec.
    parent_type
        For subtypes: which content_type is the parent.  Must be set when
        ``is_subtype=True``.
    """

    name: str
    content_type: str
    model_cls: type[ContentModel]
    transitions: dict[str, list[str]]
    template_name: str
    required_sections: list[str] = field(default_factory=list)
    initial_status: str = ""
    is_subtype: bool = False
    parent_type: str | None = None


# ---------------------------------------------------------------------------
# NoteTypeRegistry
# ---------------------------------------------------------------------------


class NoteTypeRegistry:
    """Registry of NoteTypeDefinitions for all note types.

    Validates transition map integrity and subtype constraints on
    registration.  Thread safety is out of scope; registrations are
    expected to happen at module-load time only.
    """

    def __init__(self) -> None:
        self._types: dict[str, NoteTypeDefinition] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def register(self, note_type: NoteTypeDefinition) -> None:
        """Register *note_type*.

        Raises
        ------
        ValueError
            If the name is already registered, if ``is_subtype=True`` and
            ``parent_type`` is ``None``, or if the transition map has
            unreachable target states.
        """
        if note_type.name in self._types:
            msg = f"Note type {note_type.name!r} is already registered"
            raise ValueError(msg)

        if note_type.is_subtype and note_type.parent_type is None:
            msg = (
                f"Note type {note_type.name!r} has is_subtype=True but "
                f"parent_type is None — subtypes must declare a parent_type"
            )
            raise ValueError(msg)

        self._validate_transitions(note_type)

        self._types[note_type.name] = note_type

    def get(self, name: str) -> NoteTypeDefinition:
        """Return the NoteTypeDefinition for *name*.

        Raises
        ------
        KeyError
            If no type is registered under *name*.
        """
        try:
            return self._types[name]
        except KeyError:
            msg = f"No note type registered for name={name!r}"
            raise KeyError(msg) from None

    def list_types(self, content_type: str | None = None) -> list[NoteTypeDefinition]:
        """Return all registered types, optionally filtered by *content_type*."""
        types = list(self._types.values())
        if content_type is not None:
            types = [t for t in types if t.content_type == content_type]
        return types

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _validate_transitions(self, note_type: NoteTypeDefinition) -> None:
        """Validate that all transition target states are also keys.

        Every state that appears as a target in any transition list must
        also appear as a key in the transition map.  This prevents
        unreachable "orphaned" target states that could never be left.

        Raises
        ------
        ValueError
            With the first orphaned state name found.
        """
        transitions = note_type.transitions
        all_keys = set(transitions.keys())
        for _source, targets in transitions.items():
            for target in targets:
                if target not in all_keys:
                    msg = (
                        f"Note type {note_type.name!r} has invalid transition: "
                        f"target state {target!r} is not a key in the transition map. "
                        f"All target states must also be map keys."
                    )
                    raise ValueError(msg)


# ---------------------------------------------------------------------------
# Built-in registrations
# ---------------------------------------------------------------------------


def _register_builtins() -> None:
    """Register all 9 built-in NoteTypeDefinitions into *_REGISTRY*."""
    # ---- note ----
    _REGISTRY.register(
        NoteTypeDefinition(
            name="note",
            content_type="note",
            model_cls=NoteModel,
            transitions=NOTE_TRANSITIONS,
            template_name="note.md.j2",
        )
    )
    # ---- knowledge (note subtype, inherits NOTE_TRANSITIONS) ----
    _REGISTRY.register(
        NoteTypeDefinition(
            name="knowledge",
            content_type="note",
            model_cls=KnowledgeModel,
            transitions=NOTE_TRANSITIONS,
            template_name="knowledge.md.j2",
            is_subtype=True,
            parent_type="note",
        )
    )
    # ---- decision (note subtype, custom transitions + sections) ----
    _REGISTRY.register(
        NoteTypeDefinition(
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
    )
    # ---- reference ----
    _REGISTRY.register(
        NoteTypeDefinition(
            name="reference",
            content_type="reference",
            model_cls=ReferenceModel,
            transitions=REFERENCE_TRANSITIONS,
            template_name="reference.md.j2",
        )
    )
    # ---- article (reference subtype) ----
    _REGISTRY.register(
        NoteTypeDefinition(
            name="article",
            content_type="reference",
            model_cls=ReferenceModel,
            transitions=REFERENCE_TRANSITIONS,
            template_name="reference.md.j2",
            is_subtype=True,
            parent_type="reference",
        )
    )
    # ---- tool (reference subtype) ----
    _REGISTRY.register(
        NoteTypeDefinition(
            name="tool",
            content_type="reference",
            model_cls=ReferenceModel,
            transitions=REFERENCE_TRANSITIONS,
            template_name="reference.md.j2",
            is_subtype=True,
            parent_type="reference",
        )
    )
    # ---- spec (reference subtype) ----
    _REGISTRY.register(
        NoteTypeDefinition(
            name="spec",
            content_type="reference",
            model_cls=ReferenceModel,
            transitions=REFERENCE_TRANSITIONS,
            template_name="reference.md.j2",
            is_subtype=True,
            parent_type="reference",
        )
    )
    # ---- task ----
    _REGISTRY.register(
        NoteTypeDefinition(
            name="task",
            content_type="task",
            model_cls=TaskModel,
            transitions=TASK_TRANSITIONS,
            template_name="task.md.j2",
        )
    )
    # ---- log (DB-only, no template) ----
    _REGISTRY.register(
        NoteTypeDefinition(
            name="log",
            content_type="log",
            model_cls=ContentModel,
            transitions=LOG_TRANSITIONS,
            template_name="",
        )
    )


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

_REGISTRY = NoteTypeRegistry()
_register_builtins()


def get_note_type_registry() -> NoteTypeRegistry:
    """Return the module-level NoteTypeRegistry singleton."""
    return _REGISTRY
