"""Command: graph densification and link management."""

from __future__ import annotations

from typing import TYPE_CHECKING

import click

from ztlctl.commands._base import ZtlCommand

if TYPE_CHECKING:
    from ztlctl.commands._context import AppContext


@click.command(
    cls=ZtlCommand,
    examples="""\
  ztlctl reweave                          # interactive: preview → confirm → apply
  ztlctl reweave --dry-run                # show suggestions only
  ztlctl reweave --auto-link-related      # apply without confirmation
  ztlctl reweave --id ztl_abc12345        # interactive for specific note
  ztlctl reweave --prune --dry-run
  ztlctl reweave --undo
  ztlctl reweave --undo-id 42""",
)
@click.option("--prune", is_flag=True, help="Remove stale links.")
@click.option("--dry-run", is_flag=True, help="Show changes without applying.")
@click.option(
    "--auto-link-related",
    is_flag=True,
    help="Skip confirmation, auto-approve all suggestions.",
)
@click.option("--undo", is_flag=True, help="Reverse last reweave via audit trail.")
@click.option("--undo-id", type=int, default=None, help="Undo a specific reweave log entry by ID.")
@click.option("--id", "content_id", default=None, help="Target a specific content ID.")
@click.option("--cost", "token_cost", type=int, default=0, help="Token cost for this action.")
@click.pass_obj
def reweave(
    app: AppContext,
    prune: bool,
    dry_run: bool,
    auto_link_related: bool,
    undo: bool,
    undo_id: int | None,
    content_id: str | None,
    token_cost: int,
) -> None:
    """Reweave links to densify the knowledge graph."""
    from ztlctl.services.reweave import ReweaveService

    svc = ReweaveService(app.vault)

    if undo or undo_id is not None:
        result = svc.undo(reweave_id=undo_id)
        app.emit(result)
        app.log_action_cost(result, token_cost)
    elif prune:
        result = svc.prune(content_id=content_id, dry_run=dry_run)
        app.emit(result)
        app.log_action_cost(result, token_cost)
    else:
        interactive = not dry_run and not auto_link_related and not app.settings.no_interact

        if interactive:
            # Phase 1: Preview suggestions
            preview = svc.reweave(content_id=content_id, dry_run=True)
            if not preview.ok or preview.data.get("count", 0) == 0:
                app.emit(preview)
                return

            # Phase 2: Show suggestions table
            app.emit(preview)

            # Phase 3: Confirm with user
            count = preview.data["count"]
            if not click.confirm(f"\nApply {count} link(s)?"):
                click.echo("Cancelled.")
                return

            # Phase 4: Connect
            result = svc.reweave(content_id=content_id, dry_run=False)
            app.emit(result)
            app.log_action_cost(result, token_cost)
        else:
            result = svc.reweave(content_id=content_id, dry_run=dry_run)
            app.emit(result)
            app.log_action_cost(result, token_cost)
