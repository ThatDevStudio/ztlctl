"""Session ActionDefinition registrations."""

from __future__ import annotations

from typing import Any


def _register_session_actions() -> None:
    """Register session ActionDefinitions."""
    from ztlctl.actions.definitions import ActionDefinition, ActionParam
    from ztlctl.actions.registry import get_action_registry

    # Lazy controller imports
    from ztlctl.controllers.session import SessionController

    registry = get_action_registry()

    registry.register(
        ActionDefinition(
            name="start",
            description="Start a new session, returning the LOG-NNNN id.",
            category="session",
            params=(
                ActionParam(
                    "topic",
                    str,
                    required=True,
                    description="Short session topic used for tracking and later context assembly.",
                    cli_is_argument=True,
                    mcp_example="Refactoring the graph engine",
                ),
            ),
            handler=lambda vault, **kw: SessionController(vault).start(**kw),
            side_effect="write",
            mcp_when_to_use="Beginning a focused work session that should be tracked in the vault.",
            mcp_avoid_when="A session is already active.",
            mcp_common_errors=("ACTIVE_SESSION_EXISTS",),
            cli_group="session",
            cli_interactive_params=("topic",),
        )
    )

    registry.register(
        ActionDefinition(
            name="close",
            description="Close the active session with enrichment pipeline.",
            category="session",
            params=(
                ActionParam(
                    "summary",
                    str,
                    required=False,
                    default=None,
                    description="Optional end-of-session summary for the log.",
                ),
            ),
            handler=lambda vault, **kw: SessionController(vault).close(**kw),
            side_effect="write",
            mcp_when_to_use="Ending a tracked work session and triggering session enrichment.",
            mcp_avoid_when="No session is active.",
            mcp_common_errors=("NO_ACTIVE_SESSION",),
            cli_group="session",
        )
    )

    registry.register(
        ActionDefinition(
            name="reopen",
            description="Reopen a previously closed session.",
            category="session",
            params=(
                ActionParam(
                    "session_id",
                    str,
                    required=True,
                    description="ID of the session to reopen.",
                    cli_is_argument=True,
                    mcp_example="LOG-0001",
                ),
            ),
            handler=lambda vault, **kw: SessionController(vault).reopen(**kw),
            side_effect="write",
            mcp_when_to_use="Resuming work on a previously closed session.",
            mcp_avoid_when="An active session already exists.",
            mcp_common_errors=("NOT_FOUND", "ACTIVE_SESSION_EXISTS"),
            cli_group="session",
        )
    )

    registry.register(
        ActionDefinition(
            name="status",
            description="Return the active session summary, if any.",
            category="session",
            params=(),
            handler=lambda vault, **kw: SessionController(vault).status(**kw),
            side_effect="read",
            mcp_when_to_use="Checking whether a session is open and what it is tracking.",
            mcp_avoid_when="You need the full vault context rather than session state.",
            cli_group="session",
        )
    )

    registry.register(
        ActionDefinition(
            name="log_entry",
            description="Append a log entry to the active session.",
            category="session",
            params=(
                ActionParam(
                    "message",
                    str,
                    required=True,
                    description="Log entry message text.",
                    cli_is_argument=True,
                ),
                ActionParam(
                    "pin",
                    bool,
                    required=False,
                    default=False,
                    description="Pin this entry for extraction and summary.",
                    cli_flag=True,
                ),
                ActionParam(
                    "cost",
                    int,
                    required=False,
                    default=0,
                    description="Token cost to report for this entry.",
                ),
                ActionParam(
                    "detail",
                    str,
                    required=False,
                    default=None,
                    description="Extended detail or context for the entry.",
                ),
                ActionParam(
                    "entry_type",
                    str,
                    required=False,
                    default="log_entry",
                    description="Entry type classification.",
                ),
                ActionParam(
                    "subtype",
                    str,
                    required=False,
                    default=None,
                    description="Optional entry subtype.",
                ),
                ActionParam(
                    "references",
                    list,
                    required=False,
                    default=None,
                    description="Optional vault IDs referenced by this entry.",
                    cli_multiple=True,
                ),
            ),
            handler=lambda vault, **kw: SessionController(vault).log_entry(**kw),
            side_effect="write",
            mcp_when_to_use="Recording a progress note, decision, or cost in the active session.",
            mcp_avoid_when="No session is active.",
            mcp_common_errors=("NO_ACTIVE_SESSION",),
            cli_group="session",
            cli_name="log",
        )
    )

    registry.register(
        ActionDefinition(
            name="cost",
            description="Query or report accumulated token cost for the active session.",
            category="session",
            params=(
                ActionParam(
                    "report",
                    int,
                    required=False,
                    default=None,
                    description="Token cost to report (adds to running total). Omit to query.",
                ),
            ),
            handler=lambda vault, **kw: SessionController(vault).cost(**kw),
            side_effect="read",
            mcp_when_to_use="Checking or updating the running token cost for the active session.",
            mcp_avoid_when="No session is active or you need full session details.",
            cli_group="session",
        )
    )

    registry.register(
        ActionDefinition(
            name="context",
            description="Build token-budgeted agent context payload.",
            category="session",
            params=(
                ActionParam(
                    "topic",
                    str,
                    required=False,
                    default=None,
                    description="Optional topic to enrich the context snapshot.",
                ),
                ActionParam(
                    "budget",
                    int,
                    required=False,
                    default=8000,
                    description="Token budget for the assembled context.",
                ),
                ActionParam(
                    "ignore_checkpoints",
                    bool,
                    required=False,
                    default=False,
                    description="Ignore checkpoint markers when assembling context.",
                    cli_flag=True,
                ),
            ),
            handler=lambda vault, **kw: SessionController(vault).context(**kw),
            side_effect="read",
            mcp_when_to_use="Assembling a read-only snapshot of recent items and work queue.",
            mcp_avoid_when="You only need a single document or single-purpose query result.",
            cli_group="session",
        )
    )

    registry.register(
        ActionDefinition(
            name="brief",
            description="Quick orientation (delegates to ContextAssembler).",
            category="session",
            params=(),
            handler=lambda vault, **kw: SessionController(vault).brief(**kw),
            side_effect="read",
            mcp_when_to_use="Getting a quick orientation to the current vault and session state.",
            mcp_avoid_when="You need a full token-budgeted context payload.",
            cli_group="session",
        )
    )

    registry.register(
        ActionDefinition(
            name="extract_decision",
            description="Extract a decision note from a session log's pinned/decision entries.",
            category="session",
            params=(
                ActionParam(
                    "session_id",
                    str,
                    required=True,
                    description="Session log ID to extract a decision from.",
                    cli_is_argument=True,
                    mcp_example="LOG-0001",
                ),
                ActionParam(
                    "title",
                    str,
                    required=False,
                    default=None,
                    description="Optional title for the extracted decision note.",
                ),
            ),
            handler=lambda vault, **kw: SessionController(vault).extract_decision(**kw),
            side_effect="write",
            mcp_when_to_use="Materializing a formal decision note from a session log.",
            mcp_avoid_when="The session has no pinned or decision entries.",
            mcp_common_errors=("NOT_FOUND",),
            cli_group="session",
            cli_name="extract",
        )
    )
