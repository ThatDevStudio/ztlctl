"""CreateService — five-stage content creation pipeline.

Pipeline: VALIDATE → GENERATE → PERSIST → INDEX → RESPOND
(DESIGN.md Section 4)
"""

from __future__ import annotations

from ztlctl.services.result import ServiceResult


class CreateService:
    """Handles content creation for all types."""

    def create_note(
        self,
        title: str,
        *,
        subtype: str | None = None,
        tags: list[str] | None = None,
        topic: str | None = None,
        session: str | None = None,
    ) -> ServiceResult:
        """Create a new note (plain, knowledge, or decision subtype)."""
        raise NotImplementedError

    def create_reference(
        self,
        title: str,
        *,
        url: str | None = None,
        subtype: str | None = None,
        tags: list[str] | None = None,
        topic: str | None = None,
        session: str | None = None,
    ) -> ServiceResult:
        """Create a new reference to an external source."""
        raise NotImplementedError

    def create_task(
        self,
        title: str,
        *,
        priority: str = "medium",
        impact: str = "medium",
        effort: str = "medium",
        tags: list[str] | None = None,
        session: str | None = None,
    ) -> ServiceResult:
        """Create a new task with priority/impact/effort matrix."""
        raise NotImplementedError

    def create_batch(
        self,
        items: list[dict[str, object]],
        *,
        partial: bool = False,
    ) -> ServiceResult:
        """Create multiple items. All-or-nothing unless *partial* is True."""
        raise NotImplementedError
