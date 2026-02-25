"""Command: extract decision from session log."""

from __future__ import annotations

from typing import TYPE_CHECKING

import click

from ztlctl.commands._base import ZtlCommand

if TYPE_CHECKING:
    from ztlctl.commands._context import AppContext


@click.command(cls=ZtlCommand)
@click.argument("session_id")
@click.pass_obj
def extract(app: AppContext, session_id: str) -> None:
    """Extract a decision note from a session log."""
    click.echo("extract: not yet implemented")
