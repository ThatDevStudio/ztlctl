"""Command group: cultivation persona (garden seed)."""

from __future__ import annotations

from typing import TYPE_CHECKING

import click

from ztlctl.commands._base import ZtlGroup

if TYPE_CHECKING:
    from ztlctl.commands._context import AppContext


@click.group(cls=ZtlGroup)
@click.pass_obj
def garden(app: AppContext) -> None:
    """Cultivate knowledge with the garden persona."""
