"""Command group: session and context management for agents."""

from __future__ import annotations

from typing import TYPE_CHECKING

import click

if TYPE_CHECKING:
    from ztlctl.config.models import AppContext


@click.group()
@click.pass_obj
def agent(ctx: AppContext) -> None:
    """Manage sessions, context, and agent workflows."""
