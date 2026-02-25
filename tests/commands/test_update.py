"""Tests for the update CLI command."""

from __future__ import annotations

import json

import pytest
from click.testing import CliRunner

from ztlctl.cli import cli


@pytest.mark.usefixtures("_isolated_vault")
class TestUpdateCommand:
    def test_update_help(self, cli_runner: CliRunner) -> None:
        result = cli_runner.invoke(cli, ["update", "--help"])
        assert result.exit_code == 0
        assert "--title" in result.output
        assert "--status" in result.output
        assert "--tags" in result.output
        assert "--topic" in result.output
        assert "--body" in result.output
        assert "--maturity" in result.output

    def test_update_title(self, cli_runner: CliRunner) -> None:
        # Create a note first
        r = cli_runner.invoke(cli, ["--json", "create", "note", "Old Title"])
        assert r.exit_code == 0
        content_id = json.loads(r.output)["data"]["id"]

        # Update the title
        result = cli_runner.invoke(cli, ["--json", "update", content_id, "--title", "New Title"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert "title" in data["data"]["fields_changed"]

    def test_update_tags(self, cli_runner: CliRunner) -> None:
        r = cli_runner.invoke(cli, ["--json", "create", "note", "Tag Target"])
        assert r.exit_code == 0
        content_id = json.loads(r.output)["data"]["id"]

        result = cli_runner.invoke(cli, ["--json", "update", content_id, "--tags", "domain/new"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert "tags" in data["data"]["fields_changed"]

    def test_update_topic(self, cli_runner: CliRunner) -> None:
        r = cli_runner.invoke(cli, ["--json", "create", "note", "Topic Note"])
        assert r.exit_code == 0
        content_id = json.loads(r.output)["data"]["id"]

        result = cli_runner.invoke(cli, ["--json", "update", content_id, "--topic", "math"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert "topic" in data["data"]["fields_changed"]

    def test_update_maturity(self, cli_runner: CliRunner) -> None:
        r = cli_runner.invoke(cli, ["--json", "create", "note", "Garden Note"])
        assert r.exit_code == 0
        content_id = json.loads(r.output)["data"]["id"]

        result = cli_runner.invoke(cli, ["--json", "update", content_id, "--maturity", "seed"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert "maturity" in data["data"]["fields_changed"]

    def test_update_invalid_maturity(self, cli_runner: CliRunner) -> None:
        result = cli_runner.invoke(cli, ["update", "ztl_fakeid", "--maturity", "invalid"])
        assert result.exit_code != 0

    def test_update_not_found(self, cli_runner: CliRunner) -> None:
        result = cli_runner.invoke(cli, ["update", "ztl_nonexist", "--title", "Nope"])
        assert result.exit_code == 1

    def test_update_no_changes(self, cli_runner: CliRunner) -> None:
        result = cli_runner.invoke(cli, ["update", "ztl_fakeid"])
        assert result.exit_code == 1
        assert "No changes specified" in result.output

    def test_update_body(self, cli_runner: CliRunner) -> None:
        r = cli_runner.invoke(cli, ["--json", "create", "note", "Body Note"])
        assert r.exit_code == 0
        content_id = json.loads(r.output)["data"]["id"]

        result = cli_runner.invoke(
            cli, ["--json", "update", content_id, "--body", "New body content"]
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert "body" in data["data"]["fields_changed"]

    def test_update_multiple_fields(self, cli_runner: CliRunner) -> None:
        r = cli_runner.invoke(cli, ["--json", "create", "note", "Multi Update"])
        assert r.exit_code == 0
        content_id = json.loads(r.output)["data"]["id"]

        result = cli_runner.invoke(
            cli,
            [
                "--json",
                "update",
                content_id,
                "--title",
                "Updated Multi",
                "--topic",
                "science",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert "title" in data["data"]["fields_changed"]
        assert "topic" in data["data"]["fields_changed"]
