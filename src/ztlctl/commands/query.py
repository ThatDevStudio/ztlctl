"""Command group: search, retrieval, and agent-oriented queries."""

from __future__ import annotations

from typing import TYPE_CHECKING

import click

if TYPE_CHECKING:
    from ztlctl.config.models import AppContext


@click.group()
@click.pass_obj
def query(ctx: AppContext) -> None:
    """Search, list, and query vault content."""
