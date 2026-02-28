"""Command: vault integrity checking and repair."""

from __future__ import annotations

from typing import TYPE_CHECKING

import click

from ztlctl.commands._base import ZtlCommand

if TYPE_CHECKING:
    from ztlctl.commands._context import AppContext


@click.command(
    cls=ZtlCommand,
    examples="""\
  ztlctl check
  ztlctl check --errors-only
  ztlctl check --min-severity error
  ztlctl check --fix
  ztlctl check --fix --level aggressive
  ztlctl check --rebuild
  ztlctl check --rollback""",
)
@click.option(
    "--min-severity",
    type=click.Choice(["warning", "error"]),
    default="warning",
    help="Hide issues below this severity.",
)
@click.option("--errors-only", is_flag=True, help="Shortcut for --min-severity error.")
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
    min_severity: str,
    errors_only: bool,
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
        threshold = "error" if errors_only else min_severity
        app.emit(svc.check(min_severity=threshold))
