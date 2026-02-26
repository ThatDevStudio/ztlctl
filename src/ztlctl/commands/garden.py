"""Command group: cultivation persona (garden seed)."""

from __future__ import annotations

from typing import TYPE_CHECKING

import click

from ztlctl.commands._base import ZtlGroup

if TYPE_CHECKING:
    from ztlctl.commands._context import AppContext

_GARDEN_EXAMPLES = """\
  ztlctl garden seed "Half-formed idea"
  ztlctl garden seed "Quick thought" --tags "domain/topic"
  ztlctl --json garden seed "API design hunch" --topic architecture"""


@click.group(cls=ZtlGroup, examples=_GARDEN_EXAMPLES)
@click.pass_obj
def garden(app: AppContext) -> None:
    """Cultivate knowledge with the garden persona."""


@garden.command(
    examples="""\
  ztlctl garden seed "Half-formed idea"
  ztlctl garden seed "Quick thought" --tags "domain/topic"
  ztlctl --json garden seed "API design hunch" --topic architecture"""
)
@click.argument("title")
@click.option("--tags", default=None, help="Comma-separated tags.")
@click.option("--topic", default=None, help="Topic scope.")
@click.pass_obj
def seed(app: AppContext, title: str, tags: str | None, topic: str | None) -> None:
    """Plant a seed note — quick capture with minimal metadata."""
    from ztlctl.services.create import CreateService

    tag_list = [t.strip() for t in tags.split(",")] if tags else None
    app.emit(
        CreateService(app.vault).create_note(
            title,
            tags=tag_list,
            topic=topic,
            maturity="seed",
        )
    )
