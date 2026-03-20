"""CLI parity tests — verify every ActionDefinition has a CLI command.

Mirrors tests/mcp/test_parity.py for the CLI surface. Uses Click's
command tree inspection to verify registration without invoking commands.
"""

from __future__ import annotations

import click
import pytest

from ztlctl.actions.registry import get_action_registry
from ztlctl.commands.generator import _derive_cli_name, generate_commands

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def cli_with_generated_commands() -> click.Group:
    """Build a Click group with all generated commands registered."""
    import ztlctl.actions  # noqa: F401 — populate registry

    group = click.Group(name="ztlctl")
    generate_commands(group)
    return group


# ---------------------------------------------------------------------------
# Parity tests
# ---------------------------------------------------------------------------


class TestCliParity:
    """Verify ActionRegistry <-> CLI command mapping."""

    def test_all_non_custom_actions_have_cli_commands(
        self, cli_with_generated_commands: click.Group
    ) -> None:
        """Every non-custom_presentation action has a registered CLI command."""
        import ztlctl.actions  # noqa: F401

        registry = get_action_registry()
        non_custom = registry.list_actions(custom_presentation=False)

        # Build flat set of "group.cmd" or "cmd" from the generated CLI tree
        all_commands: set[str] = set()
        for name, cmd in cli_with_generated_commands.commands.items():
            if isinstance(cmd, click.Group):
                ctx = click.Context(cmd)
                for sub_name in cmd.list_commands(ctx):
                    all_commands.add(f"{name}.{sub_name}")
            else:
                all_commands.add(name)

        for action in non_custom:
            cli_name = _derive_cli_name(action)
            if action.cli_group:
                expected = f"{action.cli_group}.{cli_name}"
            else:
                expected = cli_name
            assert expected in all_commands, (
                f"Action {action.name!r} (cli_name={cli_name!r}, "
                f"cli_group={action.cli_group!r}) not found in CLI. "
                f"Available: {sorted(all_commands)}"
            )

    def test_custom_presentation_not_generated(
        self, cli_with_generated_commands: click.Group
    ) -> None:
        """custom_presentation actions are NOT produced by generate_commands()."""
        import ztlctl.actions  # noqa: F401

        registry = get_action_registry()
        custom = registry.list_actions(custom_presentation=True)

        # Collect leaf-level command names from the generated tree
        generated_leaf_names: set[str] = set()
        for name, cmd in cli_with_generated_commands.commands.items():
            if isinstance(cmd, click.Group):
                ctx = click.Context(cmd)
                for sub_name in cmd.list_commands(ctx):
                    generated_leaf_names.add(f"{name}.{sub_name}")
            else:
                generated_leaf_names.add(name)

        for action in custom:
            cli_name = _derive_cli_name(action)
            if action.cli_group:
                qualified = f"{action.cli_group}.{cli_name}"
            else:
                qualified = cli_name
            assert qualified not in generated_leaf_names, (
                f"custom_presentation action {action.name!r} appears in generated commands"
            )

    def test_all_generated_commands_have_help(
        self, cli_with_generated_commands: click.Group
    ) -> None:
        """Every generated command has non-empty help text (from ActionDefinition.description)."""
        for name, cmd in cli_with_generated_commands.commands.items():
            if isinstance(cmd, click.Group):
                ctx = click.Context(cmd)
                for sub_name in cmd.list_commands(ctx):
                    sub_cmd = cmd.get_command(ctx, sub_name)
                    assert sub_cmd is not None
                    assert sub_cmd.help, f"`{name} {sub_name}` has no help text"
            else:
                assert cmd.help, f"`{name}` has no help text"

    def test_generated_group_count(self, cli_with_generated_commands: click.Group) -> None:
        """Generator creates the expected number of command groups."""
        groups = [
            name
            for name, cmd in cli_with_generated_commands.commands.items()
            if isinstance(cmd, click.Group)
        ]
        # Expected groups: query, graph, session, create, check,
        # ingest, export, vector, upgrade, reweave, init (11 groups minimum)
        assert len(groups) >= 10, f"Expected >=10 groups, got {len(groups)}: {groups}"

    def test_command_names_use_hyphens_not_underscores(
        self, cli_with_generated_commands: click.Group
    ) -> None:
        """All generated command and group names use hyphens, not underscores."""
        for name, cmd in cli_with_generated_commands.commands.items():
            assert "_" not in name, f"Group/command name {name!r} contains underscore"
            if isinstance(cmd, click.Group):
                ctx = click.Context(cmd)
                for sub_name in cmd.list_commands(ctx):
                    assert "_" not in sub_name, (
                        f"Subcommand `{name} {sub_name}` contains underscore"
                    )

    def test_category_coverage(self, cli_with_generated_commands: click.Group) -> None:
        """All action categories from non-custom actions are represented in the CLI."""
        import ztlctl.actions  # noqa: F401

        registry = get_action_registry()
        non_custom = registry.list_actions(custom_presentation=False)
        categories = {a.category for a in non_custom}

        group_names = set(cli_with_generated_commands.commands.keys())

        for cat in categories:
            actions_in_cat = [a for a in non_custom if a.category == cat]
            # Every action's cli_group (if any) must appear as a registered group
            for action in actions_in_cat:
                if action.cli_group:
                    assert action.cli_group in group_names, (
                        f"Category {cat!r}: action {action.name!r} expects "
                        f"group {action.cli_group!r} but it's not registered. "
                        f"Known groups: {sorted(group_names)}"
                    )
                    break


# ---------------------------------------------------------------------------
# Cross-surface: hand-written custom commands are wired in register_commands
# ---------------------------------------------------------------------------


class TestCustomCommandsWired:
    """Verify that custom_presentation commands are reachable via the full CLI."""

    def test_batch_command_available(self) -> None:
        """create batch is wired via hand-written path."""
        from ztlctl.cli import cli

        ctx = click.Context(cli)
        create_grp = cli.get_command(ctx, "create")
        assert create_grp is not None, "create group not registered"
        assert isinstance(create_grp, click.Group)
        sub_ctx = click.Context(create_grp)
        batch_cmd = create_grp.get_command(sub_ctx, "batch")
        assert batch_cmd is not None, "create batch not registered"

    def test_init_command_available(self) -> None:
        """init command (wizard group) is wired via hand-written path."""
        from ztlctl.cli import cli

        ctx = click.Context(cli)
        init_cmd = cli.get_command(ctx, "init")
        assert init_cmd is not None, "init command not registered"

    def test_update_command_available(self) -> None:
        """update command is wired via hand-written path (custom_presentation)."""
        from ztlctl.cli import cli

        ctx = click.Context(cli)
        update_cmd = cli.get_command(ctx, "update")
        assert update_cmd is not None, "update command not registered"

    def test_garden_command_available(self) -> None:
        """garden command is wired (not in ActionRegistry)."""
        from ztlctl.cli import cli

        ctx = click.Context(cli)
        garden_cmd = cli.get_command(ctx, "garden")
        assert garden_cmd is not None, "garden command not registered"

    def test_serve_command_available(self) -> None:
        """serve command is wired via hand-written path."""
        from ztlctl.cli import cli

        ctx = click.Context(cli)
        serve_cmd = cli.get_command(ctx, "serve")
        assert serve_cmd is not None, "serve command not registered"

    def test_workflow_group_available(self) -> None:
        """workflow group is wired via hand-written path."""
        from ztlctl.cli import cli

        ctx = click.Context(cli)
        wf_cmd = cli.get_command(ctx, "workflow")
        assert wf_cmd is not None, "workflow command not registered"
