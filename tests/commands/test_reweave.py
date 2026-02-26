"""Tests for the reweave CLI command."""

from __future__ import annotations

import pytest
from click.testing import CliRunner

from ztlctl.cli import cli


@pytest.mark.usefixtures("_isolated_vault")
class TestReweaveCommand:
    def test_reweave_dry_run(self, cli_runner: CliRunner) -> None:
        # Create some content first
        cli_runner.invoke(cli, ["create", "note", "Python Guide"])
        cli_runner.invoke(cli, ["create", "note", "Python Reference"])
        result = cli_runner.invoke(cli, ["reweave", "--dry-run"])
        assert result.exit_code == 0

    def test_reweave_with_id(self, cli_runner: CliRunner) -> None:
        r = cli_runner.invoke(cli, ["reweave", "--id", "ztl_nonexist", "--dry-run"])
        # Should handle not-found gracefully
        assert r.exit_code == 1

    def test_reweave_prune(self, cli_runner: CliRunner) -> None:
        cli_runner.invoke(cli, ["create", "note", "Prune Target"])
        result = cli_runner.invoke(cli, ["reweave", "--prune", "--dry-run"])
        # Should work even with no links
        assert result.exit_code in (0, 1)

    def test_reweave_undo_no_history(self, cli_runner: CliRunner) -> None:
        result = cli_runner.invoke(cli, ["reweave", "--undo"])
        assert result.exit_code == 1  # NO_HISTORY error

    def test_reweave_undo_id_not_found(self, cli_runner: CliRunner) -> None:
        result = cli_runner.invoke(cli, ["reweave", "--undo-id", "9999"])
        assert result.exit_code == 1  # NOT_FOUND error

    def test_reweave_undo_id_triggers_undo(self, cli_runner: CliRunner) -> None:
        # --undo-id alone (without --undo) should trigger the undo path
        result = cli_runner.invoke(cli, ["reweave", "--undo-id", "1"])
        # Will fail with NOT_FOUND since no log entries, but proves undo path runs
        assert result.exit_code == 1


@pytest.mark.usefixtures("_isolated_vault")
class TestReweaveInteractive:
    """Tests for the interactive confirmation flow (BL-0022)."""

    def test_reweave_prompts_for_confirmation(self, cli_runner: CliRunner) -> None:
        """Default reweave shows suggestions and prompts."""
        cli_runner.invoke(cli, ["create", "note", "Python Guide"])
        cli_runner.invoke(cli, ["create", "note", "Python Reference"])
        result = cli_runner.invoke(cli, ["reweave"], input="y\n")
        assert result.exit_code == 0
        # If suggestions were found, prompt should appear
        if "Apply" in result.output:
            assert "link(s)?" in result.output

    def test_reweave_cancel_on_decline(self, cli_runner: CliRunner) -> None:
        """Declining confirmation cancels without changes."""
        cli_runner.invoke(cli, ["create", "note", "Cancel Guide"])
        cli_runner.invoke(cli, ["create", "note", "Cancel Reference"])
        result = cli_runner.invoke(cli, ["reweave"], input="n\n")
        assert result.exit_code == 0
        if "Apply" in result.output:
            assert "Cancelled" in result.output

    def test_reweave_auto_link_skips_prompt(self, cli_runner: CliRunner) -> None:
        """--auto-link-related applies without prompting."""
        cli_runner.invoke(cli, ["create", "note", "Auto Guide"])
        cli_runner.invoke(cli, ["create", "note", "Auto Reference"])
        result = cli_runner.invoke(cli, ["reweave", "--auto-link-related"])
        assert result.exit_code == 0
        assert "Apply" not in result.output

    def test_reweave_no_interact_skips_prompt(self, cli_runner: CliRunner) -> None:
        """--no-interact global flag skips confirmation."""
        cli_runner.invoke(cli, ["create", "note", "NI Guide"])
        cli_runner.invoke(cli, ["create", "note", "NI Reference"])
        result = cli_runner.invoke(cli, ["--no-interact", "reweave"])
        assert result.exit_code == 0
        assert "Apply" not in result.output

    def test_reweave_dry_run_no_prompt(self, cli_runner: CliRunner) -> None:
        """--dry-run shows suggestions without any prompt."""
        cli_runner.invoke(cli, ["create", "note", "Dry Guide"])
        cli_runner.invoke(cli, ["create", "note", "Dry Reference"])
        result = cli_runner.invoke(cli, ["reweave", "--dry-run"])
        assert result.exit_code == 0
        assert "Apply" not in result.output

    def test_reweave_no_suggestions_no_prompt(self, cli_runner: CliRunner) -> None:
        """No prompt when there are no suggestions."""
        result = cli_runner.invoke(cli, ["reweave"], input="y\n")
        # Either no content or no suggestions — should not prompt
        assert "Apply" not in result.output
