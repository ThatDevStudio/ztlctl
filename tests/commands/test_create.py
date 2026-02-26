"""Tests for create CLI commands (note, reference, task)."""

from __future__ import annotations

import json

import pytest
from click.testing import CliRunner

from ztlctl.cli import cli


@pytest.mark.usefixtures("_isolated_vault")
class TestCreateNoteCommand:
    def test_create_note(self, cli_runner: CliRunner) -> None:
        result = cli_runner.invoke(cli, ["create", "note", "CLI Note"])
        assert result.exit_code == 0
        assert "OK" in result.output

    def test_create_note_json(self, cli_runner: CliRunner) -> None:
        result = cli_runner.invoke(cli, ["--json", "create", "note", "JSON Note"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["data"]["title"] == "JSON Note"

    def test_create_note_with_subtype(self, cli_runner: CliRunner) -> None:
        result = cli_runner.invoke(
            cli, ["--json", "create", "note", "Decision", "--subtype", "decision"]
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True

    def test_create_note_with_tags(self, cli_runner: CliRunner) -> None:
        result = cli_runner.invoke(cli, ["--json", "create", "note", "Tagged", "--tags", "ai/ml"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True

    def test_create_note_with_topic(self, cli_runner: CliRunner) -> None:
        result = cli_runner.invoke(
            cli, ["--json", "create", "note", "Topic Note", "--topic", "math"]
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "math" in data["data"]["path"]


@pytest.mark.usefixtures("_isolated_vault")
class TestCreateReferenceCommand:
    def test_create_reference(self, cli_runner: CliRunner) -> None:
        result = cli_runner.invoke(cli, ["--json", "create", "reference", "Cool Article"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["data"]["id"].startswith("ref_")

    def test_create_reference_with_url(self, cli_runner: CliRunner) -> None:
        result = cli_runner.invoke(
            cli,
            ["--json", "create", "reference", "Python Docs", "--url", "https://python.org"],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True


@pytest.mark.usefixtures("_isolated_vault")
class TestCreateTaskCommand:
    def test_create_task(self, cli_runner: CliRunner) -> None:
        result = cli_runner.invoke(cli, ["--json", "create", "task", "Fix bug"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["data"]["id"].startswith("TASK-")

    def test_create_task_with_priority(self, cli_runner: CliRunner) -> None:
        result = cli_runner.invoke(
            cli, ["--json", "create", "task", "Urgent", "--priority", "high"]
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True

    def test_create_task_invalid_priority(self, cli_runner: CliRunner) -> None:
        result = cli_runner.invoke(cli, ["create", "task", "Bad", "--priority", "invalid"])
        assert result.exit_code != 0
