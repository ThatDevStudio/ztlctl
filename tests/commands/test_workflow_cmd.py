"""Tests for workflow init/update CLI commands."""

from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from ztlctl.cli import cli


class TestWorkflowCommands:
    def _init_vault(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        result = cli_runner.invoke(
            cli,
            [
                "--no-interact",
                "init",
                str(tmp_path),
                "--name",
                "workflow-vault",
                "--no-workflow",
            ],
        )
        assert result.exit_code == 0, result.output

    def test_workflow_init_json(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        self._init_vault(cli_runner, tmp_path)

        result = cli_runner.invoke(
            cli,
            [
                "--json",
                "--no-interact",
                "workflow",
                "init",
                str(tmp_path),
                "--viewer",
                "vanilla",
                "--workflow",
                "agent-generic",
                "--skill-set",
                "engineering",
            ],
        )

        assert result.exit_code == 0, result.output
        payload = json.loads(result.output)
        assert payload["ok"] is True
        assert payload["data"]["choices"]["viewer"] == "vanilla"
        assert payload["data"]["choices"]["workflow"] == "agent-generic"

    def test_workflow_update_json(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        self._init_vault(cli_runner, tmp_path)
        cli_runner.invoke(cli, ["--no-interact", "workflow", "init", str(tmp_path)])

        result = cli_runner.invoke(
            cli,
            [
                "--json",
                "--no-interact",
                "workflow",
                "update",
                str(tmp_path),
                "--workflow",
                "manual",
                "--skill-set",
                "minimal",
            ],
        )

        assert result.exit_code == 0, result.output
        payload = json.loads(result.output)
        assert payload["ok"] is True
        assert payload["data"]["choices"]["workflow"] == "manual"
        assert payload["data"]["choices"]["skill_set"] == "minimal"

    def test_workflow_init_interactive_prompts(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        self._init_vault(cli_runner, tmp_path)

        result = cli_runner.invoke(
            cli,
            ["workflow", "init", str(tmp_path)],
            input="none\nvanilla\nmanual\nminimal\n",
        )

        assert result.exit_code == 0, result.output
        answers = (tmp_path / ".ztlctl" / "workflow-answers.yml").read_text()
        assert "source_control: none" in answers
        assert "viewer: vanilla" in answers
        assert "workflow: manual" in answers
        assert "skill_set: minimal" in answers

    def test_workflow_update_requires_existing_workflow(
        self, cli_runner: CliRunner, tmp_path: Path
    ) -> None:
        self._init_vault(cli_runner, tmp_path)

        result = cli_runner.invoke(cli, ["workflow", "update", str(tmp_path)])

        assert result.exit_code == 1
        assert "Source control" not in result.output
        assert "Workflow scaffolding has not been initialized" in result.output

    def test_workflow_init_invalid_target_fails_before_prompting(
        self, cli_runner: CliRunner, tmp_path: Path
    ) -> None:
        result = cli_runner.invoke(cli, ["workflow", "init", str(tmp_path)], input="git\n")

        assert result.exit_code == 1
        assert "Source control" not in result.output
        assert "No ztlctl vault found" in result.output

    def test_workflow_init_duplicate_fails_before_prompting(
        self, cli_runner: CliRunner, tmp_path: Path
    ) -> None:
        self._init_vault(cli_runner, tmp_path)
        cli_runner.invoke(cli, ["--no-interact", "workflow", "init", str(tmp_path)])

        result = cli_runner.invoke(cli, ["workflow", "init", str(tmp_path)], input="none\n")

        assert result.exit_code == 1
        assert "Source control" not in result.output
        assert "Workflow scaffolding already exists" in result.output
