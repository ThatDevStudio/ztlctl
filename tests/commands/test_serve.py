"""Tests for the serve command."""

from __future__ import annotations

import pytest
from click.testing import CliRunner

from ztlctl.cli import cli


@pytest.fixture
def cli_runner() -> CliRunner:
    return CliRunner()


class TestServeCommand:
    """Tests for ztlctl serve."""

    def test_serve_registered(self, cli_runner: CliRunner):
        result = cli_runner.invoke(cli, ["--help"])
        assert "serve" in result.output

    def test_serve_help_shows_transports(self, cli_runner: CliRunner) -> None:
        result = cli_runner.invoke(cli, ["serve", "--help"])
        assert "stdio" in result.output
        assert "sse" in result.output
        assert "streamable-http" in result.output

    def test_serve_help_shows_host_port(self, cli_runner: CliRunner) -> None:
        result = cli_runner.invoke(cli, ["serve", "--help"])
        assert "--host" in result.output
        assert "--port" in result.output
