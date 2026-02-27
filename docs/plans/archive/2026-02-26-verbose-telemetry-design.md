# Verbose Mode with structlog + Hierarchical Performance Telemetry

## Context

ztlctl has **no logging or performance telemetry** in the service layer. The `--verbose` flag exists and is wired through CLI → ZtlSettings → AppContext → OutputSettings → renderers, but services don't populate `ServiceResult.meta` (the field exists but is unused). This feature adds:

- **structlog** for both Rich human-readable output and structured JSON machine output
- **Hierarchical spans** with timing and cost/token tracking
- **`@traced` decorator** + **`trace_span()` context manager** for service instrumentation
- **`--log-json` CLI flag** for structured JSON logs to stderr
- **Context vars** for zero-signature-change wiring

---

## New Files

### `src/ztlctl/services/telemetry.py` — Core telemetry primitives

**Context vars:**
- `_verbose_enabled: ContextVar[bool]` — when False, all telemetry is near-zero-cost (single ContextVar.get)
- `_current_span: ContextVar[Span | None]` — current span in the hierarchy

**`Span` dataclass:**
- `name`, `parent`, `children`, `start_time`, `end_time` (perf_counter)
- `tokens: int | None`, `cost: float | None` — for context assembly and session tracking
- `annotations: dict[str, Any]` — arbitrary metadata (rows_fetched, reweave_count, etc.)
- `to_dict()` — serializes span tree for ServiceResult.meta

**`trace_span(name)` context manager:**
- Creates a child span under `_current_span`
- Yields `Span | None` (None when telemetry disabled)
- Auto-closes span on exit, resets context var

**`@traced` decorator:**
- Creates root span named after `func.__qualname__` (e.g., `CreateService.create_note`)
- Intercepts `ServiceResult` return → creates new instance via `result.model_copy(update={"meta": merged})` (frozen model safe)
- Logs completed span via structlog
- On exception: logs span with `ok=False`, then re-raises
- When disabled: pure pass-through (~10ns overhead)

**Public helpers:**
- `enable_telemetry()` / `disable_telemetry()` — called by AppContext
- `get_current_span()` — for manual annotation in service code

### `src/ztlctl/config/logging.py` — structlog configuration

- `configure_logging(verbose: bool, log_json: bool)`
- Shared processors: `merge_contextvars`, `add_log_level`, `add_logger_name`, `TimeStamper(fmt="iso")`, `StackInfoRenderer`, `UnicodeDecoder`
- Human mode: `structlog.dev.ConsoleRenderer(colors=stderr.isatty())`
- JSON mode: `structlog.processors.JSONRenderer()`
- Routes stdlib logging through structlog (existing `logging.getLogger(__name__)` calls auto-format)
- Level: DEBUG when verbose, WARNING otherwise
- All output to stderr (keeps stdout clean for ServiceResult)

---

## Modified Files

### `pyproject.toml`
- Add `structlog>=24.0` to dependencies

### `src/ztlctl/cli.py`
- Add `--log-json` flag: `@click.option("--log-json", is_flag=True, help="Structured JSON log output to stderr.")`
- Pass `log_json` through to `ZtlSettings.from_cli()`

### `src/ztlctl/config/settings.py`
- Add `log_json: bool = False` to CLI flags section of `ZtlSettings`

### `src/ztlctl/commands/_context.py`
- In `AppContext.__init__()`: call `configure_logging(verbose=, log_json=)` and `enable_telemetry()` when verbose

### `src/ztlctl/output/renderers.py`
- Enhance `_render_meta()` to detect `telemetry` key and render hierarchical span tree
- Add `_render_telemetry_tree()` helper with duration color-coding (>1s red, >100ms yellow, else dim) and token/cost/annotation display

### All 10 service files (apply `@traced` to public methods)

| Service file | Methods to decorate | trace_span stages |
|---|---|---|
| `create.py` | `create_note`, `create_reference`, `create_task`, `create_batch` | In `_create_content`: validate, generate, persist, index, dispatch_event |
| `query.py` | `search`, `get`, `list_items`, `work_queue`, `decision_support` | FTS query, scoring, graph re-rank |
| `graph.py` | `related`, `themes`, `rank`, `path`, `gaps`, `bridges`, `materialize_metrics` | build_graph, algorithm, format |
| `check.py` | `check`, `fix`, `rebuild`, `rollback` | db_file_sync, schema, graph, structural |
| `update.py` | `update`, `archive`, `supersede` | validate, apply, propagate, index |
| `reweave.py` | `reweave`, `prune`, `undo` | discover, score, filter, connect |
| `session.py` | `start`, `close`, `reopen`, `log_entry`, `cost`, `context`, `brief`, `extract_decision` | close: log_close, cross_session_reweave, orphan_sweep, integrity_check, materialize |
| `export.py` | `export_markdown`, `export_indexes`, `export_graph` | query, write |
| `init.py` | `init_vault`, `regenerate_self`, `check_staleness` (all @staticmethod) | scaffold, generate_self |
| `context.py` | `assemble`, `build_brief` | layer_0 through layer_4 (with span.tokens) |

**Total: ~45 public methods + ~30-40 trace_span sub-stages**

### Cost/Token Tracking Locations
- `ContextAssembler.assemble()`: set `span.tokens` on each layer span as token budget is consumed
- `SessionService.log_entry()`: annotate with cost parameter
- `SessionService.cost()`: annotate with total_cost from query

---

## Key Design Decisions

1. **`model_copy(update={"meta": ...})`** on frozen ServiceResult — Pydantic v2 creates a new instance, original untouched
2. **`@staticmethod` + `@traced` ordering**: `@staticmethod` on outside, `@traced` on inside — decorates the function before staticmethod wraps it
3. **Thin public methods** (create_note/create_reference/create_task) get `@traced` — inner `_create_content` gets `trace_span()` stages. The decorator captures the public method name in the span.
4. **Cross-service calls** (e.g., SessionService.close calls GraphService.materialize_metrics): inner call gets its own independent root span via @traced. The calling method uses trace_span() to capture wall-clock time of the sub-step.
5. **Existing stdlib loggers** (base.py, git plugin, etc.) automatically get structlog formatting via stdlib integration — zero changes needed.

---

## Commit Sequence

1. `feat(deps): add structlog dependency`
2. `feat(telemetry): add Span, @traced, and trace_span primitives` + unit tests
3. `feat(config): add structlog configuration module` + `log_json` setting + tests
4. `feat(cli): add --log-json flag and telemetry initialization in AppContext`
5. `feat(services): apply @traced to all public service methods` (verify 882+ tests still pass)
6. `feat(services): add trace_span sub-stage instrumentation` with cost/token tracking
7. `feat(output): add hierarchical span tree rendering` + tests
8. `test(telemetry): add integration tests for end-to-end verbose + log-json flow`

---

## Verification

1. **Unit tests pass**: `uv run pytest` — all 882+ existing tests pass (telemetry disabled by default = no-op)
2. **New unit tests**: Span, trace_span, @traced, configure_logging, telemetry tree rendering
3. **Integration test**: `uv run ztlctl -v create note "Test"` shows telemetry tree in meta block
4. **JSON mode**: `uv run ztlctl -v --log-json create note "Test"` outputs JSON span logs to stderr
5. **Lint/type**: `uv run ruff check . && uv run ruff format --check . && uv run mypy src/`
6. **Performance**: Without `--verbose`, overhead is ~10ns per service method call (single ContextVar.get)
