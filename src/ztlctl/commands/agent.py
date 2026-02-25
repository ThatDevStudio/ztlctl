"""Command group: session and context management for agents."""

from __future__ import annotations

from typing import TYPE_CHECKING

import click

from ztlctl.commands._base import ZtlGroup

if TYPE_CHECKING:
    from ztlctl.commands._context import AppContext

_AGENT_EXAMPLES = """\
  ztlctl agent session start "refactor auth module"
  ztlctl agent session close --summary "Completed auth refactor"
  ztlctl agent session reopen LOG-0001
  ztlctl agent regenerate"""


@click.group(cls=ZtlGroup, examples=_AGENT_EXAMPLES)
@click.pass_obj
def agent(app: AppContext) -> None:
    """Manage sessions, context, and agent workflows."""


@agent.group(
    cls=ZtlGroup,
    examples="""\
  ztlctl agent session start "refactor auth module"
  ztlctl agent session close --summary "Done"
  ztlctl agent session reopen LOG-0001""",
)
@click.pass_obj
def session(app: AppContext) -> None:
    """Session lifecycle commands."""


@session.command(
    examples="""\
  ztlctl agent session start "refactor auth module"
  ztlctl agent session start "investigate performance"
  ztlctl --json agent session start "review API design" """
)
@click.argument("topic")
@click.pass_obj
def start(app: AppContext, topic: str) -> None:
    """Start a new session with the given topic."""
    from ztlctl.services.session import SessionService

    app.emit(SessionService(app.vault).start(topic))


@session.command(
    examples="""\
  ztlctl agent session close
  ztlctl agent session close --summary "Completed auth refactor" """
)
@click.option("--summary", default=None, help="Close summary.")
@click.pass_obj
def close(app: AppContext, summary: str | None) -> None:
    """Close the active session with enrichment pipeline."""
    from ztlctl.services.session import SessionService

    app.emit(SessionService(app.vault).close(summary=summary))


@session.command(
    examples="""\
  ztlctl agent session reopen LOG-0001
  ztlctl --json agent session reopen LOG-0042"""
)
@click.argument("session_id")
@click.pass_obj
def reopen(app: AppContext, session_id: str) -> None:
    """Reopen a previously closed session."""
    from ztlctl.services.session import SessionService

    app.emit(SessionService(app.vault).reopen(session_id))


@agent.command(
    examples="""\
  ztlctl agent regenerate"""
)
@click.pass_obj
def regenerate(app: AppContext) -> None:
    """Re-render self/ files from current vault settings."""
    from ztlctl.services.init import InitService

    app.emit(InitService.regenerate_self(app.vault))
