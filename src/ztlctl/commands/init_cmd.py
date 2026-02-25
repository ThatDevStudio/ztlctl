"""Command: vault initialization (named init_cmd to avoid shadowing builtins)."""

from __future__ import annotations

from typing import TYPE_CHECKING

import click

from ztlctl.commands._base import ZtlCommand

if TYPE_CHECKING:
    from ztlctl.commands._context import AppContext


@click.command("init", cls=ZtlCommand)
@click.argument("path", required=False)
@click.option("--no-workflow", is_flag=True, help="Skip workflow setup.")
@click.pass_obj
def init_cmd(app: AppContext, path: str | None, no_workflow: bool) -> None:
    """Initialize a new ztlctl vault."""
    click.echo("init: not yet implemented")
