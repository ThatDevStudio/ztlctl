"""Content models — frontmatter schema + body methods + validation.

ContentModel attributes map 1:1 to YAML frontmatter keys (similar to
how Pydantic Settings maps fields to environment variables).  Body
content is handled exclusively via methods:

- ``write_body()``: renders a body-only Jinja2 template with kwargs.
- ``read_body()``: returns the raw body string — no structural parsing.

Validation lives directly on the model hierarchy:

- ``validate_create()``: business-rule checks before creation.
- ``validate_update()``: business-rule checks before modification.
- ``required_sections()``: body sections required for this content type.
- ``status_transitions()``: delegates to ``lifecycle.py`` maps.

Pure parsing utilities (``parse_frontmatter``, ``order_frontmatter``,
``render_frontmatter``) live here so that the dependency direction stays
clean: infrastructure -> domain, never the reverse.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from io import StringIO
from pathlib import Path
from typing import Any, ClassVar, Self

from pydantic import BaseModel, Field
from ruamel.yaml import YAML

from ztlctl.domain.lifecycle import (
    DECISION_TRANSITIONS,
    NOTE_TRANSITIONS,
    REFERENCE_TRANSITIONS,
    TASK_TRANSITIONS,
)
from ztlctl.infrastructure.templates import build_template_environment

# ---------------------------------------------------------------------------
# YAML parser (round-trip preserves comments and quote styles)
# ---------------------------------------------------------------------------


def _new_yaml() -> YAML:
    """Create a fresh round-trip YAML parser.

    A new instance per call avoids corrupted internal emitter state from
    propagating across operations (ruamel.yaml's YAML object is stateful
    and a failed dump can leave the singleton in a broken state).
    """
    y = YAML()
    y.preserve_quotes = True
    y.default_flow_style = False
    return y


# ---------------------------------------------------------------------------
# Canonical frontmatter key ordering (DESIGN.md Section 2)
# ---------------------------------------------------------------------------

CANONICAL_KEY_ORDER: list[str] = [
    "id",
    "type",
    "subtype",
    "status",
    "maturity",
    "title",
    "session",
    "tags",
    "aliases",
    "topic",
    "links",
    "key_points",
    "supersedes",
    "superseded_by",
    "url",
    "priority",
    "impact",
    "effort",
    "created",
    "modified",
]

_FRONTMATTER_DELIMITER = "---"


# ---------------------------------------------------------------------------
# Validation result
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ValidationResult:
    """Result of a content validation check."""

    valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Pure parsing / rendering utilities
# ---------------------------------------------------------------------------


def parse_frontmatter(content: str) -> tuple[dict[str, Any], str]:
    """Parse YAML frontmatter and body from markdown content.

    Expects the file to start with ``---`` on the first line. The second
    ``---`` closes the YAML block. Everything after is the body.

    Handles both ``\\n`` and ``\\r\\n`` line endings.

    Returns:
        A ``(frontmatter_dict, body_text)`` tuple. If no valid
        frontmatter delimiters are found, returns ``({}, content)``.
    """
    # Normalize line endings to \n before parsing.
    normalized = content.replace("\r\n", "\n")
    lines = normalized.split("\n")
    if not lines or lines[0].strip() != _FRONTMATTER_DELIMITER:
        return {}, content

    end_idx: int | None = None
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == _FRONTMATTER_DELIMITER:
            end_idx = i
            break

    if end_idx is None:
        return {}, content

    yaml_block = "\n".join(lines[1:end_idx])
    body = "\n".join(lines[end_idx + 1 :])

    if body.startswith("\n"):
        body = body[1:]

    fm: dict[str, Any] = _new_yaml().load(yaml_block) or {}
    return fm, body


def order_frontmatter(fm: dict[str, Any]) -> dict[str, Any]:
    """Return *fm* with keys in canonical order.

    Keys present in :data:`CANONICAL_KEY_ORDER` come first (in that
    order), followed by any remaining keys sorted alphabetically.
    ``None`` values are omitted.
    """
    ordered: dict[str, Any] = {}
    for key in CANONICAL_KEY_ORDER:
        if key in fm and fm[key] is not None:
            ordered[key] = fm[key]

    for key in sorted(fm.keys()):
        if key not in ordered and fm[key] is not None:
            ordered[key] = fm[key]

    return ordered


def render_frontmatter(frontmatter: dict[str, Any], body: str) -> str:
    """Render a frontmatter dict and body text into markdown.

    Keys are emitted in :data:`CANONICAL_KEY_ORDER`. Keys not in the
    canonical list are appended alphabetically at the end.
    """
    ordered = order_frontmatter(frontmatter)
    buf = StringIO()
    _new_yaml().dump(ordered, buf)
    yaml_text = buf.getvalue()

    parts = [_FRONTMATTER_DELIMITER, "\n", yaml_text, _FRONTMATTER_DELIMITER, "\n"]
    if body:
        parts.append(body)
    return "".join(parts)


# ---------------------------------------------------------------------------
# Content model registry
# ---------------------------------------------------------------------------

# Populated by _register_models() at module load time.
CONTENT_REGISTRY: dict[str, type[ContentModel]] = {}


def get_content_model(
    content_type: str,
    subtype: str | None = None,
) -> type[ContentModel]:
    """Look up the ContentModel class for a content type + optional subtype.

    Checks subtype-specific registration first, then falls back to the
    base type registration.

    Raises:
        KeyError: If no model is registered for the given type/subtype.
    """
    if subtype and subtype in CONTENT_REGISTRY:
        return CONTENT_REGISTRY[subtype]
    if content_type in CONTENT_REGISTRY:
        return CONTENT_REGISTRY[content_type]
    msg = f"No content model registered for type={content_type!r}, subtype={subtype!r}"
    raise KeyError(msg)


def register_content_model(name: str, model_cls: type[ContentModel]) -> None:
    """Register a custom content subtype model.

    The model must extend :class:`ContentModel`, resolve to a concrete base
    content type, and expose the standard validation/status APIs. Built-in
    names are reserved and cannot be overridden by plugins.
    """

    normalized_name = name.strip()
    if not normalized_name:
        msg = "Content model name must not be empty"
        raise ValueError(msg)

    if not issubclass(model_cls, ContentModel):
        msg = f"Content model {normalized_name!r} must extend ContentModel"
        raise TypeError(msg)

    if normalized_name in _builtin_model_map():
        msg = f"Content model {normalized_name!r} conflicts with a built-in registration"
        raise ValueError(msg)

    if model_cls._subtype_name is None:
        model_cls._subtype_name = normalized_name
    elif model_cls._subtype_name != normalized_name:
        msg = (
            f"Content model {normalized_name!r} declares subtype "
            f"{model_cls._subtype_name!r}; these must match"
        )
        raise ValueError(msg)

    if not model_cls._content_type:
        msg = f"Content model {normalized_name!r} must declare a concrete _content_type"
        raise ValueError(msg)

    required_api = (
        "validate_create",
        "validate_update",
        "required_sections",
        "status_transitions",
    )
    for attr_name in required_api:
        attr = getattr(model_cls, attr_name, None)
        if not callable(attr):
            msg = f"Content model {normalized_name!r} is missing required API: {attr_name}"
            raise TypeError(msg)

    existing = CONTENT_REGISTRY.get(normalized_name)
    if existing is not None and existing is not model_cls:
        msg = f"Content model {normalized_name!r} is already registered"
        raise ValueError(msg)

    CONTENT_REGISTRY[normalized_name] = model_cls


# ---------------------------------------------------------------------------
# Base content model
# ---------------------------------------------------------------------------


class ContentModel(BaseModel):
    """Base content model — attributes ARE frontmatter keys.

    Subclasses add type-specific fields and may override:

    - ``write_body(**kwargs)`` for type-specific template parameters.
    - ``validate_create()`` / ``validate_update()`` for business rules.
    - ``required_sections()`` for body section requirements.
    - ``status_transitions()`` to delegate to lifecycle.py maps.
    """

    model_config = {"frozen": True}

    id: str
    type: str
    status: str
    title: str
    session: str | None = None
    tags: list[str] = Field(default_factory=list)
    created: date
    modified: date | None = None

    # Subclasses set these to their body-only template filename and type info.
    _template_name: ClassVar[str] = ""
    _content_type: ClassVar[str] = ""
    _subtype_name: ClassVar[str | None] = None

    def to_frontmatter(self) -> dict[str, Any]:
        """Serialize model attributes to an ordered frontmatter dict."""
        fm = self.model_dump(mode="json", exclude_none=True)
        return order_frontmatter(fm)

    def write_body(self, *, template_root: Path | None = None, **kwargs: Any) -> str:
        """Render the body-only Jinja2 template.

        All keyword arguments are passed to the Jinja2 template. Common
        usage: ``model.write_body(body="...")`` for simple templates,
        ``model.write_body(context="...", choice="...")`` for structured
        templates like decisions.
        """
        if not self._template_name:
            return str(kwargs.get("body", ""))
        env = build_template_environment("content", vault_root=template_root)
        template = env.get_template(self._template_name)
        return template.render(**kwargs)

    @staticmethod
    def read_body(raw: str) -> str:
        """Return the body as-is — no structural parsing."""
        return raw

    @classmethod
    def from_file(cls, path: Path) -> tuple[Self, str]:
        """Parse a markdown file into ``(model_instance, body_string)``.

        Reads the file, splits frontmatter from body, validates the
        frontmatter against the model schema, and returns the body
        through :meth:`read_body`.
        """
        content = path.read_text(encoding="utf-8")
        fm, raw_body = parse_frontmatter(content)
        instance = cls.model_validate(fm)
        return instance, cls.read_body(raw_body)

    # --- Validation (override in subclasses for business rules) ---

    @classmethod
    def validate_create(cls, data: dict[str, Any]) -> ValidationResult:
        """Validate data before creation.

        Base implementation accepts all valid data. Subclasses override
        to enforce business rules (e.g. required initial status).
        """
        return ValidationResult(valid=True)

    @classmethod
    def validate_update(
        cls,
        existing: dict[str, Any],
        changes: dict[str, Any],
    ) -> ValidationResult:
        """Validate an update against existing content.

        Base implementation accepts all updates. Subclasses override
        for invariants (e.g. immutability after acceptance).
        """
        return ValidationResult(valid=True)

    @classmethod
    def required_sections(cls) -> list[str]:
        """Markdown body sections required for this content type."""
        return []

    @classmethod
    def status_transitions(cls) -> dict[str, list[str]]:
        """Allowed status transitions — delegates to lifecycle.py."""
        return {}


# ---------------------------------------------------------------------------
# Concrete content models
# ---------------------------------------------------------------------------


class NoteModel(ContentModel):
    """Plain note — flexible structure, no enforced sections."""

    _template_name: ClassVar[str] = "note.md.j2"
    _content_type: ClassVar[str] = "note"

    subtype: str | None = None
    maturity: str | None = None
    aliases: list[str] = Field(default_factory=list)
    topic: str | None = None
    links: dict[str, list[str]] = Field(default_factory=dict)

    @classmethod
    def status_transitions(cls) -> dict[str, list[str]]:
        return NOTE_TRANSITIONS


class KnowledgeModel(NoteModel):
    """Knowledge note — advisory key_points, same body as plain note."""

    _template_name: ClassVar[str] = "knowledge.md.j2"
    _subtype_name: ClassVar[str] = "knowledge"

    key_points: list[str] = Field(default_factory=list)

    @classmethod
    def validate_create(cls, data: dict[str, Any]) -> ValidationResult:
        warnings: list[str] = []
        if not data.get("key_points"):
            warnings.append("Knowledge notes benefit from key_points in frontmatter")
        return ValidationResult(valid=True, warnings=warnings)

    @classmethod
    def validate_update(
        cls,
        existing: dict[str, Any],
        changes: dict[str, Any],
    ) -> ValidationResult:
        warnings: list[str] = []
        if "key_points" in changes:
            kp = changes["key_points"]
            if isinstance(kp, list) and len(kp) == 0:
                warnings.append("Removing all key_points is not recommended")
        return ValidationResult(valid=True, warnings=warnings)


class DecisionModel(NoteModel):
    """Decision note — strict sections, immutable after acceptance.

    INVARIANT: Decisions are immutable after ``status = accepted``.
    Required sections: Context, Choice, Rationale, Alternatives, Consequences.
    Status flow: ``proposed -> accepted -> superseded``.
    """

    _template_name: ClassVar[str] = "decision.md.j2"
    _subtype_name: ClassVar[str] = "decision"

    supersedes: str | None = None
    superseded_by: str | None = None

    @classmethod
    def validate_create(cls, data: dict[str, Any]) -> ValidationResult:
        errors: list[str] = []
        if data.get("status") != "proposed":
            errors.append("New decisions must have status 'proposed'")
        return ValidationResult(valid=len(errors) == 0, errors=errors)

    @classmethod
    def validate_update(
        cls,
        existing: dict[str, Any],
        changes: dict[str, Any],
    ) -> ValidationResult:
        errors: list[str] = []
        current_status = existing.get("status")

        # INVARIANT: Decisions are immutable after accepted.
        if current_status == "accepted":
            allowed_after_accepted = {
                "status",
                "superseded_by",
                "modified",
                "tags",
                "aliases",
                "topic",
            }
            disallowed = set(changes.keys()) - allowed_after_accepted
            if disallowed:
                errors.append(
                    f"Cannot modify accepted decision. "
                    f"Disallowed fields: {sorted(disallowed)}. "
                    f"Supersede with a new decision instead."
                )

        if "status" in changes:
            new_status = str(changes["status"])
            allowed = cls.status_transitions().get(str(current_status), [])
            if new_status not in allowed:
                errors.append(
                    f"Invalid status transition: "
                    f"{current_status} -> {new_status}. "
                    f"Allowed: {allowed}"
                )

        return ValidationResult(valid=len(errors) == 0, errors=errors)

    @classmethod
    def required_sections(cls) -> list[str]:
        return ["Context", "Choice", "Rationale", "Alternatives", "Consequences"]

    @classmethod
    def status_transitions(cls) -> dict[str, list[str]]:
        return DECISION_TRANSITIONS


class ReferenceModel(ContentModel):
    """External reference — article, tool, or spec."""

    _template_name: ClassVar[str] = "reference.md.j2"
    _content_type: ClassVar[str] = "reference"

    subtype: str | None = None
    url: str | None = None
    aliases: list[str] = Field(default_factory=list)
    topic: str | None = None
    links: dict[str, list[str]] = Field(default_factory=dict)

    @classmethod
    def status_transitions(cls) -> dict[str, list[str]]:
        return REFERENCE_TRANSITIONS


class TaskModel(ContentModel):
    """Actionable task with priority/impact/effort matrix."""

    _template_name: ClassVar[str] = "task.md.j2"
    _content_type: ClassVar[str] = "task"

    priority: str = "medium"
    impact: str = "medium"
    effort: str = "medium"

    @classmethod
    def status_transitions(cls) -> dict[str, list[str]]:
        return TASK_TRANSITIONS


# ---------------------------------------------------------------------------
# Registry population
# ---------------------------------------------------------------------------


def _builtin_model_map() -> dict[str, type[ContentModel]]:
    """Return the built-in content model registry."""
    return {
        "note": NoteModel,
        "knowledge": KnowledgeModel,
        "decision": DecisionModel,
        "reference": ReferenceModel,
        "task": TaskModel,
    }


def _register_models() -> None:
    """Populate :data:`CONTENT_REGISTRY` with built-in content models."""
    CONTENT_REGISTRY.update(_builtin_model_map())


_register_models()
