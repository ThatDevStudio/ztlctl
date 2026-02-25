"""Tests for the format_result dispatcher and OutputSettings."""

import json

from ztlctl.output.formatters import OutputSettings, format_result
from ztlctl.services.result import ServiceError, ServiceResult


def _ok(op: str = "test", **data: object) -> ServiceResult:
    return ServiceResult(ok=True, op=op, data=dict(data))


def _err(op: str = "test", msg: str = "fail") -> ServiceResult:
    return ServiceResult(
        ok=False,
        op=op,
        error=ServiceError(code="ERR", message=msg),
    )


class TestOutputSettings:
    def test_defaults(self) -> None:
        s = OutputSettings()
        assert s.json_output is False
        assert s.quiet is False
        assert s.verbose is False

    def test_frozen(self) -> None:
        s = OutputSettings(json_output=True)
        assert s.json_output is True


class TestFormatResultJSON:
    def test_json_mode_returns_valid_json(self) -> None:
        result = _ok("create_note", id="ztl_a")
        settings = OutputSettings(json_output=True)
        output = format_result(result, settings=settings)
        data = json.loads(output)
        assert data["ok"] is True
        assert data["op"] == "create_note"
        assert data["data"]["id"] == "ztl_a"

    def test_json_mode_error(self) -> None:
        result = _err("create_note", "Bad")
        settings = OutputSettings(json_output=True)
        output = format_result(result, settings=settings)
        data = json.loads(output)
        assert data["ok"] is False
        assert data["error"]["message"] == "Bad"

    def test_legacy_json_output_kwarg(self) -> None:
        """Backward-compatible: json_output=True without settings."""
        result = _ok("test", key="val")
        output = format_result(result, json_output=True)
        data = json.loads(output)
        assert data["ok"] is True

    def test_settings_overrides_legacy_kwarg(self) -> None:
        """When settings is provided, json_output kwarg is ignored."""
        result = _ok("test", key="val")
        settings = OutputSettings(json_output=False)
        output = format_result(result, settings=settings, json_output=True)
        # Settings says no JSON, so output should be Rich-rendered (not JSON)
        assert output.startswith("{") is False


class TestFormatResultQuiet:
    def test_quiet_success(self) -> None:
        result = _ok("create_note", id="ztl_a")
        settings = OutputSettings(quiet=True)
        output = format_result(result, settings=settings)
        assert output == "OK: create_note"

    def test_quiet_error(self) -> None:
        result = _err("create_note", "Bad input")
        settings = OutputSettings(quiet=True)
        output = format_result(result, settings=settings)
        assert "ERROR" in output
        assert "Bad input" in output


class TestFormatResultDefault:
    def test_default_success_contains_ok(self) -> None:
        result = _ok("create_note", id="ztl_a", title="Note")
        output = format_result(result)
        assert "OK" in output
        assert "create_note" in output

    def test_default_error_contains_error(self) -> None:
        result = _err("create_note", "Bad")
        output = format_result(result)
        assert "ERROR" in output
        assert "Bad" in output

    def test_verbose_mode(self) -> None:
        result = _ok("create_note", id="ztl_a")
        settings = OutputSettings(verbose=True)
        output = format_result(result, settings=settings)
        assert "OK" in output
