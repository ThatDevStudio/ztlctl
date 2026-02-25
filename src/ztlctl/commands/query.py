"""Command group: search, retrieval, and agent-oriented queries."""

from __future__ import annotations

import click

from ztlctl.commands._context import AppContext
from ztlctl.services.query import QueryService


@click.group()
@click.pass_obj
def query(app: AppContext) -> None:
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
    app: AppContext,
    query_text: str,
    content_type: str | None,
    tag: str | None,
    rank_by: str,
    limit: int,
) -> None:
    """Full-text search across vault content."""
    svc = QueryService(app.vault)
    result = svc.search(
        query_text,
        content_type=content_type,
        tag=tag,
        rank_by=rank_by,
        limit=limit,
    )
    app.emit(result)


@query.command()
@click.argument("content_id")
@click.pass_obj
def get(app: AppContext, content_id: str) -> None:
    """Retrieve a single content item by ID."""
    app.emit(QueryService(app.vault).get(content_id))


@query.command(name="list")
@click.option("--type", "content_type", default=None, help="Filter by content type.")
@click.option("--status", default=None, help="Filter by status.")
@click.option("--tag", default=None, help="Filter by tag.")
@click.option("--topic", default=None, help="Filter by topic.")
@click.option("--subtype", default=None, help="Filter by subtype (e.g. decision).")
@click.option(
    "--maturity",
    type=click.Choice(["seed", "budding", "evergreen"]),
    default=None,
    help="Filter by garden maturity.",
)
@click.option("--since", default=None, help="Modified on or after ISO date (YYYY-MM-DD).")
@click.option("--include-archived", is_flag=True, default=False, help="Include archived items.")
@click.option(
    "--sort",
    type=click.Choice(["recency", "title", "type", "priority"]),
    default="recency",
    help="Sort mode.",
)
@click.option("--limit", default=20, type=int, help="Max results.")
@click.pass_obj
def list_cmd(
    app: AppContext,
    content_type: str | None,
    status: str | None,
    tag: str | None,
    topic: str | None,
    subtype: str | None,
    maturity: str | None,
    since: str | None,
    include_archived: bool,
    sort: str,
    limit: int,
) -> None:
    """List content items with filters."""
    svc = QueryService(app.vault)
    result = svc.list_items(
        content_type=content_type,
        status=status,
        tag=tag,
        topic=topic,
        subtype=subtype,
        maturity=maturity,
        since=since,
        include_archived=include_archived,
        sort=sort,
        limit=limit,
    )
    app.emit(result)


@query.command(name="work-queue")
@click.pass_obj
def work_queue(app: AppContext) -> None:
    """Show prioritized task queue."""
    app.emit(QueryService(app.vault).work_queue())


@query.command(name="decision-support")
@click.option("--topic", default=None, help="Filter by topic.")
@click.pass_obj
def decision_support(app: AppContext, topic: str | None) -> None:
    """Aggregate context for decision-making."""
    app.emit(QueryService(app.vault).decision_support(topic=topic))
