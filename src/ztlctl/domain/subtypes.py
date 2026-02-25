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


SUBTYPE_REGISTRY: dict[str, SubtypeRule] = {}


# ---------------------------------------------------------------------------
# Concrete subtype rules
# ---------------------------------------------------------------------------


class DecisionSubtypeRule(SubtypeRule):
    """Strict rule for decision notes.

    INVARIANT: Decisions are immutable after ``status = accepted``.
    Required sections: Context, Choice, Rationale, Alternatives, Consequences.
    Status flow: ``proposed -> accepted -> superseded``.
    """

    @property
    def name(self) -> str:
        return "decision"

    @property
    def parent_type(self) -> str:
        return "note"

    def required_frontmatter(self) -> dict[str, type]:
        return {
            "id": str,
            "type": str,
            "subtype": str,
            "status": str,
            "title": str,
            "tags": list,
            "created": str,
        }

    def validate_create(self, content: dict[str, object]) -> SubtypeValidation:
        errors: list[str] = []
        warnings: list[str] = []

        for key, expected_type in self.required_frontmatter().items():
            val = content.get(key)
            if val is None:
                errors.append(f"Missing required field: {key}")
            elif not isinstance(val, expected_type):
                errors.append(
                    f"Field '{key}' must be {expected_type.__name__}, got {type(val).__name__}"
                )

        if content.get("subtype") != "decision":
            errors.append("subtype must be 'decision'")

        if content.get("status") != "proposed":
            errors.append("New decisions must have status 'proposed'")

        return SubtypeValidation(valid=len(errors) == 0, errors=errors, warnings=warnings)

    def validate_update(
        self,
        existing: dict[str, object],
        changes: dict[str, object],
    ) -> SubtypeValidation:
        errors: list[str] = []
        warnings: list[str] = []

        current_status = existing.get("status")

        # INVARIANT: Decisions are immutable after accepted.
        # Only metadata fields may be modified.
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
            allowed = self.allowed_status_transitions().get(str(current_status), [])
            if new_status not in allowed:
                errors.append(
                    f"Invalid status transition: "
                    f"{current_status} -> {new_status}. "
                    f"Allowed: {allowed}"
                )

        return SubtypeValidation(valid=len(errors) == 0, errors=errors, warnings=warnings)

    def required_sections(self) -> list[str]:
        return ["Context", "Choice", "Rationale", "Alternatives", "Consequences"]

    def allowed_status_transitions(self) -> dict[str, list[str]]:
        return {
            "proposed": ["accepted"],
            "accepted": ["superseded"],
            "superseded": [],
        }


class KnowledgeSubtypeRule(SubtypeRule):
    """Advisory rule for knowledge notes.

    Warns on missing ``key_points`` but never blocks creation.
    """

    @property
    def name(self) -> str:
        return "knowledge"

    @property
    def parent_type(self) -> str:
        return "note"

    def required_frontmatter(self) -> dict[str, type]:
        return {
            "id": str,
            "type": str,
            "subtype": str,
            "status": str,
            "title": str,
            "tags": list,
            "created": str,
        }

    def validate_create(self, content: dict[str, object]) -> SubtypeValidation:
        errors: list[str] = []
        warnings: list[str] = []

        if content.get("subtype") != "knowledge":
            errors.append("subtype must be 'knowledge'")

        if not content.get("key_points"):
            warnings.append("Knowledge notes benefit from key_points in frontmatter")

        return SubtypeValidation(valid=len(errors) == 0, errors=errors, warnings=warnings)

    def validate_update(
        self,
        existing: dict[str, object],
        changes: dict[str, object],
    ) -> SubtypeValidation:
        warnings: list[str] = []

        if "key_points" in changes:
            kp = changes["key_points"]
            if isinstance(kp, list) and len(kp) == 0:
                warnings.append("Removing all key_points is not recommended")

        return SubtypeValidation(valid=True, errors=[], warnings=warnings)

    def required_sections(self) -> list[str]:
        return []

    def allowed_status_transitions(self) -> dict[str, list[str]]:
        return {
            "draft": ["linked"],
            "linked": ["connected"],
            "connected": [],
        }


class ReferenceSubtypeRule(SubtypeRule):
    """Classification-only rule for reference subtypes.

    Always valid — no lifecycle enforcement. Parameterized by name
    to avoid duplicate classes for ``article``, ``tool``, ``spec``.
    """

    def __init__(self, subtype_name: str) -> None:
        self._name = subtype_name

    @property
    def name(self) -> str:
        return self._name

    @property
    def parent_type(self) -> str:
        return "reference"

    def required_frontmatter(self) -> dict[str, type]:
        return {
            "id": str,
            "type": str,
            "status": str,
            "title": str,
            "created": str,
        }

    def validate_create(self, content: dict[str, object]) -> SubtypeValidation:
        return SubtypeValidation(valid=True, errors=[], warnings=[])

    def validate_update(
        self,
        existing: dict[str, object],
        changes: dict[str, object],
    ) -> SubtypeValidation:
        return SubtypeValidation(valid=True, errors=[], warnings=[])

    def required_sections(self) -> list[str]:
        return []

    def allowed_status_transitions(self) -> dict[str, list[str]]:
        return {
            "captured": ["annotated"],
            "annotated": [],
        }


def _register_subtypes() -> None:
    """Populate :data:`SUBTYPE_REGISTRY` with built-in subtype rules."""
    SUBTYPE_REGISTRY["decision"] = DecisionSubtypeRule()
    SUBTYPE_REGISTRY["knowledge"] = KnowledgeSubtypeRule()
    SUBTYPE_REGISTRY["article"] = ReferenceSubtypeRule("article")
    SUBTYPE_REGISTRY["tool"] = ReferenceSubtypeRule("tool")
    SUBTYPE_REGISTRY["spec"] = ReferenceSubtypeRule("spec")


_register_subtypes()
