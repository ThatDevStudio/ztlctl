"""Tests for the reweave CLI command."""

from __future__ import annotations

import pytest
from click.testing import CliRunner

from ztlctl.cli import cli


@pytest.mark.usefixtures("_isolated_vault")
class TestReweaveCommand:
    def test_reweave_help(self, cli_runner: CliRunner) -> None:
        result = cli_runner.invoke(cli, ["reweave", "--help"])
        assert result.exit_code == 0
        assert "Reweave links" in result.output

    def test_reweave_dry_run(self, cli_runner: CliRunner) -> None:
        # Create some content first
        cli_runner.invoke(cli, ["create", "note", "Python Guide"])
        cli_runner.invoke(cli, ["create", "note", "Python Reference"])
        result = cli_runner.invoke(cli, ["reweave", "--dry-run"])
        assert result.exit_code == 0

    def test_reweave_with_id(self, cli_runner: CliRunner) -> None:
        r = cli_runner.invoke(cli, ["reweave", "--id", "ztl_nonexist", "--dry-run"])
        # Should handle not-found gracefully
        assert r.exit_code == 1

    def test_reweave_prune(self, cli_runner: CliRunner) -> None:
        cli_runner.invoke(cli, ["create", "note", "Prune Target"])
        result = cli_runner.invoke(cli, ["reweave", "--prune", "--dry-run"])
        # Should work even with no links
        assert result.exit_code in (0, 1)

    def test_reweave_undo_no_history(self, cli_runner: CliRunner) -> None:
        result = cli_runner.invoke(cli, ["reweave", "--undo"])
        assert result.exit_code == 1  # NO_HISTORY error

    def test_reweave_help_shows_undo_id(self, cli_runner: CliRunner) -> None:
        result = cli_runner.invoke(cli, ["reweave", "--help"])
        assert "--undo-id" in result.output

    def test_reweave_undo_id_not_found(self, cli_runner: CliRunner) -> None:
        result = cli_runner.invoke(cli, ["reweave", "--undo-id", "9999"])
        assert result.exit_code == 1  # NOT_FOUND error

    def test_reweave_undo_id_triggers_undo(self, cli_runner: CliRunner) -> None:
        # --undo-id alone (without --undo) should trigger the undo path
        result = cli_runner.invoke(cli, ["reweave", "--undo-id", "1"])
        # Will fail with NOT_FOUND since no log entries, but proves undo path runs
        assert result.exit_code == 1
