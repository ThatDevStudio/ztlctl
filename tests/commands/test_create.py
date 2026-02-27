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


@pytest.mark.usefixtures("_isolated_vault")
class TestCreateInteractivePrompts:
    """Interactive prompts fire when --no-interact and --json are absent.

    ``_is_interactive`` checks ``sys.stdin.isatty()`` which returns False
    in CliRunner, so prompt-testing methods monkeypatch it to return True.
    Skip-prompt tests don't patch it (naturally non-interactive in tests).
    """

    def test_note_tags_prompt(self, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch) -> None:
        """Providing tags via stdin when no --tags flag is given."""
        monkeypatch.setattr("ztlctl.commands.create._is_interactive", lambda _app: True)
        result = cli_runner.invoke(
            cli,
            ["create", "note", "Prompted Tags"],
            input="ai/ml, dev/ops\n\n",  # tags prompt, topic prompt
        )
        assert result.exit_code == 0
        assert "OK" in result.output

    def test_note_topic_prompt(
        self, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Providing topic via stdin."""
        monkeypatch.setattr("ztlctl.commands.create._is_interactive", lambda _app: True)
        result = cli_runner.invoke(
            cli,
            ["create", "note", "Topic Prompted"],
            input="\nmathematics\n",
        )
        assert result.exit_code == 0

    def test_reference_url_prompt(
        self, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Providing URL via stdin when no --url flag is given."""
        monkeypatch.setattr("ztlctl.commands.create._is_interactive", lambda _app: True)
        result = cli_runner.invoke(
            cli,
            ["create", "reference", "Ref Prompted"],
            input="https://example.com\n\n",
        )
        assert result.exit_code == 0

    def test_task_priority_prompt(
        self, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Providing priority/impact/effort via stdin."""
        monkeypatch.setattr("ztlctl.commands.create._is_interactive", lambda _app: True)
        result = cli_runner.invoke(
            cli,
            ["create", "task", "Task Prompted"],
            input="high\nhigh\nlow\n",
        )
        assert result.exit_code == 0

    def test_no_interact_skips_prompts(self, cli_runner: CliRunner) -> None:
        """--no-interact flag prevents prompting (no stdin needed)."""
        result = cli_runner.invoke(
            cli,
            ["--no-interact", "--json", "create", "note", "No Prompt Note"],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True

    def test_json_mode_skips_prompts(self, cli_runner: CliRunner) -> None:
        """--json flag prevents prompting (no stdin needed)."""
        result = cli_runner.invoke(
            cli,
            ["--json", "create", "task", "JSON Task"],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True

    def test_provided_flags_skip_prompt(
        self, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Explicit --tags flag skips the tag prompt (only topic prompt fires)."""
        monkeypatch.setattr("ztlctl.commands.create._is_interactive", lambda _app: True)
        result = cli_runner.invoke(
            cli,
            ["create", "note", "Pre-Tagged", "--tags", "ai/ml"],
            input="\n",  # Only topic prompt should fire
        )
        assert result.exit_code == 0
