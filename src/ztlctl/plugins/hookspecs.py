"""Pluggy hook specifications for ztlctl lifecycle events and extensions."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pluggy

if TYPE_CHECKING:
    from ztlctl.domain.content import ContentModel
    from ztlctl.plugins.contracts import (
        CliCommandContribution,
        McpPromptContribution,
        McpResourceContribution,
        McpToolContribution,
        SourceProviderContribution,
        VaultInitStepContribution,
        WorkflowModuleContribution,
        WorkspaceProfileContribution,
    )

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
    def post_init_profile(
        self,
        vault_name: str,
        profile: str,
        tone: str,
        managed_paths: list[str],
    ) -> None:
        """Called after vault init with canonical workspace profile metadata.

        ``managed_paths`` reports the scaffold surface associated with the
        selected profile during init. It is descriptive metadata, not a promise
        of future lifecycle management by ztlctl.
        """

    @hookspec
    def register_content_models(self) -> dict[str, type[ContentModel]] | None:
        """Return subtype -> ContentModel mappings to extend CONTENT_REGISTRY."""

    @hookspec
    def register_cli_commands(self) -> list[CliCommandContribution] | None:
        """Return plugin CLI command contributions."""

    @hookspec
    def register_mcp_tools(self) -> list[McpToolContribution] | None:
        """Return plugin MCP tool contributions."""

    @hookspec
    def register_mcp_resources(self) -> list[McpResourceContribution] | None:
        """Return plugin MCP resource contributions."""

    @hookspec
    def register_mcp_prompts(self) -> list[McpPromptContribution] | None:
        """Return plugin MCP prompt contributions."""

    @hookspec
    def register_workflow_modules(self) -> list[WorkflowModuleContribution] | None:
        """Return plugin workflow export modules."""

    @hookspec
    def register_workspace_profiles(self) -> list[WorkspaceProfileContribution] | None:
        """Return plugin workspace profile contributions."""

    @hookspec
    def register_vault_init_steps(self) -> list[VaultInitStepContribution] | None:
        """Return ordered plugin steps to run during `ztlctl init`."""

    @hookspec
    def register_source_providers(self) -> list[SourceProviderContribution] | None:
        """Return plugin-provided source ingestion providers."""
