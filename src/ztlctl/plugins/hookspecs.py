"""Pluggy hook specifications for ztlctl lifecycle events and extensions."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pluggy

if TYPE_CHECKING:
    from pydantic import BaseModel

    from ztlctl.domain.content import ContentModel
    from ztlctl.domain.registry import NoteTypeDefinition
    from ztlctl.plugins.contracts import (
        ActionRejection,
        CliCommandContribution,
        McpPromptContribution,
        McpResourceContribution,
        McpToolContribution,
        RenderContribution,
        SourceProviderContribution,
        VaultInitStepContribution,
        WorkflowModuleContribution,
        WorkspaceProfileContribution,
    )

hookspec = pluggy.HookspecMarker("ztlctl")


class ZtlctlHookSpec:
    """Hook specifications for the ztlctl plugin system."""

    # ------------------------------------------------------------------
    # Generic action hooks (PLUG-02) — preferred over per-event hooks
    # ------------------------------------------------------------------

    @hookspec(firstresult=True)
    def pre_action(
        self, action_name: str, kwargs: dict[str, Any]
    ) -> ActionRejection | dict[str, Any] | None:
        """Called before action execution.

        Return an :class:`~ztlctl.plugins.contracts.ActionRejection` to abort
        the action, a modified *kwargs* dict to replace the original keyword
        arguments, or ``None`` to pass through unchanged.

        This is a ``firstresult`` hook — the first plugin returning a non-``None``
        value wins and subsequent plugins are not called.
        """

    @hookspec
    def post_action(self, action_name: str, kwargs: dict[str, Any], result: Any) -> None:
        """Called after action execution with the ServiceResult.

        All registered plugins receive this hook regardless of the action outcome.
        """

    # ------------------------------------------------------------------
    # Plugin configuration (PLUG-03)
    # ------------------------------------------------------------------

    @hookspec(firstresult=True)
    def get_config_schema(self) -> type[BaseModel] | None:
        """Return the Pydantic model class used to validate this plugin's config.

        The schema is retrieved once at load time. If the ``[plugins.<name>]``
        TOML section exists, its contents are validated against the returned
        model and then passed to :meth:`initialize`.
        """

    @hookspec
    def initialize(self, config: BaseModel | None) -> None:
        """Called once after plugin loading with validated configuration.

        *config* is a validated Pydantic model instance if a schema was
        declared via :meth:`get_config_schema` and a matching TOML section
        exists, otherwise ``None``.
        """

    # ------------------------------------------------------------------
    # Deprecated per-event lifecycle hooks
    # Prefer implementing post_action and filtering by action_name.
    # ------------------------------------------------------------------

    @hookspec(
        warn_on_impl=DeprecationWarning(
            "post_create is deprecated since plugin API v2; "
            "implement post_action and filter by action_name instead"
        )
    )
    def post_create(
        self,
        content_type: str,
        content_id: str,
        title: str,
        path: str,
        tags: list[str],
    ) -> None:
        """Called after content creation."""

    @hookspec(
        warn_on_impl=DeprecationWarning(
            "post_update is deprecated since plugin API v2; "
            "implement post_action and filter by action_name instead"
        )
    )
    def post_update(
        self,
        content_type: str,
        content_id: str,
        fields_changed: list[str],
        path: str,
    ) -> None:
        """Called after content update."""

    @hookspec(
        warn_on_impl=DeprecationWarning(
            "post_close is deprecated since plugin API v2; "
            "implement post_action and filter by action_name instead"
        )
    )
    def post_close(
        self,
        content_type: str,
        content_id: str,
        path: str,
        summary: str,
    ) -> None:
        """Called after close/archive."""

    @hookspec(
        warn_on_impl=DeprecationWarning(
            "post_reweave is deprecated since plugin API v2; "
            "implement post_action and filter by action_name instead"
        )
    )
    def post_reweave(
        self,
        source_id: str,
        affected_ids: list[str],
        links_added: int,
    ) -> None:
        """Called after reweave completes."""

    @hookspec(
        warn_on_impl=DeprecationWarning(
            "post_session_start is deprecated since plugin API v2; "
            "implement post_action and filter by action_name instead"
        )
    )
    def post_session_start(self, session_id: str) -> None:
        """Called after a session begins."""

    @hookspec(
        warn_on_impl=DeprecationWarning(
            "post_session_close is deprecated since plugin API v2; "
            "implement post_action and filter by action_name instead"
        )
    )
    def post_session_close(
        self,
        session_id: str,
        stats: dict[str, Any],
    ) -> None:
        """Called after a session closes."""

    @hookspec(
        warn_on_impl=DeprecationWarning(
            "post_check is deprecated since plugin API v2; "
            "implement post_action and filter by action_name instead"
        )
    )
    def post_check(
        self,
        issues_found: int,
        issues_fixed: int,
    ) -> None:
        """Called after integrity check."""

    @hookspec(
        warn_on_impl=DeprecationWarning(
            "post_init is deprecated since plugin API v2; "
            "implement post_action and filter by action_name instead"
        )
    )
    def post_init(
        self,
        vault_name: str,
        client: str,
        tone: str,
    ) -> None:
        """Called after vault init."""

    @hookspec(
        warn_on_impl=DeprecationWarning(
            "post_init_profile is deprecated since plugin API v2; "
            "implement post_action and filter by action_name instead"
        )
    )
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

    # ------------------------------------------------------------------
    # Extension contribution hooks
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # Custom note type + rendering hooks (PLUG-05, PLUG-06)
    # ------------------------------------------------------------------

    @hookspec
    def register_note_types(self) -> list[NoteTypeDefinition] | None:
        """Return NoteTypeDefinitions to register into NoteTypeRegistry + ActionRegistry.

        PluginManager will auto-create create/update/close ActionDefinitions for
        each registered NoteTypeDefinition and add them to the ActionRegistry so
        the CLI and MCP generators pick them up automatically.
        """

    @hookspec
    def register_render_contributions(self) -> list[RenderContribution] | None:
        """Return render contributions for custom note types.

        Each :class:`~ztlctl.plugins.contracts.RenderContribution` provides a
        ``rich_formatter`` and an ``mcp_formatter`` callable for one note type,
        enabling custom terminal and MCP output formatting.
        """

    # ------------------------------------------------------------------
    # Security — capability declarations (SECU-02)
    # ------------------------------------------------------------------

    @hookspec
    def declare_capabilities(self) -> set[str] | None:
        """Return the set of capabilities this plugin requires.

        Valid values: ``{"filesystem", "network", "database", "git"}``.

        Missing declaration is treated as a warning (not an error) in plugin
        API v2 to avoid breaking existing plugins. Future API versions may
        enforce declarations. Returns ``None`` or does not implement to
        indicate no declaration.
        """
