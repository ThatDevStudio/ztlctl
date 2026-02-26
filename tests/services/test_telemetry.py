"""Tests for telemetry primitives: Span, trace_span, @traced."""

from __future__ import annotations

import time
from collections.abc import Generator

import pytest

from ztlctl.services.result import ServiceResult
from ztlctl.services.telemetry import (
    Span,
    _current_span,
    disable_telemetry,
    enable_telemetry,
    get_current_span,
    trace_span,
    traced,
)


@pytest.fixture(autouse=True)
def _reset_telemetry_state() -> Generator[None]:
    """Ensure clean telemetry state for every test."""
    yield
    disable_telemetry()
    _current_span.set(None)


# ── Span unit tests ──────────────────────────────────────────────────


class TestSpan:
    def test_duration_before_end_is_zero(self) -> None:
        span = Span(name="test")
        assert span.duration_ms == 0.0

    def test_duration_after_end(self) -> None:
        span = Span(name="test")
        time.sleep(0.005)
        span.end()
        assert span.duration_ms > 0

    def test_to_dict_minimal(self) -> None:
        span = Span(name="root")
        span.end()
        d = span.to_dict()
        assert d["name"] == "root"
        assert "duration_ms" in d
        assert "children" not in d  # no empty children key

    def test_to_dict_with_children(self) -> None:
        root = Span(name="root")
        child = Span(name="child", parent=root)
        root.children.append(child)
        child.end()
        root.end()
        d = root.to_dict()
        assert len(d["children"]) == 1
        assert d["children"][0]["name"] == "child"

    def test_annotate(self) -> None:
        span = Span(name="test")
        span.annotate("rows", 42)
        span.end()
        d = span.to_dict()
        assert d["annotations"] == {"rows": 42}

    def test_tokens_and_cost(self) -> None:
        span = Span(name="test")
        span.tokens = 500
        span.cost = 0.01
        span.end()
        d = span.to_dict()
        assert d["tokens"] == 500
        assert d["cost"] == 0.01

    def test_no_tokens_or_cost_omitted(self) -> None:
        span = Span(name="test")
        span.end()
        d = span.to_dict()
        assert "tokens" not in d
        assert "cost" not in d


# ── trace_span tests ─────────────────────────────────────────────────


class TestTraceSpan:
    def test_disabled_yields_none(self) -> None:
        with trace_span("test") as span:
            assert span is None

    def test_no_root_yields_none(self) -> None:
        enable_telemetry()
        try:
            with trace_span("test") as span:
                assert span is None
        finally:
            disable_telemetry()

    def test_enabled_with_root(self) -> None:
        enable_telemetry()
        root = Span(name="root")
        token = _current_span.set(root)
        try:
            with trace_span("child") as span:
                assert span is not None
                assert span.name == "child"
            assert len(root.children) == 1
            assert root.children[0].end_time is not None
        finally:
            _current_span.reset(token)
            disable_telemetry()

    def test_nested_spans(self) -> None:
        enable_telemetry()
        root = Span(name="root")
        token = _current_span.set(root)
        try:
            with trace_span("a"):
                with trace_span("b"):
                    pass
            assert len(root.children) == 1
            assert root.children[0].name == "a"
            assert len(root.children[0].children) == 1
            assert root.children[0].children[0].name == "b"
        finally:
            _current_span.reset(token)
            disable_telemetry()

    def test_span_annotation_within_context(self) -> None:
        enable_telemetry()
        root = Span(name="root")
        token = _current_span.set(root)
        try:
            with trace_span("child") as span:
                assert span is not None
                span.annotate("key", "value")
            assert root.children[0].annotations == {"key": "value"}
        finally:
            _current_span.reset(token)
            disable_telemetry()


# ── @traced decorator tests ──────────────────────────────────────────


class TestTracedDecorator:
    def test_noop_when_disabled(self) -> None:
        @traced
        def my_func() -> ServiceResult:
            return ServiceResult(ok=True, op="test")

        result = my_func()
        assert result.ok
        assert result.meta is None

    def test_injects_meta_when_enabled(self) -> None:
        @traced
        def my_func() -> ServiceResult:
            return ServiceResult(ok=True, op="test")

        enable_telemetry()
        try:
            result = my_func()
            assert result.meta is not None
            assert "telemetry" in result.meta
            expected_name = "TestTracedDecorator.test_injects_meta_when_enabled.<locals>.my_func"
            assert result.meta["telemetry"]["name"] == expected_name
            assert result.meta["telemetry"]["duration_ms"] >= 0
        finally:
            disable_telemetry()

    def test_preserves_existing_meta(self) -> None:
        @traced
        def my_func() -> ServiceResult:
            return ServiceResult(ok=True, op="test", meta={"existing": "data"})

        enable_telemetry()
        try:
            result = my_func()
            assert result.meta is not None
            assert result.meta["existing"] == "data"
            assert "telemetry" in result.meta
        finally:
            disable_telemetry()

    def test_non_service_result_passthrough(self) -> None:
        @traced
        def my_func() -> str:
            return "hello"

        enable_telemetry()
        try:
            result = my_func()
            assert result == "hello"
        finally:
            disable_telemetry()

    def test_child_spans_in_meta(self) -> None:
        @traced
        def my_func() -> ServiceResult:
            with trace_span("stage_a"):
                pass
            with trace_span("stage_b"):
                pass
            return ServiceResult(ok=True, op="test")

        enable_telemetry()
        try:
            result = my_func()
            assert result.meta is not None
            children = result.meta["telemetry"]["children"]
            assert len(children) == 2
            assert children[0]["name"] == "stage_a"
            assert children[1]["name"] == "stage_b"
        finally:
            disable_telemetry()

    def test_exception_still_logs(self) -> None:
        @traced
        def my_func() -> ServiceResult:
            msg = "boom"
            raise ValueError(msg)

        enable_telemetry()
        try:
            with pytest.raises(ValueError, match="boom"):
                my_func()
        finally:
            disable_telemetry()

    def test_error_result_gets_telemetry(self) -> None:
        @traced
        def my_func() -> ServiceResult:
            from ztlctl.services.result import ServiceError

            return ServiceResult(
                ok=False,
                op="test",
                error=ServiceError(code="FAIL", message="oops"),
            )

        enable_telemetry()
        try:
            result = my_func()
            assert not result.ok
            assert result.meta is not None
            assert "telemetry" in result.meta
        finally:
            disable_telemetry()


# ── get_current_span tests ───────────────────────────────────────────


class TestGetCurrentSpan:
    def test_returns_none_when_disabled(self) -> None:
        assert get_current_span() is None

    def test_returns_span_when_enabled(self) -> None:
        enable_telemetry()
        root = Span(name="root")
        token = _current_span.set(root)
        try:
            assert get_current_span() is root
        finally:
            _current_span.reset(token)
            disable_telemetry()
