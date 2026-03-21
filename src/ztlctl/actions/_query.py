"""Query ActionDefinition registrations."""

from __future__ import annotations


def _register_query_actions() -> None:
    """Register query ActionDefinitions."""
    from ztlctl.actions.definitions import ActionDefinition, ActionParam
    from ztlctl.actions.registry import get_action_registry

    # Lazy controller imports
    from ztlctl.controllers.query import QueryController

    registry = get_action_registry()

    registry.register(
        ActionDefinition(
            name="count_items",
            description="Return total indexed item count.",
            category="query",
            params=(
                ActionParam(
                    "include_archived",
                    bool,
                    required=False,
                    default=False,
                    description="Include archived items in the count.",
                    cli_flag=True,
                ),
            ),
            handler=lambda vault, **kw: QueryController(vault).count_items(**kw),
            side_effect="read",
            mcp_when_to_use="Getting a quick overview of vault size.",
            mcp_avoid_when="You need a filtered listing or full-text search.",
            cli_group="query",
            cli_name="count",
        )
    )

    registry.register(
        ActionDefinition(
            name="search",
            description="Full-text search via FTS5 BM25.",
            category="query",
            params=(
                ActionParam(
                    "query",
                    str,
                    required=True,
                    description="Non-empty search string.",
                    cli_is_argument=True,
                    mcp_example="python typing patterns",
                ),
                ActionParam(
                    "content_type",
                    str,
                    required=False,
                    default=None,
                    description="Optional filter: note, reference, task, or log.",
                    choices=("note", "reference", "task", "log"),
                    cli_name="type",
                ),
                ActionParam(
                    "tag",
                    str,
                    required=False,
                    default=None,
                    description="Optional tag filter.",
                ),
                ActionParam(
                    "space",
                    str,
                    required=False,
                    default=None,
                    description="Filter by vault space: notes, ops, or self.",
                    choices=("notes", "ops", "self"),
                ),
                ActionParam(
                    "rank_by",
                    str,
                    required=False,
                    default="relevance",
                    description="Ranking mode: relevance, recency, graph, semantic, or hybrid.",
                    choices=(
                        "relevance",
                        "recency",
                        "graph",
                        "semantic",
                        "hybrid",
                        "review",
                        "garden",
                    ),
                ),
                ActionParam(
                    "limit",
                    int,
                    required=False,
                    default=20,
                    description="Maximum number of results to return.",
                ),
            ),
            handler=lambda vault, **kw: QueryController(vault).search(**kw),
            side_effect="read",
            mcp_when_to_use="Finding content by keywords with optional type, tag, or space filter.",
            mcp_avoid_when="You already have an exact ID or only need a filtered listing.",
            mcp_common_errors=("EMPTY_QUERY",),
            cli_group="query",
        )
    )

    registry.register(
        ActionDefinition(
            name="get",
            description="Retrieve a single content item by ID.",
            category="query",
            params=(
                ActionParam(
                    "content_id",
                    str,
                    required=True,
                    description="Exact vault ID to fetch.",
                    cli_is_argument=True,
                    mcp_example="NOTE-0001",
                ),
            ),
            handler=lambda vault, **kw: QueryController(vault).get(**kw),
            side_effect="read",
            mcp_when_to_use="Retrieving the full content of a known item.",
            mcp_avoid_when="You still need to discover the correct target item.",
            mcp_common_errors=("NOT_FOUND",),
            cli_group="query",
        )
    )

    registry.register(
        ActionDefinition(
            name="list_items",
            description="List content items with optional filters.",
            category="query",
            params=(
                ActionParam(
                    "content_type",
                    str,
                    required=False,
                    default=None,
                    description="Optional type filter: note, reference, task, or log.",
                    choices=("note", "reference", "task", "log"),
                    cli_name="type",
                ),
                ActionParam(
                    "status",
                    str,
                    required=False,
                    default=None,
                    description="Optional status filter.",
                ),
                ActionParam(
                    "tag",
                    str,
                    required=False,
                    default=None,
                    description="Optional tag filter.",
                ),
                ActionParam(
                    "topic",
                    str,
                    required=False,
                    default=None,
                    description="Optional topic filter.",
                ),
                ActionParam(
                    "subtype",
                    str,
                    required=False,
                    default=None,
                    description="Optional subtype filter.",
                ),
                ActionParam(
                    "maturity",
                    str,
                    required=False,
                    default=None,
                    description="Optional maturity filter for garden notes.",
                    choices=("seed", "sprout", "evergreen"),
                ),
                ActionParam(
                    "space",
                    str,
                    required=False,
                    default=None,
                    description="Filter by vault space: notes, ops, or self.",
                    choices=("notes", "ops", "self"),
                ),
                ActionParam(
                    "since",
                    str,
                    required=False,
                    default=None,
                    description="Optional lower bound timestamp or date string.",
                ),
                ActionParam(
                    "include_archived",
                    bool,
                    required=False,
                    default=False,
                    description="Set true to include archived items.",
                    cli_flag=True,
                ),
                ActionParam(
                    "sort",
                    str,
                    required=False,
                    default="recency",
                    description="Sort mode: recency, title, type, or priority.",
                    choices=("recency", "title", "type", "priority"),
                ),
                ActionParam(
                    "limit",
                    int,
                    required=False,
                    default=20,
                    description="Maximum number of items to return.",
                ),
            ),
            handler=lambda vault, **kw: QueryController(vault).list_items(**kw),
            side_effect="read",
            mcp_when_to_use="Browsing and filtering the vault without keyword search.",
            mcp_avoid_when="You need ranked full-text results or a single exact document.",
            cli_group="query",
            cli_name="list",
        )
    )

    registry.register(
        ActionDefinition(
            name="work_queue",
            description="Return prioritized task list using scoring formula.",
            category="query",
            params=(
                ActionParam(
                    "space",
                    str,
                    required=False,
                    default=None,
                    description="Filter by vault space: notes, ops, or self.",
                    choices=("notes", "ops", "self"),
                ),
            ),
            handler=lambda vault, **kw: QueryController(vault).work_queue(**kw),
            side_effect="read",
            mcp_when_to_use="Finding the next task to work on from the scored queue.",
            mcp_avoid_when="You are looking for notes, references, or broad listings.",
            cli_group="query",
        )
    )

    registry.register(
        ActionDefinition(
            name="list_tags",
            description="List active tags with usage counts.",
            category="query",
            params=(
                ActionParam(
                    "prefix",
                    str,
                    required=False,
                    default=None,
                    description="Optional tag prefix to filter results (e.g. research/).",
                ),
                ActionParam(
                    "limit",
                    int,
                    required=False,
                    default=100,
                    description="Maximum number of tags to return.",
                ),
            ),
            handler=lambda vault, **kw: QueryController(vault).list_tags(**kw),
            side_effect="read",
            mcp_when_to_use="Before creating content, to reuse existing tag conventions.",
            mcp_avoid_when="You are searching for content rather than tag taxonomy.",
            cli_group="query",
            cli_name="tags",
        )
    )

    registry.register(
        ActionDefinition(
            name="decision_support",
            description="Aggregate notes, decisions, and references for a topic.",
            category="query",
            params=(
                ActionParam(
                    "topic",
                    str,
                    required=False,
                    default=None,
                    description="Topic to analyze.",
                ),
                ActionParam(
                    "space",
                    str,
                    required=False,
                    default=None,
                    description="Filter by vault space: notes, ops, or self.",
                    choices=("notes", "ops", "self"),
                ),
            ),
            handler=lambda vault, **kw: QueryController(vault).decision_support(**kw),
            side_effect="read",
            mcp_when_to_use="Preparing to make or document a decision with nearby vault evidence.",
            mcp_avoid_when="Simple search is enough or the topic has no existing vault content.",
            cli_group="query",
            cli_name="decision-support",
        )
    )

    registry.register(
        ActionDefinition(
            name="topic_packet",
            description="Build a topic packet for learning, review, or decision support.",
            category="query",
            params=(
                ActionParam(
                    "topic",
                    str,
                    required=True,
                    description="Topic name or query anchor for the packet.",
                    cli_is_argument=True,
                    mcp_example="python async patterns",
                ),
                ActionParam(
                    "mode",
                    str,
                    required=False,
                    default="learn",
                    description="Packet mode: learn, review, or decision.",
                    choices=("learn", "review", "decision"),
                ),
                ActionParam(
                    "budget",
                    int,
                    required=False,
                    default=4000,
                    description="Approximate token budget for assembled results.",
                ),
            ),
            handler=lambda vault, **kw: QueryController(vault).topic_packet(**kw),
            side_effect="read",
            mcp_when_to_use="You need a topic-focused retrieval bundle without an active session.",
            mcp_avoid_when="A single document lookup or plain search result list is sufficient.",
            cli_group="query",
            cli_name="packet",
        )
    )

    registry.register(
        ActionDefinition(
            name="draft_from_topic",
            description="Generate a draft note, task, or decision from a topic packet.",
            category="query",
            params=(
                ActionParam(
                    "topic",
                    str,
                    required=True,
                    description="Topic name or query anchor for the draft context.",
                    cli_is_argument=True,
                ),
                ActionParam(
                    "target",
                    str,
                    required=False,
                    default="note",
                    description="Draft target type: note, task, or decision.",
                    choices=("note", "task", "decision"),
                ),
                ActionParam(
                    "mode",
                    str,
                    required=False,
                    default="learn",
                    description="Packet mode used to gather evidence before drafting.",
                    choices=("learn", "review", "decision"),
                ),
                ActionParam(
                    "budget",
                    int,
                    required=False,
                    default=4000,
                    description="Approximate token budget for packet assembly before drafting.",
                ),
            ),
            handler=lambda vault, **kw: QueryController(vault).draft_from_topic(**kw),
            side_effect="read",
            mcp_when_to_use="You want a durable draft derived from topic evidence.",
            mcp_avoid_when="You only need the packet itself, not a draft artifact.",
            cli_group="query",
            cli_name="draft",
        )
    )

    registry.register(
        ActionDefinition(
            name="vault_review",
            description="Aggregate a review-ready snapshot of vault health and structure.",
            category="query",
            params=(
                ActionParam(
                    "top",
                    int,
                    required=False,
                    default=10,
                    description="Maximum items to include in each ranked section.",
                ),
                ActionParam(
                    "stale_days",
                    int,
                    required=False,
                    default=7,
                    description="Age threshold in days for stale-item reporting.",
                ),
            ),
            handler=lambda vault, **kw: QueryController(vault).vault_review(**kw),
            side_effect="read",
            mcp_when_to_use="Periodic maintenance, triage, and finding stale nodes.",
            mcp_avoid_when="You only need a focused document lookup.",
            cli_group="query",
            cli_name="review",
        )
    )
