"""Unit tests for McpResponse.from_result()."""

from __future__ import annotations

from ztlctl.mcp.response import COMMON_ERROR_RECOVERY, McpError, McpResponse
from ztlctl.services.result import ServiceError, ServiceResult


def test_from_result_ok() -> None:
    """from_result on ok result has ok=True, op, and data set."""
    r = ServiceResult(ok=True, op="test", data={"key": "val"})
    resp = McpResponse.from_result(r)
    assert resp.ok is True
    assert resp.op == "test"
    assert resp.data == {"key": "val"}


def test_from_result_error() -> None:
    """from_result on error result maps ServiceError to McpError."""
    r = ServiceResult(
        ok=False,
        op="test",
        error=ServiceError(code="NOT_FOUND", message="gone"),
    )
    resp = McpResponse.from_result(r)
    assert resp.ok is False
    assert resp.error is not None
    assert resp.error.code == "NOT_FOUND"
    assert resp.error.message == "gone"


def test_from_result_warnings() -> None:
    """from_result propagates warnings list."""
    r = ServiceResult(ok=True, op="test", warnings=["w1"])
    resp = McpResponse.from_result(r)
    assert resp.warnings == ["w1"]


def test_from_result_drops_meta() -> None:
    """from_result does NOT forward result.meta to MCP response."""
    r = ServiceResult(ok=True, op="test", meta={"timing": 1.0})
    resp = McpResponse.from_result(r)
    dumped = resp.model_dump(exclude_none=True)
    assert "meta" not in dumped


def test_model_dump_shape() -> None:
    """model_dump(exclude_none=True) on ok result has no warnings or error keys."""
    r = ServiceResult(ok=True, op="test_op", data={"x": 1})
    resp = McpResponse.from_result(r)
    dumped = resp.model_dump(exclude_none=True)
    assert dumped["ok"] is True
    assert dumped["op"] == "test_op"
    assert dumped["data"] == {"x": 1}
    # empty warnings should not appear
    assert "warnings" not in dumped
    # no error
    assert "error" not in dumped


def test_mcp_error_recovery_field() -> None:
    """McpError stores recovery when provided."""
    error = McpError(code="X", message="Y", recovery="R")
    assert error.recovery == "R"


def test_recovery_populated_from_common_dict() -> None:
    """from_result() falls back to COMMON_ERROR_RECOVERY when ServiceError.recovery is None."""
    r = ServiceResult(
        ok=False,
        op="test",
        error=ServiceError(code="NOT_FOUND", message="gone"),
    )
    resp = McpResponse.from_result(r)
    assert resp.error is not None
    assert resp.error.recovery == COMMON_ERROR_RECOVERY["NOT_FOUND"]


def test_recovery_from_service_error_overrides_dict() -> None:
    """ServiceError.recovery takes priority over COMMON_ERROR_RECOVERY fallback."""
    r = ServiceResult(
        ok=False,
        op="test",
        error=ServiceError(code="NOT_FOUND", message="gone", recovery="custom recovery"),
    )
    resp = McpResponse.from_result(r)
    assert resp.error is not None
    assert resp.error.recovery == "custom recovery"


def test_recovery_none_when_code_not_in_dict() -> None:
    """McpError.recovery is None when code not in COMMON_ERROR_RECOVERY and no recovery set."""
    r = ServiceResult(
        ok=False,
        op="test",
        error=ServiceError(code="UNKNOWN_CODE_XYZ", message="x"),
    )
    resp = McpResponse.from_result(r)
    assert resp.error is not None
    assert resp.error.recovery is None


def test_recovery_excluded_when_none_in_dump() -> None:
    """model_dump(exclude_none=True) omits recovery when None."""
    error = McpError(code="X", message="Y")
    dump = error.model_dump(exclude_none=True)
    assert "recovery" not in dump


def test_recovery_included_when_set_in_dump() -> None:
    """model_dump(exclude_none=True) includes recovery when set."""
    error = McpError(code="X", message="Y", recovery="R")
    dump = error.model_dump(exclude_none=True)
    assert dump["recovery"] == "R"


def test_all_codes_have_recovery() -> None:
    """All known ServiceError codes appear as keys in COMMON_ERROR_RECOVERY."""
    all_known_codes = {
        "NOT_FOUND",
        "VALIDATION_FAILED",
        "ID_COLLISION",
        "NO_ACTIVE_SESSION",
        "ACTIVE_SESSION_EXISTS",
        "INVALID_TRANSITION",
        "EMPTY_QUERY",
        "UNKNOWN_TYPE",
        "NO_PATH",
        "ALREADY_OPEN",
        "NO_ENTRIES",
        "NO_HISTORY",
        "NO_LINK",
        "BATCH_PARTIAL",
        "BATCH_FAILED",
        "INIT_STEP_FAILED",
        "INVALID_PROFILE",
        "VAULT_EXISTS",
        "NO_CONFIG",
        "PROFILE_NOT_FOUND",
        "NOT_A_VAULT",
        "WORKFLOW_EXISTS",
        "WORKFLOW_NOT_INITIALIZED",
        "WORKFLOW_INIT_FAILED",
        "WORKFLOW_UPDATE_FAILED",
        "WORKFLOW_VALIDATION_FAILED",
        "CHECK_FAILED",
        "BACKUP_FAILED",
        "MIGRATION_FAILED",
        "STAMP_FAILED",
        "INVALID_FORMAT",
        "INVALID_VIEWER",
        "NO_BACKUPS",
        "SEMANTIC_UNAVAILABLE",
        "UNSUPPORTED_INPUT",
        "NO_PROVIDER",
    }
    missing = all_known_codes - set(COMMON_ERROR_RECOVERY.keys())
    assert not missing, f"Codes missing from COMMON_ERROR_RECOVERY: {sorted(missing)}"
