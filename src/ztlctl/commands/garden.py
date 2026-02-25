"""Command group: cultivation persona (garden seed)."""

from __future__ import annotations

from typing import TYPE_CHECKING

import click

if TYPE_CHECKING:
    from ztlctl.config.settings import ZtlSettings


@click.group()
@click.pass_obj
def garden(ctx: ZtlSettings) -> None:
    """Cultivate knowledge with the garden persona."""
