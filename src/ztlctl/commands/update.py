"""Command: update content metadata and body."""

from __future__ import annotations

from typing import TYPE_CHECKING

import click

if TYPE_CHECKING:
    from ztlctl.commands._context import AppContext


@click.command()
@click.argument("content_id")
@click.option("--title", default=None, help="New title.")
@click.option("--status", default=None, help="New status (must be valid transition).")
@click.option("--tags", multiple=True, help="Replace tags (repeatable).")
@click.option("--topic", default=None, help="New topic subdirectory.")
@click.option("--body", default=None, help="New body text.")
@click.option(
    "--maturity",
    type=click.Choice(["seed", "budding", "evergreen"]),
    default=None,
    help="Set garden maturity level.",
)
@click.pass_obj
def update(
    app: AppContext,
    content_id: str,
    title: str | None,
    status: str | None,
    tags: tuple[str, ...],
    topic: str | None,
    body: str | None,
    maturity: str | None,
) -> None:
    """Update a content item's metadata or body."""
    from ztlctl.services.update import UpdateService

    changes: dict[str, object] = {}
    if title is not None:
        changes["title"] = title
    if status is not None:
        changes["status"] = status
    if tags:
        changes["tags"] = list(tags)
    if topic is not None:
        changes["topic"] = topic
    if body is not None:
        changes["body"] = body
    if maturity is not None:
        changes["maturity"] = maturity

    if not changes:
        click.echo("No changes specified. Use --help for options.", err=True)
        raise SystemExit(1)

    app.emit(UpdateService(app.vault).update(content_id, changes=changes))
