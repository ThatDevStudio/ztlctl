"""Content models — frontmatter schema + body methods.

ContentModel attributes map 1:1 to YAML frontmatter keys (similar to
how Pydantic Settings maps fields to environment variables).  Body
content is handled exclusively via methods:

- ``write_body()``: renders a body-only Jinja2 template with typed args.
- ``read_body()``: returns the raw body string — no structural parsing.

These models replace the former ``frontmatter.py`` Pydantic schemas.
They are the single source of truth for content structure.

Pure parsing utilities (``parse_frontmatter``, ``order_frontmatter``,
``render_frontmatter``) live here so that the dependency direction stays
clean: infrastructure → domain, never the reverse.
"""

from __future__ import annotations

from datetime import date
from io import StringIO
from pathlib import Path
from typing import Any, ClassVar, Self

from jinja2 import Environment, PackageLoader
from pydantic import BaseModel, Field
from ruamel.yaml import YAML

# ---------------------------------------------------------------------------
# YAML parser (round-trip preserves comments and quote styles)
# ---------------------------------------------------------------------------

_yaml = YAML()
_yaml.preserve_quotes = True
_yaml.default_flow_style = False

# ---------------------------------------------------------------------------
# Jinja2 environment for body-only templates
# ---------------------------------------------------------------------------

_jinja_env = Environment(
    loader=PackageLoader("ztlctl", "templates/content"),
    keep_trailing_newline=True,
)

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
# Pure parsing / rendering utilities
# ---------------------------------------------------------------------------


def parse_frontmatter(content: str) -> tuple[dict[str, Any], str]:
    """Parse YAML frontmatter and body from markdown content.

    Expects the file to start with ``---`` on the first line. The second
    ``---`` closes the YAML block. Everything after is the body.

    Returns:
        A ``(frontmatter_dict, body_text)`` tuple. If no valid
        frontmatter delimiters are found, returns ``({}, content)``.
    """
    lines = content.split("\n")
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

    fm: dict[str, Any] = _yaml.load(yaml_block) or {}
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
    _yaml.dump(ordered, buf)
    yaml_text = buf.getvalue()

    parts = [_FRONTMATTER_DELIMITER, "\n", yaml_text, _FRONTMATTER_DELIMITER, "\n"]
    if body:
        parts.append(body)
    return "".join(parts)


# ---------------------------------------------------------------------------
# Base content model
# ---------------------------------------------------------------------------


class ContentModel(BaseModel):
    """Base content model — attributes ARE frontmatter keys.

    Subclasses add type-specific fields and override ``write_body()``
    when the body template requires typed parameters beyond ``body``.
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

    # Subclasses set this to their body-only template filename.
    _template_name: ClassVar[str] = ""

    def to_frontmatter(self) -> dict[str, Any]:
        """Serialize model attributes to an ordered frontmatter dict."""
        fm = self.model_dump(mode="json", exclude_none=True)
        return order_frontmatter(fm)

    def write_body(self, body: str = "") -> str:
        """Render the body-only Jinja2 template.

        Base implementation returns *body* as-is when no template is
        configured, or renders the template with ``body`` as the only
        variable. Subclasses override for typed template parameters.
        """
        if not self._template_name:
            return body
        template = _jinja_env.get_template(self._template_name)
        return template.render(body=body)

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


# ---------------------------------------------------------------------------
# Concrete content models
# ---------------------------------------------------------------------------


class NoteModel(ContentModel):
    """Plain note — flexible structure, no enforced sections."""

    _template_name: ClassVar[str] = "note.md.j2"

    subtype: str | None = None
    maturity: str | None = None
    aliases: list[str] = Field(default_factory=list)
    topic: str | None = None
    links: dict[str, list[str]] = Field(default_factory=dict)


class KnowledgeModel(NoteModel):
    """Knowledge note — advisory key_points, same body as plain note."""

    _template_name: ClassVar[str] = "knowledge.md.j2"

    key_points: list[str] = Field(default_factory=list)


class DecisionModel(NoteModel):
    """Decision note — strict sections, immutable after acceptance."""

    _template_name: ClassVar[str] = "decision.md.j2"

    supersedes: str | None = None
    superseded_by: str | None = None

    def write_body(  # type: ignore[override]
        self,
        *,
        context: str = "",
        choice: str = "",
        rationale: str = "",
        alternatives: str = "",
        consequences: str = "",
    ) -> str:
        """Render decision body with required section content."""
        template = _jinja_env.get_template(self._template_name)
        return template.render(
            context=context,
            choice=choice,
            rationale=rationale,
            alternatives=alternatives,
            consequences=consequences,
        )


class ReferenceModel(ContentModel):
    """External reference — article, tool, or spec."""

    _template_name: ClassVar[str] = "reference.md.j2"

    subtype: str | None = None
    url: str | None = None
    aliases: list[str] = Field(default_factory=list)
    topic: str | None = None
    links: dict[str, list[str]] = Field(default_factory=dict)


class TaskModel(ContentModel):
    """Actionable task with priority/impact/effort matrix."""

    _template_name: ClassVar[str] = "task.md.j2"

    priority: str = "medium"
    impact: str = "medium"
    effort: str = "medium"
