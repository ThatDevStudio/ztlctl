"""Command group: content creation (note, reference, task, batch)."""

from __future__ import annotations

import json

import click

from ztlctl.commands._context import AppContext
from ztlctl.services.create import CreateService


@click.group()
@click.pass_obj
def create(app: AppContext) -> None:
    """Create notes, references, and tasks."""


@create.command()
@click.argument("title")
@click.option("--subtype", type=click.Choice(["knowledge", "decision"]), help="Note subtype.")
@click.option("--tags", multiple=True, help="Tags (repeatable, e.g. --tags domain/scope).")
@click.option("--topic", default=None, help="Topic subdirectory.")
@click.option("--session", default=None, help="Session ID (LOG-NNNN).")
@click.pass_obj
def note(
    app: AppContext,
    title: str,
    subtype: str | None,
    tags: tuple[str, ...],
    topic: str | None,
    session: str | None,
) -> None:
    """Create a new note."""
    svc = CreateService(app.vault)
    result = svc.create_note(
        title,
        subtype=subtype,
        tags=list(tags) if tags else None,
        topic=topic,
        session=session,
    )
    app.emit(result)


@create.command()
@click.argument("title")
@click.option("--url", default=None, help="Source URL.")
@click.option(
    "--subtype", type=click.Choice(["article", "tool", "spec"]), help="Reference subtype."
)
@click.option("--tags", multiple=True, help="Tags (repeatable).")
@click.option("--topic", default=None, help="Topic subdirectory.")
@click.option("--session", default=None, help="Session ID (LOG-NNNN).")
@click.pass_obj
def reference(
    app: AppContext,
    title: str,
    url: str | None,
    subtype: str | None,
    tags: tuple[str, ...],
    topic: str | None,
    session: str | None,
) -> None:
    """Create a new reference."""
    svc = CreateService(app.vault)
    result = svc.create_reference(
        title,
        url=url,
        subtype=subtype,
        tags=list(tags) if tags else None,
        topic=topic,
        session=session,
    )
    app.emit(result)


@create.command()
@click.argument("title")
@click.option(
    "--priority",
    type=click.Choice(["low", "medium", "high", "critical"]),
    default="medium",
    help="Priority level.",
)
@click.option(
    "--impact",
    type=click.Choice(["low", "medium", "high"]),
    default="medium",
    help="Impact level.",
)
@click.option(
    "--effort",
    type=click.Choice(["low", "medium", "high"]),
    default="medium",
    help="Effort level.",
)
@click.option("--tags", multiple=True, help="Tags (repeatable).")
@click.option("--session", default=None, help="Session ID (LOG-NNNN).")
@click.pass_obj
def task(
    app: AppContext,
    title: str,
    priority: str,
    impact: str,
    effort: str,
    tags: tuple[str, ...],
    session: str | None,
) -> None:
    """Create a new task."""
    svc = CreateService(app.vault)
    result = svc.create_task(
        title,
        priority=priority,
        impact=impact,
        effort=effort,
        tags=list(tags) if tags else None,
        session=session,
    )
    app.emit(result)


@create.command()
@click.argument("file", type=click.Path(exists=True))
@click.option("--partial", is_flag=True, help="Continue on errors (partial mode).")
@click.pass_obj
def batch(app: AppContext, file: str, partial: bool) -> None:
    """Create multiple items from a JSON file.

    FILE must contain a JSON array of objects, each with at least
    "type" and "title" keys.
    """
    try:
        with open(file, encoding="utf-8") as f:
            items = json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        click.echo(f"Error reading {file}: {exc}", err=True)
        raise SystemExit(1) from exc

    if not isinstance(items, list):
        click.echo("JSON file must contain a top-level array.", err=True)
        raise SystemExit(1)

    svc = CreateService(app.vault)
    app.emit(svc.create_batch(items, partial=partial))
