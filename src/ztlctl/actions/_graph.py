"""Graph ActionDefinition registrations."""

from __future__ import annotations

from typing import Any


def _register_graph_actions() -> None:
    """Register graph ActionDefinitions."""
    from ztlctl.actions.definitions import ActionDefinition, ActionParam
    from ztlctl.actions.registry import get_action_registry

    # Lazy controller imports
    from ztlctl.controllers.graph import GraphController

    registry = get_action_registry()

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
