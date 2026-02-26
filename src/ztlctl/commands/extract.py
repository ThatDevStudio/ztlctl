"""Command: extract decision from session log."""

from __future__ import annotations

from typing import TYPE_CHECKING

import click

from ztlctl.commands._base import ZtlCommand

if TYPE_CHECKING:
    from ztlctl.commands._context import AppContext


@click.command(
    cls=ZtlCommand,
    examples="""\
  ztlctl extract LOG-0001
  ztlctl extract LOG-0042 --title "Auth approach decision"
  ztlctl --json extract LOG-0001""",
)
@click.argument("session_id")
@click.option("--title", default=None, help="Decision note title (auto-generated if omitted).")
@click.pass_obj
def extract(app: AppContext, session_id: str, title: str | None) -> None:
    """Extract a decision note from a session log."""
    from ztlctl.services.session import SessionService

    app.emit(SessionService(app.vault).extract_decision(session_id, title=title))
