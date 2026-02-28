"""Pluggy hook specifications for ztlctl lifecycle events and setup extensions.

Eight lifecycle events are dispatched asynchronously via ThreadPoolExecutor.
One setup-time hook allows plugins to register custom content subtypes.
(DESIGN.md Section 15)
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pluggy

if TYPE_CHECKING:
    from ztlctl.domain.content import ContentModel

hookspec = pluggy.HookspecMarker("ztlctl")


class ZtlctlHookSpec:
    """Hook specifications for the ztlctl plugin system."""

    @hookspec
    def post_create(
        self,
        content_type: str,
        content_id: str,
        title: str,
        path: str,
        tags: list[str],
    ) -> None:
        """Called after content creation."""

    @hookspec
    def post_update(
        self,
        content_type: str,
        content_id: str,
        fields_changed: list[str],
        path: str,
    ) -> None:
        """Called after content update."""

    @hookspec
    def post_close(
        self,
        content_type: str,
        content_id: str,
        path: str,
        summary: str,
    ) -> None:
        """Called after close/archive."""

    @hookspec
    def post_reweave(
        self,
        source_id: str,
        affected_ids: list[str],
        links_added: int,
    ) -> None:
        """Called after reweave completes."""

    @hookspec
    def post_session_start(self, session_id: str) -> None:
        """Called after a session begins."""

    @hookspec
    def post_session_close(
        self,
        session_id: str,
        stats: dict[str, Any],
    ) -> None:
        """Called after a session closes."""

    @hookspec
    def post_check(
        self,
        issues_found: int,
        issues_fixed: int,
    ) -> None:
        """Called after integrity check."""

    @hookspec
    def post_init(
        self,
        vault_name: str,
        client: str,
        tone: str,
    ) -> None:
        """Called after vault init."""

    @hookspec
    def register_content_models(self) -> dict[str, type[ContentModel]] | None:
        """Return subtype -> ContentModel mappings to extend CONTENT_REGISTRY."""
