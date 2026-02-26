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
  ztlctl agent session cost --report 10000
  ztlctl agent session log "Found relevant pattern" --pin
  ztlctl agent context --topic "auth" --budget 4000
  ztlctl agent brief
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
  ztlctl agent session reopen LOG-0001
  ztlctl agent session cost
  ztlctl agent session cost --report 10000
  ztlctl agent session log "Important finding" --pin""",
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


@session.command(
    examples="""\
  ztlctl agent session cost
  ztlctl agent session cost --report 10000
  ztlctl --json agent session cost"""
)
@click.option("--report", type=int, default=None, help="Budget to report against.")
@click.pass_obj
def cost(app: AppContext, report: int | None) -> None:
    """Show accumulated token cost for active session."""
    from ztlctl.services.session import SessionService

    app.emit(SessionService(app.vault).cost(report=report))


@session.command(
    name="log",
    examples="""\
  ztlctl agent session log "Found relevant pattern"
  ztlctl agent session log "Key decision" --pin
  ztlctl agent session log "API call" --cost 1500""",
)
@click.argument("message")
@click.option("--pin", is_flag=True, help="Pin this entry.")
@click.option("--cost", "token_cost", type=int, default=0, help="Token cost.")
@click.pass_obj
def log_entry(app: AppContext, message: str, pin: bool, token_cost: int) -> None:
    """Append a log entry to the active session."""
    from ztlctl.services.session import SessionService

    app.emit(SessionService(app.vault).log_entry(message, pin=pin, cost=token_cost))


@agent.command(
    examples="""\
  ztlctl agent context
  ztlctl agent context --topic "auth" --budget 4000
  ztlctl agent context --ignore-checkpoints
  ztlctl --json agent context"""
)
@click.option("--topic", default=None, help="Focus topic.")
@click.option("--budget", type=int, default=8000, help="Token budget.")
@click.option(
    "--ignore-checkpoints",
    is_flag=True,
    help="Read full session history instead of from latest checkpoint.",
)
@click.pass_obj
def context(app: AppContext, topic: str | None, budget: int, ignore_checkpoints: bool) -> None:
    """Build token-budgeted agent context payload."""
    from ztlctl.services.session import SessionService

    app.emit(
        SessionService(app.vault).context(
            topic=topic, budget=budget, ignore_checkpoints=ignore_checkpoints
        )
    )


@agent.command(
    examples="""\
  ztlctl agent brief
  ztlctl --json agent brief"""
)
@click.pass_obj
def brief(app: AppContext) -> None:
    """Quick orientation summary."""
    from ztlctl.services.session import SessionService

    app.emit(SessionService(app.vault).brief())


@agent.command(
    examples="""\
  ztlctl agent regenerate"""
)
@click.pass_obj
def regenerate(app: AppContext) -> None:
    """Re-render self/ files from current vault settings."""
    from ztlctl.services.init import InitService

    app.emit(InitService.regenerate_self(app.vault))
