"""Tests for init CLI command."""

from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from ztlctl.cli import cli


class TestInitCommandNonInteractive:
    """Tests for init with --no-interact flag."""

    def test_init_basic(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        result = cli_runner.invoke(
            cli,
            ["--no-interact", "init", str(tmp_path), "--name", "test-vault"],
        )
        assert result.exit_code == 0
        assert "init_vault" in result.output

    def test_init_json_output(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        result = cli_runner.invoke(
            cli,
            ["--json", "--no-interact", "init", str(tmp_path), "--name", "json-vault"],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["op"] == "init_vault"
        assert data["data"]["name"] == "json-vault"

    def test_init_with_all_options(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        result = cli_runner.invoke(
            cli,
            [
                "--json",
                "--no-interact",
                "init",
                str(tmp_path),
                "--name",
                "full-vault",
                "--client",
                "vanilla",
                "--tone",
                "minimal",
                "--topics",
                "ai,engineering",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["data"]["client"] == "vanilla"
        assert data["data"]["tone"] == "minimal"
        assert data["data"]["topics"] == ["ai", "engineering"]

    def test_init_no_workflow(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        result = cli_runner.invoke(
            cli,
            [
                "--json",
                "--no-interact",
                "init",
                str(tmp_path),
                "--name",
                "nowf",
                "--no-workflow",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert ".ztlctl/workflow-answers.yml" not in data["data"]["files_created"]

    def test_init_existing_vault_fails(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        cli_runner.invoke(
            cli,
            ["--no-interact", "init", str(tmp_path), "--name", "first"],
        )
        result = cli_runner.invoke(
            cli,
            ["--no-interact", "init", str(tmp_path), "--name", "second"],
        )
        assert result.exit_code == 1

    def test_init_defaults_without_flags(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        result = cli_runner.invoke(
            cli,
            ["--json", "--no-interact", "init", str(tmp_path), "--name", "defaults"],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["data"]["client"] == "obsidian"
        assert data["data"]["tone"] == "research-partner"

    def test_init_creates_directories(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        cli_runner.invoke(
            cli,
            ["--no-interact", "init", str(tmp_path), "--name", "dirs"],
        )
        assert (tmp_path / ".ztlctl").is_dir()
        assert (tmp_path / "self").is_dir()
        assert (tmp_path / "notes").is_dir()


class TestInitCommandInteractive:
    """Tests for init with interactive prompts.

    Interactive prompts write to stdout before the JSON output, so we
    extract the JSON portion starting from the first '{'.
    """

    @staticmethod
    def _extract_json(output: str) -> dict:
        """Extract JSON object from mixed prompt+JSON output."""
        idx = output.index("{")
        return json.loads(output[idx:])

    def test_init_interactive_prompts(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        result = cli_runner.invoke(
            cli,
            ["--json", "init", str(tmp_path)],
            input="my-vault\nobsidian\nresearch-partner\nai,ml\n",
        )
        assert result.exit_code == 0
        data = self._extract_json(result.output)
        assert data["data"]["name"] == "my-vault"
        assert data["data"]["topics"] == ["ai", "ml"]

    def test_init_interactive_defaults(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        # Press enter for all defaults
        result = cli_runner.invoke(
            cli,
            ["--json", "init", str(tmp_path)],
            input="\n\n\n\n",
        )
        assert result.exit_code == 0
        data = self._extract_json(result.output)
        assert data["data"]["client"] == "obsidian"
        assert data["data"]["tone"] == "research-partner"

    def test_init_partial_flags_prompts_remaining(
        self, cli_runner: CliRunner, tmp_path: Path
    ) -> None:
        result = cli_runner.invoke(
            cli,
            ["--json", "init", str(tmp_path), "--name", "partial", "--client", "vanilla"],
            input="assistant\nweb\n",
        )
        assert result.exit_code == 0
        data = self._extract_json(result.output)
        assert data["data"]["name"] == "partial"
        assert data["data"]["client"] == "vanilla"
        assert data["data"]["tone"] == "assistant"

    def test_init_empty_topics_interactive(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        result = cli_runner.invoke(
            cli,
            ["--json", "init", str(tmp_path)],
            input="empty-topics\nobsidian\nminimal\n\n",
        )
        assert result.exit_code == 0
        data = self._extract_json(result.output)
        assert data["data"]["topics"] == []
