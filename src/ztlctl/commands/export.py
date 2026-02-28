"""Command group: vault export (markdown, indexes, graph)."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING

import click

from ztlctl.commands._base import ZtlGroup
from ztlctl.services.export import ArchivedMode, ExportFilters

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


def _export_filter_options[**P, R](func: Callable[P, R]) -> Callable[P, R]:
    """Apply shared export filter flags to a subcommand."""
    func = click.option(
        "--archived",
        type=click.Choice(["include", "exclude", "only"], case_sensitive=False),
        default=None,
        help="Archived item handling.",
    )(func)
    func = click.option(
        "--since",
        default=None,
        help="Modified on or after ISO date (YYYY-MM-DD).",
    )(func)
    func = click.option("--topic", default=None, help="Filter by topic.")(func)
    func = click.option("--tag", default=None, help="Filter by tag.")(func)
    func = click.option("--status", default=None, help="Filter by status.")(func)
    func = click.option("--type", "content_type", default=None, help="Filter by content type.")(
        func
    )
    return func


def _build_export_filters(
    *,
    content_type: str | None,
    status: str | None,
    tag: str | None,
    topic: str | None,
    since: str | None,
    archived: ArchivedMode | None,
) -> ExportFilters | None:
    """Build an ExportFilters instance when any export filter is supplied."""

    if all(value is None for value in (content_type, status, tag, topic, since, archived)):
        return None
    return ExportFilters(
        content_type=content_type,
        status=status,
        tag=tag,
        topic=topic,
        since=since,
        archived=archived,
    )


@export.command(
    examples="""\
  ztlctl export markdown --output /tmp/export
  ztlctl export markdown --output ~/Desktop/vault-backup"""
)
@_export_filter_options
@click.option(
    "--output",
    required=True,
    type=click.Path(),
    help="Output directory for exported markdown.",
)
@click.pass_obj
def markdown(
    app: AppContext,
    content_type: str | None,
    status: str | None,
    tag: str | None,
    topic: str | None,
    since: str | None,
    archived: ArchivedMode | None,
    output: str,
) -> None:
    """Export all content files as portable markdown."""
    from ztlctl.services.export import ExportService

    filters = _build_export_filters(
        content_type=content_type,
        status=status,
        tag=tag,
        topic=topic,
        since=since,
        archived=archived,
    )
    app.emit(ExportService(app.vault).export_markdown(Path(output), filters=filters))


@export.command(
    examples="""\
  ztlctl export indexes --output /tmp/indexes
  ztlctl export indexes --output ~/vault-indexes"""
)
@_export_filter_options
@click.option(
    "--output",
    required=True,
    type=click.Path(),
    help="Output directory for generated index files.",
)
@click.pass_obj
def indexes(
    app: AppContext,
    content_type: str | None,
    status: str | None,
    tag: str | None,
    topic: str | None,
    since: str | None,
    archived: ArchivedMode | None,
    output: str,
) -> None:
    """Generate index files grouped by type and topic."""
    from ztlctl.services.export import ExportService

    filters = _build_export_filters(
        content_type=content_type,
        status=status,
        tag=tag,
        topic=topic,
        since=since,
        archived=archived,
    )
    app.emit(ExportService(app.vault).export_indexes(Path(output), filters=filters))


@export.command(
    examples="""\
  ztlctl export graph --format dot
  ztlctl export graph --format json --output graph.json
  ztlctl export graph --format dot | dot -Tpng -o graph.png"""
)
@_export_filter_options
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
def graph(
    app: AppContext,
    content_type: str | None,
    status: str | None,
    tag: str | None,
    topic: str | None,
    since: str | None,
    archived: ArchivedMode | None,
    fmt: str,
    output_file: str | None,
) -> None:
    """Export the knowledge graph in DOT or JSON format."""
    from ztlctl.services.export import ExportService

    filters = _build_export_filters(
        content_type=content_type,
        status=status,
        tag=tag,
        topic=topic,
        since=since,
        archived=archived,
    )
    result = ExportService(app.vault).export_graph(fmt=fmt, filters=filters)

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
                    **({"filters": result.data["filters"]} if "filters" in result.data else {}),
                },
            )
        )
    else:
        # Pipe-friendly: raw content to stdout
        click.echo(result.data["content"], nl=False)
