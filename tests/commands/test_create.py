"""Tests for create CLI commands (note, reference, task)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from ztlctl.cli import cli
from ztlctl.domain.content import CONTENT_REGISTRY


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

    def test_create_note_with_plugin_subtype(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        original_registry = CONTENT_REGISTRY.copy()
        plugin_dir = tmp_path / ".ztlctl" / "plugins"
        plugin_dir.mkdir(parents=True)
        plugin_dir.joinpath("custom_content.py").write_text(
            """import pluggy
from ztlctl.domain.content import NoteModel

hookimpl = pluggy.HookimplMarker("ztlctl")


class ExperimentModel(NoteModel):
    _subtype_name = "experiment"


class CustomContentPlugin:
    @hookimpl
    def register_content_models(self):
        return {"experiment": ExperimentModel}
""",
            encoding="utf-8",
        )

        try:
            result = cli_runner.invoke(
                cli,
                ["--json", "--sync", "create", "note", "Experiment", "--subtype", "experiment"],
            )
        finally:
            CONTENT_REGISTRY.clear()
            CONTENT_REGISTRY.update(original_registry)

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True


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


@pytest.mark.usefixtures("_isolated_vault")
class TestCreateNonInteractive:
    """Generated create commands are non-interactive; options are passed via flags."""

    def test_note_with_tags_flag(self, cli_runner: CliRunner) -> None:
        """Tags passed via --tags flag."""
        result = cli_runner.invoke(
            cli,
            ["--json", "create", "note", "Tagged Note", "--tags", "ai/ml", "--tags", "dev/ops"],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True

    def test_note_with_topic_flag(self, cli_runner: CliRunner) -> None:
        """Topic passed via --topic flag."""
        result = cli_runner.invoke(
            cli,
            ["--json", "create", "note", "Topic Note", "--topic", "mathematics"],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True

    def test_reference_with_url_flag(self, cli_runner: CliRunner) -> None:
        """URL passed via --url flag."""
        result = cli_runner.invoke(
            cli,
            ["--json", "create", "reference", "Ref", "--url", "https://example.com"],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True

    def test_task_with_priority_flag(self, cli_runner: CliRunner) -> None:
        """Priority passed via --priority flag."""
        result = cli_runner.invoke(
            cli,
            ["--json", "create", "task", "Task", "--priority", "high"],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True

    def test_create_note_no_interact(self, cli_runner: CliRunner) -> None:
        """--no-interact flag works with generated command."""
        result = cli_runner.invoke(
            cli,
            ["--no-interact", "--json", "create", "note", "No Prompt Note"],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True

    def test_create_task_json_mode(self, cli_runner: CliRunner) -> None:
        """--json flag works with generated command."""
        result = cli_runner.invoke(
            cli,
            ["--json", "create", "task", "JSON Task"],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
