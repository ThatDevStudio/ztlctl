"""Tests for ServiceResult and ServiceError."""

import json

from ztlctl.services.result import ServiceError, ServiceResult


class TestServiceResult:
    def test_success_construction(self) -> None:
        result = ServiceResult(ok=True, op="create_note", data={"id": "ztl_abc12345"})
        assert result.ok is True
        assert result.op == "create_note"
        assert result.data == {"id": "ztl_abc12345"}
        assert result.warnings == []
        assert result.error is None
        assert result.meta is None

    def test_error_construction(self) -> None:
        error = ServiceError(code="E001", message="Not found")
        result = ServiceResult(ok=False, op="get", error=error)
        assert result.ok is False
        assert result.error is not None
        assert result.error.code == "E001"
        assert result.error.message == "Not found"

    def test_with_warnings(self) -> None:
        result = ServiceResult(
            ok=True,
            op="create_note",
            warnings=["Orphan note created (no links)"],
        )
        assert len(result.warnings) == 1

    def test_json_serialization(self) -> None:
        result = ServiceResult(
            ok=True,
            op="test",
            data={"key": "value"},
            meta={"duration_ms": 42},
        )
        raw = result.model_dump_json()
        parsed = json.loads(raw)
        assert parsed["ok"] is True
        assert parsed["op"] == "test"
        assert parsed["data"]["key"] == "value"
        assert parsed["meta"]["duration_ms"] == 42

    def test_frozen(self) -> None:
        result = ServiceResult(ok=True, op="test")
        try:
            result.ok = False  # type: ignore[misc]
            raise AssertionError("Should have raised")
        except Exception:
            pass  # Expected — frozen model


class TestServiceError:
    def test_with_detail(self) -> None:
        error = ServiceError(
            code="COLLISION",
            message="ID collision",
            detail={"existing_id": "ztl_abc12345", "title": "Test"},
        )
        assert error.detail["existing_id"] == "ztl_abc12345"

    def test_default_detail(self) -> None:
        error = ServiceError(code="E001", message="bad")
        assert error.detail == {}
