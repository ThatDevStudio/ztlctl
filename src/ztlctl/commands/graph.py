"""Command group: graph traversal and analysis."""

from __future__ import annotations

import click

from ztlctl.commands._base import ZtlGroup
from ztlctl.commands._context import AppContext
from ztlctl.services.graph import GraphService

_GRAPH_EXAMPLES = """\
  ztlctl graph related ztl_abc12345 --depth 3
  ztlctl graph themes
  ztlctl graph rank --top 10
  ztlctl graph path ztl_abc12345 ztl_def67890
  ztlctl graph gaps
  ztlctl graph bridges --top 5"""


@click.group(cls=ZtlGroup, examples=_GRAPH_EXAMPLES)
@click.pass_obj
def graph(app: AppContext) -> None:
    """Traverse and analyze the knowledge graph."""


@graph.command(
    examples="""\
  ztlctl graph related ztl_abc12345
  ztlctl graph related ztl_abc12345 --depth 3 --top 10
  ztlctl --json graph related TASK-0001"""
)
@click.argument("content_id")
@click.option("--depth", default=2, type=int, help="Maximum hops from source (1-5).")
@click.option("--top", default=20, type=int, help="Max results.")
@click.pass_obj
def related(app: AppContext, content_id: str, depth: int, top: int) -> None:
    """Find related content via spreading activation."""
    app.emit(GraphService(app.vault).related(content_id, depth=depth, top=top))


@graph.command(
    examples="""\
  ztlctl graph themes
  ztlctl --json graph themes"""
)
@click.pass_obj
def themes(app: AppContext) -> None:
    """Discover topic clusters via community detection."""
    app.emit(GraphService(app.vault).themes())


@graph.command(
    examples="""\
  ztlctl graph rank
  ztlctl graph rank --top 10
  ztlctl --json graph rank --top 5"""
)
@click.option("--top", default=20, type=int, help="Max results.")
@click.pass_obj
def rank(app: AppContext, top: int) -> None:
    """Identify important nodes via PageRank."""
    app.emit(GraphService(app.vault).rank(top=top))


@graph.command(
    examples="""\
  ztlctl graph path ztl_abc12345 ztl_def67890
  ztlctl --json graph path TASK-0001 ref_abc12345"""
)
@click.argument("source_id")
@click.argument("target_id")
@click.pass_obj
def path(app: AppContext, source_id: str, target_id: str) -> None:
    """Find shortest connection chain between two nodes."""
    app.emit(GraphService(app.vault).path(source_id, target_id))


@graph.command(
    examples="""\
  ztlctl graph gaps
  ztlctl graph gaps --top 10"""
)
@click.option("--top", default=20, type=int, help="Max results.")
@click.pass_obj
def gaps(app: AppContext, top: int) -> None:
    """Find structural holes in the graph."""
    app.emit(GraphService(app.vault).gaps(top=top))


@graph.command(
    examples="""\
  ztlctl graph bridges
  ztlctl graph bridges --top 5"""
)
@click.option("--top", default=20, type=int, help="Max results.")
@click.pass_obj
def bridges(app: AppContext, top: int) -> None:
    """Find bridge nodes via betweenness centrality."""
    app.emit(GraphService(app.vault).bridges(top=top))
