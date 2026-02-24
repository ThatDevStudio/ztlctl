"""Command group: content creation (note, reference, task)."""

from __future__ import annotations

from typing import TYPE_CHECKING

import click

if TYPE_CHECKING:
    from ztlctl.config.models import AppContext


@click.group()
@click.pass_obj
def create(ctx: AppContext) -> None:
    """Create notes, references, and tasks."""
