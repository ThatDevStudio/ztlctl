"""Tests for graph CLI commands."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner
from sqlalchemy import insert

from ztlctl.cli import cli
from ztlctl.config.settings import ZtlSettings
from ztlctl.infrastructure.database.schema import edges
from ztlctl.infrastructure.vault import Vault


def _seed_graph(runner: CliRunner, vault_root: Path) -> dict[str, str]:
    """Create notes and link them, returning a map of title -> id.

    Creates: A -> B -> C chain plus D (isolated).
    """
    titles = ["Alpha", "Beta", "Gamma", "Delta"]
    id_map: dict[str, str] = {}

    for title in titles:
        runner.invoke(cli, ["create", "note", title])

    # Get IDs from the vault
    result = runner.invoke(cli, ["--json", "query", "list", "--type", "note"])
    data = json.loads(result.output)
    for item in data["data"]["items"]:
        id_map[item["title"]] = item["id"]

    # Insert edges directly into the DB
    now = "2025-01-01T00:00:00"
    settings = ZtlSettings.from_cli(vault_root=vault_root)
    vault = Vault(settings)
    with vault.engine.begin() as conn:
        # Chain: Alpha -> Beta -> Gamma
        conn.execute(
            insert(edges).values(
                source_id=id_map["Alpha"],
                target_id=id_map["Beta"],
                edge_type="relates",
                weight=1.0,
                source_layer="body",
                created=now,
            )
        )
        conn.execute(
            insert(edges).values(
                source_id=id_map["Beta"],
                target_id=id_map["Gamma"],
                edge_type="relates",
                weight=1.0,
                source_layer="body",
                created=now,
            )
        )

    return id_map


@pytest.mark.usefixtures("_isolated_vault")
class TestRelatedCommand:
    def test_related_basic(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        id_map = _seed_graph(cli_runner, tmp_path)
        result = cli_runner.invoke(cli, ["--json", "graph", "related", id_map["Alpha"]])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["data"]["count"] >= 1

    def test_related_not_found(self, cli_runner: CliRunner) -> None:
        result = cli_runner.invoke(cli, ["--json", "graph", "related", "nonexistent"])
        assert result.exit_code == 1
        data = json.loads(result.output)
        assert data["ok"] is False
        assert data["error"]["code"] == "NOT_FOUND"

    def test_related_help(self, cli_runner: CliRunner) -> None:
        result = cli_runner.invoke(cli, ["graph", "related", "--help"])
        assert result.exit_code == 0
        assert "CONTENT_ID" in result.output
        assert "--depth" in result.output
        assert "--top" in result.output


@pytest.mark.usefixtures("_isolated_vault")
class TestThemesCommand:
    def test_themes_basic(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        _seed_graph(cli_runner, tmp_path)
        result = cli_runner.invoke(cli, ["--json", "graph", "themes"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert "communities" in data["data"]

    def test_themes_empty(self, cli_runner: CliRunner) -> None:
        result = cli_runner.invoke(cli, ["--json", "graph", "themes"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["data"]["count"] == 0

    def test_themes_help(self, cli_runner: CliRunner) -> None:
        result = cli_runner.invoke(cli, ["graph", "themes", "--help"])
        assert result.exit_code == 0


@pytest.mark.usefixtures("_isolated_vault")
class TestRankCommand:
    def test_rank_basic(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        _seed_graph(cli_runner, tmp_path)
        result = cli_runner.invoke(cli, ["--json", "graph", "rank"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["data"]["count"] >= 1

    def test_rank_with_top(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        _seed_graph(cli_runner, tmp_path)
        result = cli_runner.invoke(cli, ["--json", "graph", "rank", "--top", "2"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["data"]["count"] <= 2

    def test_rank_help(self, cli_runner: CliRunner) -> None:
        result = cli_runner.invoke(cli, ["graph", "rank", "--help"])
        assert result.exit_code == 0
        assert "--top" in result.output


@pytest.mark.usefixtures("_isolated_vault")
class TestPathCommand:
    def test_path_basic(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        id_map = _seed_graph(cli_runner, tmp_path)
        result = cli_runner.invoke(
            cli,
            ["--json", "graph", "path", id_map["Alpha"], id_map["Gamma"]],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["data"]["length"] >= 1

    def test_path_no_path(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        id_map = _seed_graph(cli_runner, tmp_path)
        # Delta is isolated — no path from Alpha
        result = cli_runner.invoke(
            cli,
            ["--json", "graph", "path", id_map["Alpha"], id_map["Delta"]],
        )
        assert result.exit_code == 1
        data = json.loads(result.output)
        assert data["ok"] is False
        assert data["error"]["code"] == "NO_PATH"

    def test_path_help(self, cli_runner: CliRunner) -> None:
        result = cli_runner.invoke(cli, ["graph", "path", "--help"])
        assert result.exit_code == 0
        assert "SOURCE_ID" in result.output
        assert "TARGET_ID" in result.output


@pytest.mark.usefixtures("_isolated_vault")
class TestGapsCommand:
    def test_gaps_basic(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        _seed_graph(cli_runner, tmp_path)
        result = cli_runner.invoke(cli, ["--json", "graph", "gaps"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True

    def test_gaps_help(self, cli_runner: CliRunner) -> None:
        result = cli_runner.invoke(cli, ["graph", "gaps", "--help"])
        assert result.exit_code == 0
        assert "--top" in result.output


@pytest.mark.usefixtures("_isolated_vault")
class TestBridgesCommand:
    def test_bridges_basic(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        _seed_graph(cli_runner, tmp_path)
        result = cli_runner.invoke(cli, ["--json", "graph", "bridges"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True

    def test_bridges_help(self, cli_runner: CliRunner) -> None:
        result = cli_runner.invoke(cli, ["graph", "bridges", "--help"])
        assert result.exit_code == 0
        assert "--top" in result.output


class TestGraphGroupHelp:
    def test_graph_group_help(self, cli_runner: CliRunner) -> None:
        result = cli_runner.invoke(cli, ["graph", "--help"])
        assert result.exit_code == 0
        assert "related" in result.output
        assert "themes" in result.output
        assert "rank" in result.output
        assert "path" in result.output
        assert "gaps" in result.output
        assert "bridges" in result.output
