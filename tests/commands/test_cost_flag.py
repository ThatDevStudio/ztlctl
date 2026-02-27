"""Tests for --cost flag on content-modifying commands."""

from __future__ import annotations

import json

import pytest
from click.testing import CliRunner

from ztlctl.cli import cli


def _start_session(cli_runner: CliRunner) -> str:
    """Start a session and return the session ID."""
    r = cli_runner.invoke(cli, ["--json", "agent", "session", "start", "Cost Test"])
    assert r.exit_code == 0
    return json.loads(r.output)["data"]["id"]


def _get_total_cost(cli_runner: CliRunner) -> int:
    """Get total session cost."""
    r = cli_runner.invoke(cli, ["--json", "agent", "session", "cost"])
    assert r.exit_code == 0
    return json.loads(r.output)["data"]["total_cost"]


@pytest.mark.usefixtures("_isolated_vault")
class TestCostFlagCreateNote:
    def test_cost_flag_accepted(self, cli_runner: CliRunner) -> None:
        """--cost flag is accepted without error."""
        result = cli_runner.invoke(cli, ["create", "note", "Test", "--cost", "500"])
        assert result.exit_code == 0

    def test_cost_logged_to_session(self, cli_runner: CliRunner) -> None:
        """--cost value is logged to the active session."""
        _start_session(cli_runner)
        cli_runner.invoke(cli, ["create", "note", "Costed Note", "--cost", "1200"])
        assert _get_total_cost(cli_runner) == 1200

    def test_zero_cost_is_noop(self, cli_runner: CliRunner) -> None:
        """--cost 0 (default) does not create a log entry."""
        _start_session(cli_runner)
        cli_runner.invoke(cli, ["create", "note", "Free Note"])
        assert _get_total_cost(cli_runner) == 0


@pytest.mark.usefixtures("_isolated_vault")
class TestCostFlagCreateReference:
    def test_cost_logged(self, cli_runner: CliRunner) -> None:
        _start_session(cli_runner)
        cli_runner.invoke(cli, ["create", "reference", "Ref", "--cost", "800"])
        assert _get_total_cost(cli_runner) == 800


@pytest.mark.usefixtures("_isolated_vault")
class TestCostFlagCreateTask:
    def test_cost_logged(self, cli_runner: CliRunner) -> None:
        _start_session(cli_runner)
        cli_runner.invoke(cli, ["create", "task", "Task", "--cost", "300"])
        assert _get_total_cost(cli_runner) == 300


@pytest.mark.usefixtures("_isolated_vault")
class TestCostFlagUpdate:
    def test_cost_logged(self, cli_runner: CliRunner) -> None:
        _start_session(cli_runner)
        r = cli_runner.invoke(cli, ["--json", "create", "note", "Update Me"])
        content_id = json.loads(r.output)["data"]["id"]
        cli_runner.invoke(cli, ["update", content_id, "--title", "Updated", "--cost", "600"])
        assert _get_total_cost(cli_runner) == 600


@pytest.mark.usefixtures("_isolated_vault")
class TestCostFlagArchive:
    def test_cost_logged(self, cli_runner: CliRunner) -> None:
        _start_session(cli_runner)
        r = cli_runner.invoke(cli, ["--json", "create", "note", "Archive Me"])
        content_id = json.loads(r.output)["data"]["id"]
        cli_runner.invoke(cli, ["archive", content_id, "--cost", "200"])
        assert _get_total_cost(cli_runner) == 200


@pytest.mark.usefixtures("_isolated_vault")
class TestCostFlagSupersede:
    def test_cost_logged(self, cli_runner: CliRunner) -> None:
        _start_session(cli_runner)
        r1 = cli_runner.invoke(
            cli,
            ["--json", "create", "note", "Old Decision", "--subtype", "decision"],
        )
        old_id = json.loads(r1.output)["data"]["id"]
        # Transition old decision to accepted (required before supersede)
        update_result = cli_runner.invoke(cli, ["update", old_id, "--status", "accepted"])
        assert update_result.exit_code == 0
        r2 = cli_runner.invoke(
            cli,
            ["--json", "create", "note", "New Decision", "--subtype", "decision"],
        )
        new_id = json.loads(r2.output)["data"]["id"]
        supersede_result = cli_runner.invoke(cli, ["supersede", old_id, new_id, "--cost", "400"])
        assert supersede_result.exit_code == 0
        assert _get_total_cost(cli_runner) == 400


@pytest.mark.usefixtures("_isolated_vault")
class TestCostFlagReweave:
    def test_cost_flag_accepted(self, cli_runner: CliRunner) -> None:
        """--cost flag is accepted on reweave command."""
        # Create two notes so reweave has a target
        cli_runner.invoke(cli, ["create", "note", "Alpha Note"])
        cli_runner.invoke(cli, ["create", "note", "Beta Note"])
        result = cli_runner.invoke(cli, ["reweave", "--dry-run", "--cost", "1000"])
        assert result.exit_code == 0


@pytest.mark.usefixtures("_isolated_vault")
class TestCostFlagNoSession:
    def test_cost_without_session_silently_ignored(self, cli_runner: CliRunner) -> None:
        """--cost is silently ignored when no session is active."""
        result = cli_runner.invoke(cli, ["create", "note", "No Session", "--cost", "500"])
        assert result.exit_code == 0
