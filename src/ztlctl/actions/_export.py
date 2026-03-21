"""Export ActionDefinition registrations."""

from __future__ import annotations

from typing import Any


def _register_export_actions() -> None:
    """Register export ActionDefinitions."""
    from ztlctl.actions.definitions import ActionDefinition, ActionParam
    from ztlctl.actions.registry import get_action_registry

    # Lazy controller imports
    from ztlctl.controllers.export import ExportController

    registry = get_action_registry()

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
