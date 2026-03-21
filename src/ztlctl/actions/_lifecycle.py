"""Lifecycle and reweave ActionDefinition registrations."""

from __future__ import annotations


def _register_lifecycle_actions() -> None:
    """Register lifecycle and reweave ActionDefinitions."""
    from ztlctl.actions.definitions import ActionDefinition, ActionParam
    from ztlctl.actions.registry import get_action_registry

    # Lazy controller imports
    from ztlctl.controllers.reweave import ReweaveController
    from ztlctl.controllers.update import UpdateController

    registry = get_action_registry()

    # -----------------------------------------------------------------------
    # lifecycle category
    # -----------------------------------------------------------------------

    registry.register(
        ActionDefinition(
            name="update",
            description="Update a content item via the five-stage pipeline.",
            category="lifecycle",
            params=(
                ActionParam(
                    "content_id",
                    str,
                    required=True,
                    description="Existing vault ID to modify.",
                    cli_is_argument=True,
                    mcp_example="NOTE-0001",
                ),
                ActionParam(
                    "changes",
                    dict,
                    required=True,
                    description="Partial field map to merge into frontmatter and content.",
                    mcp_example='{"tags": ["project/alpha"], "status": "active"}',
                ),
            ),
            handler=lambda vault, **kw: UpdateController(vault).update(**kw),
            side_effect="write",
            mcp_when_to_use="Changing fields on an existing item (title, tags, topic, or body).",
            mcp_avoid_when="You need to archive the item or create a new one instead.",
            mcp_common_errors=(
                "NOT_FOUND",
                "VALIDATION_FAILED",
                "INVALID_TRANSITION",
                "UNKNOWN_TYPE",
            ),
            custom_presentation=True,
        )
    )

    registry.register(
        ActionDefinition(
            name="archive",
            description="Archive a content item (soft delete, preserves edges).",
            category="lifecycle",
            params=(
                ActionParam(
                    "content_id",
                    str,
                    required=True,
                    description="Existing vault ID to archive or close.",
                    cli_is_argument=True,
                    mcp_example="NOTE-0001",
                ),
            ),
            handler=lambda vault, **kw: UpdateController(vault).archive(**kw),
            side_effect="write",
            mcp_when_to_use="Marking an item complete or archived.",
            mcp_avoid_when="You only need to edit fields without changing lifecycle state.",
            mcp_common_errors=("NOT_FOUND",),
            cli_group=None,
            cli_name="archive",
        )
    )

    registry.register(
        ActionDefinition(
            name="supersede",
            description="Supersede a decision with a new one.",
            category="lifecycle",
            params=(
                ActionParam(
                    "old_id",
                    str,
                    required=True,
                    description="Decision ID to supersede.",
                    cli_is_argument=True,
                ),
                ActionParam(
                    "new_id",
                    str,
                    required=True,
                    description="Replacement decision ID.",
                    cli_is_argument=True,
                ),
            ),
            handler=lambda vault, **kw: UpdateController(vault).supersede(**kw),
            side_effect="write",
            mcp_when_to_use="Replacing an outdated decision with a newer one.",
            mcp_avoid_when="The old decision is still valid or no replacement exists.",
            mcp_common_errors=("NOT_FOUND", "INVALID_TRANSITION"),
            cli_group=None,
            cli_name="supersede",
        )
    )

    # -----------------------------------------------------------------------
    # reweave category
    # -----------------------------------------------------------------------

    registry.register(
        ActionDefinition(
            name="reweave",
            description="Run reweave on a specific item or the latest creation.",
            category="reweave",
            params=(
                ActionParam(
                    "content_id",
                    str,
                    required=False,
                    default=None,
                    description="Optional target item ID. Omit to run across the broader vault.",
                    mcp_example="NOTE-0001",
                ),
                ActionParam(
                    "dry_run",
                    bool,
                    required=False,
                    default=False,
                    description="Set true to preview suggestions without mutating the vault.",
                    cli_flag=True,
                ),
                ActionParam(
                    "min_score_override",
                    float,
                    required=False,
                    default=None,
                    description="Override the minimum relevance score threshold.",
                ),
            ),
            handler=lambda vault, **kw: ReweaveController(vault).reweave(**kw),
            side_effect="write",
            mcp_when_to_use="After creating or updating content, to discover and add useful links.",
            mcp_avoid_when="The vault is still too small for meaningful graph-based suggestions.",
            mcp_common_errors=("NOT_FOUND",),
            cli_group="reweave",
            cli_name="run",
        )
    )

    registry.register(
        ActionDefinition(
            name="prune",
            description="Remove stale links that score below threshold.",
            category="reweave",
            params=(
                ActionParam(
                    "content_id",
                    str,
                    required=False,
                    default=None,
                    description="Optional target item ID. Omit to prune across the vault.",
                ),
                ActionParam(
                    "dry_run",
                    bool,
                    required=False,
                    default=False,
                    description="Preview pruning candidates without removing links.",
                    cli_flag=True,
                ),
            ),
            handler=lambda vault, **kw: ReweaveController(vault).prune(**kw),
            side_effect="write",
            mcp_when_to_use="After significant vault changes to remove obsolete low-scoring links.",
            mcp_avoid_when="The vault is new or reweave has not run yet.",
            cli_group="reweave",
            cli_name="prune",
        )
    )

    registry.register(
        ActionDefinition(
            name="undo",
            description="Reverse a reweave operation via audit trail.",
            category="reweave",
            params=(
                ActionParam(
                    "reweave_id",
                    int,
                    required=False,
                    default=None,
                    description="ID of the reweave operation to reverse. Omit to undo the latest.",
                ),
            ),
            handler=lambda vault, **kw: ReweaveController(vault).undo(**kw),
            side_effect="write",
            mcp_when_to_use="Reversing an incorrect or undesired reweave operation.",
            mcp_avoid_when="No reweave operations have been recorded.",
            cli_group="reweave",
            cli_name="undo",
        )
    )
