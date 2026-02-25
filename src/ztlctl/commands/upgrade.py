"""Command: database schema migration."""

from __future__ import annotations

from typing import TYPE_CHECKING

import click

if TYPE_CHECKING:
    from ztlctl.config.settings import ZtlSettings


@click.command()
@click.option(
    "--check", "check_only", is_flag=True, help="Show pending migrations without applying."
)
@click.pass_obj
def upgrade(ctx: ZtlSettings, check_only: bool) -> None:
    """Run pending database migrations."""
    click.echo("upgrade: not yet implemented")
