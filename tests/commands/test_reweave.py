"""Tests for the reweave CLI command group."""

from __future__ import annotations

import json

import pytest
from click.testing import CliRunner

from ztlctl.cli import cli


@pytest.mark.usefixtures("_isolated_vault")
class TestReweaveCommand:
    def test_reweave_dry_run(self, cli_runner: CliRunner) -> None:
        # Create some content first
        cli_runner.invoke(cli, ["create", "note", "Python Guide"])
        cli_runner.invoke(cli, ["create", "note", "Python Reference"])
        result = cli_runner.invoke(cli, ["reweave", "run", "--dry-run"])
        assert result.exit_code == 0

    def test_reweave_with_id(self, cli_runner: CliRunner) -> None:
        r = cli_runner.invoke(cli, ["reweave", "run", "--content-id", "ztl_nonexist", "--dry-run"])
        # Should handle not-found gracefully
        assert r.exit_code == 1

    def test_reweave_prune(self, cli_runner: CliRunner) -> None:
        cli_runner.invoke(cli, ["create", "note", "Prune Target"])
        result = cli_runner.invoke(cli, ["reweave", "prune", "--dry-run"])
        # Should work even with no links
        assert result.exit_code in (0, 1)

    def test_reweave_undo_no_history(self, cli_runner: CliRunner) -> None:
        result = cli_runner.invoke(cli, ["reweave", "undo"])
        assert result.exit_code == 1  # NO_HISTORY error

    def test_reweave_undo_id_not_found(self, cli_runner: CliRunner) -> None:
        result = cli_runner.invoke(cli, ["reweave", "undo", "--reweave-id", "9999"])
        assert result.exit_code == 1  # NOT_FOUND error

    def test_reweave_undo_id_triggers_undo(self, cli_runner: CliRunner) -> None:
        # --reweave-id alone should trigger the undo path
        result = cli_runner.invoke(cli, ["reweave", "undo", "--reweave-id", "1"])
        # Will fail with NOT_FOUND since no log entries, but proves undo path runs
        assert result.exit_code == 1


@pytest.mark.usefixtures("_isolated_vault")
class TestReweaveRun:
    """Tests for the reweave run subcommand."""

    def test_reweave_run_dry_run(self, cli_runner: CliRunner) -> None:
        """reweave run --dry-run shows suggestions without applying."""
        cli_runner.invoke(cli, ["create", "note", "Dry Guide"])
        cli_runner.invoke(cli, ["create", "note", "Dry Reference"])
        result = cli_runner.invoke(cli, ["reweave", "run", "--dry-run"])
        assert result.exit_code == 0

    def test_reweave_run_no_interact(self, cli_runner: CliRunner) -> None:
        """--no-interact global flag applies reweave without prompting."""
        cli_runner.invoke(cli, ["create", "note", "NI Guide"])
        cli_runner.invoke(cli, ["create", "note", "NI Reference"])
        result = cli_runner.invoke(cli, ["--no-interact", "reweave", "run"])
        assert result.exit_code == 0

    def test_reweave_run_dry_run_json_no_candidates(self, cli_runner: CliRunner) -> None:
        cli_runner.invoke(cli, ["create", "note", "Lonely Reweave Note"])

        result = cli_runner.invoke(cli, ["--json", "reweave", "run", "--dry-run"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["data"]["count"] == 0
        assert data["data"]["dry_run"] is True
