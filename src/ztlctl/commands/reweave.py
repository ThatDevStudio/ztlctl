"""Command: graph densification and link management."""

from __future__ import annotations

from typing import TYPE_CHECKING

import click

if TYPE_CHECKING:
    from ztlctl.commands._context import AppContext


@click.command()
@click.option("--prune", is_flag=True, help="Remove stale links.")
@click.option("--dry-run", is_flag=True, help="Show changes without applying.")
@click.option("--undo", is_flag=True, help="Reverse last reweave via audit trail.")
@click.option("--undo-id", type=int, default=None, help="Undo a specific reweave log entry by ID.")
@click.option("--id", "content_id", default=None, help="Target a specific content ID.")
@click.pass_obj
def reweave(
    app: AppContext,
    prune: bool,
    dry_run: bool,
    undo: bool,
    undo_id: int | None,
    content_id: str | None,
) -> None:
    """Reweave links to densify the knowledge graph."""
    from ztlctl.services.reweave import ReweaveService

    svc = ReweaveService(app.vault)

    if undo or undo_id is not None:
        app.emit(svc.undo(reweave_id=undo_id))
    elif prune:
        app.emit(svc.prune(content_id=content_id, dry_run=dry_run))
    else:
        app.emit(svc.reweave(content_id=content_id, dry_run=dry_run))
