"""Subcommand modules for ztlctl.

Provides register_commands() which uses deferred imports to keep
``ztlctl --help`` fast as the codebase grows.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import click


def load_plugin_commands(ctx: click.Context) -> dict[str, click.Command]:
    """Resolve plugin CLI commands for the current invocation context."""
    from ztlctl.catalogs import cli_command_catalog
    from ztlctl.config.settings import ZtlSettings
    from ztlctl.plugins.manager import PluginManager

    try:
        settings = ZtlSettings.from_cli(
            config_path=ctx.params.get("config_path"),
            json_output=bool(ctx.params.get("json_output", False)),
            quiet=bool(ctx.params.get("quiet", False)),
            verbose=bool(ctx.params.get("verbose", False)),
            log_json=bool(ctx.params.get("log_json", False)),
            no_interact=bool(ctx.params.get("no_interact", False)),
            no_reweave=bool(ctx.params.get("no_reweave", False)),
            sync=bool(ctx.params.get("sync", False)),
        )
    except Exception:
        return {}

    pm = PluginManager()
    pm.discover_and_load(local_dir=settings.vault_root / ".ztlctl" / "plugins")
    reserved = {entry["name"] for entry in cli_command_catalog()}
    return {
        entry.name: entry.command for entry in pm.cli_command_contributions(reserved_names=reserved)
    }


def register_commands(cli: click.Group) -> None:
    """Register all command groups and standalone commands on the root CLI group.

    Uses deferred imports so modules are only loaded when actually invoked.
    8 groups (have subcommands) + 8 standalone commands.
    """
    # --- Groups ---
    from ztlctl.commands.agent import agent
    from ztlctl.commands.create import create
    from ztlctl.commands.export import export
    from ztlctl.commands.garden import garden
    from ztlctl.commands.graph import graph
    from ztlctl.commands.ingest import ingest
    from ztlctl.commands.query import query
    from ztlctl.commands.vector import vector
    from ztlctl.commands.workflow import workflow

    cli.add_command(create)
    cli.add_command(query)
    cli.add_command(graph)
    cli.add_command(agent)
    cli.add_command(garden)
    cli.add_command(export)
    cli.add_command(ingest)
    cli.add_command(vector)
    cli.add_command(workflow)

    # --- Standalone commands ---
    from ztlctl.commands.archive import archive
    from ztlctl.commands.check import check
    from ztlctl.commands.extract import extract
    from ztlctl.commands.init_cmd import init_cmd
    from ztlctl.commands.reweave import reweave
    from ztlctl.commands.serve import serve
    from ztlctl.commands.supersede import supersede
    from ztlctl.commands.update import update
    from ztlctl.commands.upgrade import upgrade

    cli.add_command(check)
    cli.add_command(init_cmd)
    cli.add_command(upgrade)
    cli.add_command(update)
    cli.add_command(reweave)
    cli.add_command(archive)
    cli.add_command(extract)
    cli.add_command(supersede)
    cli.add_command(serve)
