"""Tests for archive CLI command."""

from __future__ import annotations

import json

import pytest
from click.testing import CliRunner

from ztlctl.cli import cli


@pytest.mark.usefixtures("_isolated_vault")
class TestArchiveCommand:
    def test_archive_success(self, cli_runner: CliRunner) -> None:
        """Archive a created note via CLI."""
        # Create a note first
        create_result = cli_runner.invoke(cli, ["--json", "create", "note", "Archive CLI Test"])
        assert create_result.exit_code == 0
        data = json.loads(create_result.output)
        note_id = data["data"]["id"]

        # Archive it
        result = cli_runner.invoke(cli, ["--json", "archive", note_id])
        assert result.exit_code == 0
        archive_data = json.loads(result.output)
        assert archive_data["ok"] is True
        assert archive_data["data"]["id"] == note_id

    def test_archive_not_found(self, cli_runner: CliRunner) -> None:
        """Archive nonexistent ID fails."""
        result = cli_runner.invoke(cli, ["--json", "archive", "ztl_nonexist"])
        assert result.exit_code == 1

    def test_archive_help(self, cli_runner: CliRunner) -> None:
        result = cli_runner.invoke(cli, ["archive", "--help"])
        assert result.exit_code == 0
        assert "CONTENT_ID" in result.output
