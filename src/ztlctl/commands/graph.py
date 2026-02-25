"""Command group: graph traversal and analysis."""

from __future__ import annotations

import click

from ztlctl.config.settings import ZtlSettings
from ztlctl.infrastructure.vault import Vault
from ztlctl.output.formatters import format_result
from ztlctl.services.graph import GraphService


@click.group()
@click.pass_obj
def graph(ctx: ZtlSettings) -> None:
    """Traverse and analyze the knowledge graph."""


@graph.command()
@click.argument("content_id")
@click.option("--depth", default=2, type=int, help="Maximum hops from source (1-5).")
@click.option("--top", default=20, type=int, help="Max results.")
@click.pass_obj
def related(settings: ZtlSettings, content_id: str, depth: int, top: int) -> None:
    """Find related content via spreading activation."""
    vault = Vault(settings)
    svc = GraphService(vault)
    result = svc.related(content_id, depth=depth, top=top)
    click.echo(format_result(result, json_output=settings.json_output))


@graph.command()
@click.pass_obj
def themes(settings: ZtlSettings) -> None:
    """Discover topic clusters via community detection."""
    vault = Vault(settings)
    svc = GraphService(vault)
    result = svc.themes()
    click.echo(format_result(result, json_output=settings.json_output))


@graph.command()
@click.option("--top", default=20, type=int, help="Max results.")
@click.pass_obj
def rank(settings: ZtlSettings, top: int) -> None:
    """Identify important nodes via PageRank."""
    vault = Vault(settings)
    svc = GraphService(vault)
    result = svc.rank(top=top)
    click.echo(format_result(result, json_output=settings.json_output))


@graph.command()
@click.argument("source_id")
@click.argument("target_id")
@click.pass_obj
def path(settings: ZtlSettings, source_id: str, target_id: str) -> None:
    """Find shortest connection chain between two nodes."""
    vault = Vault(settings)
    svc = GraphService(vault)
    result = svc.path(source_id, target_id)
    click.echo(format_result(result, json_output=settings.json_output))


@graph.command()
@click.option("--top", default=20, type=int, help="Max results.")
@click.pass_obj
def gaps(settings: ZtlSettings, top: int) -> None:
    """Find structural holes in the graph."""
    vault = Vault(settings)
    svc = GraphService(vault)
    result = svc.gaps(top=top)
    click.echo(format_result(result, json_output=settings.json_output))


@graph.command()
@click.option("--top", default=20, type=int, help="Max results.")
@click.pass_obj
def bridges(settings: ZtlSettings, top: int) -> None:
    """Find bridge nodes via betweenness centrality."""
    vault = Vault(settings)
    svc = GraphService(vault)
    result = svc.bridges(top=top)
    click.echo(format_result(result, json_output=settings.json_output))
