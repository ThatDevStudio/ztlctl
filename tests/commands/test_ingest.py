"""Tests for ingest CLI commands."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from ztlctl.cli import cli


@pytest.mark.usefixtures("_isolated_vault")
class TestIngestCommands:
    def test_ingest_text_from_stdin_json(self, cli_runner: CliRunner) -> None:
        result = cli_runner.invoke(
            cli,
            ["--json", "ingest", "text", "CLI Capture", "--stdin", "--as", "reference"],
            input="Captured body",
        )

        assert result.exit_code == 0, result.output
        payload = json.loads(result.output)
        assert payload["ok"] is True
        assert payload["data"]["type"] == "reference"

    def test_ingest_file_json(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        source = tmp_path / "source.txt"
        source.write_text("Imported file body", encoding="utf-8")

        result = cli_runner.invoke(
            cli,
            ["--json", "ingest", "file", str(source), "--title", "Imported File", "--as", "note"],
        )

        assert result.exit_code == 0, result.output
        payload = json.loads(result.output)
        assert payload["ok"] is True
        assert payload["data"]["type"] == "note"

    def test_ingest_url_without_provider_returns_error(self, cli_runner: CliRunner) -> None:
        result = cli_runner.invoke(
            cli,
            ["--json", "ingest", "url", "https://example.com/article", "--as", "reference"],
        )

        assert result.exit_code != 0
        payload = json.loads(result.output)
        assert payload["error"]["code"] == "NO_PROVIDER"

    def test_ingest_providers_lists_local_plugin_provider(
        self, cli_runner: CliRunner, tmp_path: Path
    ) -> None:
        plugin_dir = tmp_path / ".ztlctl" / "plugins"
        plugin_dir.mkdir(parents=True)
        plugin_dir.joinpath("mock_provider.py").write_text(
            """import pluggy
from ztlctl.plugins.contracts import SourceFetchResult, SourceProviderContribution

hookimpl = pluggy.HookimplMarker("ztlctl")


class MockProviderPlugin:
    @hookimpl
    def register_source_providers(self):
        return [
            SourceProviderContribution(
                name="mock-web",
                description="Mock provider",
                schemes=("https",),
                fetch=lambda request: SourceFetchResult(
                    body_text="Fetched body",
                    title="Fetched title",
                    canonical_url=request.content,
                ),
            )
        ]
""",
            encoding="utf-8",
        )

        result = cli_runner.invoke(cli, ["--json", "--sync", "ingest", "providers"])

        assert result.exit_code == 0, result.output
        payload = json.loads(result.output)
        assert payload["ok"] is True
        assert any(item["name"] == "mock-web" for item in payload["data"]["items"])

    def test_ingest_url_with_local_provider(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        plugin_dir = tmp_path / ".ztlctl" / "plugins"
        plugin_dir.mkdir(parents=True)
        plugin_dir.joinpath("mock_provider.py").write_text(
            """import pluggy
from ztlctl.plugins.contracts import SourceFetchResult, SourceProviderContribution

hookimpl = pluggy.HookimplMarker("ztlctl")


class MockProviderPlugin:
    @hookimpl
    def register_source_providers(self):
        return [
            SourceProviderContribution(
                name="mock-web",
                description="Mock provider",
                schemes=("https",),
                fetch=lambda request: SourceFetchResult(
                    body_text="Fetched body",
                    title="Fetched title",
                    canonical_url=request.content,
                    source_type="web",
                ),
            )
        ]
""",
            encoding="utf-8",
        )

        result = cli_runner.invoke(
            cli,
            [
                "--json",
                "--sync",
                "ingest",
                "url",
                "https://example.com/article",
                "--provider",
                "mock-web",
                "--as",
                "reference",
            ],
        )

        assert result.exit_code == 0, result.output
        payload = json.loads(result.output)
        assert payload["ok"] is True
        assert payload["data"]["provider"] == "mock-web"
