"""Tests for the extract CLI command."""

from __future__ import annotations

import json

import pytest
from click.testing import CliRunner

from ztlctl.cli import cli


@pytest.mark.usefixtures("_isolated_vault")
class TestExtractCommand:
    def test_extract_help(self, cli_runner: CliRunner) -> None:
        result = cli_runner.invoke(cli, ["extract", "--help"])
        assert result.exit_code == 0
        assert "SESSION_ID" in result.output
        assert "--title" in result.output

    def test_extract_basic(self, cli_runner: CliRunner) -> None:
        # Start session, log entries, close, then extract
        start = cli_runner.invoke(cli, ["--json", "agent", "session", "start", "Auth design"])
        session_id = json.loads(start.output)["data"]["id"]
        cli_runner.invoke(cli, ["agent", "session", "log", "Key finding", "--pin"])
        cli_runner.invoke(cli, ["agent", "session", "log", "Minor note"])
        cli_runner.invoke(cli, ["agent", "session", "close"])

        result = cli_runner.invoke(cli, ["--json", "extract", session_id])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["op"] == "extract_decision"
        assert data["data"]["session_id"] == session_id

    def test_extract_with_title(self, cli_runner: CliRunner) -> None:
        start = cli_runner.invoke(cli, ["--json", "agent", "session", "start", "DB choice"])
        session_id = json.loads(start.output)["data"]["id"]
        cli_runner.invoke(cli, ["agent", "session", "log", "Use Postgres", "--pin"])
        cli_runner.invoke(cli, ["agent", "session", "close"])

        result = cli_runner.invoke(cli, ["--json", "extract", session_id, "--title", "My Decision"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["data"]["title"] == "My Decision"

    def test_extract_not_found(self, cli_runner: CliRunner) -> None:
        result = cli_runner.invoke(cli, ["extract", "LOG-9999"])
        assert result.exit_code == 1

    def test_extract_examples(self, cli_runner: CliRunner) -> None:
        result = cli_runner.invoke(cli, ["extract", "--examples"])
        assert result.exit_code == 0
        assert "extract" in result.output
