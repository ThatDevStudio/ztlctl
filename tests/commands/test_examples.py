"""Tests for --examples flag on CLI commands."""

from __future__ import annotations

import pytest
from click.testing import CliRunner

from ztlctl.cli import cli


class TestExamplesFlag:
    """Test that --examples works on all commands that define examples."""

    def test_create_group_examples(self, cli_runner: CliRunner) -> None:
        result = cli_runner.invoke(cli, ["create", "--examples"])
        assert result.exit_code == 0
        assert "Examples for 'cli create'" in result.output
        assert "ztlctl create note" in result.output

    def test_create_note_examples(self, cli_runner: CliRunner) -> None:
        result = cli_runner.invoke(cli, ["create", "note", "--examples"])
        assert result.exit_code == 0
        assert "Examples for 'cli create note'" in result.output
        assert "--subtype decision" in result.output

    def test_create_reference_examples(self, cli_runner: CliRunner) -> None:
        result = cli_runner.invoke(cli, ["create", "reference", "--examples"])
        assert result.exit_code == 0
        assert "ztlctl create reference" in result.output

    def test_create_task_examples(self, cli_runner: CliRunner) -> None:
        result = cli_runner.invoke(cli, ["create", "task", "--examples"])
        assert result.exit_code == 0
        assert "--priority high" in result.output

    def test_create_batch_examples(self, cli_runner: CliRunner) -> None:
        result = cli_runner.invoke(cli, ["create", "batch", "--examples"])
        assert result.exit_code == 0
        assert "--partial" in result.output

    def test_query_group_examples(self, cli_runner: CliRunner) -> None:
        result = cli_runner.invoke(cli, ["query", "--examples"])
        assert result.exit_code == 0
        assert "ztlctl query search" in result.output
        assert "ztlctl query list" in result.output

    def test_query_search_examples(self, cli_runner: CliRunner) -> None:
        result = cli_runner.invoke(cli, ["query", "search", "--examples"])
        assert result.exit_code == 0
        assert "--rank-by recency" in result.output

    def test_query_list_examples(self, cli_runner: CliRunner) -> None:
        result = cli_runner.invoke(cli, ["query", "list", "--examples"])
        assert result.exit_code == 0
        assert "--sort priority" in result.output
        assert "--include-archived" in result.output

    def test_query_work_queue_examples(self, cli_runner: CliRunner) -> None:
        result = cli_runner.invoke(cli, ["query", "work-queue", "--examples"])
        assert result.exit_code == 0
        assert "ztlctl query work-queue" in result.output

    def test_query_decision_support_examples(self, cli_runner: CliRunner) -> None:
        result = cli_runner.invoke(cli, ["query", "decision-support", "--examples"])
        assert result.exit_code == 0
        assert "--topic architecture" in result.output

    def test_graph_group_examples(self, cli_runner: CliRunner) -> None:
        result = cli_runner.invoke(cli, ["graph", "--examples"])
        assert result.exit_code == 0
        assert "ztlctl graph related" in result.output
        assert "ztlctl graph themes" in result.output

    def test_graph_related_examples(self, cli_runner: CliRunner) -> None:
        result = cli_runner.invoke(cli, ["graph", "related", "--examples"])
        assert result.exit_code == 0
        assert "--depth 3" in result.output

    def test_graph_path_examples(self, cli_runner: CliRunner) -> None:
        result = cli_runner.invoke(cli, ["graph", "path", "--examples"])
        assert result.exit_code == 0
        assert "ztlctl graph path" in result.output

    def test_agent_group_examples(self, cli_runner: CliRunner) -> None:
        result = cli_runner.invoke(cli, ["agent", "--examples"])
        assert result.exit_code == 0
        assert "ztlctl agent session start" in result.output

    def test_agent_session_start_examples(self, cli_runner: CliRunner) -> None:
        result = cli_runner.invoke(cli, ["agent", "session", "start", "--examples"])
        assert result.exit_code == 0
        assert "ztlctl agent session start" in result.output

    def test_check_examples(self, cli_runner: CliRunner) -> None:
        result = cli_runner.invoke(cli, ["check", "--examples"])
        assert result.exit_code == 0
        assert "ztlctl check --fix" in result.output
        assert "ztlctl check --rebuild" in result.output

    def test_reweave_examples(self, cli_runner: CliRunner) -> None:
        result = cli_runner.invoke(cli, ["reweave", "--examples"])
        assert result.exit_code == 0
        assert "--dry-run" in result.output
        assert "--undo-id 42" in result.output

    def test_update_examples(self, cli_runner: CliRunner) -> None:
        result = cli_runner.invoke(cli, ["update", "--examples"])
        assert result.exit_code == 0
        assert "--title" in result.output
        assert "--maturity seed" in result.output

    def test_archive_examples(self, cli_runner: CliRunner) -> None:
        result = cli_runner.invoke(cli, ["archive", "--examples"])
        assert result.exit_code == 0
        assert "ztlctl archive" in result.output

    def test_supersede_examples(self, cli_runner: CliRunner) -> None:
        result = cli_runner.invoke(cli, ["supersede", "--examples"])
        assert result.exit_code == 0
        assert "ztlctl supersede" in result.output


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
