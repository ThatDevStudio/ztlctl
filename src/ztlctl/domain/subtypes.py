"""Subtype rule ABC and registry.

From DESIGN.md Section 2: subtypes are enforced via a code-baked
SubtypeRule registry. Each subtype defines frontmatter schema,
lifecycle rules, validation constraints, and Jinja2 creation templates.

Machine-layer subtypes are strict (validation blocks creation).
Garden-layer content is flexible (advisory warnings, never blocking).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class SubtypeValidation:
    """Result of a subtype validation check."""

    valid: bool
    errors: list[str]
    warnings: list[str]


class SubtypeRule(ABC):
    """Abstract base class for content subtype rules.

    Each subtype ships with bundled Jinja2 creation templates.
    The 7 methods below define the full subtype contract.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Subtype identifier (e.g. 'decision', 'knowledge')."""
        ...

    @property
    @abstractmethod
    def parent_type(self) -> str:
        """Parent content type (e.g. 'note', 'reference')."""
        ...

    @abstractmethod
    def required_frontmatter(self) -> dict[str, type]:
        """Map of required frontmatter keys to their expected types."""
        ...

    @abstractmethod
    def validate_create(self, content: dict[str, object]) -> SubtypeValidation:
        """Validate content before creation."""
        ...

    @abstractmethod
    def validate_update(
        self,
        existing: dict[str, object],
        changes: dict[str, object],
    ) -> SubtypeValidation:
        """Validate an update against existing content."""
        ...

    @abstractmethod
    def required_sections(self) -> list[str]:
        """Markdown body sections required for this subtype."""
        ...

    @abstractmethod
    def allowed_status_transitions(self) -> dict[str, list[str]]:
        """Map of current status to list of allowed next statuses."""
        ...


# Registry — populated by concrete subtype implementations in future phases.
SUBTYPE_REGISTRY: dict[str, SubtypeRule] = {}
