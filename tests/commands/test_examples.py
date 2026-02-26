"""Tests for --examples flag on CLI commands.

Parametrized to cover all commands that define examples text.
"""

from __future__ import annotations

import pytest
from click.testing import CliRunner

from ztlctl.cli import cli

# (CLI args, expected keywords in output)
EXAMPLES_COMMANDS: list[tuple[list[str], list[str]]] = [
    # -- create --
    (["create", "--examples"], ["ztlctl create note"]),
    (["create", "note", "--examples"], ["--subtype decision"]),
    (["create", "reference", "--examples"], ["ztlctl create reference"]),
    (["create", "task", "--examples"], ["--priority high"]),
    (["create", "batch", "--examples"], ["--partial"]),
    # -- query --
    (["query", "--examples"], ["ztlctl query search", "ztlctl query list"]),
    (["query", "search", "--examples"], ["--rank-by recency"]),
    (["query", "list", "--examples"], ["--sort priority", "--include-archived"]),
    (["query", "work-queue", "--examples"], ["ztlctl query work-queue"]),
    (["query", "decision-support", "--examples"], ["--topic architecture"]),
    # -- graph --
    (["graph", "--examples"], ["ztlctl graph related", "ztlctl graph themes"]),
    (["graph", "related", "--examples"], ["--depth 3"]),
    (["graph", "path", "--examples"], ["ztlctl graph path"]),
    # -- agent --
    (["agent", "--examples"], ["ztlctl agent session start"]),
    (["agent", "session", "start", "--examples"], ["ztlctl agent session start"]),
    (["agent", "session", "cost", "--examples"], []),
    (["agent", "session", "log", "--examples"], []),
    (["agent", "context", "--examples"], []),
    (["agent", "brief", "--examples"], []),
    (["agent", "regenerate", "--examples"], ["ztlctl agent regenerate"]),
    # -- standalone commands --
    (["check", "--examples"], ["ztlctl check --fix", "ztlctl check --rebuild"]),
    (["reweave", "--examples"], ["--dry-run", "--undo-id 42"]),
    (["update", "--examples"], ["--title", "--maturity seed"]),
    (["archive", "--examples"], ["ztlctl archive"]),
    (["supersede", "--examples"], ["ztlctl supersede"]),
    (["init", "--examples"], ["ztlctl init"]),
    (["export", "--examples"], ["ztlctl export"]),
    (["garden", "seed", "--examples"], ["garden seed"]),
    (["serve", "--examples"], ["ztlctl serve"]),
    (["extract", "--examples"], ["extract"]),
    (["upgrade", "--examples"], ["upgrade"]),
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
            ["create", "--help"],
            ["create", "note", "--help"],
            ["query", "--help"],
            ["query", "list", "--help"],
            ["graph", "--help"],
            ["graph", "related", "--help"],
            ["check", "--help"],
            ["reweave", "--help"],
            ["update", "--help"],
            ["archive", "--help"],
            ["supersede", "--help"],
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

    def test_examples_skips_required_args_archive(self, cli_runner: CliRunner) -> None:
        result = cli_runner.invoke(cli, ["archive", "--examples"])
        assert result.exit_code == 0

    def test_examples_skips_required_args_supersede(self, cli_runner: CliRunner) -> None:
        result = cli_runner.invoke(cli, ["supersede", "--examples"])
        assert result.exit_code == 0
