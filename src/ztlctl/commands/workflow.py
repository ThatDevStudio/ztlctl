"""Command group: workflow init and update (Copier templates)."""

from __future__ import annotations

from typing import TYPE_CHECKING

import click

if TYPE_CHECKING:
    from ztlctl.config.settings import ZtlSettings


@click.group()
@click.pass_obj
def workflow(ctx: ZtlSettings) -> None:
    """Manage workflow templates and configuration."""
