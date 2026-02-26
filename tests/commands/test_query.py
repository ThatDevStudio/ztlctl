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

    # -- Extended filters ---------------------------------------------------

    def test_list_by_subtype(self, cli_runner: CliRunner) -> None:
        cli_runner.invoke(cli, ["create", "note", "My Decision", "--subtype", "decision"])
        result = cli_runner.invoke(cli, ["--json", "query", "list", "--subtype", "decision"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        for item in data["data"]["items"]:
            assert item["subtype"] == "decision"

    def test_list_by_maturity(self, cli_runner: CliRunner) -> None:
        result = cli_runner.invoke(cli, ["--json", "query", "list", "--maturity", "seed"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True

    def test_list_since(self, cli_runner: CliRunner) -> None:
        _seed_via_cli(cli_runner)
        result = cli_runner.invoke(cli, ["--json", "query", "list", "--since", "2000-01-01"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["data"]["count"] == 5

    def test_list_since_future(self, cli_runner: CliRunner) -> None:
        _seed_via_cli(cli_runner)
        result = cli_runner.invoke(cli, ["--json", "query", "list", "--since", "2099-01-01"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["data"]["count"] == 0

    def test_list_include_archived(self, cli_runner: CliRunner) -> None:
        _seed_via_cli(cli_runner)
        # Find an item to archive
        search = cli_runner.invoke(cli, ["--json", "query", "search", "Alpha"])
        item_id = json.loads(search.output)["data"]["items"][0]["id"]
        cli_runner.invoke(cli, ["archive", item_id])

        # Default: archived excluded
        result = cli_runner.invoke(cli, ["--json", "query", "list"])
        data = json.loads(result.output)
        assert data["data"]["count"] == 4

        # With flag: all items
        result = cli_runner.invoke(cli, ["--json", "query", "list", "--include-archived"])
        data = json.loads(result.output)
        assert data["data"]["count"] == 5

    def test_list_sort_priority(self, cli_runner: CliRunner) -> None:
        _seed_via_cli(cli_runner)
        result = cli_runner.invoke(cli, ["--json", "query", "list", "--sort", "priority"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        for item in data["data"]["items"]:
            assert "score" in item

    def test_list_invalid_maturity(self, cli_runner: CliRunner) -> None:
        result = cli_runner.invoke(cli, ["query", "list", "--maturity", "invalid"])
        assert result.exit_code != 0


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


@pytest.mark.usefixtures("_isolated_vault")
class TestSpaceFilterCLI:
    """CLI tests for --space option."""

    def test_search_with_space_filter(self, cli_runner: CliRunner) -> None:
        _seed_via_cli(cli_runner)
        result = cli_runner.invoke(cli, ["--json", "query", "search", "Note", "--space", "notes"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        for item in data["data"]["items"]:
            assert item["path"].startswith("notes/")

    def test_list_with_space_filter(self, cli_runner: CliRunner) -> None:
        _seed_via_cli(cli_runner)
        result = cli_runner.invoke(cli, ["--json", "query", "list", "--space", "ops"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        for item in data["data"]["items"]:
            assert item["path"].startswith("ops/")

    def test_search_invalid_space(self, cli_runner: CliRunner) -> None:
        result = cli_runner.invoke(cli, ["query", "search", "test", "--space", "invalid"])
        assert result.exit_code != 0


@pytest.mark.usefixtures("_isolated_vault")
class TestGraphRankCLI:
    """CLI tests for --rank-by graph."""

    def test_search_rank_by_graph_cli(self, cli_runner: CliRunner) -> None:
        _seed_via_cli(cli_runner)
        result = cli_runner.invoke(cli, ["--json", "query", "search", "Note", "--rank-by", "graph"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
