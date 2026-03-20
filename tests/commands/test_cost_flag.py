"""Tests for --cost flag on hand-written commands that support it.

Generated commands (create note/reference/task, archive, supersede) no longer
carry the --cost flag since it is not part of the ActionDefinition schema.
Only the hand-written update.py retains the --cost flag.
"""

from __future__ import annotations

import json

import pytest
from click.testing import CliRunner

from ztlctl.cli import cli


def _start_session(cli_runner: CliRunner) -> str:
    """Start a session and return the session ID."""
    r = cli_runner.invoke(cli, ["--json", "session", "start", "Cost Test"])
    assert r.exit_code == 0
    return json.loads(r.output)["data"]["id"]


def _get_total_cost(cli_runner: CliRunner) -> int:
    """Get total session cost."""
    r = cli_runner.invoke(cli, ["--json", "session", "cost"])
    assert r.exit_code == 0
    return json.loads(r.output)["data"]["total_cost"]


@pytest.mark.usefixtures("_isolated_vault")
class TestCostFlagUpdate:
    def test_cost_logged(self, cli_runner: CliRunner) -> None:
        _start_session(cli_runner)
        r = cli_runner.invoke(cli, ["--json", "create", "note", "Update Me"])
        content_id = json.loads(r.output)["data"]["id"]
        cli_runner.invoke(cli, ["update", content_id, "--title", "Updated", "--cost", "600"])
        assert _get_total_cost(cli_runner) == 600


@pytest.mark.usefixtures("_isolated_vault")
class TestCostFlagReweave:
    def test_reweave_run_dry_run_succeeds(self, cli_runner: CliRunner) -> None:
        """reweave run --dry-run executes without error."""
        cli_runner.invoke(cli, ["create", "note", "Alpha Note"])
        cli_runner.invoke(cli, ["create", "note", "Beta Note"])
        result = cli_runner.invoke(cli, ["reweave", "run", "--dry-run"])
        assert result.exit_code == 0


@pytest.mark.usefixtures("_isolated_vault")
class TestSessionAndCreate:
    def test_create_without_session_succeeds(self, cli_runner: CliRunner) -> None:
        """create note succeeds even without an active session."""
        result = cli_runner.invoke(cli, ["create", "note", "No Session Note"])
        assert result.exit_code == 0

    def test_create_note_with_session_succeeds(self, cli_runner: CliRunner) -> None:
        """create note works when a session is active."""
        _start_session(cli_runner)
        result = cli_runner.invoke(cli, ["create", "note", "Session Note"])
        assert result.exit_code == 0
