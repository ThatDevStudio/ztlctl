"""Command group: vault export (markdown, indexes, graph)."""

from __future__ import annotations

from typing import TYPE_CHECKING

import click

if TYPE_CHECKING:
    from ztlctl.config.settings import ZtlSettings


@click.group()
@click.pass_obj
def export(ctx: ZtlSettings) -> None:
    """Export vault content in various formats."""
