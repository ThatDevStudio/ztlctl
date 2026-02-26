"""Tests for agent CLI commands (regenerate)."""

from __future__ import annotations

import json

import pytest
from click.testing import CliRunner

from ztlctl.cli import cli


@pytest.mark.usefixtures("_isolated_vault")
class TestAgentRegenerate:
    """Tests for `agent regenerate` subcommand."""

    def test_regenerate_succeeds(self, cli_runner: CliRunner) -> None:
        result = cli_runner.invoke(cli, ["agent", "regenerate"])
        assert result.exit_code == 0
        assert "regenerate_self" in result.output

    def test_regenerate_json(self, cli_runner: CliRunner) -> None:
        result = cli_runner.invoke(cli, ["--json", "agent", "regenerate"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["op"] == "regenerate_self"
        assert "files_written" in data["data"]
