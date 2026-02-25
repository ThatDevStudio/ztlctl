"""Command: supersede a decision with a newer one."""

from __future__ import annotations

from typing import TYPE_CHECKING

import click

from ztlctl.commands._base import ZtlCommand

if TYPE_CHECKING:
    from ztlctl.commands._context import AppContext


@click.command(
    cls=ZtlCommand,
    examples="""\
  ztlctl supersede ztl_olddecision ztl_newdecision
  ztlctl --json supersede ztl_abc12345 ztl_def67890""",
)
@click.argument("old_id")
@click.argument("new_id")
@click.pass_obj
def supersede(app: AppContext, old_id: str, new_id: str) -> None:
    """Mark a decision as superseded by a newer decision."""
    from ztlctl.services.update import UpdateService

    app.emit(UpdateService(app.vault).supersede(old_id, new_id))
