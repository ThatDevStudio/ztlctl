"""Root CLI group for ztlctl."""

import click

from ztlctl import __version__


@click.group(invoke_without_command=True)
@click.version_option(version=__version__, prog_name="ztlctl")
@click.pass_context
def cli(ctx: click.Context) -> None:
    """ztlctl — Zettelkasten Control CLI utility."""
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())
