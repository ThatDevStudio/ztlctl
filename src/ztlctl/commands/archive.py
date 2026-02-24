"""Command: archive content (soft delete, preserves edges)."""

from __future__ import annotations

from typing import TYPE_CHECKING

import click

if TYPE_CHECKING:
    from ztlctl.config.models import AppContext


@click.command()
@click.argument("content_id")
@click.pass_obj
def archive(ctx: AppContext, content_id: str) -> None:
    """Archive a content item by ID (sets archived flag, preserves edges)."""
    click.echo("archive: not yet implemented")
