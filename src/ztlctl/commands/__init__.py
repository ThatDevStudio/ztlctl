"""Subcommand modules for ztlctl.

Provides register_commands() which uses deferred imports to keep
``ztlctl --help`` fast as the codebase grows.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import click


def register_commands(cli: click.Group) -> None:
    """Register all command groups and standalone commands on the root CLI group.

    Uses deferred imports so modules are only loaded when actually invoked.
    7 groups (have subcommands) + 6 standalone commands.
    """
    # --- Groups ---
    from ztlctl.commands.agent import agent
    from ztlctl.commands.create import create
    from ztlctl.commands.export import export
    from ztlctl.commands.garden import garden
    from ztlctl.commands.graph import graph
    from ztlctl.commands.query import query
    from ztlctl.commands.workflow import workflow

    cli.add_command(create)
    cli.add_command(query)
    cli.add_command(graph)
    cli.add_command(agent)
    cli.add_command(garden)
    cli.add_command(export)
    cli.add_command(workflow)

    # --- Standalone commands ---
    from ztlctl.commands.archive import archive
    from ztlctl.commands.check import check
    from ztlctl.commands.extract import extract
    from ztlctl.commands.init_cmd import init_cmd
    from ztlctl.commands.reweave import reweave
    from ztlctl.commands.upgrade import upgrade

    cli.add_command(check)
    cli.add_command(init_cmd)
    cli.add_command(upgrade)
    cli.add_command(reweave)
    cli.add_command(archive)
    cli.add_command(extract)
