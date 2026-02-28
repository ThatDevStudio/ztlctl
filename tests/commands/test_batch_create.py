"""Tests for the create batch CLI subcommand."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from ztlctl.cli import cli


@pytest.mark.usefixtures("_isolated_vault")
class TestBatchCreateCommand:
    def test_batch_create_notes(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        items = [
            {"type": "note", "title": "Batch Note A"},
            {"type": "note", "title": "Batch Note B"},
        ]
        batch_file = tmp_path / "batch.json"
        batch_file.write_text(json.dumps(items), encoding="utf-8")

        result = cli_runner.invoke(cli, ["--json", "create", "batch", str(batch_file)])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert len(data["data"]["created"]) == 2

    def test_batch_create_mixed_types(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        items = [
            {"type": "note", "title": "Batch Mixed Note"},
            {"type": "reference", "title": "Batch Mixed Ref"},
            {"type": "task", "title": "Batch Mixed Task"},
        ]
        batch_file = tmp_path / "batch.json"
        batch_file.write_text(json.dumps(items), encoding="utf-8")

        result = cli_runner.invoke(cli, ["--json", "create", "batch", str(batch_file)])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert len(data["data"]["created"]) == 3

    def test_batch_strict_fails_on_bad_item(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        items = [
            {"type": "note", "title": "Good Note"},
            {"type": "invalid_type", "title": "Bad Item"},
        ]
        batch_file = tmp_path / "batch.json"
        batch_file.write_text(json.dumps(items), encoding="utf-8")

        result = cli_runner.invoke(cli, ["--json", "create", "batch", str(batch_file)])
        assert result.exit_code == 1

    def test_batch_partial_continues_on_error(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        items = [
            {"type": "note", "title": "Partial Good"},
            {"type": "invalid_type", "title": "Partial Bad"},
            {"type": "note", "title": "Partial Good 2"},
        ]
        batch_file = tmp_path / "batch.json"
        batch_file.write_text(json.dumps(items), encoding="utf-8")

        result = cli_runner.invoke(cli, ["--json", "create", "batch", str(batch_file), "--partial"])
        # Partial mode: succeeds overall but with errors
        data = json.loads(result.output)
        assert len(data["data"]["created"]) == 2
        assert len(data["data"]["errors"]) == 1

    def test_batch_invalid_json(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        batch_file = tmp_path / "bad.json"
        batch_file.write_text("not valid json", encoding="utf-8")

        result = cli_runner.invoke(cli, ["create", "batch", str(batch_file)])
        assert result.exit_code == 1

    def test_batch_not_array(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        batch_file = tmp_path / "obj.json"
        batch_file.write_text('{"type": "note", "title": "Single"}', encoding="utf-8")

        result = cli_runner.invoke(cli, ["create", "batch", str(batch_file)])
        assert result.exit_code == 1
        assert "array" in result.output

    def test_batch_not_array_json_uses_consistent_op(
        self, cli_runner: CliRunner, tmp_path: Path
    ) -> None:
        batch_file = tmp_path / "obj.json"
        batch_file.write_text('{"type": "note", "title": "Single"}', encoding="utf-8")

        result = cli_runner.invoke(cli, ["--json", "create", "batch", str(batch_file)])

        assert result.exit_code == 1
        data = json.loads(result.output)
        assert data["op"] == "create_batch"

    def test_batch_file_not_found(self, cli_runner: CliRunner) -> None:
        result = cli_runner.invoke(cli, ["create", "batch", "/nonexistent/file.json"])
        assert result.exit_code != 0
