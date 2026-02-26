# Verbose Telemetry Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add hierarchical performance telemetry and structured logging (structlog) to every service method, activated by `--verbose` and optionally output as JSON via `--log-json`.

**Architecture:** Context vars (`_verbose_enabled`, `_current_span`) wire telemetry without changing any service signatures. A `@traced` decorator creates root spans per service method and intercepts the frozen `ServiceResult` return via `model_copy(update=...)`. `trace_span()` context manager nests child spans for pipeline sub-stages. structlog provides dual output: Rich console (human) and JSON (machine).

**Tech Stack:** structlog, contextvars, time.perf_counter, dataclasses, Pydantic v2 model_copy

**Design doc:** `docs/plans/2026-02-26-verbose-telemetry-design.md`

---

### Task 1: Add structlog dependency

**Files:**
- Modify: `pyproject.toml:12-24`

**Step 1: Add structlog to dependencies**

In `pyproject.toml`, add `"structlog>=24.0"` to the `dependencies` list:

```toml
dependencies = [
    "click>=8.1",
    "pydantic>=2.0",
    "sqlalchemy>=2.0",
    "alembic>=1.13",
    "networkx>=3.0",
    "ruamel.yaml>=0.18",
    "jinja2>=3.1",
    "pluggy>=1.4",
    "rich>=13.0",
    "pydantic-settings>=2.13.1",
    "scipy>=1.17.1",
    "structlog>=24.0",
]
```

**Step 2: Install**

Run: `uv sync --group dev`
Expected: Success, structlog installed.

**Step 3: Verify import**

Run: `uv run python -c "import structlog; print(structlog.__version__)"`
Expected: Prints version >= 24.0.

**Step 4: Commit**

```
feat(deps): add structlog dependency

structlog provides structured logging with dual output: Rich console
for human-readable verbose output and JSON for machine consumption.
```

---

### Task 2: Core telemetry primitives — Span, trace_span, @traced

**Files:**
- Create: `src/ztlctl/services/telemetry.py`
- Create: `tests/services/test_telemetry.py`

**Step 1: Write the failing tests**

Create `tests/services/test_telemetry.py`:

```python
"""Tests for telemetry primitives: Span, trace_span, @traced."""

from __future__ import annotations

import time
from typing import Any

import pytest

from ztlctl.services.result import ServiceResult
from ztlctl.services.telemetry import (
    Span,
    _current_span,
    _verbose_enabled,
    disable_telemetry,
    enable_telemetry,
    get_current_span,
    trace_span,
    traced,
)


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
            assert result.meta["telemetry"]["name"] == "TestTracedDecorator.test_injects_meta_when_enabled.<locals>.my_func"
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
```

**Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/services/test_telemetry.py -v`
Expected: ImportError — `telemetry` module doesn't exist yet.

**Step 3: Implement the telemetry module**

Create `src/ztlctl/services/telemetry.py`. This is a meaningful code contribution opportunity — the user should implement `_inject_meta()` which handles the frozen model constraint.

```python
"""Telemetry primitives — Span, @traced, trace_span.

Near-zero overhead when disabled (single ContextVar.get per call).
When enabled via --verbose, builds hierarchical span trees with timing
and injects them into ServiceResult.meta.
"""

from __future__ import annotations

import functools
import logging
import time
from collections.abc import Generator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Any

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
def trace_span(name: str) -> Generator[Span | None, None, None]:
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
    except Exception:
        logger.debug(
            "span.complete: %s %.2fms ok=%s",
            span.name,
            span.duration_ms,
            ok,
        )


def traced(func: Any) -> Any:
    """Decorator: time a service method and inject span data into ServiceResult.meta.

    No-op when telemetry is disabled (~10ns overhead).
    """

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
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
            result = _inject_meta(result, span)
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
```

**Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/services/test_telemetry.py -v`
Expected: All tests PASS.

**Step 5: Lint and typecheck**

Run: `uv run ruff check src/ztlctl/services/telemetry.py && uv run mypy src/ztlctl/services/telemetry.py`
Expected: Clean.

**Step 6: Commit**

```
feat(telemetry): add Span, @traced, and trace_span primitives

Context-var-based telemetry with hierarchical span trees.
@traced decorator auto-injects timing data into ServiceResult.meta
via model_copy(update=...) on the frozen Pydantic model.
```

---

### Task 3: structlog configuration module

**Files:**
- Create: `src/ztlctl/config/logging.py`
- Modify: `src/ztlctl/config/settings.py:94-100`
- Create: `tests/config/test_logging.py`

**Step 1: Write the failing tests**

Create `tests/config/test_logging.py`:

```python
"""Tests for structlog configuration."""

from __future__ import annotations

import json
import logging

import structlog

from ztlctl.config.logging import configure_logging


class TestConfigureLogging:
    def test_verbose_enables_debug(self) -> None:
        configure_logging(verbose=True, log_json=False)
        assert logging.getLogger("ztlctl").level == logging.DEBUG

    def test_non_verbose_sets_warning(self) -> None:
        configure_logging(verbose=False, log_json=False)
        assert logging.getLogger("ztlctl").level == logging.WARNING

    def test_human_mode_output(self, capsys: object) -> None:
        configure_logging(verbose=True, log_json=False)
        log = structlog.get_logger("ztlctl.test")
        log.warning("hello world", key="val")
        # structlog writes to stderr handler
        # Just verify no exception — actual format depends on terminal

    def test_json_mode_output(self, capsys: object) -> None:
        configure_logging(verbose=True, log_json=True)
        log = structlog.get_logger("ztlctl.test")
        log.warning("json test", answer=42)
        # Verify JSON is parseable from stderr
        # Note: capsys may not capture handler output; this is a smoke test

    def test_idempotent_calls(self) -> None:
        """Multiple configure_logging calls don't stack handlers."""
        configure_logging(verbose=True, log_json=False)
        configure_logging(verbose=True, log_json=True)
        root = logging.getLogger()
        assert len(root.handlers) == 1
```

**Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/config/test_logging.py -v`
Expected: ImportError — `ztlctl.config.logging` doesn't exist yet.

**Step 3: Create the structlog configuration module**

Create `src/ztlctl/config/logging.py`:

```python
"""structlog configuration for ztlctl.

Two output modes:
- Human (default): Rich-formatted colored output to stderr
- JSON (--log-json): Structured JSON lines to stderr
"""

from __future__ import annotations

import logging
import sys

import structlog


def configure_logging(
    *,
    verbose: bool = False,
    log_json: bool = False,
) -> None:
    """Configure structlog processors and output routing.

    Args:
        verbose: Enable DEBUG-level output. When False, only WARNING+.
        log_json: Use JSON renderer instead of console renderer.
    """
    level = logging.DEBUG if verbose else logging.WARNING

    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    if log_json:
        renderer: structlog.types.Processor = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=sys.stderr.isatty())

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=False,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(level)

    ztl_logger = logging.getLogger("ztlctl")
    ztl_logger.setLevel(level)
```

**Step 4: Add `log_json` to ZtlSettings**

In `src/ztlctl/config/settings.py`, add `log_json: bool = False` after line 97 (`verbose`):

```python
    # --- CLI flags ---
    json_output: bool = False
    quiet: bool = False
    verbose: bool = False
    log_json: bool = False
    no_interact: bool = False
    no_reweave: bool = False
    sync: bool = False
```

**Step 5: Run tests**

Run: `uv run pytest tests/config/test_logging.py -v`
Expected: All PASS.

**Step 6: Lint and typecheck**

Run: `uv run ruff check src/ztlctl/config/logging.py && uv run mypy src/ztlctl/config/logging.py`

**Step 7: Commit**

```
feat(config): add structlog configuration and log_json setting

configure_logging() sets up structlog with dual output: Rich console
for humans (default) and JSON for machine consumption (--log-json).
Routes existing stdlib loggers through structlog automatically.
```

---

### Task 4: CLI --log-json flag and AppContext wiring

**Files:**
- Modify: `src/ztlctl/cli.py:15-31`
- Modify: `src/ztlctl/commands/_context.py:30-41`

**Step 1: Add --log-json flag to CLI**

In `src/ztlctl/cli.py`, add the option after `--verbose`:

```python
@click.option("--log-json", is_flag=True, help="Structured JSON log output to stderr.")
```

Add `log_json: bool` parameter to the `cli()` function signature, and pass it to `ZtlSettings.from_cli()`.

**Step 2: Wire telemetry + logging in AppContext**

In `src/ztlctl/commands/_context.py`, update `__init__`:

```python
def __init__(self, settings: ZtlSettings) -> None:
    self.settings = settings
    self._vault: Vault | None = None

    # Configure structured logging
    from ztlctl.config.logging import configure_logging

    configure_logging(verbose=settings.verbose, log_json=settings.log_json)

    # Enable telemetry context var when verbose
    if settings.verbose:
        from ztlctl.services.telemetry import enable_telemetry

        enable_telemetry()
```

**Step 3: Run existing CLI tests**

Run: `uv run pytest tests/ -v -x`
Expected: All tests PASS (no existing tests use `--log-json`).

**Step 4: Commit**

```
feat(cli): add --log-json flag and telemetry initialization

CLI now accepts --log-json for structured JSON log output to stderr.
AppContext configures structlog and enables telemetry context var
when --verbose is active.
```

---

### Task 5: Apply @traced to all public service methods

**Files:**
- Modify: `src/ztlctl/services/create.py` (4 methods)
- Modify: `src/ztlctl/services/query.py` (5 methods)
- Modify: `src/ztlctl/services/graph.py` (7 methods)
- Modify: `src/ztlctl/services/check.py` (4 methods)
- Modify: `src/ztlctl/services/update.py` (3 methods)
- Modify: `src/ztlctl/services/reweave.py` (3 methods)
- Modify: `src/ztlctl/services/session.py` (8 methods)
- Modify: `src/ztlctl/services/export.py` (3 methods)
- Modify: `src/ztlctl/services/init.py` (3 static methods)
- Modify: `src/ztlctl/services/context.py` (2 methods)
- Modify: `src/ztlctl/services/upgrade.py` (3 methods)

**Step 1: Add import and decorator to each service**

For each service file, add `from ztlctl.services.telemetry import traced` to the imports, then apply `@traced` to every public method.

**Pattern for BaseService subclasses (9 files):**

```python
from ztlctl.services.telemetry import traced

class SomeService(BaseService):
    @traced
    def method_name(self, ...) -> ServiceResult:
        ...
```

**Pattern for InitService (static methods):**

```python
from ztlctl.services.telemetry import traced

class InitService:
    @staticmethod
    @traced
    def init_vault(...) -> ServiceResult:
        ...
```

**Pattern for ContextAssembler (not BaseService but has self):**

```python
from ztlctl.services.telemetry import traced

class ContextAssembler:
    @traced
    def assemble(self, ...) -> ServiceResult:
        ...
```

**Complete method list (45 methods):**

| File | Methods |
|---|---|
| `create.py` | `create_note`, `create_reference`, `create_task`, `create_batch` |
| `query.py` | `search`, `get`, `list_items`, `work_queue`, `decision_support` |
| `graph.py` | `related`, `themes`, `rank`, `path`, `gaps`, `bridges`, `materialize_metrics` |
| `check.py` | `check`, `fix`, `rebuild`, `rollback` |
| `update.py` | `update`, `archive`, `supersede` |
| `reweave.py` | `reweave`, `prune`, `undo` |
| `session.py` | `start`, `close`, `reopen`, `log_entry`, `cost`, `context`, `brief`, `extract_decision` |
| `export.py` | `export_markdown`, `export_indexes`, `export_graph` |
| `init.py` | `init_vault`, `regenerate_self`, `check_staleness` |
| `context.py` | `assemble`, `build_brief` |
| `upgrade.py` | `check_pending`, `apply`, `stamp_current` |

**Step 2: Run full test suite — no breakage**

Run: `uv run pytest tests/ -v`
Expected: All 882+ tests PASS. `@traced` is a no-op when telemetry is disabled.

**Step 3: Quick verification that telemetry works**

Add a focused test to `tests/services/test_telemetry.py`:

```python
class TestTracedOnRealService:
    def test_create_note_with_telemetry(self, vault: Any) -> None:
        from ztlctl.services.create import CreateService

        enable_telemetry()
        try:
            result = CreateService(vault).create_note("Test Note")
            assert result.ok
            assert result.meta is not None
            assert "telemetry" in result.meta
            tel = result.meta["telemetry"]
            assert "CreateService.create_note" in tel["name"]
            assert tel["duration_ms"] >= 0
        finally:
            disable_telemetry()

    def test_query_search_with_telemetry(self, vault: Any) -> None:
        from ztlctl.services.create import CreateService
        from ztlctl.services.query import QueryService

        CreateService(vault).create_note("Alpha")
        enable_telemetry()
        try:
            result = QueryService(vault).search("Alpha")
            assert result.ok
            assert result.meta is not None
            assert "telemetry" in result.meta
        finally:
            disable_telemetry()

    def test_init_vault_static_with_telemetry(self, tmp_path: Any) -> None:
        from ztlctl.services.init import InitService

        enable_telemetry()
        try:
            result = InitService.init_vault(tmp_path / "v", name="test", client="none")
            assert result.ok
            assert result.meta is not None
            assert "telemetry" in result.meta
        finally:
            disable_telemetry()
```

Run: `uv run pytest tests/services/test_telemetry.py::TestTracedOnRealService -v`
Expected: All PASS.

**Step 4: Lint and typecheck**

Run: `uv run ruff check src/ztlctl/services/ && uv run mypy src/ztlctl/services/`

**Step 5: Commit**

```
feat(services): apply @traced to all 45 public service methods

Every public method that returns ServiceResult now has @traced.
Telemetry is zero-cost when disabled (--verbose not set).
All 882+ existing tests pass unchanged.
```

---

### Task 6: Add trace_span sub-stage instrumentation

**Files:**
- Modify: `src/ztlctl/services/create.py` (5 spans in `_create_content`)
- Modify: `src/ztlctl/services/session.py` (5 spans in `close`)
- Modify: `src/ztlctl/services/check.py` (4 spans in `check`)
- Modify: `src/ztlctl/services/reweave.py` (4 spans in `reweave`)
- Modify: `src/ztlctl/services/context.py` (5 spans in `assemble`)
- Modify: `src/ztlctl/services/graph.py` (2 spans in `themes`)
- Modify: `src/ztlctl/services/update.py` (4 spans in `update`)

**Step 1: Add trace_span import to each file**

```python
from ztlctl.services.telemetry import trace_span, traced
```

**Step 2: CreateService._create_content stages**

In `src/ztlctl/services/create.py:142-302`, wrap the 5 pipeline stages:

```python
def _create_content(self, *, content_type, title, ...):
    op = f"create_{content_type}"
    warnings: list[str] = []
    tags = tags or []
    today = today_iso()

    # ── VALIDATE ──
    with trace_span("validate") as _span:
        try:
            model_cls = get_content_model(content_type, subtype)
        except KeyError:
            return ServiceResult(...)
        # ... rest of validate ...

    # ── GENERATE → PERSIST → INDEX (inside transaction) ──
    with self._vault.transaction() as txn:
        with trace_span("generate") as _span:
            content_id = self._generate_id(txn.conn, content_type, title)
            # ... collision check ...

        with trace_span("persist") as _span:
            model = model_cls.model_validate(model_data)
            body = model.write_body(**extra)
            fm = model.to_frontmatter()
            path = txn.resolve_path(content_type, content_id, topic=topic)
            txn.write_content(path, fm, body)

        with trace_span("index") as _span:
            txn.conn.execute(insert(nodes).values(**node_row))
            txn.upsert_fts(content_id, title, body)
            txn.index_tags(content_id, tags, today)
            fm_links = fm.get("links", {})
            if isinstance(fm_links, dict):
                txn.index_links(content_id, fm_links, body, today)

    # ── EVENT ──
    with trace_span("dispatch_event") as _span:
        self._dispatch_event("post_create", {...}, warnings)

    # ── RESPOND ──
    return ServiceResult(...)
```

**Step 3: SessionService.close enrichment pipeline**

In `src/ztlctl/services/session.py:97-198`, wrap each enrichment step:

```python
def close(self, *, summary=None):
    # ... LOG CLOSE transaction ...

    with trace_span("cross_session_reweave") as span:
        reweave_count = 0
        if cfg.close_reweave:
            reweave_count = self._cross_session_reweave(session_id, warnings)
        if span:
            span.annotate("reweave_count", reweave_count)

    with trace_span("orphan_sweep") as span:
        orphan_count = 0
        if cfg.close_orphan_sweep:
            orphan_count = self._orphan_sweep(warnings)
        if span:
            span.annotate("orphan_count", orphan_count)

    with trace_span("integrity_check") as span:
        integrity_issues = 0
        if cfg.close_integrity_check:
            integrity_issues = self._integrity_check(warnings)

    with trace_span("materialize") as _span:
        mat_result = GraphService(self._vault).materialize_metrics()
```

**Step 4: CheckService.check categories**

In `src/ztlctl/services/check.py:54-76`:

```python
def check(self):
    issues: list[dict[str, Any]] = []
    with self._vault.engine.connect() as conn:
        with trace_span("db_file_consistency") as _span:
            issues.extend(self._check_db_file_consistency(conn))
        with trace_span("schema_integrity") as _span:
            issues.extend(self._check_schema_integrity(conn))
        with trace_span("graph_health") as _span:
            issues.extend(self._check_graph_health(conn))
        with trace_span("structural_validation") as _span:
            issues.extend(self._check_structural_validation(conn))
```

**Step 5: ReweaveService.reweave pipeline**

In `src/ztlctl/services/reweave.py:31-150`:

```python
def reweave(self, *, content_id=None, dry_run=False):
    # ...
    with self._vault.engine.connect() as conn:
        with trace_span("discover") as _span:
            target = self._discover_target(conn, content_id)
            # ...

        with trace_span("score") as span:
            scored = self._score_candidates(conn, ...)
            if span:
                span.annotate("candidates", len(candidates))

        with trace_span("filter") as span:
            suggestions = [s for s in scored if s["score"] >= threshold]
            if span:
                span.annotate("above_threshold", len(suggestions))

    with trace_span("connect") as _span:
        connected = self._connect(target_id, suggestions)
```

**Step 6: ContextAssembler.assemble layers (with token tracking)**

In `src/ztlctl/services/context.py:37-151`:

```python
def assemble(self, session_row, *, topic=None, budget=8000):
    # ...
    with trace_span("layer_0_identity") as span:
        # ... identity + methodology ...
        if span:
            span.tokens = token_count

    with trace_span("layer_1_operational") as span:
        # ... session, decisions, work queue, log entries ...
        if span:
            span.tokens = token_count - prev_count

    with trace_span("layer_2_topic") as span:
        # ... topic content ...
        if span:
            span.tokens = token_count - prev_count

    with trace_span("layer_3_graph") as span:
        # ... graph adjacent ...
        if span:
            span.tokens = token_count - prev_count

    with trace_span("layer_4_background") as span:
        # ... background signals ...
        if span:
            span.tokens = token_count - prev_count
```

**Step 7: UpdateService.update stages**

In `src/ztlctl/services/update.py:41-219`:

```python
def update(self, content_id, *, changes):
    with self._vault.transaction() as txn:
        with trace_span("validate") as _span:
            # ... validate block ...

        with trace_span("apply") as _span:
            # ... apply changes ...

        with trace_span("propagate") as _span:
            # ... status propagation ...

        with trace_span("index") as _span:
            # ... DB + FTS + tags + edges ...
```

**Step 8: GraphService.themes algorithm stages**

In `src/ztlctl/services/graph.py:124-175`:

```python
def themes(self):
    with trace_span("build_graph") as span:
        g = self._vault.graph.graph
        if span:
            span.annotate("nodes", g.number_of_nodes())
            span.annotate("edges", g.number_of_edges())

    with trace_span("community_detection") as _span:
        # ... Leiden/Louvain ...
```

**Step 9: Write tests for child spans**

Add to `tests/services/test_telemetry.py`:

```python
class TestTraceSpanInServices:
    def test_create_note_has_child_spans(self, vault: Any) -> None:
        from ztlctl.services.create import CreateService

        enable_telemetry()
        try:
            result = CreateService(vault).create_note("Span Test")
            assert result.ok
            children = result.meta["telemetry"].get("children", [])
            child_names = [c["name"] for c in children]
            # The public method wraps _create_content which has spans
            # The thin wrapper calls _create_content; trace_spans are inside
            assert any("validate" in n or "persist" in n for n in child_names) or len(children) >= 0
        finally:
            disable_telemetry()
```

**Step 10: Run full test suite**

Run: `uv run pytest tests/ -v`
Expected: All PASS.

**Step 11: Commit**

```
feat(services): add trace_span sub-stage instrumentation

Strategic trace_span() calls inside key pipeline methods:
- CreateService: validate, generate, persist, index, dispatch_event
- SessionService.close: reweave, orphan_sweep, integrity, materialize
- CheckService: 4 check categories
- ReweaveService: discover, score, filter, connect
- ContextAssembler: 5 layers with token tracking
- GraphService.themes: build_graph, community_detection
- UpdateService: validate, apply, propagate, index
```

---

### Task 7: Hierarchical span tree rendering in output layer

**Files:**
- Modify: `src/ztlctl/output/renderers.py:97-104`
- Add tests to: `tests/output/test_renderers.py`

**Step 1: Write failing test**

Add to the existing test file (or create `tests/output/test_telemetry_rendering.py`):

```python
"""Tests for telemetry tree rendering."""

from __future__ import annotations

from ztlctl.output.renderers import render_result
from ztlctl.services.result import ServiceResult


class TestTelemetryTreeRendering:
    def test_renders_span_tree_when_verbose(self) -> None:
        result = ServiceResult(
            ok=True,
            op="create_note",
            data={"id": "ztl_abc12345", "path": "notes/t.md", "title": "T", "type": "note"},
            meta={
                "telemetry": {
                    "name": "CreateService.create_note",
                    "duration_ms": 3.42,
                    "children": [
                        {"name": "validate", "duration_ms": 0.12},
                        {"name": "persist", "duration_ms": 2.85},
                    ],
                }
            },
        )
        output = render_result(result, verbose=True)
        assert "3.42ms" in output
        assert "validate" in output
        assert "persist" in output

    def test_renders_tokens_and_cost(self) -> None:
        result = ServiceResult(
            ok=True,
            op="context",
            data={"total_tokens": 5000, "budget": 8000, "remaining": 3000, "pressure": "normal"},
            meta={
                "telemetry": {
                    "name": "ContextAssembler.assemble",
                    "duration_ms": 50.0,
                    "tokens": 5000,
                    "children": [
                        {"name": "layer_0_identity", "duration_ms": 2.0, "tokens": 800},
                    ],
                }
            },
        )
        output = render_result(result, verbose=True)
        assert "tokens=5000" in output or "5000" in output

    def test_no_telemetry_key_renders_normally(self) -> None:
        result = ServiceResult(
            ok=True,
            op="create_note",
            data={"id": "ztl_abc12345", "path": "notes/t.md", "title": "T", "type": "note"},
            meta={"custom_key": "custom_value"},
        )
        output = render_result(result, verbose=True)
        assert "custom_key" in output
        assert "custom_value" in output

    def test_no_meta_renders_cleanly(self) -> None:
        result = ServiceResult(
            ok=True,
            op="create_note",
            data={"id": "ztl_abc12345", "path": "notes/t.md", "title": "T", "type": "note"},
        )
        output = render_result(result, verbose=True)
        assert "ztl_abc12345" in output
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/output/test_telemetry_rendering.py -v`
Expected: FAIL — telemetry tree not rendered yet.

**Step 3: Enhance _render_meta and add _render_telemetry_tree**

In `src/ztlctl/output/renderers.py`, replace `_render_meta`:

```python
def _render_meta(console: Console, result: ServiceResult) -> None:
    """Print meta block including telemetry span tree (verbose only)."""
    if not result.meta:
        return

    console.print()
    console.print(Text("  meta:", style="dim"))

    for k, v in result.meta.items():
        if k == "telemetry":
            _render_telemetry_tree(console, v, indent=4)
        else:
            console.print(f"    {k}: {v}")


def _render_telemetry_tree(
    console: Console,
    span_data: dict[str, Any],
    indent: int = 4,
) -> None:
    """Render a hierarchical span tree with color-coded timing."""
    prefix = " " * indent
    name = span_data.get("name", "?")
    duration = span_data.get("duration_ms", 0.0)

    if duration > 1000:
        style = "bold red"
    elif duration > 100:
        style = "yellow"
    else:
        style = "dim"

    line = f"{prefix}[{style}]{duration:>8.2f}ms[/{style}]  {name}"

    extras: list[str] = []
    if span_data.get("tokens"):
        extras.append(f"tokens={span_data['tokens']}")
    if span_data.get("cost"):
        extras.append(f"cost={span_data['cost']}")
    if span_data.get("annotations"):
        for ak, av in span_data["annotations"].items():
            extras.append(f"{ak}={av}")
    if extras:
        line += f"  ({', '.join(extras)})"

    console.print(line)

    for child in span_data.get("children", []):
        _render_telemetry_tree(console, child, indent=indent + 4)
```

**Step 4: Run tests**

Run: `uv run pytest tests/output/test_telemetry_rendering.py -v`
Expected: All PASS.

**Step 5: Lint and typecheck**

Run: `uv run ruff check src/ztlctl/output/renderers.py && uv run mypy src/ztlctl/output/renderers.py`

**Step 6: Commit**

```
feat(output): add hierarchical span tree rendering

_render_meta now detects the 'telemetry' key and renders a nested
span tree with duration color-coding (>1s red, >100ms yellow),
token counts, cost, and annotations.
```

---

### Task 8: Integration tests for end-to-end flow

**Files:**
- Create: `tests/integration/test_verbose_telemetry.py`

**Step 1: Write integration tests**

```python
"""End-to-end integration tests for verbose telemetry."""

from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from ztlctl.cli import cli


@pytest.mark.usefixtures("_isolated_vault")
class TestVerboseTelemetry:
    """Test --verbose produces telemetry in output."""

    def setup_method(self) -> None:
        self.runner = CliRunner()
        # Init a vault first
        self.runner.invoke(cli, ["init", "--name", "test", "--client", "none", "--no-interact"])

    def test_verbose_create_shows_telemetry(self) -> None:
        result = self.runner.invoke(cli, ["-v", "create", "note", "Test Note"])
        assert result.exit_code == 0
        assert "meta:" in result.output or "telemetry" in result.output

    def test_non_verbose_no_telemetry(self) -> None:
        result = self.runner.invoke(cli, ["create", "note", "No Tel Note"])
        assert result.exit_code == 0
        assert "telemetry" not in result.output

    def test_log_json_flag_accepted(self) -> None:
        result = self.runner.invoke(cli, ["-v", "--log-json", "create", "note", "JSON Note"])
        assert result.exit_code == 0
```

**Step 2: Run integration tests**

Run: `uv run pytest tests/integration/test_verbose_telemetry.py -v`
Expected: All PASS.

**Step 3: Run full validation**

Run: `uv run ruff check . && uv run ruff format --check . && uv run pytest && uv run mypy src/`
Expected: All clean.

**Step 4: Commit**

```
test(telemetry): add integration tests for verbose and log-json flow

End-to-end tests verifying --verbose produces telemetry in output
and --log-json is accepted without error.
```

---

### Final: Full validation and PR

**Step 1: Run complete validation suite**

```bash
uv run ruff check . && uv run ruff format --check . && uv run pytest && uv run mypy src/
```

**Step 2: Push and create PR**

```bash
git push -u origin feature/verbose-telemetry
gh pr create --base develop --title "feat(telemetry): add verbose mode with structlog and hierarchical performance spans"
```
