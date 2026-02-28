"""Tests for the vector CLI command group."""

from __future__ import annotations

import json

import pytest
from click.testing import CliRunner

from ztlctl.cli import cli


@pytest.mark.usefixtures("_isolated_vault")
class TestVectorCommandGroup:
    def test_vector_registered(self, cli_runner: CliRunner) -> None:
        """vector command appears in top-level help."""
        result = cli_runner.invoke(cli, ["--help"])
        assert "vector" in result.output

    def test_vector_status(self, cli_runner: CliRunner) -> None:
        """vector status runs without crashing."""
        result = cli_runner.invoke(cli, ["vector", "status"])
        assert result.exit_code == 0
        assert "search" in result.output.lower()

    def test_vector_status_json(self, cli_runner: CliRunner) -> None:
        """vector status --json returns valid JSON."""
        result = cli_runner.invoke(cli, ["--json", "vector", "status"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "ok" in data
        assert "available" in data.get("data", {})

    def test_vector_reindex_unavailable(self, cli_runner: CliRunner) -> None:
        """vector reindex fails gracefully when sqlite-vec is not installed."""
        result = cli_runner.invoke(cli, ["--json", "vector", "reindex"])
        # sqlite-vec is not in the test environment; expect graceful failure
        assert result.exit_code == 1
        data = json.loads(result.output)
        assert data["ok"] is False
        assert data["error"]["code"] == "SEMANTIC_UNAVAILABLE"

    def test_search_help_shows_semantic_choices(self, cli_runner: CliRunner) -> None:
        """search --help shows semantic and hybrid rank-by options."""
        result = cli_runner.invoke(cli, ["query", "search", "--help"])
        assert "semantic" in result.output
        assert "hybrid" in result.output
