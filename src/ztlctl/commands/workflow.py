"""Command group: workflow init and update (Copier templates)."""

from __future__ import annotations

from typing import TYPE_CHECKING

import click

from ztlctl.commands._base import ZtlGroup

if TYPE_CHECKING:
    from ztlctl.commands._context import AppContext


@click.group(
    cls=ZtlGroup,
    examples="""\
  ztlctl workflow init
  ztlctl workflow update""",
)
@click.pass_obj
def workflow(app: AppContext) -> None:
    """Manage workflow templates and configuration."""
