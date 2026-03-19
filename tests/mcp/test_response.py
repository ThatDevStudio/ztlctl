"""Unit tests for McpResponse.from_result()."""

from __future__ import annotations

from ztlctl.mcp.response import McpResponse
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
