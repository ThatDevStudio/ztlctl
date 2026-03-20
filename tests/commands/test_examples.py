"""Tests for --examples flag on CLI commands.

Parametrized to cover all commands that define examples text.
"""

from __future__ import annotations

import pytest
from click.testing import CliRunner

from ztlctl.cli import cli

# (CLI args, expected keywords in output)
EXAMPLES_COMMANDS: list[tuple[list[str], list[str]]] = [
    # -- create (batch is the only hand-written command with examples) --
    (["create", "batch", "--examples"], ["--partial"]),
    # -- workflow (fully hand-written, has examples) --
    (["workflow", "--examples"], ["ztlctl workflow init", "ztlctl workflow update"]),
    (["workflow", "init", "--examples"], ["--profile obsidian"]),
    (["workflow", "update", "--examples"], ["--skill-set minimal"]),
    (["workflow", "export", "--examples"], ["--client both"]),
    (["workflow", "validate", "--examples"], ["--client claude"]),
    # -- standalone hand-written commands with examples --
    (["update", "--examples"], ["--title", "--maturity seed"]),
    (["init", "--examples"], ["ztlctl init"]),
    (["garden", "seed", "--examples"], ["garden seed"]),
    (["serve", "--examples"], ["ztlctl serve"]),
]


def _examples_id(item: tuple[list[str], list[str]]) -> str:
    """Generate a readable test ID from args."""
    args, _ = item
    return "_".join(a for a in args if a != "--examples")


@pytest.mark.parametrize(
    "args,expected_keywords",
    EXAMPLES_COMMANDS,
    ids=[_examples_id(item) for item in EXAMPLES_COMMANDS],
)
def test_examples_flag(
    cli_runner: CliRunner, args: list[str], expected_keywords: list[str]
) -> None:
    result = cli_runner.invoke(cli, args)
    assert result.exit_code == 0
    for kw in expected_keywords:
        assert kw in result.output, f"Expected '{kw}' in examples output for {args}"


class TestExamplesInHelp:
    """Test that --examples appears in --help output for commands that have it."""

    @pytest.mark.parametrize(
        "args",
        [
            # Hand-written commands that still have --examples
            ["workflow", "--help"],
            ["workflow", "init", "--help"],
            ["workflow", "update", "--help"],
            ["workflow", "export", "--help"],
            ["workflow", "validate", "--help"],
            ["create", "batch", "--help"],
            ["update", "--help"],
            ["init", "--help"],
            ["serve", "--help"],
        ],
    )
    def test_examples_in_help(self, cli_runner: CliRunner, args: list[str]) -> None:
        result = cli_runner.invoke(cli, args)
        assert result.exit_code == 0
        assert "--examples" in result.output


class TestExamplesEagerExit:
    """Test that --examples exits before validation (eager option)."""

    def test_examples_skips_required_args(self, cli_runner: CliRunner) -> None:
        # 'update' requires CONTENT_ID, but --examples should work without it
        result = cli_runner.invoke(cli, ["update", "--examples"])
        assert result.exit_code == 0
        assert "Examples for" in result.output

    def test_examples_skips_required_args_init(self, cli_runner: CliRunner) -> None:
        """init is a wizard group — --examples exits immediately."""
        result = cli_runner.invoke(cli, ["init", "--examples"])
        assert result.exit_code == 0
