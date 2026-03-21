"""Check and maintenance ActionDefinition registrations."""

from __future__ import annotations


def _register_check_actions() -> None:
    """Register check and maintenance ActionDefinitions."""
    from ztlctl.actions.definitions import ActionDefinition, ActionParam
    from ztlctl.actions.registry import get_action_registry

    # Lazy controller imports
    from ztlctl.controllers.check import CheckController

    registry = get_action_registry()

    # -----------------------------------------------------------------------
    # check category
    # -----------------------------------------------------------------------

    registry.register(
        ActionDefinition(
            name="check",
            description="Report integrity issues without modifying anything.",
            category="check",
            params=(
                ActionParam(
                    "min_severity",
                    str,
                    required=False,
                    default="warning",
                    description="Minimum severity level to report: info, warning, or error.",
                    choices=("info", "warning", "error"),
                ),
            ),
            handler=lambda vault, **kw: CheckController(vault).check(**kw),
            side_effect="read",
            mcp_when_to_use="Auditing vault health before bulk operations or maintenance.",
            mcp_avoid_when="You need automatic repairs; use fix instead.",
            cli_group="check",
        )
    )

    registry.register(
        ActionDefinition(
            name="fix",
            description="Automatically repair integrity issues.",
            category="check",
            params=(
                ActionParam(
                    "level",
                    str,
                    required=False,
                    default="safe",
                    description="Repair level: safe or aggressive.",
                    choices=("safe", "aggressive"),
                ),
            ),
            handler=lambda vault, **kw: CheckController(vault).fix(**kw),
            side_effect="write",
            mcp_when_to_use="Automatically repairing vault issues after a check scan.",
            mcp_avoid_when="You want a non-destructive audit only.",
            cli_group="check",
        )
    )

    registry.register(
        ActionDefinition(
            name="rebuild",
            description="Full DB rebuild from filesystem (files are the source of truth).",
            category="check",
            params=(),
            handler=lambda vault, **kw: CheckController(vault).rebuild(**kw),
            side_effect="write",
            mcp_when_to_use="Recovering from DB corruption or after manual file edits.",
            mcp_avoid_when="The DB is in a consistent state; use fix for targeted repairs.",
            cli_group="check",
        )
    )

    registry.register(
        ActionDefinition(
            name="rollback",
            description="Restore DB from latest backup.",
            category="check",
            params=(),
            handler=lambda vault, **kw: CheckController(vault).rollback(**kw),
            side_effect="write",
            mcp_when_to_use="Reverting to a previous DB state after a problematic operation.",
            mcp_avoid_when="No backup exists or the backup is also corrupt.",
            cli_group="check",
        )
    )

    registry.register(
        ActionDefinition(
            name="check_alignment",
            description="Check a decision against polaris priorities for alignment.",
            category="check",
            params=(
                ActionParam(
                    "decision",
                    str,
                    required=True,
                    description=(
                        "Description of the decision to evaluate against polaris priorities."
                    ),
                ),
            ),
            handler=lambda vault, **kw: CheckController(vault).check_alignment(**kw),
            side_effect="read",
            mcp_when_to_use=(
                "Before making a significant decision, to check alignment "
                "with the vault's polaris priorities."
            ),
            mcp_avoid_when="No polaris file exists yet, or the decision is trivial.",
            cli_group="check",
            cli_name="alignment",
        )
    )

    # -----------------------------------------------------------------------
    # maintenance category
    # -----------------------------------------------------------------------

    registry.register(
        ActionDefinition(
            name="event_purge",
            description="Purge dead-letter events from the event WAL.",
            category="maintenance",
            params=(
                ActionParam(
                    "older_than_days",
                    int,
                    required=False,
                    default=None,
                    description=(
                        "Delete dead-letter events older than N days "
                        "(default: config dead_letter_retention_days)."
                    ),
                ),
            ),
            handler=lambda vault, **kw: CheckController(vault).event_purge(**kw),
            side_effect="write",
            mcp_when_to_use=(
                "Clearing accumulated dead-letter events from the event WAL "
                "after resolving plugin failures."
            ),
            mcp_avoid_when="Dead-letter events are still being investigated.",
            cli_group="event",
            cli_name="purge",
        )
    )
