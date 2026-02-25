"""Command group: graph traversal and analysis."""

from __future__ import annotations

from typing import TYPE_CHECKING

import click

if TYPE_CHECKING:
    from ztlctl.config.settings import ZtlSettings


@click.group()
@click.pass_obj
def graph(ctx: ZtlSettings) -> None:
    """Traverse and analyze the knowledge graph."""
