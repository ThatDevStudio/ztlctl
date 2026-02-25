"""Command group: vault export (markdown, indexes, graph)."""

from __future__ import annotations

from typing import TYPE_CHECKING

import click

from ztlctl.commands._base import ZtlGroup

if TYPE_CHECKING:
    from ztlctl.commands._context import AppContext


@click.group(cls=ZtlGroup)
@click.pass_obj
def export(app: AppContext) -> None:
    """Export vault content in various formats."""
