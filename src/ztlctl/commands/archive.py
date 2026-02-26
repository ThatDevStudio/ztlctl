"""Command: archive content (soft delete, preserves edges)."""

from __future__ import annotations

from typing import TYPE_CHECKING

import click

from ztlctl.commands._base import ZtlCommand

if TYPE_CHECKING:
    from ztlctl.commands._context import AppContext


@click.command(
    cls=ZtlCommand,
    examples="""\
  ztlctl archive ztl_abc12345
  ztlctl archive TASK-0001
  ztlctl --json archive ref_abc12345""",
)
@click.argument("content_id")
@click.option("--cost", "token_cost", type=int, default=0, help="Token cost for this action.")
@click.pass_obj
def archive(app: AppContext, content_id: str, token_cost: int) -> None:
    """Archive a content item by ID (sets archived flag, preserves edges)."""
    from ztlctl.services.update import UpdateService

    result = UpdateService(app.vault).archive(content_id)
    app.emit(result)
    app.log_action_cost(result, token_cost)
