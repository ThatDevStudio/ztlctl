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
                "--profile",
                "core",
                "--tone",
                "minimal",
                "--topics",
                "ai,engineering",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["data"]["profile"] == "core"
        assert data["data"]["client"] == "none"
        assert data["data"]["tone"] == "minimal"
        assert data["data"]["topics"] == ["ai", "engineering"]
        assert data["data"]["setup_steps"] == []

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
        assert data["data"]["profile"] == "core"
        assert data["data"]["client"] == "none"
        assert data["data"]["tone"] == "research-partner"

    def test_init_vanilla_alias_emits_warning_and_normalizes(
        self, cli_runner: CliRunner, tmp_path: Path
    ) -> None:
        result = cli_runner.invoke(
            cli,
            [
                "--json",
                "--no-interact",
                "init",
                str(tmp_path),
                "--name",
                "alias-vault",
                "--client",
                "vanilla",
            ],
        )

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["data"]["profile"] == "core"
        assert data["data"]["client"] == "none"
        assert any("deprecated" in warning.lower() for warning in data["warnings"])

    def test_init_creates_directories(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        cli_runner.invoke(
            cli,
            ["--no-interact", "init", str(tmp_path), "--name", "dirs"],
        )
        assert (tmp_path / ".ztlctl").is_dir()
        assert (tmp_path / "self").is_dir()
        assert (tmp_path / "notes").is_dir()

    def test_init_obsidian_json_includes_setup_steps(
        self, cli_runner: CliRunner, tmp_path: Path
    ) -> None:
        result = cli_runner.invoke(
            cli,
            [
                "--json",
                "--no-interact",
                "init",
                str(tmp_path),
                "--name",
                "obsidian-json",
                "--profile",
                "obsidian",
            ],
        )

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["data"]["profile"] == "obsidian"
        assert len(data["data"]["setup_steps"]) == 3
        assert "Install the curated Obsidian plugins" in data["data"]["setup_steps"][0]["title"]

    def test_init_obsidian_output_prints_next_steps(
        self, cli_runner: CliRunner, tmp_path: Path
    ) -> None:
        result = cli_runner.invoke(
            cli,
            [
                "--no-interact",
                "init",
                str(tmp_path),
                "--name",
                "obsidian-output",
                "--profile",
                "obsidian",
            ],
        )

        assert result.exit_code == 0
        assert "Next steps:" in result.output
        assert "Install the curated Obsidian plugins" in result.output
        assert "Dataview" in result.output


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
            input="my-vault\ncore\nresearch-partner\nai,ml\n",
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
        assert data["data"]["profile"] == "core"
        assert data["data"]["client"] == "none"
        assert data["data"]["tone"] == "research-partner"

    def test_init_partial_flags_prompts_remaining(
        self, cli_runner: CliRunner, tmp_path: Path
    ) -> None:
        result = cli_runner.invoke(
            cli,
            ["--json", "init", str(tmp_path), "--name", "partial", "--profile", "core"],
            input="assistant\nweb\n",
        )
        assert result.exit_code == 0
        data = self._extract_json(result.output)
        assert data["data"]["name"] == "partial"
        assert data["data"]["profile"] == "core"
        assert data["data"]["client"] == "none"
        assert data["data"]["tone"] == "assistant"

    def test_init_empty_topics_interactive(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        result = cli_runner.invoke(
            cli,
            ["--json", "init", str(tmp_path)],
            input="empty-topics\ncore\nminimal\n\n",
        )
        assert result.exit_code == 0
        data = self._extract_json(result.output)
        assert data["data"]["topics"] == []
