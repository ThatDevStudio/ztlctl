"""Custom Click base classes with --examples support.

Provides ZtlCommand and ZtlGroup that accept an ``examples`` parameter.
When ``--examples`` is passed, the command prints usage examples and exits.
This keeps ``--help`` concise while making examples available on demand.
"""

from __future__ import annotations

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
