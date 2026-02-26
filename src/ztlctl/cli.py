"""Root CLI group for ztlctl with global flags and command registration."""

from __future__ import annotations

import click

from ztlctl import __version__
from ztlctl.commands import register_commands
from ztlctl.commands._context import AppContext
from ztlctl.config.settings import ZtlSettings


@click.group(invoke_without_command=True)
@click.version_option(version=__version__, prog_name="ztlctl")
@click.option("--json", "json_output", is_flag=True, help="Structured JSON output.")
@click.option("-q", "--quiet", is_flag=True, help="Minimal output.")
@click.option("-v", "--verbose", is_flag=True, help="Detailed output with debug info.")
@click.option("--log-json", is_flag=True, help="Structured JSON log output to stderr.")
@click.option("--no-interact", is_flag=True, help="Non-interactive mode (no prompts).")
@click.option("--no-reweave", is_flag=True, help="Skip reweave on creation.")
@click.option("-c", "--config", "config_path", default=None, help="Override config file path.")
@click.option("--sync", is_flag=True, help="Force synchronous event dispatch.")
@click.pass_context
def cli(
    ctx: click.Context,
    json_output: bool,
    quiet: bool,
    verbose: bool,
    log_json: bool,
    no_interact: bool,
    no_reweave: bool,
    config_path: str | None,
    sync: bool,
) -> None:
    """ztlctl — Zettelkasten Control CLI utility."""
    ctx.ensure_object(dict)
    settings = ZtlSettings.from_cli(
        config_path=config_path,
        json_output=json_output,
        quiet=quiet,
        verbose=verbose,
        log_json=log_json,
        no_interact=no_interact,
        no_reweave=no_reweave,
        sync=sync,
    )
    ctx.obj = AppContext(settings)
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


register_commands(cli)
