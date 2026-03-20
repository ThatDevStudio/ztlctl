"""CLI command generator -- ActionRegistry-driven Click command registration.

Replaces hand-written command files with auto-generated Click commands derived
from ActionDefinitions. ``generate_commands()`` iterates the registry and
builds a ZtlCommand for each non-custom_presentation action, registering it
under the appropriate ZtlGroup.

Mirrors the approach of ``mcp/generator.py`` for the MCP surface.
"""

from __future__ import annotations

import json
from typing import Any

import click

from ztlctl.actions.definitions import ActionDefinition, ActionParam
from ztlctl.commands._base import ZtlCommand, ZtlGroup

# ---------------------------------------------------------------------------
# CLI name derivation
# ---------------------------------------------------------------------------


def _derive_cli_name(action: ActionDefinition) -> str:
    """Derive the Click command name for an ActionDefinition.

    Priority:
    1. Explicit ``action.cli_name`` if set.
    2. Strip ``{cli_group}_`` prefix from action.name if cli_group is set and
       action.name starts with that prefix.
    3. Replace underscores with hyphens in action.name.
    """
    if action.cli_name is not None:
        return action.cli_name
    name = action.name
    if action.cli_group and name.startswith(f"{action.cli_group}_"):
        name = name[len(action.cli_group) + 1 :]
    return name.replace("_", "-")


# ---------------------------------------------------------------------------
# ActionParam -> Click parameter mapping
# ---------------------------------------------------------------------------


def _param_to_click(p: ActionParam) -> click.Parameter:
    """Map one ActionParam to a Click Argument or Option."""
    if p.cli_is_argument:
        return click.Argument([p.name])

    # cli_name overrides the flag name (e.g. cli_name="type" -> --type)
    # while p.name remains the Python kwarg key passed to the handler.
    # When cli_name differs from p.name, pass both to Click so it maps
    # --<cli_name> to the p.name kwarg (e.g. ["--type", "content_type"]).
    flag_name = p.cli_name if p.cli_name is not None else p.name.replace("_", "-")
    option_name = f"--{flag_name}"
    # Param decls: if cli_name differs from p.name, include p.name so Click
    # uses it as the Python kwarg key.
    if p.cli_name is not None and p.cli_name.replace("-", "_") != p.name:
        param_decls = [option_name, p.name]
    else:
        param_decls = [option_name]

    if p.cli_flag:
        return click.Option(
            param_decls,
            is_flag=True,
            default=False,
            help=p.description,
        )

    if p.choices is not None:
        return click.Option(
            param_decls,
            type=click.Choice(list(p.choices)),
            default=p.default,
            required=p.required and p.default is None,
            help=p.description,
        )

    if p.cli_multiple:
        return click.Option(
            param_decls,
            multiple=True,
            default=(),
            help=p.description,
        )

    # dict type -> JSON string input
    if p.type is dict:
        return click.Option(
            param_decls,
            type=click.STRING,
            default=p.default,
            required=p.required and p.default is None,
            help=f"{p.description} [JSON]" if p.description else "[JSON]",
        )

    click_type = {int: click.INT, float: click.FLOAT, bool: click.BOOL}.get(p.type, click.STRING)
    return click.Option(
        param_decls,
        type=click_type,
        default=p.default,
        required=p.required and p.default is None,
        help=p.description,
    )


# ---------------------------------------------------------------------------
# Command factory
# ---------------------------------------------------------------------------


def _make_command(action: ActionDefinition) -> click.Command:
    """Build a ZtlCommand from an ActionDefinition.

    The callback:
    1. Normalizes cli_multiple params: empty tuple () -> None, non-empty -> list.
    2. Parses JSON for dict-typed params.
    3. Calls action.handler(app.vault, **kwargs).
    4. Emits result via app.emit().

    ``@click.pass_obj`` is applied to the callback BEFORE constructing the
    ZtlCommand so Click's context injection works correctly.
    """
    cli_name = _derive_cli_name(action)
    params = [_param_to_click(p) for p in action.params]

    # Identify params that need normalization
    multiple_params = {p.name for p in action.params if p.cli_multiple}
    dict_params = {p.name for p in action.params if p.type is dict}

    @click.pass_obj
    def callback(app: Any, /, **kwargs: Any) -> None:
        # Normalize cli_multiple: () -> None, ("a", "b") -> ["a", "b"]
        for pname in multiple_params:
            if pname in kwargs:
                val = kwargs[pname]
                kwargs[pname] = list(val) if val else None
        # Parse JSON for dict-typed params
        for pname in dict_params:
            if pname in kwargs and isinstance(kwargs[pname], str):
                kwargs[pname] = json.loads(kwargs[pname])

        result = action.handler(app.vault, **kwargs)
        app.emit(result)

    # Set __name__ for Click introspection
    callback.__name__ = cli_name.replace("-", "_")

    return ZtlCommand(
        name=cli_name,
        callback=callback,
        params=params,
        help=action.description,
        examples=action.cli_examples or None,
    )


# ---------------------------------------------------------------------------
# Group help text
# ---------------------------------------------------------------------------

_GROUP_HELP: dict[str, str] = {
    "query": "Search, list, and query vault content.",
    "graph": "Traverse and analyze the knowledge graph.",
    "session": "Manage sessions, context, and agent workflows.",
    "create": "Create notes, references, and tasks.",
    "check": "Check vault integrity and repair issues.",
    "ingest": "Ingest text and source material into the vault.",
    "export": "Export vault content and dashboards.",
    "vector": "Manage semantic search indexing.",
    "upgrade": "Run pending database migrations.",
    "reweave": "Densify the knowledge graph with links.",
    "init": "Initialize and manage vault configuration.",
}


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def generate_commands(cli: click.Group) -> None:
    """Register all non-custom_presentation actions as Click commands.

    Iterates ``get_action_registry().list_actions(custom_presentation=False)``,
    creates a ZtlCommand for each, and registers under the appropriate group
    (or directly on ``cli`` if ``cli_group`` is ``None``).

    Groups are created lazily and stored in a local dict to avoid duplicates.
    """
    import ztlctl.actions  # noqa: F401 — triggers _register_core_actions()
    from ztlctl.actions.registry import get_action_registry

    registry = get_action_registry()
    groups: dict[str, ZtlGroup] = {}

    for action in registry.list_actions(custom_presentation=False):
        cmd = _make_command(action)
        group_name = action.cli_group

        if group_name is None:
            cli.add_command(cmd)
        else:
            if group_name not in groups:
                groups[group_name] = ZtlGroup(
                    name=group_name,
                    help=_GROUP_HELP.get(group_name, ""),
                )
                cli.add_command(groups[group_name])
            groups[group_name].add_command(cmd)
