"""Command group: vault export (markdown, indexes, graph)."""

from __future__ import annotations

from typing import TYPE_CHECKING

import click

if TYPE_CHECKING:
    from ztlctl.config.models import AppContext


@click.group()
@click.pass_obj
def export(ctx: AppContext) -> None:
    """Export vault content in various formats."""
