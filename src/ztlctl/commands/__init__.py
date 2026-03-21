"""Subcommand modules for ztlctl.

Provides register_commands() which uses the CLI generator for standard
actions and manually registers custom_presentation commands.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import click


def load_plugin_commands(ctx: click.Context) -> dict[str, click.Command]:
    """Resolve plugin CLI commands for the current invocation context."""
    from ztlctl.actions.registry import get_action_registry
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

    import ztlctl.actions  # noqa: F401 — ensure registry is populated

    reserved = {a.name for a in get_action_registry().list_actions()}
    return {
        entry.name: entry.command for entry in pm.cli_command_contributions(reserved_names=reserved)
    }


def register_commands(cli: click.Group) -> None:
    """Register all command groups and standalone commands on the root CLI group.

    Uses the generator for standard ActionDefinitions, then manually adds
    custom_presentation commands that require hand-written implementations.
    """
    from ztlctl.commands.generator import generate_commands

    # Auto-generate standard commands from ActionRegistry
    generate_commands(cli)

    # --- Custom presentation commands (hand-written) ---

    import click as _click

    # create group: batch subcommand added to the generator-created 'create' group
    from ztlctl.commands.create import batch

    create_group = cli.commands.get("create")
    if isinstance(create_group, _click.Group):
        create_group.add_command(batch)

    # update: decomposed --title/--status/--tags/--body/--maturity flags (custom_presentation)
    from ztlctl.commands.update import update

    cli.add_command(update)

    # init: The generator creates an 'init' group with regenerate/staleness subcommands.
    # We harvest those subcommands, then replace the generated group with the hand-written
    # wizard group (which supports invoke_without_command for `ztlctl init [--name ...]`),
    # and re-attach the generated subcommands to the wizard group.
    from ztlctl.commands.init_cmd import init_wizard_group

    generated_init = cli.commands.get("init")
    generated_init_subcommands: dict[str, _click.Command] = {}
    if generated_init is not None and isinstance(generated_init, _click.Group):
        ctx = _click.Context(generated_init)
        for sub_name in generated_init.list_commands(ctx):
            sub_cmd = generated_init.get_command(ctx, sub_name)
            if sub_cmd is not None:
                generated_init_subcommands[sub_name] = sub_cmd

    # Register the wizard group (overwrites generated init group)
    cli.add_command(init_wizard_group)

    # Re-attach generated subcommands (regenerate, staleness) to the wizard group
    for sub_name, sub_cmd in generated_init_subcommands.items():
        init_wizard_group.add_command(sub_cmd, name=sub_name)

    # serve (custom_presentation)
    from ztlctl.commands.serve import serve

    cli.add_command(serve)

    # workflow (custom_presentation: init_workflow, update_workflow, export_assets)
    from ztlctl.commands.workflow import workflow

    cli.add_command(workflow)

    # docs (custom_presentation: --json flag requires hand-written command)
    from ztlctl.commands.docs import docs_group

    cli.add_command(docs_group)
