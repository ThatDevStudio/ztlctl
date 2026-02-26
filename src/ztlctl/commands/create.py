"""Command group: content creation (note, reference, task, batch)."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import click

from ztlctl.commands._base import ZtlGroup
from ztlctl.services.create import CreateService

if TYPE_CHECKING:
    from ztlctl.commands._context import AppContext

_CREATE_EXAMPLES = """\
  ztlctl create note "Python Design Patterns"
  ztlctl create note "Use Composition" --subtype decision --tags arch/patterns
  ztlctl create reference "FastAPI Docs" --url https://fastapi.tiangolo.com
  ztlctl create task "Fix login bug" --priority high --impact high --effort low
  ztlctl create batch items.json --partial"""


@click.group(cls=ZtlGroup, examples=_CREATE_EXAMPLES)
@click.pass_obj
def create(app: AppContext) -> None:
    """Create notes, references, and tasks."""


@create.command(
    examples="""\
  ztlctl create note "Python Design Patterns"
  ztlctl create note "Use Composition" --subtype decision
  ztlctl create note "ML Overview" --tags ai/ml --topic machine-learning
  ztlctl create note "Session Note" --session LOG-0001"""
)
@click.argument("title")
@click.option("--subtype", type=click.Choice(["knowledge", "decision"]), help="Note subtype.")
@click.option("--tags", multiple=True, help="Tags (repeatable, e.g. --tags domain/scope).")
@click.option("--topic", default=None, help="Topic subdirectory.")
@click.option("--session", default=None, help="Session ID (LOG-NNNN).")
@click.pass_obj
def note(
    app: AppContext,
    title: str,
    subtype: str | None,
    tags: tuple[str, ...],
    topic: str | None,
    session: str | None,
) -> None:
    """Create a new note."""
    svc = CreateService(app.vault)
    result = svc.create_note(
        title,
        subtype=subtype,
        tags=list(tags) if tags else None,
        topic=topic,
        session=session,
    )
    app.emit(result)


@create.command(
    examples="""\
  ztlctl create reference "FastAPI Docs" --url https://fastapi.tiangolo.com
  ztlctl create reference "OAuth2 Spec" --subtype spec --tags auth/oauth
  ztlctl create reference "pytest" --subtype tool --topic testing"""
)
@click.argument("title")
@click.option("--url", default=None, help="Source URL.")
@click.option(
    "--subtype", type=click.Choice(["article", "tool", "spec"]), help="Reference subtype."
)
@click.option("--tags", multiple=True, help="Tags (repeatable).")
@click.option("--topic", default=None, help="Topic subdirectory.")
@click.option("--session", default=None, help="Session ID (LOG-NNNN).")
@click.pass_obj
def reference(
    app: AppContext,
    title: str,
    url: str | None,
    subtype: str | None,
    tags: tuple[str, ...],
    topic: str | None,
    session: str | None,
) -> None:
    """Create a new reference."""
    svc = CreateService(app.vault)
    result = svc.create_reference(
        title,
        url=url,
        subtype=subtype,
        tags=list(tags) if tags else None,
        topic=topic,
        session=session,
    )
    app.emit(result)


@create.command(
    examples="""\
  ztlctl create task "Fix login bug" --priority high --impact high --effort low
  ztlctl create task "Write tests" --priority medium
  ztlctl create task "Refactor auth" --tags tech/debt --session LOG-0001"""
)
@click.argument("title")
@click.option(
    "--priority",
    type=click.Choice(["low", "medium", "high", "critical"]),
    default="medium",
    help="Priority level.",
)
@click.option(
    "--impact",
    type=click.Choice(["low", "medium", "high"]),
    default="medium",
    help="Impact level.",
)
@click.option(
    "--effort",
    type=click.Choice(["low", "medium", "high"]),
    default="medium",
    help="Effort level.",
)
@click.option("--tags", multiple=True, help="Tags (repeatable).")
@click.option("--session", default=None, help="Session ID (LOG-NNNN).")
@click.pass_obj
def task(
    app: AppContext,
    title: str,
    priority: str,
    impact: str,
    effort: str,
    tags: tuple[str, ...],
    session: str | None,
) -> None:
    """Create a new task."""
    svc = CreateService(app.vault)
    result = svc.create_task(
        title,
        priority=priority,
        impact=impact,
        effort=effort,
        tags=list(tags) if tags else None,
        session=session,
    )
    app.emit(result)


@create.command(
    examples="""\
  ztlctl create batch items.json
  ztlctl create batch items.json --partial
  ztlctl --json create batch bulk-notes.json"""
)
@click.argument("file", type=click.Path(exists=True))
@click.option("--partial", is_flag=True, help="Continue on errors (partial mode).")
@click.pass_obj
def batch(app: AppContext, file: str, partial: bool) -> None:
    """Create multiple items from a JSON file.

    FILE must contain a JSON array of objects, each with at least
    "type" and "title" keys.
    """
    try:
        with open(file, encoding="utf-8") as f:
            items = json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        from ztlctl.services.result import ServiceError, ServiceResult

        app.emit(
            ServiceResult(
                ok=False,
                op="batch_create",
                error=ServiceError(
                    code="invalid_file",
                    message=f"Error reading {file}: {exc}",
                ),
            )
        )
        return

    if not isinstance(items, list):
        from ztlctl.services.result import ServiceError, ServiceResult

        app.emit(
            ServiceResult(
                ok=False,
                op="batch_create",
                error=ServiceError(
                    code="invalid_format",
                    message="JSON file must contain a top-level array.",
                ),
            )
        )
        return

    svc = CreateService(app.vault)
    app.emit(svc.create_batch(items, partial=partial))
