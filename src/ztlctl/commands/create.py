"""Custom presentation: batch create command."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import click

from ztlctl.commands._base import ZtlCommand

if TYPE_CHECKING:
    from ztlctl.commands._context import AppContext


@click.command(
    cls=ZtlCommand,
    examples="""\
  ztlctl create batch items.json
  ztlctl create batch items.json --partial
  ztlctl --json create batch bulk-notes.json""",
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

    from ztlctl.services.create import CreateService

    svc = CreateService(app.vault)
    app.emit(svc.create_batch(items, partial=partial))
