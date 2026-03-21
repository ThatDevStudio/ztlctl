"""Admin ActionDefinition registrations (vector, upgrade, workflow, init, discovery, docs)."""

from __future__ import annotations

from typing import Any


def _register_admin_actions() -> None:
    """Register admin ActionDefinitions (vector, upgrade, workflow, init, discovery, docs)."""
    from ztlctl.actions.definitions import ActionDefinition, ActionParam
    from ztlctl.actions.registry import get_action_registry

    # Lazy controller imports
    from ztlctl.controllers.discovery import DiscoveryController
    from ztlctl.controllers.docs import DocsController
    from ztlctl.controllers.init_ctrl import InitController
    from ztlctl.controllers.upgrade import UpgradeController
    from ztlctl.controllers.vector import VectorController
    from ztlctl.controllers.workflow import WorkflowController

    registry = get_action_registry()

    # -----------------------------------------------------------------------
    # vector category
    # -----------------------------------------------------------------------

    registry.register(
        ActionDefinition(
            name="vector_status",
            description="Check semantic search availability and index status.",
            category="vector",
            params=(),
            handler=lambda vault, **kw: VectorController(vault).status(),
            side_effect="read",
            mcp_when_to_use="Checking whether semantic search is available before using it.",
            mcp_avoid_when="You already know semantic search is available.",
            cli_group="vector",
            cli_name="status",
        )
    )

    registry.register(
        ActionDefinition(
            name="reindex_all",
            description="Re-embed all non-archived nodes for semantic search.",
            category="vector",
            params=(),
            handler=lambda vault, **kw: VectorController(vault).reindex_all(**kw),
            side_effect="read",
            mcp_when_to_use="After bulk imports or model changes to refresh the vector index.",
            mcp_avoid_when="The index is already up to date.",
            cli_group="vector",
            cli_name="reindex",
        )
    )

    # -----------------------------------------------------------------------
    # upgrade category
    # -----------------------------------------------------------------------

    registry.register(
        ActionDefinition(
            name="check_pending",
            description="List pending migrations without applying.",
            category="upgrade",
            params=(),
            handler=lambda vault, **kw: UpgradeController(vault).check_pending(**kw),
            side_effect="read",
            mcp_when_to_use="Checking whether the vault DB schema is up to date before upgrading.",
            mcp_avoid_when="You want to apply migrations immediately.",
            cli_group="upgrade",
            cli_name="check",
        )
    )

    registry.register(
        ActionDefinition(
            name="apply",
            description="BACKUP → MIGRATE → VALIDATE → REPORT pipeline.",
            category="upgrade",
            params=(),
            handler=lambda vault, **kw: UpgradeController(vault).apply(**kw),
            side_effect="write",
            mcp_when_to_use="Upgrading the vault DB schema to the current head.",
            mcp_avoid_when="The vault is already at the current schema version.",
            cli_group="upgrade",
            cli_name="apply",
        )
    )

    registry.register(
        ActionDefinition(
            name="stamp_current",
            description="Stamp DB as at current head (for freshly created DBs).",
            category="upgrade",
            params=(),
            handler=lambda vault, **kw: UpgradeController(vault).stamp_current(**kw),
            side_effect="write",
            mcp_when_to_use="Initializing the migration tracking for a newly created vault.",
            mcp_avoid_when="The vault already has migration history.",
            cli_group="upgrade",
            cli_name="stamp",
        )
    )

    # -----------------------------------------------------------------------
    # workflow category
    # -----------------------------------------------------------------------

    registry.register(
        ActionDefinition(
            name="init_workflow",
            description="Initialize Copier-backed workflow scaffolding for a vault.",
            category="workflow",
            params=(
                ActionParam(
                    "vault_root",
                    str,
                    required=True,
                    description="Path to the vault root directory.",
                    cli_is_argument=True,
                ),
                ActionParam(
                    "choices",
                    dict,
                    required=True,
                    description="Workflow scaffolding choices (profile, client, tone, etc.).",
                ),
                ActionParam(
                    "force_trust",
                    bool,
                    required=False,
                    default=False,
                    description=(
                        "Allow plugin template hooks to execute (unsafe mode). "
                        "Built-in templates always use unsafe=False regardless of this flag."
                    ),
                    cli_flag=True,
                ),
            ),
            handler=lambda vault, **kw: WorkflowController(vault).init_workflow(**kw),
            side_effect="write",
            mcp_when_to_use="Setting up workflow templates for a newly initialized vault.",
            mcp_avoid_when="Workflow scaffolding is already initialized.",
            custom_presentation=True,
        )
    )

    registry.register(
        ActionDefinition(
            name="update_workflow",
            description="Update workflow scaffolding using stored answers plus optional overrides.",
            category="workflow",
            params=(
                ActionParam(
                    "vault_root",
                    str,
                    required=True,
                    description="Path to the vault root directory.",
                    cli_is_argument=True,
                ),
                ActionParam(
                    "choices",
                    dict,
                    required=False,
                    default=None,
                    description="Optional choice overrides to apply during update.",
                ),
                ActionParam(
                    "force_trust",
                    bool,
                    required=False,
                    default=False,
                    description=(
                        "Allow plugin template hooks to execute (unsafe mode). "
                        "Built-in templates always use unsafe=False regardless of this flag."
                    ),
                    cli_flag=True,
                ),
            ),
            handler=lambda vault, **kw: WorkflowController(vault).update_workflow(**kw),
            side_effect="write",
            mcp_when_to_use="Refreshing workflow templates after configuration changes.",
            mcp_avoid_when="No workflow scaffolding has been initialized.",
            custom_presentation=True,
        )
    )

    registry.register(
        ActionDefinition(
            name="export_assets",
            description="Render portable client workflow assets into a vault.",
            category="workflow",
            params=(
                ActionParam(
                    "vault_root",
                    str,
                    required=True,
                    description="Path to the vault root directory.",
                    cli_is_argument=True,
                ),
                ActionParam(
                    "client",
                    str,
                    required=False,
                    default="both",
                    description="Client to export assets for: obsidian, cli, or both.",
                    choices=("obsidian", "cli", "both"),
                ),
            ),
            handler=lambda vault, **kw: WorkflowController(vault).export_assets(**kw),
            side_effect="write",
            mcp_when_to_use="Generating or refreshing workflow client assets for a vault.",
            mcp_avoid_when="No workflow scaffolding exists yet.",
            custom_presentation=True,
        )
    )

    # -----------------------------------------------------------------------
    # init category
    # -----------------------------------------------------------------------

    registry.register(
        ActionDefinition(
            name="init_vault",
            description="Create a new ztlctl vault at path.",
            category="init",
            params=(
                ActionParam(
                    "path",
                    str,
                    required=True,
                    description="Filesystem path where the vault will be created.",
                    cli_is_argument=True,
                ),
                ActionParam(
                    "name",
                    str,
                    required=True,
                    description="Human-readable vault name.",
                ),
                ActionParam(
                    "profile",
                    str,
                    required=False,
                    default=None,
                    description="Workflow profile to apply during initialization.",
                ),
                ActionParam(
                    "client",
                    str,
                    required=False,
                    default=None,
                    description="Client integration to configure (obsidian, cli, etc.).",
                ),
                ActionParam(
                    "tone",
                    str,
                    required=False,
                    default="research-partner",
                    description="Vault tone/persona for self/ generation.",
                ),
                ActionParam(
                    "topics",
                    list,
                    required=False,
                    default=None,
                    description="Initial topic directories to scaffold.",
                    cli_multiple=True,
                ),
                ActionParam(
                    "no_workflow",
                    bool,
                    required=False,
                    default=False,
                    description="Skip workflow scaffolding during init.",
                    cli_flag=True,
                ),
            ),
            handler=lambda vault, **kw: InitController(vault).init_vault(**kw),
            side_effect="write",
            mcp_when_to_use="Creating a new ztlctl vault from scratch.",
            mcp_avoid_when="A vault already exists at the target path.",
            custom_presentation=True,
            cli_interactive_params=("name",),
        )
    )

    registry.register(
        ActionDefinition(
            name="regenerate_self",
            description="Re-render self/ files from current vault settings.",
            category="init",
            params=(),
            handler=lambda vault, **kw: InitController(vault).regenerate_self(**kw),
            side_effect="write",
            mcp_when_to_use="Refreshing self/ agent context files after configuration changes.",
            mcp_avoid_when="The self/ files are already current.",
            cli_group="init",
            cli_name="regenerate",
        )
    )

    registry.register(
        ActionDefinition(
            name="check_staleness",
            description="Compare ztlctl.toml mtime vs self/*.md mtimes.",
            category="init",
            params=(),
            handler=lambda vault, **kw: InitController(vault).check_staleness(**kw),
            side_effect="read",
            mcp_when_to_use="Checking whether self/ agent context files need regeneration.",
            mcp_avoid_when="You already know the self/ files are current.",
            cli_group="init",
            cli_name="staleness",
        )
    )

    # -----------------------------------------------------------------------
    # discovery category (AGNT-04 — progressive tool disclosure)
    # -----------------------------------------------------------------------

    registry.register(
        ActionDefinition(
            name="discover_categories",
            description="List all tool categories with their active/core status and tool names.",
            category="discovery",
            params=(),
            handler=lambda vault, **kw: DiscoveryController(vault).discover_categories(**kw),
            side_effect="read",
            mcp_when_to_use=(
                "Use to understand the available tool surface and which categories are active."
            ),
            mcp_avoid_when="Unnecessary if you already know which tools you need.",
        )
    )

    registry.register(
        ActionDefinition(
            name="activate_category",
            description="Activate a tool category to include its tools in the active surface.",
            category="discovery",
            params=(
                ActionParam(
                    "category",
                    str,
                    required=True,
                    description="Category name to activate.",
                ),
            ),
            handler=lambda vault, **kw: DiscoveryController(vault).activate_category(**kw),
            side_effect="write",
            mcp_when_to_use=(
                "Use when you need tools from an inactive category (e.g., export, workflow, admin)."
            ),
            mcp_avoid_when="Core categories are already active by default.",
            mcp_common_errors=("VALIDATION_FAILED",),
        )
    )

    registry.register(
        ActionDefinition(
            name="deactivate_category",
            description="Deactivate a non-core tool category to reduce the active tool surface.",
            category="discovery",
            params=(
                ActionParam(
                    "category",
                    str,
                    required=True,
                    description="Category name to deactivate.",
                ),
            ),
            handler=lambda vault, **kw: DiscoveryController(vault).deactivate_category(**kw),
            side_effect="write",
            mcp_when_to_use="Use to reduce tool noise after finishing work in a specific category.",
            mcp_avoid_when=(
                "Cannot deactivate core categories "
                "(creation, mutation, query, graph, lifecycle, session)."
            ),
            mcp_common_errors=("VALIDATION_FAILED", "NOT_FOUND"),
        )
    )

    # -----------------------------------------------------------------------
    # docs category
    # -----------------------------------------------------------------------

    registry.register(
        ActionDefinition(
            name="docs_search",
            description="Search the ztlctl documentation corpus.",
            category="docs",
            params=(
                ActionParam(
                    "query",
                    str,
                    required=True,
                    description="Search query string.",
                    cli_is_argument=True,
                    mcp_example="how to create a note",
                ),
                ActionParam(
                    "limit",
                    int,
                    required=False,
                    default=5,
                    description="Maximum number of results to return.",
                ),
            ),
            handler=lambda vault, **kw: DocsController(vault).search(**kw),
            side_effect="read",
            mcp_when_to_use=(
                "Finding documentation pages relevant to a query without leaving the tool."
            ),
            mcp_avoid_when="You are searching vault notes, not ztlctl documentation.",
            cli_group="docs",
            cli_name="search",
            custom_presentation=True,  # CLI is hand-written in commands/docs.py
        )
    )
