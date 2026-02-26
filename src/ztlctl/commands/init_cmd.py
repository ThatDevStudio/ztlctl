"""Command: vault initialization (named init_cmd to avoid shadowing builtins)."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import click

from ztlctl.commands._base import ZtlCommand

if TYPE_CHECKING:
    from ztlctl.commands._context import AppContext

_INIT_EXAMPLES = """\
  ztlctl init
  ztlctl init /path/to/vault --name my-research
  ztlctl init . --name lab --client obsidian --tone research-partner --topics "ai,engineering"
  ztlctl init --no-interact --name test --tone minimal /tmp/vault"""


@click.command("init", cls=ZtlCommand, examples=_INIT_EXAMPLES)
@click.argument("path", required=False, default=".")
@click.option("--name", default=None, help="Vault name.")
@click.option(
    "--client",
    type=click.Choice(["obsidian", "vanilla"], case_sensitive=False),
    default=None,
    help="Client application.",
)
@click.option(
    "--tone",
    type=click.Choice(["research-partner", "assistant", "minimal"], case_sensitive=False),
    default=None,
    help="Agent tone.",
)
@click.option("--topics", default=None, help="Comma-separated topic directories.")
@click.option("--no-workflow", is_flag=True, help="Skip workflow setup.")
@click.pass_obj
def init_cmd(
    app: AppContext,
    path: str,
    name: str | None,
    client: str | None,
    tone: str | None,
    topics: str | None,
    no_workflow: bool,
) -> None:
    """Initialize a new ztlctl vault."""
    vault_path = Path(path).resolve()
    interactive = not app.settings.no_interact

    # Interactive prompts for missing options
    if name is None:
        name = (
            click.prompt("Vault name", default=vault_path.name) if interactive else vault_path.name
        )

    if client is None:
        client = (
            click.prompt(
                "Client",
                type=click.Choice(["obsidian", "vanilla"], case_sensitive=False),
                default="obsidian",
            )
            if interactive
            else "obsidian"
        )

    if tone is None:
        tone = (
            click.prompt(
                "Agent tone",
                type=click.Choice(
                    ["research-partner", "assistant", "minimal"], case_sensitive=False
                ),
                default="research-partner",
            )
            if interactive
            else "research-partner"
        )

    topic_list: list[str] = []
    if topics is not None:
        topic_list = [t.strip() for t in topics.split(",") if t.strip()]
    elif interactive:
        raw = click.prompt("Topics (comma-separated, empty for none)", default="")
        topic_list = [t.strip() for t in raw.split(",") if t.strip()]

    from ztlctl.services.init import InitService

    app.emit(
        InitService.init_vault(
            vault_path,
            name=name,
            client=client,
            tone=tone,
            topics=topic_list,
            no_workflow=no_workflow,
        )
    )
