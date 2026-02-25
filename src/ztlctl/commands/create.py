"""Command group: content creation (note, reference, task)."""

from __future__ import annotations

import click

from ztlctl.config.settings import ZtlSettings
from ztlctl.infrastructure.vault import Vault
from ztlctl.output.formatters import format_result
from ztlctl.services.create import CreateService


@click.group()
@click.pass_obj
def create(ctx: ZtlSettings) -> None:
    """Create notes, references, and tasks."""


@create.command()
@click.argument("title")
@click.option("--subtype", type=click.Choice(["knowledge", "decision"]), help="Note subtype.")
@click.option("--tags", multiple=True, help="Tags (repeatable, e.g. --tags domain/scope).")
@click.option("--topic", default=None, help="Topic subdirectory.")
@click.option("--session", default=None, help="Session ID (LOG-NNNN).")
@click.pass_obj
def note(
    settings: ZtlSettings,
    title: str,
    subtype: str | None,
    tags: tuple[str, ...],
    topic: str | None,
    session: str | None,
) -> None:
    """Create a new note."""
    vault = Vault(settings)
    svc = CreateService(vault)
    result = svc.create_note(
        title,
        subtype=subtype,
        tags=list(tags) if tags else None,
        topic=topic,
        session=session,
    )
    click.echo(format_result(result, json_output=settings.json_output))


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
    settings: ZtlSettings,
    title: str,
    url: str | None,
    subtype: str | None,
    tags: tuple[str, ...],
    topic: str | None,
    session: str | None,
) -> None:
    """Create a new reference."""
    vault = Vault(settings)
    svc = CreateService(vault)
    result = svc.create_reference(
        title,
        url=url,
        subtype=subtype,
        tags=list(tags) if tags else None,
        topic=topic,
        session=session,
    )
    click.echo(format_result(result, json_output=settings.json_output))


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
    settings: ZtlSettings,
    title: str,
    priority: str,
    impact: str,
    effort: str,
    tags: tuple[str, ...],
    session: str | None,
) -> None:
    """Create a new task."""
    vault = Vault(settings)
    svc = CreateService(vault)
    result = svc.create_task(
        title,
        priority=priority,
        impact=impact,
        effort=effort,
        tags=list(tags) if tags else None,
        session=session,
    )
    click.echo(format_result(result, json_output=settings.json_output))
