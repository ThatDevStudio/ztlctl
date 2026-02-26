"""Tests for agent session cost/log and agent context/brief CLI commands."""

from __future__ import annotations

import json

import pytest
from click.testing import CliRunner

from ztlctl.cli import cli


@pytest.mark.usefixtures("_isolated_vault")
class TestSessionCost:
    def test_cost_no_session(self, cli_runner: CliRunner) -> None:
        result = cli_runner.invoke(cli, ["agent", "session", "cost"])
        assert result.exit_code == 1

    def test_cost_with_session(self, cli_runner: CliRunner) -> None:
        cli_runner.invoke(cli, ["agent", "session", "start", "Cost Topic"])
        result = cli_runner.invoke(cli, ["agent", "session", "cost"])
        assert result.exit_code == 0
        assert "cost" in result.output

    def test_cost_json(self, cli_runner: CliRunner) -> None:
        cli_runner.invoke(cli, ["agent", "session", "start", "Cost JSON"])
        result = cli_runner.invoke(cli, ["--json", "agent", "session", "cost"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["op"] == "cost"
        assert "total_cost" in data["data"]

    def test_cost_report_mode(self, cli_runner: CliRunner) -> None:
        cli_runner.invoke(cli, ["agent", "session", "start", "Budget Test"])
        result = cli_runner.invoke(cli, ["--json", "agent", "session", "cost", "--report", "10000"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["data"]["budget"] == 10000
        assert "remaining" in data["data"]


@pytest.mark.usefixtures("_isolated_vault")
class TestSessionLog:
    def test_log_basic(self, cli_runner: CliRunner) -> None:
        cli_runner.invoke(cli, ["agent", "session", "start", "Log Topic"])
        result = cli_runner.invoke(cli, ["agent", "session", "log", "Found a pattern"])
        assert result.exit_code == 0
        assert "log_entry" in result.output

    def test_log_json(self, cli_runner: CliRunner) -> None:
        cli_runner.invoke(cli, ["agent", "session", "start", "Log JSON"])
        result = cli_runner.invoke(cli, ["--json", "agent", "session", "log", "Entry message"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["op"] == "log_entry"
        assert "entry_id" in data["data"]

    def test_log_with_pin(self, cli_runner: CliRunner) -> None:
        cli_runner.invoke(cli, ["agent", "session", "start", "Pin Topic"])
        result = cli_runner.invoke(cli, ["agent", "session", "log", "Important!", "--pin"])
        assert result.exit_code == 0

    def test_log_with_cost(self, cli_runner: CliRunner) -> None:
        cli_runner.invoke(cli, ["agent", "session", "start", "Cost Log"])
        result = cli_runner.invoke(cli, ["agent", "session", "log", "API call", "--cost", "1500"])
        assert result.exit_code == 0

    def test_log_no_session(self, cli_runner: CliRunner) -> None:
        result = cli_runner.invoke(cli, ["agent", "session", "log", "Orphan"])
        assert result.exit_code == 1


@pytest.mark.usefixtures("_isolated_vault")
class TestAgentContext:
    def test_context_with_session(self, cli_runner: CliRunner) -> None:
        cli_runner.invoke(cli, ["agent", "session", "start", "Context Topic"])
        result = cli_runner.invoke(cli, ["agent", "context"])
        assert result.exit_code == 0
        assert "context" in result.output

    def test_context_json(self, cli_runner: CliRunner) -> None:
        cli_runner.invoke(cli, ["agent", "session", "start", "Context JSON"])
        result = cli_runner.invoke(cli, ["--json", "agent", "context"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["op"] == "context"
        assert "layers" in data["data"]
        assert "total_tokens" in data["data"]

    def test_context_no_session(self, cli_runner: CliRunner) -> None:
        result = cli_runner.invoke(cli, ["agent", "context"])
        assert result.exit_code == 1

    def test_context_with_topic(self, cli_runner: CliRunner) -> None:
        cli_runner.invoke(cli, ["agent", "session", "start", "Topic Test"])
        result = cli_runner.invoke(cli, ["--json", "agent", "context", "--topic", "auth"])
        assert result.exit_code == 0

    def test_context_with_budget(self, cli_runner: CliRunner) -> None:
        cli_runner.invoke(cli, ["agent", "session", "start", "Budget Test"])
        result = cli_runner.invoke(cli, ["--json", "agent", "context", "--budget", "4000"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["data"]["budget"] == 4000


@pytest.mark.usefixtures("_isolated_vault")
class TestAgentBrief:
    def test_brief_with_session(self, cli_runner: CliRunner) -> None:
        cli_runner.invoke(cli, ["agent", "session", "start", "Brief Topic"])
        result = cli_runner.invoke(cli, ["agent", "brief"])
        assert result.exit_code == 0
        assert "brief" in result.output

    def test_brief_json_with_session(self, cli_runner: CliRunner) -> None:
        cli_runner.invoke(cli, ["agent", "session", "start", "Brief JSON"])
        result = cli_runner.invoke(cli, ["--json", "agent", "brief"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["op"] == "brief"
        assert data["data"]["session"] is not None

    def test_brief_no_session(self, cli_runner: CliRunner) -> None:
        """Brief still works without an active session."""
        result = cli_runner.invoke(cli, ["--json", "agent", "brief"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["data"]["session"] is None
        assert "vault_stats" in data["data"]
