"""Tests for the root ztlctl CLI."""

from click.testing import CliRunner

from ztlctl import __version__
from ztlctl.cli import cli


def test_cli_help(cli_runner: CliRunner) -> None:
    result = cli_runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "ztlctl" in result.output


def test_cli_version(cli_runner: CliRunner) -> None:
    result = cli_runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert __version__ in result.output


def test_cli_no_args(cli_runner: CliRunner) -> None:
    result = cli_runner.invoke(cli, [])
    assert result.exit_code == 0
    assert "Usage" in result.output
