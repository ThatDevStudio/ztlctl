"""Tests for the serve command."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

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

    @pytest.mark.usefixtures("_isolated_vault")
    def test_serve_invokes_create_server_with_transport_options(
        self, cli_runner: CliRunner
    ) -> None:
        server = MagicMock()

        with (
            patch("ztlctl.mcp.server.mcp_available", True),
            patch("ztlctl.mcp.server.create_server", return_value=server) as create_server,
        ):
            result = cli_runner.invoke(
                cli,
                [
                    "serve",
                    "--transport",
                    "sse",
                    "--host",
                    "0.0.0.0",
                    "--port",
                    "9000",
                ],
            )

        assert result.exit_code == 0
        create_server.assert_called_once()
        _, kwargs = create_server.call_args
        assert kwargs["host"] == "0.0.0.0"
        assert kwargs["port"] == 9000
        server.run.assert_called_once_with(transport="sse")
