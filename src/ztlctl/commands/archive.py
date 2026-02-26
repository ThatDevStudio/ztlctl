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
@click.pass_obj
def archive(app: AppContext, content_id: str) -> None:
    """Archive a content item by ID (sets archived flag, preserves edges)."""
    from ztlctl.services.update import UpdateService

    app.emit(UpdateService(app.vault).archive(content_id))
