"""Tests for export CLI commands (markdown, indexes, graph)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from ztlctl.cli import cli


@pytest.mark.usefixtures("_isolated_vault")
class TestExportMarkdownCommand:
    def test_export_markdown(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        output = tmp_path / "md-export"
        result = cli_runner.invoke(cli, ["export", "markdown", "--output", str(output)])
        assert result.exit_code == 0

    def test_export_markdown_json(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        output = tmp_path / "md-json"
        result = cli_runner.invoke(cli, ["--json", "export", "markdown", "--output", str(output)])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["op"] == "export_markdown"
        assert "file_count" in data["data"]

    def test_export_markdown_requires_output(self, cli_runner: CliRunner) -> None:
        result = cli_runner.invoke(cli, ["export", "markdown"])
        assert result.exit_code != 0

    def test_export_markdown_json_includes_filters(
        self, cli_runner: CliRunner, tmp_path: Path
    ) -> None:
        cli_runner.invoke(cli, ["create", "note", "Filtered Markdown Note"])
        output = tmp_path / "md-filtered"

        result = cli_runner.invoke(
            cli,
            ["--json", "export", "markdown", "--type", "note", "--output", str(output)],
        )

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["data"]["filters"] == {"type": "note"}


@pytest.mark.usefixtures("_isolated_vault")
class TestExportIndexesCommand:
    def test_export_indexes(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        output = tmp_path / "idx-export"
        result = cli_runner.invoke(cli, ["export", "indexes", "--output", str(output)])
        assert result.exit_code == 0

    def test_export_indexes_json(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        output = tmp_path / "idx-json"
        result = cli_runner.invoke(cli, ["--json", "export", "indexes", "--output", str(output)])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["op"] == "export_indexes"

    def test_export_indexes_creates_index_file(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        output = tmp_path / "idx-files"
        cli_runner.invoke(cli, ["export", "indexes", "--output", str(output)])
        assert (Path(output) / "index.md").is_file()

    def test_export_indexes_filters_by_type(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        cli_runner.invoke(cli, ["create", "note", "Index Note"])
        cli_runner.invoke(cli, ["create", "reference", "Index Reference"])
        output = tmp_path / "idx-filtered"

        result = cli_runner.invoke(
            cli,
            ["--json", "export", "indexes", "--type", "note", "--output", str(output)],
        )

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["data"]["node_count"] == 1
        assert data["data"]["filters"] == {"type": "note"}
        assert "Index Note" in (output / "by-type" / "note.md").read_text()


@pytest.mark.usefixtures("_isolated_vault")
class TestExportGraphCommand:
    def test_export_graph_dot_stdout(self, cli_runner: CliRunner) -> None:
        result = cli_runner.invoke(cli, ["export", "graph", "--format", "dot"])
        assert result.exit_code == 0
        assert "digraph vault" in result.output

    def test_export_graph_json_stdout(self, cli_runner: CliRunner) -> None:
        result = cli_runner.invoke(cli, ["export", "graph", "--format", "json"])
        assert result.exit_code == 0
        d3 = json.loads(result.output)
        assert "nodes" in d3
        assert "links" in d3

    def test_export_graph_to_file(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        output = tmp_path / "graph.dot"
        result = cli_runner.invoke(
            cli, ["export", "graph", "--format", "dot", "--output", str(output)]
        )
        assert result.exit_code == 0
        assert output.is_file()
        assert "digraph vault" in output.read_text()

    def test_export_graph_json_to_file(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        output = tmp_path / "graph.json"
        result = cli_runner.invoke(
            cli, ["export", "graph", "--format", "json", "--output", str(output)]
        )
        assert result.exit_code == 0
        d3 = json.loads(output.read_text())
        assert "nodes" in d3

    def test_export_graph_default_format(self, cli_runner: CliRunner) -> None:
        result = cli_runner.invoke(cli, ["export", "graph"])
        assert result.exit_code == 0
        assert "digraph vault" in result.output

    def test_export_graph_filtered_stdout(self, cli_runner: CliRunner) -> None:
        cli_runner.invoke(cli, ["create", "note", "Graph Note"])
        cli_runner.invoke(cli, ["create", "reference", "Graph Reference"])

        result = cli_runner.invoke(cli, ["export", "graph", "--format", "json", "--type", "note"])

        assert result.exit_code == 0
        d3 = json.loads(result.output)
        assert len(d3["nodes"]) == 1
        assert d3["nodes"][0]["type"] == "note"
