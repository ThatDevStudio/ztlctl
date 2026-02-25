"""Command group: search, retrieval, and agent-oriented queries."""

from __future__ import annotations

from typing import TYPE_CHECKING

import click

if TYPE_CHECKING:
    from ztlctl.config.settings import ZtlSettings


@click.group()
@click.pass_obj
def query(ctx: ZtlSettings) -> None:
    """Search, list, and query vault content."""
