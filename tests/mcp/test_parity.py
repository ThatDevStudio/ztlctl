"""Parity tests — every ActionDefinition has a corresponding MCP tool.

These tests verify that ``generate_tools()`` produces a 1-to-1 mapping
between the ActionRegistry and registered MCP tools.  Previously missing
tools (archive, supersede, upgrade actions, etc.) are confirmed present.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

from ztlctl.actions.registry import get_action_registry
from ztlctl.mcp.generator import generate_tools

# ---------------------------------------------------------------------------
# DummyServer (same pattern as test_generator.py)
# ---------------------------------------------------------------------------


class DummyServer:
    def __init__(self) -> None:
        self.tools: dict[str, Any] = {}

    def tool(self) -> Any:
        def decorator(fn: Any) -> Any:
            self.tools[fn.__name__] = fn
            return fn

        return decorator


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def parity_server() -> tuple[DummyServer, Any]:
    """DummyServer populated with all ActionRegistry tools."""
    server = DummyServer()
    vault = MagicMock()
    vault.plugin_manager = None
    generate_tools(server, vault)
    registry = get_action_registry()
    return server, registry


# ---------------------------------------------------------------------------
# Previously missing tools
# ---------------------------------------------------------------------------

# These tools were absent from the old 30-tool hand-written mcp/tools.py.
# Their ActionRegistry names (which the generator now uses) are listed here.
PREVIOUSLY_MISSING = {
    "archive",  # previously missing — now auto-generated from registry
    "supersede",  # previously missing — now auto-generated from registry
    "apply",  # upgrade_apply in plan docs → registry name "apply"
    "check_pending",  # upgrade_check_pending → registry name "check_pending"
    "stamp_current",  # upgrade_stamp_current → registry name "stamp_current"
    "check",  # check_integrity → registry name "check"
    "init_vault",  # previously missing — now auto-generated from registry
    "init_workflow",  # previously missing — now auto-generated from registry
    "update_workflow",  # previously missing — now auto-generated from registry
}


# ---------------------------------------------------------------------------
# Parity tests
# ---------------------------------------------------------------------------


def test_all_actions_have_mcp_tools(parity_server: tuple[DummyServer, Any]) -> None:
    """Every action in the registry has a matching registered MCP tool."""
    server, registry = parity_server
    registry_names = {a.name for a in registry.list_actions()}
    tool_names = set(server.tools.keys())
    assert registry_names <= tool_names, f"Actions without MCP tools: {registry_names - tool_names}"
    assert len(registry_names) >= 60, f"Expected >= 60 actions, got {len(registry_names)}"


def test_tool_count_matches_registry(parity_server: tuple[DummyServer, Any]) -> None:
    """Tool count equals registry action count."""
    server, registry = parity_server
    assert len(server.tools) == len(registry.list_actions()), (
        f"Tool count {len(server.tools)} != registry count {len(registry.list_actions())}"
    )


def test_previously_missing_tools_present(parity_server: tuple[DummyServer, Any]) -> None:
    """Tools that were absent from the old hand-written surface are now present."""
    server, _ = parity_server
    missing = {name for name in PREVIOUSLY_MISSING if name not in server.tools}
    assert not missing, f"Still missing tools: {missing}"


def test_every_tool_has_doc(parity_server: tuple[DummyServer, Any]) -> None:
    """Every registered MCP tool has a non-empty docstring."""
    server, _ = parity_server
    for name, fn in server.tools.items():
        assert fn.__doc__ is not None and len(fn.__doc__) > 0, f"Tool '{name}' has no docstring"


def test_every_tool_has_annotations(parity_server: tuple[DummyServer, Any]) -> None:
    """Every registered MCP tool has __annotations__ with at least 'return' key."""
    server, _ = parity_server
    for name, fn in server.tools.items():
        assert "return" in fn.__annotations__, f"Tool '{name}' missing 'return' in __annotations__"


def test_category_coverage(parity_server: tuple[DummyServer, Any]) -> None:
    """All 17 action categories produce at least one registered MCP tool."""
    server, registry = parity_server
    categories = {a.category for a in registry.list_actions()}
    assert len(categories) == 17, f"Expected 17 categories, got {len(categories)}: {categories}"
    tool_names = set(server.tools.keys())
    for category in categories:
        cat_actions = {a.name for a in registry.list_actions(category=category)}
        covered = cat_actions & tool_names
        assert covered, f"Category '{category}' has no registered MCP tools"


def test_cli_and_mcp_cover_same_actions() -> None:
    """CLI and MCP surfaces both cover all ActionDefinitions.

    - MCP surface: generate_tools() covers every action in the registry.
    - CLI surface: generate_commands() covers every non-custom action;
      custom_presentation actions are wired via hand-written commands.
    Together they prove both surfaces derive from a single source of truth.
    """
    import click

    import ztlctl.actions  # noqa: F401 — populate registry
    from ztlctl.commands.generator import generate_commands
    from ztlctl.mcp.generator import generate_tools

    registry = get_action_registry()
    all_action_names = {a.name for a in registry.list_actions()}

    # MCP: every action maps to a tool
    mcp_server = DummyServer()
    from unittest.mock import MagicMock

    vault = MagicMock()
    vault.plugin_manager = None
    generate_tools(mcp_server, vault)
    mcp_names = set(mcp_server.tools.keys())
    assert all_action_names <= mcp_names, (
        f"Actions not in MCP surface: {all_action_names - mcp_names}"
    )

    # CLI: every non-custom action maps to a generated command
    cli_group = click.Group(name="ztlctl")
    generate_commands(cli_group)
    generated_cmds: set[str] = set()
    for name, cmd in cli_group.commands.items():
        if isinstance(cmd, click.Group):
            ctx = click.Context(cmd)
            for sub_name in cmd.list_commands(ctx):
                generated_cmds.add(f"{name}.{sub_name}")
        else:
            generated_cmds.add(name)

    non_custom = registry.list_actions(custom_presentation=False)
    for action in non_custom:
        from ztlctl.commands.generator import _derive_cli_name

        cli_name = _derive_cli_name(action)
        key = f"{action.cli_group}.{cli_name}" if action.cli_group else cli_name
        assert key in generated_cmds, (
            f"Action {action.name!r} not in generated CLI commands. "
            f"Expected key {key!r} in {sorted(generated_cmds)}"
        )
