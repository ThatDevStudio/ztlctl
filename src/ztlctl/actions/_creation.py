"""Creation ActionDefinition registrations."""

from __future__ import annotations


def _register_creation_actions() -> None:
    """Register creation ActionDefinitions."""
    from ztlctl.actions.definitions import ActionDefinition, ActionParam
    from ztlctl.actions.registry import get_action_registry

    # Lazy controller imports
    from ztlctl.controllers.create import CreateController

    registry = get_action_registry()

    registry.register(
        ActionDefinition(
            name="create_note",
            description="Create a new note in the vault.",
            category="creation",
            params=(
                ActionParam(
                    "title",
                    str,
                    required=True,
                    description="Human-readable note title; used for ID generation and search.",
                    cli_is_argument=True,
                    mcp_example="Python typing patterns",
                ),
                ActionParam(
                    "subtype",
                    str,
                    required=False,
                    default=None,
                    description="Optional subtype (e.g. knowledge, decision, or plugin-defined).",
                ),
                ActionParam(
                    "tags",
                    list,
                    required=False,
                    default=None,
                    description="Optional tags. Domain/scope tags are recommended.",
                    cli_multiple=True,
                ),
                ActionParam(
                    "topic",
                    str,
                    required=False,
                    default=None,
                    description="Optional topic directory under notes/.",
                ),
                ActionParam(
                    "body",
                    str,
                    required=False,
                    default=None,
                    description="Optional markdown body for synthesized content.",
                ),
                ActionParam(
                    "key_points",
                    list,
                    required=False,
                    default=None,
                    description="Optional short bullet-style summary items.",
                    cli_multiple=True,
                ),
                ActionParam(
                    "links",
                    dict,
                    required=False,
                    default=None,
                    description="Optional explicit edge map keyed by relation type.",
                ),
                ActionParam(
                    "aliases",
                    list,
                    required=False,
                    default=None,
                    description="Optional alternate names for search and linking.",
                    cli_multiple=True,
                ),
            ),
            handler=lambda vault, **kw: CreateController(vault).create_note(**kw),
            side_effect="write",
            mcp_when_to_use="Capturing a synthesized idea, knowledge note, or decision.",
            mcp_avoid_when="You only need a quick raw capture or a source record.",
            mcp_common_errors=("VALIDATION_FAILED", "ID_COLLISION", "UNKNOWN_TYPE"),
            cli_group="create",
            cli_interactive_params=("title",),
        )
    )

    registry.register(
        ActionDefinition(
            name="create_reference",
            description="Create a new reference to an external source.",
            category="creation",
            params=(
                ActionParam(
                    "title",
                    str,
                    required=True,
                    description="Reference title as it should appear in the vault.",
                    cli_is_argument=True,
                ),
                ActionParam(
                    "url",
                    str,
                    required=False,
                    default=None,
                    description="Optional canonical source URL.",
                ),
                ActionParam(
                    "subtype",
                    str,
                    required=False,
                    default=None,
                    description="Optional reference subtype such as spec.",
                ),
                ActionParam(
                    "tags",
                    list,
                    required=False,
                    default=None,
                    description="Optional tags for source categorization.",
                    cli_multiple=True,
                ),
                ActionParam(
                    "topic",
                    str,
                    required=False,
                    default=None,
                    description="Optional topic directory under notes/.",
                ),
                ActionParam(
                    "body",
                    str,
                    required=False,
                    default=None,
                    description="Optional markdown body.",
                ),
                ActionParam(
                    "summary",
                    str,
                    required=False,
                    default=None,
                    description="Optional capture summary hint.",
                ),
            ),
            handler=lambda vault, **kw: CreateController(vault).create_reference(**kw),
            side_effect="write",
            mcp_when_to_use="Logging an external source such as an article, paper, or spec.",
            mcp_avoid_when="The content is your own synthesis rather than an external source.",
            mcp_common_errors=("VALIDATION_FAILED", "ID_COLLISION", "UNKNOWN_TYPE"),
            cli_group="create",
            cli_interactive_params=("title",),
        )
    )

    registry.register(
        ActionDefinition(
            name="create_task",
            description="Create a new task in the vault.",
            category="creation",
            params=(
                ActionParam(
                    "title",
                    str,
                    required=True,
                    description="Task title phrased as concrete work.",
                    cli_is_argument=True,
                ),
                ActionParam(
                    "priority",
                    str,
                    required=False,
                    default="medium",
                    description="Priority bucket: low, medium, or high.",
                    choices=("low", "medium", "high"),
                ),
                ActionParam(
                    "impact",
                    str,
                    required=False,
                    default="medium",
                    description="Expected impact bucket used in queue scoring.",
                    choices=("low", "medium", "high"),
                ),
                ActionParam(
                    "effort",
                    str,
                    required=False,
                    default="medium",
                    description="Estimated effort bucket used in queue scoring.",
                    choices=("low", "medium", "high"),
                ),
                ActionParam(
                    "tags",
                    list,
                    required=False,
                    default=None,
                    description="Optional tags for routing and filtering.",
                    cli_multiple=True,
                ),
            ),
            handler=lambda vault, **kw: CreateController(vault).create_task(**kw),
            side_effect="write",
            mcp_when_to_use="Tracking actionable work that should appear in the queue.",
            mcp_avoid_when="You are capturing knowledge or a session log, not executable work.",
            mcp_common_errors=("VALIDATION_FAILED", "ID_COLLISION"),
            cli_group="create",
            cli_interactive_params=("title",),
        )
    )

    registry.register(
        ActionDefinition(
            name="create_batch",
            description="Create multiple vault items atomically.",
            category="creation",
            params=(
                ActionParam(
                    "items",
                    list,
                    required=True,
                    description="List of item dicts, each with 'type' and creation fields.",
                ),
                ActionParam(
                    "partial",
                    bool,
                    required=False,
                    default=False,
                    description="Allow partial success if some items fail.",
                    cli_flag=True,
                ),
            ),
            handler=lambda vault, **kw: CreateController(vault).create_batch(**kw),
            side_effect="write",
            mcp_when_to_use="Creating multiple items in one operation from a structured import.",
            mcp_avoid_when="You are creating a single item.",
            mcp_common_errors=("VALIDATION_FAILED", "ID_COLLISION"),
            custom_presentation=True,
        )
    )

    registry.register(
        ActionDefinition(
            name="garden_seed",
            description="Plant a seed note -- quick capture with minimal metadata.",
            category="creation",
            params=(
                ActionParam(
                    "title",
                    str,
                    required=True,
                    description="Seed note title -- quick thought or half-formed idea.",
                    cli_is_argument=True,
                    mcp_example="Half-formed idea about caching",
                ),
                ActionParam(
                    "tags",
                    list,
                    required=False,
                    default=None,
                    description="Optional tags. Comma-separated in CLI.",
                    cli_multiple=True,
                ),
                ActionParam(
                    "topic",
                    str,
                    required=False,
                    default=None,
                    description="Optional topic scope.",
                ),
            ),
            handler=lambda vault, **kw: CreateController(vault).create_note(
                kw["title"],
                tags=kw.get("tags"),
                topic=kw.get("topic"),
                maturity="seed",
            ),
            side_effect="write",
            cli_group="garden",
            cli_name="seed",
            cli_examples=(
                "  ztlctl garden seed \"Half-formed idea\"\n"
                "  ztlctl garden seed \"Quick thought\" --tags domain/topic\n"
                "  ztlctl --json garden seed \"API design hunch\" --topic architecture"
            ),
        )
    )
