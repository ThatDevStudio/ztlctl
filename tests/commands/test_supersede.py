"""Tests for the supersede CLI command."""

from __future__ import annotations

import json

import pytest
from click.testing import CliRunner

from ztlctl.cli import cli


@pytest.mark.usefixtures("_isolated_vault")
class TestSupersedeCommand:
    def test_supersede_decisions(self, cli_runner: CliRunner) -> None:
        # Create two decisions
        r1 = cli_runner.invoke(
            cli, ["--json", "create", "note", "Old Decision", "--subtype", "decision"]
        )
        assert r1.exit_code == 0
        old_id = json.loads(r1.output)["data"]["id"]

        r2 = cli_runner.invoke(
            cli, ["--json", "create", "note", "New Decision", "--subtype", "decision"]
        )
        assert r2.exit_code == 0
        new_id = json.loads(r2.output)["data"]["id"]

        # Must accept the decision first (proposed → accepted → superseded)
        accept_r = cli_runner.invoke(cli, ["--json", "update", old_id, "--status", "accepted"])
        assert accept_r.exit_code == 0

        # Now supersede
        result = cli_runner.invoke(cli, ["--json", "supersede", old_id, new_id])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["data"]["status"] == "superseded"

    def test_supersede_not_found(self, cli_runner: CliRunner) -> None:
        result = cli_runner.invoke(cli, ["supersede", "ztl_fake1", "ztl_fake2"])
        assert result.exit_code == 1

    def test_supersede_missing_args(self, cli_runner: CliRunner) -> None:
        result = cli_runner.invoke(cli, ["supersede", "ztl_fake1"])
        assert result.exit_code != 0
