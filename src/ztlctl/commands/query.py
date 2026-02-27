"""Command group: search, retrieval, and agent-oriented queries."""

from __future__ import annotations

from typing import TYPE_CHECKING

import click

from ztlctl.commands._base import ZtlGroup
from ztlctl.services.query import QueryService

if TYPE_CHECKING:
    from ztlctl.commands._context import AppContext

_QUERY_EXAMPLES = """\
  ztlctl query search "python design patterns"
  ztlctl query search "auth" --space notes
  ztlctl query get ztl_abc12345
  ztlctl query list --type note --sort recency
  ztlctl query list --space ops --sort priority --limit 10
  ztlctl query work-queue --space ops
  ztlctl query decision-support --topic architecture"""


@click.group(cls=ZtlGroup, examples=_QUERY_EXAMPLES)
@click.pass_obj
def query(app: AppContext) -> None:
    """Search, list, and query vault content."""


@query.command(
    examples="""\
  ztlctl query search "python"
  ztlctl query search "design patterns" --type note
  ztlctl query search "auth" --tag security/web --rank-by recency
  ztlctl query search "auth" --space notes
  ztlctl --json query search "API" --limit 5"""
)
@click.argument("query_text")
@click.option("--type", "content_type", default=None, help="Filter by content type.")
@click.option("--tag", default=None, help="Filter by tag.")
@click.option(
    "--space",
    type=click.Choice(["notes", "ops", "self"]),
    default=None,
    help="Filter by vault space.",
)
@click.option(
    "--rank-by",
    type=click.Choice(["relevance", "recency", "graph", "semantic", "hybrid"]),
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
    space: str | None,
    rank_by: str,
    limit: int,
) -> None:
    """Full-text search across vault content."""
    svc = QueryService(app.vault)
    result = svc.search(
        query_text,
        content_type=content_type,
        tag=tag,
        space=space,
        rank_by=rank_by,
        limit=limit,
    )
    app.emit(result)


@query.command(
    examples="""\
  ztlctl query get ztl_abc12345
  ztlctl --json query get TASK-0001"""
)
@click.argument("content_id")
@click.pass_obj
def get(app: AppContext, content_id: str) -> None:
    """Retrieve a single content item by ID."""
    app.emit(QueryService(app.vault).get(content_id))


@query.command(
    name="list",
    examples="""\
  ztlctl query list
  ztlctl query list --type note --status linked
  ztlctl query list --tag ai/ml --sort title
  ztlctl query list --subtype decision --topic architecture
  ztlctl query list --maturity seed
  ztlctl query list --space notes
  ztlctl query list --since 2026-01-01 --include-archived
  ztlctl query list --sort priority --limit 10""",
)
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
@click.option(
    "--space",
    type=click.Choice(["notes", "ops", "self"]),
    default=None,
    help="Filter by vault space.",
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
    space: str | None,
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
        space=space,
        since=since,
        include_archived=include_archived,
        sort=sort,
        limit=limit,
    )
    app.emit(result)


@query.command(
    name="work-queue",
    examples="""\
  ztlctl query work-queue
  ztlctl query work-queue --space ops
  ztlctl --json query work-queue""",
)
@click.option(
    "--space",
    type=click.Choice(["notes", "ops", "self"]),
    default=None,
    help="Filter by vault space.",
)
@click.pass_obj
def work_queue(app: AppContext, space: str | None) -> None:
    """Show prioritized task queue."""
    app.emit(QueryService(app.vault).work_queue(space=space))


@query.command(
    name="decision-support",
    examples="""\
  ztlctl query decision-support
  ztlctl query decision-support --topic architecture
  ztlctl query decision-support --space notes
  ztlctl --json query decision-support --topic security""",
)
@click.option("--topic", default=None, help="Filter by topic.")
@click.option(
    "--space",
    type=click.Choice(["notes", "ops", "self"]),
    default=None,
    help="Filter by vault space.",
)
@click.pass_obj
def decision_support(app: AppContext, topic: str | None, space: str | None) -> None:
    """Aggregate context for decision-making."""
    app.emit(QueryService(app.vault).decision_support(topic=topic, space=space))
