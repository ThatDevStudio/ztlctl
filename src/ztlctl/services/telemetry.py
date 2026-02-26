"""Telemetry primitives — Span, @traced, trace_span.

Near-zero overhead when disabled (single ContextVar.get per call).
When enabled via --verbose, builds hierarchical span trees with timing
and injects them into ServiceResult.meta.
"""

from __future__ import annotations

import functools
import logging
import time
from collections.abc import Callable, Generator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Any, ParamSpec, TypeVar

from ztlctl.services.result import ServiceResult

logger = logging.getLogger(__name__)

# ── Context variables ────────────────────────────────────────────────

_verbose_enabled: ContextVar[bool] = ContextVar("_verbose_enabled", default=False)
_current_span: ContextVar[Span | None] = ContextVar("_current_span", default=None)


# ── Span ─────────────────────────────────────────────────────────────


@dataclass
class Span:
    """Hierarchical timing span with optional cost/token tracking."""

    name: str
    parent: Span | None = None
    children: list[Span] = field(default_factory=list)
    start_time: float = field(default_factory=time.perf_counter)
    end_time: float | None = None
    tokens: int | None = None
    cost: float | None = None
    annotations: dict[str, Any] = field(default_factory=dict)

    @property
    def duration_ms(self) -> float:
        if self.end_time is None:
            return 0.0
        return (self.end_time - self.start_time) * 1000

    def end(self) -> None:
        self.end_time = time.perf_counter()

    def annotate(self, key: str, value: Any) -> None:
        self.annotations[key] = value

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "name": self.name,
            "duration_ms": round(self.duration_ms, 2),
        }
        if self.tokens is not None:
            result["tokens"] = self.tokens
        if self.cost is not None:
            result["cost"] = self.cost
        if self.annotations:
            result["annotations"] = self.annotations
        if self.children:
            result["children"] = [c.to_dict() for c in self.children]
        return result


# ── trace_span context manager ───────────────────────────────────────


@contextmanager
def trace_span(name: str) -> Generator[Span | None]:
    """Create a child span under the current span.

    Yields None when telemetry is disabled (near-zero overhead).
    """
    if not _verbose_enabled.get():
        yield None
        return

    parent = _current_span.get()
    if parent is None:
        yield None
        return

    child = Span(name=name, parent=parent)
    parent.children.append(child)

    token = _current_span.set(child)
    try:
        yield child
    finally:
        child.end()
        _current_span.reset(token)


# ── @traced decorator ────────────────────────────────────────────────


def _inject_meta(result: ServiceResult, span: Span) -> ServiceResult:
    """Create a new ServiceResult with span data merged into meta.

    Uses model_copy(update=...) since ServiceResult is frozen.
    """
    telemetry = {"telemetry": span.to_dict()}
    existing_meta = result.meta or {}
    merged_meta = {**existing_meta, **telemetry}
    return result.model_copy(update={"meta": merged_meta})


def _log_span(span: Span, *, ok: bool) -> None:
    """Log a completed span via structlog (if available) or stdlib."""
    try:
        import structlog

        log = structlog.get_logger("ztlctl.telemetry")
        log.debug(
            "span.complete",
            span_name=span.name,
            duration_ms=round(span.duration_ms, 2),
            ok=ok,
            children=len(span.children),
        )
    except ImportError:
        logger.debug(
            "span.complete: %s %.2fms ok=%s",
            span.name,
            span.duration_ms,
            ok,
        )


_P = ParamSpec("_P")
_R = TypeVar("_R")


def traced(func: Callable[_P, _R]) -> Callable[_P, _R]:  # noqa: UP047
    """Decorator: time a service method and inject span data into ServiceResult.meta.

    No-op when telemetry is disabled (~10ns overhead).
    """

    @functools.wraps(func)
    def wrapper(*args: _P.args, **kwargs: _P.kwargs) -> _R:
        if not _verbose_enabled.get():
            return func(*args, **kwargs)

        span = Span(name=func.__qualname__)
        token = _current_span.set(span)
        try:
            result = func(*args, **kwargs)
        except Exception:
            span.end()
            _current_span.reset(token)
            _log_span(span, ok=False)
            raise

        span.end()
        _current_span.reset(token)

        if isinstance(result, ServiceResult):
            result = _inject_meta(result, span)  # type: ignore[assignment]
        _log_span(span, ok=True)

        return result

    return wrapper


# ── Public helpers ───────────────────────────────────────────────────


def enable_telemetry() -> None:
    """Enable verbose telemetry (called by AppContext at startup)."""
    _verbose_enabled.set(True)


def disable_telemetry() -> None:
    """Disable verbose telemetry."""
    _verbose_enabled.set(False)


def get_current_span() -> Span | None:
    """Get the current active span (for manual annotation)."""
    if not _verbose_enabled.get():
        return None
    return _current_span.get()
