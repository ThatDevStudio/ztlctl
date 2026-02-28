"""Runtime CLI coverage for missing git binary handling."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from ztlctl.cli import cli


@pytest.mark.usefixtures("_isolated_vault")
class TestGitMissingRuntime:
    def test_create_note_succeeds_when_git_missing(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        no_bin_dir = tmp_path / "no-bin"
        no_bin_dir.mkdir()
        monkeypatch.setenv("PATH", str(no_bin_dir))

        cli_runner = CliRunner()
        result = cli_runner.invoke(
            cli,
            [
                "-v",
                "--json",
                "--sync",
                "create",
                "note",
                "No Git Available",
                "--tags",
                "test/scope",
            ],
        )

        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["ok"] is True
        assert (tmp_path / data["data"]["path"]).exists()
        assert "git add failed" in result.stderr.lower()
        assert "traceback" not in result.stderr.lower()
