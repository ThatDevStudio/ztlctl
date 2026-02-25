"""Command: database schema migration."""

from __future__ import annotations

from typing import TYPE_CHECKING

import click

if TYPE_CHECKING:
    from ztlctl.commands._context import AppContext


@click.command()
@click.option(
    "--check", "check_only", is_flag=True, help="Show pending migrations without applying."
)
@click.pass_obj
def upgrade(app: AppContext, check_only: bool) -> None:
    """Run pending database migrations."""
    click.echo("upgrade: not yet implemented")
