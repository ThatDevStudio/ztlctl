"""Command group: vault initialization wizard and self/ regeneration."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

import click

from ztlctl.commands._base import DynamicProfileOption, ZtlGroup
from ztlctl.workspace_profiles import DEFAULT_PROFILE, discover_init_profiles

if TYPE_CHECKING:
    from ztlctl.commands._context import AppContext

_INIT_EXAMPLES = """\
  ztlctl init
  ztlctl init --path /path/to/vault --name my-research
  ztlctl init --name lab --profile obsidian --tone research-partner --topics "ai,engineering"
  ztlctl init --name scratch --profile core --tone minimal
  ztlctl init --no-interact --name test --tone minimal"""


class _InitGroup(ZtlGroup):
    """Click Group for init that runs the vault wizard when no subcommand is given."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        kwargs.setdefault("invoke_without_command", True)
        super().__init__(*args, **kwargs)


@click.group(
    "init",
    cls=_InitGroup,
    examples=_INIT_EXAMPLES,
)
@click.option("--path", "vault_path_str", default=".", help="Vault directory (default: cwd).")
@click.option("--name", default=None, help="Vault name.")
@click.option(
    "--profile",
    cls=DynamicProfileOption,
    discovery_scope="init",
    type=str,
    default=None,
    metavar="TEXT",
    help=(
        "Workspace profile. "
        "`none` and `vanilla` remain deprecated compatibility aliases for `core`."
    ),
)
@click.option(
    "--client",
    type=str,
    default=None,
    metavar="TEXT",
    help="Deprecated compatibility alias for --profile.",
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
    vault_path_str: str,
    name: str | None,
    profile: str | None,
    client: str | None,
    tone: str | None,
    topics: str | None,
    no_workflow: bool,
) -> None:
    """Initialize a new ztlctl vault."""
    ctx = click.get_current_context()
    if ctx.invoked_subcommand is not None:
        # A subcommand was specified — let it handle execution.
        return

    vault_path = Path(vault_path_str).resolve()
    interactive = not app.settings.no_interact

    # Interactive prompts for missing options
    if name is None:
        name = (
            click.prompt("Vault name", default=vault_path.name) if interactive else vault_path.name
        )

    if profile is None and client is None:
        profile_choices = discover_init_profiles().ordered_ids()
        profile = (
            click.prompt(
                "Profile",
                type=click.Choice(profile_choices, case_sensitive=False),
                default=DEFAULT_PROFILE,
            )
            if interactive
            else DEFAULT_PROFILE
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

    result = InitService.init_vault(
        vault_path,
        name=name,
        profile=profile,
        client=client,
        tone=tone,
        topics=topic_list,
        no_workflow=no_workflow,
    )
    if client is not None:
        result = result.model_copy(
            update={
                "warnings": [
                    *result.warnings,
                    "The --client flag is deprecated; use --profile instead.",
                ]
            }
        )
    app.emit(result)


# Alias for use in register_commands
init_wizard_group = init_cmd
