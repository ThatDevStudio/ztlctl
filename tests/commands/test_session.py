"""Tests for the agent session CLI commands."""

from __future__ import annotations

import pytest
from click.testing import CliRunner

from ztlctl.cli import cli


@pytest.mark.usefixtures("_isolated_vault")
class TestSessionCommands:
    def test_session_start(self, cli_runner: CliRunner) -> None:
        result = cli_runner.invoke(cli, ["agent", "session", "start", "My Topic"])
        assert result.exit_code == 0
        assert "session_start" in result.output

    def test_session_start_json(self, cli_runner: CliRunner) -> None:
        result = cli_runner.invoke(cli, ["--json", "agent", "session", "start", "JSON Topic"])
        assert result.exit_code == 0
        import json

        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["data"]["id"].startswith("LOG-")

    def test_session_close(self, cli_runner: CliRunner) -> None:
        # Start first
        cli_runner.invoke(cli, ["agent", "session", "start", "Close Topic"])
        result = cli_runner.invoke(cli, ["agent", "session", "close"])
        assert result.exit_code == 0

    def test_session_close_no_active(self, cli_runner: CliRunner) -> None:
        result = cli_runner.invoke(cli, ["agent", "session", "close"])
        assert result.exit_code == 1

    def test_session_reopen(self, cli_runner: CliRunner) -> None:
        import json

        # Start with JSON to get the session ID
        start_result = cli_runner.invoke(
            cli, ["--json", "agent", "session", "start", "Reopen Topic"]
        )
        assert start_result.exit_code == 0
        session_id = json.loads(start_result.output)["data"]["id"]

        cli_runner.invoke(cli, ["agent", "session", "close"])
        result = cli_runner.invoke(cli, ["agent", "session", "reopen", session_id])
        assert result.exit_code == 0

    def test_session_reopen_not_found(self, cli_runner: CliRunner) -> None:
        result = cli_runner.invoke(cli, ["agent", "session", "reopen", "LOG-9999"])
        assert result.exit_code == 1
