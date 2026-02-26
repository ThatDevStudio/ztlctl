"""Command group: vault export (markdown, indexes, graph)."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import click

from ztlctl.commands._base import ZtlGroup

if TYPE_CHECKING:
    from ztlctl.commands._context import AppContext

_EXPORT_EXAMPLES = """\
  ztlctl export markdown --output /tmp/export
  ztlctl export indexes --output /tmp/indexes
  ztlctl export graph --format dot
  ztlctl export graph --format json --output graph.json"""


@click.group(cls=ZtlGroup, examples=_EXPORT_EXAMPLES)
@click.pass_obj
def export(app: AppContext) -> None:
    """Export vault content in various formats."""


@export.command(
    examples="""\
  ztlctl export markdown --output /tmp/export
  ztlctl export markdown --output ~/Desktop/vault-backup"""
)
@click.option(
    "--output",
    required=True,
    type=click.Path(),
    help="Output directory for exported markdown.",
)
@click.pass_obj
def markdown(app: AppContext, output: str) -> None:
    """Export all content files as portable markdown."""
    from ztlctl.services.export import ExportService

    app.emit(ExportService(app.vault).export_markdown(Path(output)))


@export.command(
    examples="""\
  ztlctl export indexes --output /tmp/indexes
  ztlctl export indexes --output ~/vault-indexes"""
)
@click.option(
    "--output",
    required=True,
    type=click.Path(),
    help="Output directory for generated index files.",
)
@click.pass_obj
def indexes(app: AppContext, output: str) -> None:
    """Generate index files grouped by type and topic."""
    from ztlctl.services.export import ExportService

    app.emit(ExportService(app.vault).export_indexes(Path(output)))


@export.command(
    examples="""\
  ztlctl export graph --format dot
  ztlctl export graph --format json --output graph.json
  ztlctl export graph --format dot | dot -Tpng -o graph.png"""
)
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["dot", "json"], case_sensitive=False),
    default="dot",
    help="Graph output format.",
)
@click.option(
    "--output",
    "output_file",
    type=click.Path(),
    default=None,
    help="Output file (omit to print to stdout).",
)
@click.pass_obj
def graph(app: AppContext, fmt: str, output_file: str | None) -> None:
    """Export the knowledge graph in DOT or JSON format."""
    from ztlctl.services.export import ExportService

    result = ExportService(app.vault).export_graph(fmt=fmt)

    if not result.ok:
        app.emit(result)
        return

    if output_file:
        Path(output_file).write_text(result.data["content"], encoding="utf-8")
        # Emit summary (without content) for the renderer
        from ztlctl.services.result import ServiceResult

        app.emit(
            ServiceResult(
                ok=True,
                op="export_graph",
                data={
                    "format": fmt,
                    "output_file": output_file,
                    "node_count": result.data["node_count"],
                    "edge_count": result.data["edge_count"],
                },
            )
        )
    else:
        # Pipe-friendly: raw content to stdout
        click.echo(result.data["content"], nl=False)
