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
