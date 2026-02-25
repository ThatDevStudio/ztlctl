"""Command: graph densification and link management."""

from __future__ import annotations

from typing import TYPE_CHECKING

import click

if TYPE_CHECKING:
    from ztlctl.config.settings import ZtlSettings


@click.command()
@click.option("--prune", is_flag=True, help="Remove stale links.")
@click.option("--dry-run", is_flag=True, help="Show changes without applying.")
@click.option("--undo", is_flag=True, help="Reverse last reweave via audit trail.")
@click.option("--id", "content_id", default=None, help="Target a specific content ID.")
@click.pass_obj
def reweave(
    ctx: ZtlSettings,
    prune: bool,
    dry_run: bool,
    undo: bool,
    content_id: str | None,
) -> None:
    """Reweave links to densify the knowledge graph."""
    click.echo("reweave: not yet implemented")
