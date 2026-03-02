"""Custom Click base classes with --examples support.

Provides ZtlCommand and ZtlGroup that accept an ``examples`` parameter.
When ``--examples`` is passed, the command prints usage examples and exits.
This keeps ``--help`` concise while making examples available on demand.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

import click


def _add_examples_option(cmd: click.Command | click.Group, examples: str) -> None:
    """Attach an eager ``--examples`` flag to a Click command or group."""

    def show_examples(ctx: click.Context, _param: click.Parameter, value: bool) -> None:
        if not value:
            return
        click.echo(f"Examples for '{ctx.command_path}':\n")
        click.echo(examples)
        ctx.exit(0)

    cmd.params.append(
        click.Option(
            ["--examples"],
            is_flag=True,
            expose_value=False,
            is_eager=True,
            callback=show_examples,
            help="Show usage examples.",
        )
    )


class ZtlCommand(click.Command):
    """Click Command subclass that supports an ``--examples`` flag."""

    def __init__(self, *args: Any, examples: str | None = None, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.examples = examples
        if examples:
            _add_examples_option(self, examples)


class DynamicProfileOption(click.Option):
    """Click option that appends currently installed profiles to help text."""

    def __init__(
        self,
        *args: Any,
        discovery_scope: str,
        path_param: str = "path",
        **kwargs: Any,
    ) -> None:
        self.discovery_scope = discovery_scope
        self.path_param = path_param
        super().__init__(*args, **kwargs)

    def get_help_record(self, ctx: click.Context) -> tuple[str, str] | None:
        record = super().get_help_record(ctx)
        if record is None:
            return None
        option, help_text = record
        installed = self._installed_profiles(ctx)
        if installed:
            help_text = f"{help_text} Installed now: {', '.join(installed)}."
        return option, help_text

    def _installed_profiles(self, ctx: click.Context) -> list[str]:
        try:
            from ztlctl.workspace_profiles import discover_init_profiles, discover_vault_profiles

            if self.discovery_scope == "init":
                return discover_init_profiles().ordered_ids()
            raw_path = ctx.params.get(self.path_param, ".")
            vault_root = Path(str(raw_path)).resolve()
            return discover_vault_profiles(vault_root).ordered_ids()
        except Exception:
            return []


class ZtlGroup(click.Group):
    """Click Group subclass that supports an ``--examples`` flag.

    Sets ``command_class = ZtlCommand`` so all subcommands automatically
    accept the ``examples`` parameter without explicit ``cls=`` each time.
    """

    command_class = ZtlCommand

    def __init__(self, *args: Any, examples: str | None = None, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.examples = examples
        if examples:
            _add_examples_option(self, examples)


class RootZtlGroup(ZtlGroup):
    """Root command group with lazy dynamic subcommand support."""

    def __init__(
        self,
        *args: Any,
        dynamic_loader: Callable[[click.Context], dict[str, click.Command]] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.dynamic_loader = dynamic_loader

    def _dynamic_commands(self, ctx: click.Context) -> dict[str, click.Command]:
        cached = ctx.meta.get("_ztl_dynamic_commands")
        if isinstance(cached, dict):
            return cached
        if self.dynamic_loader is None:
            ctx.meta["_ztl_dynamic_commands"] = {}
            return {}
        commands = self.dynamic_loader(ctx)
        ctx.meta["_ztl_dynamic_commands"] = commands
        return commands

    def list_commands(self, ctx: click.Context) -> list[str]:
        names = list(super().list_commands(ctx))
        for name in self._dynamic_commands(ctx):
            if name not in names:
                names.append(name)
        return sorted(names)

    def get_command(self, ctx: click.Context, cmd_name: str) -> click.Command | None:
        command = super().get_command(ctx, cmd_name)
        if command is not None:
            return command
        return self._dynamic_commands(ctx).get(cmd_name)
