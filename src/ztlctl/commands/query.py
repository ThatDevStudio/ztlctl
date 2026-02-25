"""Command group: search, retrieval, and agent-oriented queries."""

from __future__ import annotations

import click

from ztlctl.config.settings import ZtlSettings
from ztlctl.infrastructure.vault import Vault
from ztlctl.output.formatters import format_result
from ztlctl.services.query import QueryService


@click.group()
@click.pass_obj
def query(ctx: ZtlSettings) -> None:
    """Search, list, and query vault content."""


@query.command()
@click.argument("query_text")
@click.option("--type", "content_type", default=None, help="Filter by content type.")
@click.option("--tag", default=None, help="Filter by tag.")
@click.option(
    "--rank-by",
    type=click.Choice(["relevance", "recency"]),
    default="relevance",
    help="Ranking mode.",
)
@click.option("--limit", default=20, type=int, help="Max results.")
@click.pass_obj
def search(
    settings: ZtlSettings,
    query_text: str,
    content_type: str | None,
    tag: str | None,
    rank_by: str,
    limit: int,
) -> None:
    """Full-text search across vault content."""
    vault = Vault(settings)
    svc = QueryService(vault)
    result = svc.search(
        query_text,
        content_type=content_type,
        tag=tag,
        rank_by=rank_by,
        limit=limit,
    )
    click.echo(format_result(result, json_output=settings.json_output))


@query.command()
@click.argument("content_id")
@click.pass_obj
def get(settings: ZtlSettings, content_id: str) -> None:
    """Retrieve a single content item by ID."""
    vault = Vault(settings)
    svc = QueryService(vault)
    result = svc.get(content_id)
    click.echo(format_result(result, json_output=settings.json_output))


@query.command(name="list")
@click.option("--type", "content_type", default=None, help="Filter by content type.")
@click.option("--status", default=None, help="Filter by status.")
@click.option("--tag", default=None, help="Filter by tag.")
@click.option("--topic", default=None, help="Filter by topic.")
@click.option(
    "--sort",
    type=click.Choice(["recency", "title", "type"]),
    default="recency",
    help="Sort mode.",
)
@click.option("--limit", default=20, type=int, help="Max results.")
@click.pass_obj
def list_cmd(
    settings: ZtlSettings,
    content_type: str | None,
    status: str | None,
    tag: str | None,
    topic: str | None,
    sort: str,
    limit: int,
) -> None:
    """List content items with filters."""
    vault = Vault(settings)
    svc = QueryService(vault)
    result = svc.list_items(
        content_type=content_type,
        status=status,
        tag=tag,
        topic=topic,
        sort=sort,
        limit=limit,
    )
    click.echo(format_result(result, json_output=settings.json_output))


@query.command(name="work-queue")
@click.pass_obj
def work_queue(settings: ZtlSettings) -> None:
    """Show prioritized task queue."""
    vault = Vault(settings)
    svc = QueryService(vault)
    result = svc.work_queue()
    click.echo(format_result(result, json_output=settings.json_output))


@query.command(name="decision-support")
@click.option("--topic", default=None, help="Filter by topic.")
@click.pass_obj
def decision_support(settings: ZtlSettings, topic: str | None) -> None:
    """Aggregate context for decision-making."""
    vault = Vault(settings)
    svc = QueryService(vault)
    result = svc.decision_support(topic=topic)
    click.echo(format_result(result, json_output=settings.json_output))
