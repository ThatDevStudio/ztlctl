"""Command: database schema migration."""

from __future__ import annotations

from typing import TYPE_CHECKING

import click

from ztlctl.commands._base import ZtlCommand

if TYPE_CHECKING:
    from ztlctl.commands._context import AppContext


@click.command(
    cls=ZtlCommand,
    examples="""\
  ztlctl upgrade
  ztlctl upgrade --check
  ztlctl --json upgrade --check""",
)
@click.option(
    "--check", "check_only", is_flag=True, help="Show pending migrations without applying."
)
@click.pass_obj
def upgrade(app: AppContext, check_only: bool) -> None:
    """Run pending database migrations."""
    from ztlctl.services.upgrade import UpgradeService

    svc = UpgradeService(app.vault)
    app.emit(svc.check_pending() if check_only else svc.apply())
