"""Tests for the upgrade CLI command."""

from __future__ import annotations

import json

import pytest
from click.testing import CliRunner

from ztlctl.cli import cli


@pytest.mark.usefixtures("_isolated_vault")
class TestUpgradeCommand:
    def test_upgrade_help(self, cli_runner: CliRunner) -> None:
        result = cli_runner.invoke(cli, ["upgrade", "--help"])
        assert result.exit_code == 0
        assert "--check" in result.output

    def test_upgrade_check(self, cli_runner: CliRunner) -> None:
        result = cli_runner.invoke(cli, ["upgrade", "--check"])
        assert result.exit_code == 0
        assert "upgrade" in result.output

    def test_upgrade_check_json(self, cli_runner: CliRunner) -> None:
        result = cli_runner.invoke(cli, ["--json", "upgrade", "--check"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert "pending_count" in data["data"]

    def test_upgrade_apply(self, cli_runner: CliRunner) -> None:
        result = cli_runner.invoke(cli, ["upgrade"])
        assert result.exit_code == 0

    def test_upgrade_apply_json(self, cli_runner: CliRunner) -> None:
        result = cli_runner.invoke(cli, ["--json", "upgrade"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert "applied_count" in data["data"]

    def test_upgrade_examples(self, cli_runner: CliRunner) -> None:
        result = cli_runner.invoke(cli, ["upgrade", "--examples"])
        assert result.exit_code == 0
        assert "upgrade" in result.output
