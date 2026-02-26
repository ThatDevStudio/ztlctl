"""Tests for garden CLI commands (seed)."""

from __future__ import annotations

import json

import pytest
from click.testing import CliRunner

from ztlctl.cli import cli


@pytest.mark.usefixtures("_isolated_vault")
class TestGardenSeed:
    def test_seed_basic(self, cli_runner: CliRunner) -> None:
        result = cli_runner.invoke(cli, ["garden", "seed", "Half-formed idea"])
        assert result.exit_code == 0
        assert "create_note" in result.output

    def test_seed_json(self, cli_runner: CliRunner) -> None:
        result = cli_runner.invoke(cli, ["--json", "garden", "seed", "Quick thought"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["op"] == "create_note"
        assert data["data"]["type"] == "note"

    def test_seed_with_tags(self, cli_runner: CliRunner) -> None:
        result = cli_runner.invoke(cli, ["--json", "garden", "seed", "ML idea", "--tags", "ai/ml"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True

    def test_seed_with_topic(self, cli_runner: CliRunner) -> None:
        result = cli_runner.invoke(
            cli, ["--json", "garden", "seed", "Math hunch", "--topic", "math"]
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True

    def test_seed_maturity_in_db(self, cli_runner: CliRunner) -> None:
        """Seed command sets maturity='seed' in the database."""
        result = cli_runner.invoke(cli, ["--json", "garden", "seed", "Seed Note"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        node_id = data["data"]["id"]

        # Query via list to verify maturity
        list_result = cli_runner.invoke(cli, ["--json", "query", "list", "--maturity", "seed"])
        assert list_result.exit_code == 0
        list_data = json.loads(list_result.output)
        found_ids = [item["id"] for item in list_data["data"].get("items", [])]
        assert node_id in found_ids
