"""Frontmatter schema models per content type.

Canonical key ordering from DESIGN.md Section 2:
  id, type, subtype, status, maturity, title, session, tags,
  aliases, topic, links, created, modified

All models use Pydantic with frozen config for immutability.
"""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field


class BaseFrontmatter(BaseModel):
    """Common frontmatter fields shared by all content types."""

    model_config = {"frozen": True}

    id: str
    type: str
    status: str
    title: str
    session: str | None = None
    tags: list[str] = Field(default_factory=list)
    created: date
    modified: date | None = None


class NoteFrontmatter(BaseFrontmatter):
    """Frontmatter for note content type."""

    model_config = {"frozen": True}

    subtype: str | None = None
    maturity: str | None = None
    aliases: list[str] = Field(default_factory=list)
    topic: str | None = None
    links: dict[str, list[str]] = Field(default_factory=dict)


class KnowledgeFrontmatter(NoteFrontmatter):
    """Frontmatter for knowledge-subtype notes."""

    model_config = {"frozen": True}

    key_points: list[str] = Field(default_factory=list)


class DecisionFrontmatter(NoteFrontmatter):
    """Frontmatter for decision-subtype notes."""

    model_config = {"frozen": True}

    supersedes: str | None = None
    superseded_by: str | None = None


class ReferenceFrontmatter(BaseFrontmatter):
    """Frontmatter for reference content type."""

    model_config = {"frozen": True}

    subtype: str | None = None
    url: str | None = None
    aliases: list[str] = Field(default_factory=list)
    topic: str | None = None
    links: dict[str, list[str]] = Field(default_factory=dict)


class TaskFrontmatter(BaseFrontmatter):
    """Frontmatter for task content type."""

    model_config = {"frozen": True}

    priority: str = "medium"
    impact: str = "medium"
    effort: str = "medium"
