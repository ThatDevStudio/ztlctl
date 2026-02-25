"""Command group: session and context management for agents."""

from __future__ import annotations

from typing import TYPE_CHECKING

import click

if TYPE_CHECKING:
    from ztlctl.commands._context import AppContext


@click.group()
@click.pass_obj
def agent(app: AppContext) -> None:
    """Manage sessions, context, and agent workflows."""


@agent.group()
@click.pass_obj
def session(app: AppContext) -> None:
    """Session lifecycle commands."""


@session.command()
@click.argument("topic")
@click.pass_obj
def start(app: AppContext, topic: str) -> None:
    """Start a new session with the given topic."""
    from ztlctl.services.session import SessionService

    app.emit(SessionService(app.vault).start(topic))


@session.command()
@click.option("--summary", default=None, help="Close summary.")
@click.pass_obj
def close(app: AppContext, summary: str | None) -> None:
    """Close the active session with enrichment pipeline."""
    from ztlctl.services.session import SessionService

    app.emit(SessionService(app.vault).close(summary=summary))


@session.command()
@click.argument("session_id")
@click.pass_obj
def reopen(app: AppContext, session_id: str) -> None:
    """Reopen a previously closed session."""
    from ztlctl.services.session import SessionService

    app.emit(SessionService(app.vault).reopen(session_id))
