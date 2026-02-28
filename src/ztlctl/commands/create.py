"""Command group: content creation (note, reference, task, batch)."""

from __future__ import annotations

import json
import sys
from typing import TYPE_CHECKING

import click

from ztlctl.commands._base import ZtlGroup
from ztlctl.services.create import CreateService

if TYPE_CHECKING:
    from ztlctl.commands._context import AppContext


def _is_interactive(app: AppContext) -> bool:
    """Return True when interactive prompts should fire.

    Prompts require: no ``--no-interact``, no ``--json``, and stdin is a TTY.
    """
    return not app.settings.no_interact and not app.settings.json_output and sys.stdin.isatty()


def _load_dynamic_subtypes(ctx: click.Context, content_type: str) -> list[str]:
    """Load built-in and plugin-registered subtype choices for a content type."""
    from ztlctl.domain.content import CONTENT_REGISTRY

    if ctx.obj is not None:
        try:
            _ = ctx.obj.vault
        except Exception:
            pass

    builtin_by_type = {
        "note": ["knowledge", "decision"],
        "reference": ["article", "tool", "spec"],
    }
    builtin = list(builtin_by_type.get(content_type, []))
    plugin_subtypes = sorted(
        name
        for name, model_cls in CONTENT_REGISTRY.items()
        if name not in builtin
        and name != content_type
        and getattr(model_cls, "_content_type", None) == content_type
    )
    return builtin + plugin_subtypes


def _validate_subtype(content_type: str):
    """Build a Click callback that validates subtypes lazily."""

    def _callback(ctx: click.Context, _param: click.Parameter, value: str | None) -> str | None:
        if value is None:
            return None

        choices = _load_dynamic_subtypes(ctx, content_type)
        if value not in choices:
            formatted = ", ".join(repr(choice) for choice in choices)
            raise click.BadParameter(f"{value!r} is not one of {formatted}")
        return value

    return _callback


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
@click.option(
    "--subtype",
    callback=_validate_subtype("note"),
    help="Note subtype. Supports built-ins and plugin-registered note subtypes.",
)
@click.option("--tags", multiple=True, help="Tags (repeatable, e.g. --tags domain/scope).")
@click.option("--topic", default=None, help="Topic subdirectory.")
@click.option("--session", default=None, help="Session ID (LOG-NNNN).")
@click.option("--cost", "token_cost", type=int, default=0, help="Token cost for this action.")
@click.pass_obj
def note(
    app: AppContext,
    title: str,
    subtype: str | None,
    tags: tuple[str, ...],
    topic: str | None,
    session: str | None,
    token_cost: int,
) -> None:
    """Create a new note."""
    interactive = _is_interactive(app)
    if interactive and not tags:
        raw = click.prompt("Tags (comma-separated, empty for none)", default="")
        if raw.strip():
            tags = tuple(t.strip() for t in raw.split(",") if t.strip())
    if interactive and topic is None:
        raw = click.prompt("Topic (optional)", default="")
        topic = raw.strip() or None

    svc = CreateService(app.vault)
    result = svc.create_note(
        title,
        subtype=subtype,
        tags=list(tags) if tags else None,
        topic=topic,
        session=session,
    )
    app.emit(result)
    app.log_action_cost(result, token_cost)


@create.command(
    examples="""\
  ztlctl create reference "FastAPI Docs" --url https://fastapi.tiangolo.com
  ztlctl create reference "OAuth2 Spec" --subtype spec --tags auth/oauth
  ztlctl create reference "pytest" --subtype tool --topic testing"""
)
@click.argument("title")
@click.option("--url", default=None, help="Source URL.")
@click.option(
    "--subtype",
    callback=_validate_subtype("reference"),
    help="Reference subtype. Supports built-ins and plugin-registered reference subtypes.",
)
@click.option("--tags", multiple=True, help="Tags (repeatable).")
@click.option("--topic", default=None, help="Topic subdirectory.")
@click.option("--session", default=None, help="Session ID (LOG-NNNN).")
@click.option("--cost", "token_cost", type=int, default=0, help="Token cost for this action.")
@click.pass_obj
def reference(
    app: AppContext,
    title: str,
    url: str | None,
    subtype: str | None,
    tags: tuple[str, ...],
    topic: str | None,
    session: str | None,
    token_cost: int,
) -> None:
    """Create a new reference."""
    interactive = _is_interactive(app)
    if interactive and url is None:
        raw = click.prompt("URL (optional)", default="")
        url = raw.strip() or None
    if interactive and not tags:
        raw = click.prompt("Tags (comma-separated, empty for none)", default="")
        if raw.strip():
            tags = tuple(t.strip() for t in raw.split(",") if t.strip())

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
    app.log_action_cost(result, token_cost)


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
    default=None,
    help="Priority level.",
)
@click.option(
    "--impact",
    type=click.Choice(["low", "medium", "high"]),
    default=None,
    help="Impact level.",
)
@click.option(
    "--effort",
    type=click.Choice(["low", "medium", "high"]),
    default=None,
    help="Effort level.",
)
@click.option("--tags", multiple=True, help="Tags (repeatable).")
@click.option("--session", default=None, help="Session ID (LOG-NNNN).")
@click.option("--cost", "token_cost", type=int, default=0, help="Token cost for this action.")
@click.pass_obj
def task(
    app: AppContext,
    title: str,
    priority: str | None,
    impact: str | None,
    effort: str | None,
    tags: tuple[str, ...],
    session: str | None,
    token_cost: int,
) -> None:
    """Create a new task."""
    interactive = _is_interactive(app)
    if interactive:
        if priority is None:
            priority = click.prompt(
                "Priority",
                type=click.Choice(["low", "medium", "high", "critical"]),
                default="medium",
            )
        if impact is None:
            impact = click.prompt(
                "Impact",
                type=click.Choice(["low", "medium", "high"]),
                default="medium",
            )
        if effort is None:
            effort = click.prompt(
                "Effort",
                type=click.Choice(["low", "medium", "high"]),
                default="medium",
            )
    else:
        priority = priority or "medium"
        impact = impact or "medium"
        effort = effort or "medium"

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
    app.log_action_cost(result, token_cost)


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
                op="create_batch",
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
                op="create_batch",
                error=ServiceError(
                    code="invalid_format",
                    message="JSON file must contain a top-level array.",
                ),
            )
        )
        return

    svc = CreateService(app.vault)
    app.emit(svc.create_batch(items, partial=partial))
