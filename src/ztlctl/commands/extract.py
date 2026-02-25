"""Command: extract decision from session log."""

from __future__ import annotations

from typing import TYPE_CHECKING

import click

if TYPE_CHECKING:
    from ztlctl.config.settings import ZtlSettings


@click.command()
@click.argument("session_id")
@click.pass_obj
def extract(ctx: ZtlSettings, session_id: str) -> None:
    """Extract a decision note from a session log."""
    click.echo("extract: not yet implemented")
