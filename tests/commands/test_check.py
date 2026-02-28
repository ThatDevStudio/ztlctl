"""Tests for check CLI command."""

from __future__ import annotations

import json

import pytest
from click.testing import CliRunner

from ztlctl.cli import cli


@pytest.mark.usefixtures("_isolated_vault")
class TestCheckCommand:
    def test_check_no_flags(self, cli_runner: CliRunner) -> None:
        """Default check reports issues (or zero)."""
        result = cli_runner.invoke(cli, ["check"])
        assert result.exit_code == 0
        assert "OK" in result.output

    def test_check_json_output(self, cli_runner: CliRunner) -> None:
        """JSON output includes issue count."""
        result = cli_runner.invoke(cli, ["--json", "check"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert "count" in data["data"]
        assert "error_count" in data["data"]
        assert "warning_count" in data["data"]
        assert "healthy" in data["data"]

    def test_check_fix(self, cli_runner: CliRunner) -> None:
        """--fix flag runs repair."""
        result = cli_runner.invoke(cli, ["--json", "check", "--fix"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["op"] == "fix"

    def test_check_fix_aggressive(self, cli_runner: CliRunner) -> None:
        """--fix --level aggressive runs aggressive repair."""
        result = cli_runner.invoke(cli, ["--json", "check", "--fix", "--level", "aggressive"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True

    def test_check_rebuild(self, cli_runner: CliRunner) -> None:
        """--rebuild flag runs full rebuild."""
        result = cli_runner.invoke(cli, ["--json", "check", "--rebuild"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["op"] == "rebuild"
        assert "nodes_indexed" in data["data"]

    def test_check_rollback_no_backup(self, cli_runner: CliRunner) -> None:
        """--rollback with no backups fails."""
        result = cli_runner.invoke(cli, ["--json", "check", "--rollback"])
        assert result.exit_code == 1
        assert result.stdout == ""
        payload = json.loads(result.stderr)
        assert payload["ok"] is False
        assert payload["op"] == "rollback"
        assert payload["error"]["code"] == "NO_BACKUPS"

    def test_check_errors_only_filters_warning_issues(self, cli_runner: CliRunner) -> None:
        cli_runner.invoke(cli, ["--json", "create", "note", "Warning Note", "--tags", "unscoped"])

        result = cli_runner.invoke(cli, ["--json", "check", "--errors-only"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["data"]["count"] == 0
        assert data["data"]["error_count"] == 0
        assert data["data"]["warning_count"] == 0
        assert data["data"]["healthy"] is True
        assert data["data"]["issues"] == []

    def test_check_warning_only_vault_reports_healthy(self, cli_runner: CliRunner) -> None:
        cli_runner.invoke(cli, ["create", "note", "Warning Note", "--tags", "unscoped"])

        result = cli_runner.invoke(cli, ["--json", "check"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["data"]["count"] > 0
        assert data["data"]["error_count"] == 0
        assert data["data"]["warning_count"] == data["data"]["count"]
        assert data["data"]["healthy"] is True

    def test_check_warning_only_human_output_marks_advisory(self, cli_runner: CliRunner) -> None:
        cli_runner.invoke(cli, ["create", "note", "Warning Note", "--tags", "unscoped"])

        result = cli_runner.invoke(cli, ["check"])

        assert result.exit_code == 0
        assert "No errors found; advisory warnings listed below." in result.output
