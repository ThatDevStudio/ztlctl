"""Command: vault integrity checking and repair."""

from __future__ import annotations

from typing import TYPE_CHECKING

import click

if TYPE_CHECKING:
    from ztlctl.commands._context import AppContext


@click.command()
@click.option("--fix", is_flag=True, help="Automatically repair issues.")
@click.option(
    "--level",
    type=click.Choice(["safe", "aggressive"]),
    default="safe",
    help="Repair aggressiveness level.",
)
@click.option("--rebuild", is_flag=True, help="Full DB rebuild from files.")
@click.option("--rollback", is_flag=True, help="Restore from latest backup.")
@click.pass_obj
def check(
    app: AppContext,
    fix: bool,
    level: str,
    rebuild: bool,
    rollback: bool,
) -> None:
    """Check vault integrity and optionally repair issues."""
    from ztlctl.services.check import CheckService

    svc = CheckService(app.vault)

    if rollback:
        app.emit(svc.rollback())
    elif rebuild:
        app.emit(svc.rebuild())
    elif fix:
        app.emit(svc.fix(level=level))
    else:
        app.emit(svc.check())
