"""Tests for query CLI commands."""

from __future__ import annotations

import json

import pytest
from click.testing import CliRunner

from ztlctl.cli import cli


def _seed_via_cli(runner: CliRunner) -> None:
    """Create seed content via CLI commands."""
    runner.invoke(cli, ["create", "note", "Alpha Note", "--tags", "ai/ml", "--topic", "math"])
    runner.invoke(cli, ["create", "note", "Beta Note", "--tags", "ai/nlp"])
    runner.invoke(cli, ["create", "reference", "Python Docs", "--url", "https://docs.python.org"])
    runner.invoke(cli, ["create", "task", "Fix Bug", "--priority", "high"])
    runner.invoke(cli, ["create", "task", "Write Tests", "--priority", "medium"])


@pytest.mark.usefixtures("_isolated_vault")
class TestSearchCommand:
    def test_search_basic(self, cli_runner: CliRunner) -> None:
        _seed_via_cli(cli_runner)
        result = cli_runner.invoke(cli, ["--json", "query", "search", "Alpha"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["data"]["count"] >= 1

    def test_search_with_type_filter(self, cli_runner: CliRunner) -> None:
        _seed_via_cli(cli_runner)
        result = cli_runner.invoke(
            cli, ["--json", "query", "search", "Python", "--type", "reference"]
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True

    def test_search_with_tag_filter(self, cli_runner: CliRunner) -> None:
        _seed_via_cli(cli_runner)
        result = cli_runner.invoke(cli, ["--json", "query", "search", "Alpha", "--tag", "ai/ml"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True

    def test_search_no_results(self, cli_runner: CliRunner) -> None:
        _seed_via_cli(cli_runner)
        result = cli_runner.invoke(cli, ["--json", "query", "search", "xyznonexistent"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["data"]["count"] == 0

    def test_search_help(self, cli_runner: CliRunner) -> None:
        result = cli_runner.invoke(cli, ["query", "search", "--help"])
        assert result.exit_code == 0
        assert "--type" in result.output
        assert "--tag" in result.output
        assert "--rank-by" in result.output


@pytest.mark.usefixtures("_isolated_vault")
class TestGetCommand:
    def test_get_existing(self, cli_runner: CliRunner) -> None:
        _seed_via_cli(cli_runner)
        # First find the ID via search
        search_result = cli_runner.invoke(cli, ["--json", "query", "search", "Alpha"])
        search_data = json.loads(search_result.output)
        content_id = search_data["data"]["items"][0]["id"]

        result = cli_runner.invoke(cli, ["--json", "query", "get", content_id])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["data"]["title"] == "Alpha Note"

    def test_get_not_found(self, cli_runner: CliRunner) -> None:
        result = cli_runner.invoke(cli, ["--json", "query", "get", "nonexistent"])
        assert result.exit_code == 1
        data = json.loads(result.output)
        assert data["ok"] is False
        assert data["error"]["code"] == "NOT_FOUND"

    def test_get_help(self, cli_runner: CliRunner) -> None:
        result = cli_runner.invoke(cli, ["query", "get", "--help"])
        assert result.exit_code == 0
        assert "CONTENT_ID" in result.output


@pytest.mark.usefixtures("_isolated_vault")
class TestListCommand:
    def test_list_all(self, cli_runner: CliRunner) -> None:
        _seed_via_cli(cli_runner)
        result = cli_runner.invoke(cli, ["--json", "query", "list"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["data"]["count"] == 5

    def test_list_by_type(self, cli_runner: CliRunner) -> None:
        _seed_via_cli(cli_runner)
        result = cli_runner.invoke(cli, ["--json", "query", "list", "--type", "note"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        for item in data["data"]["items"]:
            assert item["type"] == "note"

    def test_list_by_status(self, cli_runner: CliRunner) -> None:
        _seed_via_cli(cli_runner)
        result = cli_runner.invoke(
            cli, ["--json", "query", "list", "--type", "task", "--status", "inbox"]
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True

    def test_list_with_limit(self, cli_runner: CliRunner) -> None:
        _seed_via_cli(cli_runner)
        result = cli_runner.invoke(cli, ["--json", "query", "list", "--limit", "2"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["data"]["count"] <= 2

    def test_list_help(self, cli_runner: CliRunner) -> None:
        result = cli_runner.invoke(cli, ["query", "list", "--help"])
        assert result.exit_code == 0
        assert "--type" in result.output
        assert "--status" in result.output
        assert "--sort" in result.output


@pytest.mark.usefixtures("_isolated_vault")
class TestWorkQueueCommand:
    def test_work_queue(self, cli_runner: CliRunner) -> None:
        _seed_via_cli(cli_runner)
        result = cli_runner.invoke(cli, ["--json", "query", "work-queue"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["data"]["count"] == 2

    def test_work_queue_empty(self, cli_runner: CliRunner) -> None:
        result = cli_runner.invoke(cli, ["--json", "query", "work-queue"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["data"]["count"] == 0

    def test_work_queue_help(self, cli_runner: CliRunner) -> None:
        result = cli_runner.invoke(cli, ["query", "work-queue", "--help"])
        assert result.exit_code == 0


@pytest.mark.usefixtures("_isolated_vault")
class TestDecisionSupportCommand:
    def test_decision_support(self, cli_runner: CliRunner) -> None:
        _seed_via_cli(cli_runner)
        result = cli_runner.invoke(cli, ["--json", "query", "decision-support"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert "decisions" in data["data"]
        assert "notes" in data["data"]
        assert "references" in data["data"]

    def test_decision_support_with_topic(self, cli_runner: CliRunner) -> None:
        _seed_via_cli(cli_runner)
        result = cli_runner.invoke(cli, ["--json", "query", "decision-support", "--topic", "math"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True

    def test_decision_support_help(self, cli_runner: CliRunner) -> None:
        result = cli_runner.invoke(cli, ["query", "decision-support", "--help"])
        assert result.exit_code == 0
        assert "--topic" in result.output


class TestQueryGroupHelp:
    def test_query_group_help(self, cli_runner: CliRunner) -> None:
        result = cli_runner.invoke(cli, ["query", "--help"])
        assert result.exit_code == 0
        assert "search" in result.output
        assert "get" in result.output
        assert "list" in result.output
        assert "work-queue" in result.output
        assert "decision-support" in result.output
