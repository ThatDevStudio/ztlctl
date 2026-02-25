"""Command group: session and context management for agents."""

from __future__ import annotations

from typing import TYPE_CHECKING

import click

if TYPE_CHECKING:
    from ztlctl.config.settings import ZtlSettings


@click.group()
@click.pass_obj
def agent(ctx: ZtlSettings) -> None:
    """Manage sessions, context, and agent workflows."""
