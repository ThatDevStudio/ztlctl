"""Core ActionDefinition registrations for all built-in controller methods.

Called once at module load time from ``ztlctl.actions.__init__`` to populate
the singleton registry with all ~50 built-in ActionDefinitions.

Controller imports are lazy (inside the function body) to avoid circular imports
and expensive module-level imports at startup.
"""

from __future__ import annotations

from typing import Any


def _register_core_actions() -> None:
    """Register all built-in ActionDefinitions into the singleton registry."""
    from ztlctl.actions.definitions import ActionDefinition, ActionParam
    from ztlctl.actions.registry import get_action_registry

    # Lazy controller imports — avoid module-level cross-layer imports
    from ztlctl.controllers.check import CheckController
    from ztlctl.controllers.create import CreateController
    from ztlctl.controllers.discovery import DiscoveryController
    from ztlctl.controllers.docs import DocsController
    from ztlctl.controllers.export import ExportController
    from ztlctl.controllers.graph import GraphController
    from ztlctl.controllers.ingest import IngestController
    from ztlctl.controllers.init_ctrl import InitController
    from ztlctl.controllers.query import QueryController
    from ztlctl.controllers.reweave import ReweaveController
    from ztlctl.controllers.session import SessionController
    from ztlctl.controllers.update import UpdateController
    from ztlctl.controllers.upgrade import UpgradeController
    from ztlctl.controllers.vector import VectorController
    from ztlctl.controllers.workflow import WorkflowController

    registry = get_action_registry()

    # -----------------------------------------------------------------------
    # creation category
    # -----------------------------------------------------------------------

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

    # -----------------------------------------------------------------------
    # query category
    # -----------------------------------------------------------------------

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

    # -----------------------------------------------------------------------
    # graph category
    # -----------------------------------------------------------------------

    registry.register(
        ActionDefinition(
            name="related",
            description="Find related content via spreading activation (BFS with decay).",
            category="graph",
            params=(
                ActionParam(
                    "content_id",
                    str,
                    required=True,
                    description="Starting vault ID for traversal.",
                    cli_is_argument=True,
                    mcp_example="NOTE-0001",
                ),
                ActionParam(
                    "depth",
                    int,
                    required=False,
                    default=2,
                    description="Traversal depth; higher values broaden the neighborhood.",
                ),
                ActionParam(
                    "top",
                    int,
                    required=False,
                    default=20,
                    description="Maximum related items to return.",
                ),
            ),
            handler=lambda vault, **kw: GraphController(vault).related(**kw),
            side_effect="read",
            mcp_when_to_use="Exploring neighbors and graph context from a known starting item.",
            mcp_avoid_when="You need keyword search rather than graph traversal.",
            mcp_common_errors=("NOT_FOUND",),
            cli_group="graph",
        )
    )

    registry.register(
        ActionDefinition(
            name="themes",
            description="Discover topic clusters via community detection.",
            category="graph",
            params=(),
            handler=lambda vault, **kw: GraphController(vault).themes(**kw),
            side_effect="read",
            mcp_when_to_use="Discovering topic clusters in a sufficiently connected vault.",
            mcp_avoid_when="The graph is still sparse or newly created.",
            cli_group="graph",
        )
    )

    registry.register(
        ActionDefinition(
            name="rank",
            description="Identify important nodes via PageRank.",
            category="graph",
            params=(
                ActionParam(
                    "top",
                    int,
                    required=False,
                    default=20,
                    description="Maximum number of ranked items to return.",
                ),
            ),
            handler=lambda vault, **kw: GraphController(vault).rank(**kw),
            side_effect="read",
            mcp_when_to_use="Finding the most central nodes in the knowledge graph.",
            mcp_avoid_when="The vault has few items or very few edges.",
            cli_group="graph",
        )
    )

    registry.register(
        ActionDefinition(
            name="path",
            description="Find shortest connection chain between two nodes.",
            category="graph",
            params=(
                ActionParam(
                    "source_id",
                    str,
                    required=True,
                    description="Starting item ID.",
                    cli_is_argument=True,
                    mcp_example="NOTE-0001",
                ),
                ActionParam(
                    "target_id",
                    str,
                    required=True,
                    description="Ending item ID.",
                    cli_is_argument=True,
                    mcp_example="NOTE-0042",
                ),
            ),
            handler=lambda vault, **kw: GraphController(vault).path(**kw),
            side_effect="read",
            mcp_when_to_use="Tracing how two specific items are connected.",
            mcp_avoid_when="You do not yet know both target IDs.",
            mcp_common_errors=("NOT_FOUND", "NO_PATH"),
            cli_group="graph",
        )
    )

    registry.register(
        ActionDefinition(
            name="gaps",
            description="Find structural holes — nodes with high constraint.",
            category="graph",
            params=(
                ActionParam(
                    "top",
                    int,
                    required=False,
                    default=20,
                    description="Maximum number of gap candidates to return.",
                ),
            ),
            handler=lambda vault, **kw: GraphController(vault).gaps(**kw),
            side_effect="read",
            mcp_when_to_use="Looking for disconnected or weakly connected areas that need linking.",
            mcp_avoid_when="The vault is small enough that graph gaps are not yet meaningful.",
            cli_group="graph",
        )
    )

    registry.register(
        ActionDefinition(
            name="bridges",
            description="Find bridge nodes via betweenness centrality.",
            category="graph",
            params=(
                ActionParam(
                    "top",
                    int,
                    required=False,
                    default=20,
                    description="Maximum number of bridge candidates to return.",
                ),
            ),
            handler=lambda vault, **kw: GraphController(vault).bridges(**kw),
            side_effect="read",
            mcp_when_to_use="Identifying items that connect otherwise separate knowledge clusters.",
            mcp_avoid_when="The graph is too small to produce meaningful bridge nodes.",
            cli_group="graph",
        )
    )

    registry.register(
        ActionDefinition(
            name="unlink",
            description="Remove links from source_id to target_id.",
            category="graph",
            params=(
                ActionParam(
                    "source_id",
                    str,
                    required=True,
                    description="Source item ID to remove links from.",
                    cli_is_argument=True,
                ),
                ActionParam(
                    "target_id",
                    str,
                    required=True,
                    description="Target item ID to unlink.",
                    cli_is_argument=True,
                ),
                ActionParam(
                    "both",
                    bool,
                    required=False,
                    default=False,
                    description="Remove links in both directions.",
                    cli_flag=True,
                ),
            ),
            handler=lambda vault, **kw: GraphController(vault).unlink(**kw),
            side_effect="write",
            mcp_when_to_use="Removing an incorrect or stale link between two items.",
            mcp_avoid_when="You want to delete an item entirely; use archive instead.",
            mcp_common_errors=("NOT_FOUND",),
            cli_group="graph",
        )
    )

    registry.register(
        ActionDefinition(
            name="materialize_metrics",
            description="Compute and store graph metrics in the nodes table.",
            category="graph",
            params=(),
            handler=lambda vault, **kw: GraphController(vault).materialize_metrics(**kw),
            side_effect="write",
            mcp_when_to_use="After bulk imports or vault changes to refresh graph metrics.",
            mcp_avoid_when="Metrics were already computed recently.",
            cli_group="graph",
            cli_name="materialize",
        )
    )

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

    # -----------------------------------------------------------------------
    # session category
    # -----------------------------------------------------------------------

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

    # -----------------------------------------------------------------------
    # ingest category
    # -----------------------------------------------------------------------

    registry.register(
        ActionDefinition(
            name="list_providers",
            description="List registered source providers.",
            category="ingest",
            params=(),
            handler=lambda vault, **kw: IngestController(vault).list_providers(**kw),
            side_effect="read",
            mcp_when_to_use="Before ingesting URLs or when diagnosing missing provider support.",
            mcp_avoid_when="You already know the provider you need and are ingesting text.",
            cli_group="ingest",
            cli_name="providers",
        )
    )

    registry.register(
        ActionDefinition(
            name="ingest_text",
            description="Ingest raw text into a note or reference.",
            category="ingest",
            params=(
                ActionParam(
                    "title",
                    str,
                    required=True,
                    description="Title for the ingested artifact.",
                    cli_is_argument=True,
                ),
                ActionParam(
                    "body_text",
                    str,
                    required=True,
                    description="Raw text content to ingest.",
                ),
                ActionParam(
                    "target_type",
                    str,
                    required=False,
                    default=None,
                    description="Destination artifact type: reference or note.",
                    choices=("reference", "note"),
                ),
                ActionParam(
                    "topic",
                    str,
                    required=False,
                    default=None,
                    description="Optional topic directory under notes/.",
                ),
                ActionParam(
                    "tags",
                    list,
                    required=False,
                    default=None,
                    description="Optional tags applied to the created artifact.",
                    cli_multiple=True,
                ),
                ActionParam(
                    "summary",
                    str,
                    required=False,
                    default=None,
                    description="Optional capture summary hint.",
                ),
                ActionParam(
                    "dry_run",
                    bool,
                    required=False,
                    default=False,
                    description="Preview normalized capture without writing files.",
                    cli_flag=True,
                ),
            ),
            handler=lambda vault, **kw: IngestController(vault).ingest_text(**kw),
            side_effect="write",
            mcp_when_to_use="Capturing external text or source material with provenance.",
            mcp_avoid_when="You are authoring a note or reference without source normalization.",
            mcp_common_errors=("VALIDATION_FAILED", "UNKNOWN_TYPE"),
            cli_group="ingest",
            cli_name="text",
        )
    )

    registry.register(
        ActionDefinition(
            name="ingest_file",
            description="Ingest a plain text or markdown file.",
            category="ingest",
            params=(
                ActionParam(
                    "path",
                    str,
                    required=True,
                    description="Filesystem path to the file to ingest.",
                    cli_is_argument=True,
                ),
                ActionParam(
                    "title",
                    str,
                    required=False,
                    default=None,
                    description="Optional title override for the ingested artifact.",
                ),
                ActionParam(
                    "target_type",
                    str,
                    required=False,
                    default=None,
                    description="Destination artifact type: reference or note.",
                    choices=("reference", "note"),
                ),
                ActionParam(
                    "topic",
                    str,
                    required=False,
                    default=None,
                    description="Optional topic directory under notes/.",
                ),
                ActionParam(
                    "tags",
                    list,
                    required=False,
                    default=None,
                    description="Optional tags applied to the created artifact.",
                    cli_multiple=True,
                ),
                ActionParam(
                    "summary",
                    str,
                    required=False,
                    default=None,
                    description="Optional capture summary hint.",
                ),
                ActionParam(
                    "dry_run",
                    bool,
                    required=False,
                    default=False,
                    description="Preview normalized capture without writing files.",
                    cli_flag=True,
                ),
            ),
            handler=lambda vault, **kw: IngestController(vault).ingest_file(**kw),
            side_effect="write",
            mcp_when_to_use="Ingesting a local file into the vault.",
            mcp_avoid_when="You are ingesting a URL or raw text string.",
            mcp_common_errors=("NOT_FOUND", "VALIDATION_FAILED", "UNKNOWN_TYPE"),
            cli_group="ingest",
            cli_name="file",
        )
    )

    registry.register(
        ActionDefinition(
            name="ingest_url",
            description="Ingest a URL through a registered source provider.",
            category="ingest",
            params=(
                ActionParam(
                    "url",
                    str,
                    required=True,
                    description="URL to ingest via a registered provider.",
                    cli_is_argument=True,
                ),
                ActionParam(
                    "provider",
                    str,
                    required=False,
                    default=None,
                    description="Optional provider name for URL ingestion.",
                ),
                ActionParam(
                    "title",
                    str,
                    required=False,
                    default=None,
                    description="Optional title override for the ingested artifact.",
                ),
                ActionParam(
                    "target_type",
                    str,
                    required=False,
                    default=None,
                    description="Destination artifact type: reference or note.",
                    choices=("reference", "note"),
                ),
                ActionParam(
                    "topic",
                    str,
                    required=False,
                    default=None,
                    description="Optional topic directory under notes/.",
                ),
                ActionParam(
                    "tags",
                    list,
                    required=False,
                    default=None,
                    description="Optional tags applied to the created artifact.",
                    cli_multiple=True,
                ),
                ActionParam(
                    "summary",
                    str,
                    required=False,
                    default=None,
                    description="Optional capture summary hint.",
                ),
                ActionParam(
                    "dry_run",
                    bool,
                    required=False,
                    default=False,
                    description="Preview normalized capture without writing files.",
                    cli_flag=True,
                ),
            ),
            handler=lambda vault, **kw: IngestController(vault).ingest_url(**kw),
            side_effect="write",
            mcp_when_to_use="Ingesting a web URL via a registered source provider.",
            mcp_avoid_when="You are ingesting raw text or a local file.",
            mcp_common_errors=("VALIDATION_FAILED", "NO_PROVIDER", "UNKNOWN_TYPE"),
            cli_group="ingest",
            cli_name="url",
        )
    )

    # -----------------------------------------------------------------------
    # export category
    # -----------------------------------------------------------------------

    def _make_export_filters(
        content_type: str | None = None,
        **_kw: object,
    ) -> Any:
        from ztlctl.services.export import ExportFilters

        if content_type is None:
            return None
        return ExportFilters(content_type=content_type)

    registry.register(
        ActionDefinition(
            name="export_markdown",
            description="Copy all content files to output_dir, preserving relative paths.",
            category="export",
            params=(
                ActionParam(
                    "output_dir",
                    str,
                    required=True,
                    description="Destination directory for exported markdown files.",
                    cli_is_argument=True,
                ),
                ActionParam(
                    "content_type",
                    str,
                    required=False,
                    default=None,
                    description="Filter by content type (note, reference, task).",
                    cli_name="type",
                ),
            ),
            handler=lambda vault, **kw: ExportController(vault).export_markdown(
                kw["output_dir"],
                filters=_make_export_filters(**kw),
            ),
            side_effect="read",
            mcp_when_to_use="Exporting vault content as plain markdown files.",
            mcp_avoid_when="You need a graph export or structured index.",
            cli_group="export",
            cli_name="markdown",
        )
    )

    registry.register(
        ActionDefinition(
            name="export_indexes",
            description="Generate index files grouped by type and topic.",
            category="export",
            params=(
                ActionParam(
                    "output_dir",
                    str,
                    required=True,
                    description="Destination directory for exported index files.",
                    cli_is_argument=True,
                ),
                ActionParam(
                    "content_type",
                    str,
                    required=False,
                    default=None,
                    description="Filter by content type (note, reference, task).",
                    cli_name="type",
                ),
            ),
            handler=lambda vault, **kw: ExportController(vault).export_indexes(
                kw["output_dir"],
                filters=_make_export_filters(**kw),
            ),
            side_effect="read",
            mcp_when_to_use="Generating navigational index files grouped by type and topic.",
            mcp_avoid_when="You need raw markdown files or a graph export.",
            cli_group="export",
            cli_name="indexes",
        )
    )

    registry.register(
        ActionDefinition(
            name="export_graph",
            description="Export the vault's knowledge graph (dot or json format).",
            category="export",
            params=(
                ActionParam(
                    "fmt",
                    str,
                    required=False,
                    default="dot",
                    description="Export format: dot or json.",
                    choices=("dot", "json"),
                    cli_name="format",
                ),
                ActionParam(
                    "output_file",
                    str,
                    required=False,
                    default=None,
                    description="Output file path (default: stdout).",
                    cli_name="output",
                ),
                ActionParam(
                    "content_type",
                    str,
                    required=False,
                    default=None,
                    description="Filter by content type (note, reference, task).",
                    cli_name="type",
                ),
            ),
            handler=lambda vault, **kw: ExportController(vault).export_graph(
                fmt=kw.get("fmt", "dot"),
                output_file=kw.get("output_file"),
                filters=_make_export_filters(**kw),
            ),
            side_effect="read",
            mcp_when_to_use="Exporting the knowledge graph for visualization or external analysis.",
            mcp_avoid_when="You need markdown content files rather than the graph structure.",
            cli_group="export",
            cli_name="graph",
        )
    )

    registry.register(
        ActionDefinition(
            name="export_dashboard",
            description="Export an external review dashboard and JSON review indexes.",
            category="export",
            params=(
                ActionParam(
                    "output_dir",
                    str,
                    required=True,
                    description="Destination directory for the dashboard artifacts.",
                    cli_is_argument=True,
                ),
                ActionParam(
                    "viewer",
                    str,
                    required=False,
                    default="obsidian",
                    # Note: no choices — service layer normalizes "vanilla" alias.
                    description="Client viewer: obsidian, none (or legacy alias vanilla).",
                ),
            ),
            handler=lambda vault, **kw: ExportController(vault).export_dashboard(
                kw["output_dir"],
                viewer=kw.get("viewer", "obsidian"),
            ),
            side_effect="read",
            mcp_when_to_use="Generating a review workbench for use in an external tool.",
            mcp_avoid_when="You only need a graph or raw markdown export.",
            cli_group="export",
            cli_name="dashboard",
        )
    )

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
