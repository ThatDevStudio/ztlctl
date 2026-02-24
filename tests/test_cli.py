"""Tests for the root ztlctl CLI."""

import pytest
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


# --- Global flags ---


def test_json_flag_accepted(cli_runner: CliRunner) -> None:
    result = cli_runner.invoke(cli, ["--json", "--version"])
    assert result.exit_code == 0


def test_quiet_flag_accepted(cli_runner: CliRunner) -> None:
    result = cli_runner.invoke(cli, ["-q", "--version"])
    assert result.exit_code == 0


def test_verbose_flag_accepted(cli_runner: CliRunner) -> None:
    result = cli_runner.invoke(cli, ["-v", "--version"])
    assert result.exit_code == 0


def test_no_interact_flag_accepted(cli_runner: CliRunner) -> None:
    result = cli_runner.invoke(cli, ["--no-interact", "--version"])
    assert result.exit_code == 0


def test_no_reweave_flag_accepted(cli_runner: CliRunner) -> None:
    result = cli_runner.invoke(cli, ["--no-reweave", "--version"])
    assert result.exit_code == 0


def test_config_option_accepted(cli_runner: CliRunner) -> None:
    result = cli_runner.invoke(cli, ["-c", "/tmp/test.toml", "--version"])
    assert result.exit_code == 0


def test_sync_flag_accepted(cli_runner: CliRunner) -> None:
    result = cli_runner.invoke(cli, ["--sync", "--version"])
    assert result.exit_code == 0


# --- Command groups registered ---

EXPECTED_GROUPS = [
    "create",
    "query",
    "graph",
    "agent",
    "garden",
    "export",
    "workflow",
]

EXPECTED_COMMANDS = [
    "check",
    "init",
    "upgrade",
    "reweave",
    "archive",
    "extract",
]


@pytest.mark.parametrize("group", EXPECTED_GROUPS)
def test_group_registered(cli_runner: CliRunner, group: str) -> None:
    result = cli_runner.invoke(cli, [group, "--help"])
    assert result.exit_code == 0, f"{group} --help failed: {result.output}"


@pytest.mark.parametrize("command", EXPECTED_COMMANDS)
def test_command_registered(cli_runner: CliRunner, command: str) -> None:
    result = cli_runner.invoke(cli, [command, "--help"])
    assert result.exit_code == 0, f"{command} --help failed: {result.output}"


def test_all_commands_in_help(cli_runner: CliRunner) -> None:
    """All 13 commands should appear in the root --help output."""
    result = cli_runner.invoke(cli, ["--help"])
    for name in EXPECTED_GROUPS + EXPECTED_COMMANDS:
        assert name in result.output, f"{name} missing from --help"
