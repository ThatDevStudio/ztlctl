"""End-to-end integration tests for verbose telemetry.

Validates the full pipeline:
  CLI flag (-v) -> AppContext -> enable_telemetry() -> @traced service methods
  -> span tree in ServiceResult.meta -> renderer outputs hierarchical span tree.
"""

from __future__ import annotations

import json
from collections.abc import Generator

import pytest
from click.testing import CliRunner

from ztlctl.cli import cli
from ztlctl.services.telemetry import _current_span, _verbose_enabled, disable_telemetry


@pytest.fixture(autouse=True)
def _reset_telemetry() -> Generator[None]:
    """Ensure telemetry ContextVar is reset between tests.

    The --verbose flag calls enable_telemetry() which sets a ContextVar.
    Without cleanup, enabled state leaks across tests in the same thread.
    """
    yield
    disable_telemetry()
    _current_span.set(None)


@pytest.mark.usefixtures("_isolated_vault")
class TestVerboseTelemetry:
    """Test --verbose produces telemetry span tree in output."""

    def setup_method(self) -> None:
        self.runner = CliRunner()

    def test_verbose_create_shows_telemetry(self) -> None:
        """Verbose mode renders the meta block with telemetry span tree."""
        result = self.runner.invoke(cli, ["-v", "create", "note", "Verbose Tel Note"])
        assert result.exit_code == 0
        assert "meta:" in result.output
        assert "CreateService.create_note" in result.output
        assert "ms" in result.output

    def test_verbose_create_shows_sub_stages(self) -> None:
        """Verbose mode shows trace_span sub-stages (validate, generate, etc.)."""
        result = self.runner.invoke(cli, ["-v", "create", "note", "Sub Stage Note"])
        assert result.exit_code == 0
        assert "validate" in result.output
        assert "generate" in result.output
        assert "persist" in result.output
        assert "index" in result.output

    def test_non_verbose_no_telemetry(self) -> None:
        """Non-verbose mode does not include meta or telemetry output."""
        result = self.runner.invoke(cli, ["create", "note", "No Tel Note"])
        assert result.exit_code == 0
        assert "meta:" not in result.output
        assert "telemetry" not in result.output
        assert "CreateService" not in result.output

    def test_verbose_json_includes_telemetry_in_meta(self) -> None:
        """Verbose + JSON mode serializes telemetry in the meta field."""
        result = self.runner.invoke(cli, ["-v", "--json", "create", "note", "JSON Tel Note"])
        assert result.exit_code == 0
        # The JSON output may have structlog lines before it; find the JSON object
        lines = result.output.strip().splitlines()
        # The formatted JSON result spans multiple lines; find the main payload
        json_text = result.output.strip()
        # Skip any structlog lines at the start (they're also valid JSON but single-line)
        main_lines: list[str] = []
        capture = False
        for line in lines:
            if line.strip().startswith("{") and not capture:
                # Could be a structlog line or the start of the result JSON
                try:
                    obj = json.loads(line)
                    # If it parses as a single line and has "ok" key, it's the result
                    if "ok" in obj:
                        json_text = line
                        break
                except json.JSONDecodeError:
                    # Multi-line JSON starts here
                    capture = True
                    main_lines.append(line)
            elif capture:
                main_lines.append(line)

        if main_lines:
            json_text = "\n".join(main_lines)

        data = json.loads(json_text)
        assert data["ok"] is True
        assert data["meta"] is not None
        assert "telemetry" in data["meta"]
        assert data["meta"]["telemetry"]["name"] == "CreateService.create_note"
        assert "duration_ms" in data["meta"]["telemetry"]
        assert "children" in data["meta"]["telemetry"]

    def test_log_json_flag_accepted(self) -> None:
        """The --log-json flag is accepted and does not cause errors."""
        result = self.runner.invoke(cli, ["-v", "--log-json", "create", "note", "JSON Log Note"])
        assert result.exit_code == 0
        assert "OK" in result.output or "create_note" in result.output

    def test_log_json_produces_json_log_lines(self) -> None:
        """With --log-json, structlog emits JSON-formatted log lines."""
        result = self.runner.invoke(cli, ["-v", "--log-json", "create", "note", "JSON Lines Note"])
        assert result.exit_code == 0
        # structlog JSON lines appear in output; find one with span.complete
        found_json_log = False
        for line in result.output.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                if obj.get("event") == "span.complete":
                    found_json_log = True
                    assert "span_name" in obj
                    assert "duration_ms" in obj
                    break
            except (json.JSONDecodeError, AttributeError):
                continue
        assert found_json_log, "Expected a JSON log line with event=span.complete"

    def test_log_json_registration_lines_are_fully_structured(self) -> None:
        """Bootstrap plugin registration logs should include standard JSONL fields."""
        result = self.runner.invoke(
            cli,
            ["-v", "--log-json", "create", "note", "Registration JSON Note"],
        )
        assert result.exit_code == 0

        json_lines: list[dict[str, object]] = []
        for line in result.stderr.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                json_lines.append(json.loads(line))
            except json.JSONDecodeError:
                continue

        registration = [
            line
            for line in json_lines
            if str(line.get("event", "")).startswith("Registered plugin")
        ]
        assert registration, "Expected plugin registration log lines on stderr"
        for line in registration:
            assert "level" in line
            assert "logger" in line
            assert "timestamp" in line

    def test_telemetry_disabled_without_verbose(self) -> None:
        """Without --verbose, telemetry ContextVar remains disabled."""
        # Run non-verbose command
        result = self.runner.invoke(cli, ["create", "note", "Disabled Tel Note"])
        assert result.exit_code == 0
        # The ContextVar should not have been flipped (it's per-thread,
        # and CliRunner runs in the same thread)
        assert not _verbose_enabled.get()

    def test_verbose_reference_shows_telemetry(self) -> None:
        """Verbose mode works for reference creation too."""
        result = self.runner.invoke(cli, ["-v", "create", "reference", "Verbose Ref"])
        assert result.exit_code == 0
        assert "meta:" in result.output
        assert "CreateService.create_reference" in result.output

    def test_verbose_task_shows_telemetry(self) -> None:
        """Verbose mode works for task creation."""
        result = self.runner.invoke(cli, ["-v", "create", "task", "Verbose Task"])
        assert result.exit_code == 0
        assert "meta:" in result.output
        assert "CreateService.create_task" in result.output
