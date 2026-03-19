# Coding Conventions

**Analysis Date:** 2026-03-19

## Naming Patterns

**Files:**
- Modules use `snake_case.py` throughout
- Private/internal modules prefixed with `_`: `_base.py`, `_context.py`, `_helpers.py`
- Command files named after the command group: `create.py`, `query.py`, `graph.py`
- Test files prefixed `test_`: `test_create.py`, `test_query.py`

**Classes:**
- `PascalCase` everywhere: `CreateService`, `BaseService`, `AppContext`, `ServiceResult`
- Services suffix `Service`: `CreateService`, `QueryService`, `ReweaveService`
- Commands use descriptive subclasses: `ZtlCommand`, `ZtlGroup`, `RootZtlGroup`
- Pydantic models named for their payload role: `SearchResultData`, `ListItemsResultData`
- Internal dataclasses prefixed `_`: `_CreatedContent`, `_BatchAbort`, `_FileOp`

**Functions:**
- `snake_case` everywhere
- Private helpers prefixed `_`: `_create_content`, `_seed_notes`, `_git_log`
- Async or helper module-level functions prefixed `_`: `_inject_meta`, `_log_span`
- `_impl` suffix on MCP tool functions testable without the `mcp` package: `create_note_impl`, `search_impl`

**Variables:**
- `snake_case` throughout
- Constants `UPPER_SNAKE_CASE`: `NOTE_LINKED_THRESHOLD`, `CANONICAL_KEY_ORDER`, `CONTENT_REGISTRY`
- Private attributes prefixed `_`: `self._vault`, `self._data`, `self._vec_available`
- ContextVars named with leading `_`: `_verbose_enabled`, `_current_span`

**Enums:**
- Inherit `StrEnum` (Python 3.11+) — values are lowercase strings matching the domain language
- Example: `ContentType.NOTE = "note"`, `NoteStatus.DRAFT = "draft"`
- StrEnum values must be cast to `str()` before YAML serialization

## Code Style

**Formatting:**
- Tool: `ruff format`
- Line length: 100 characters (`[tool.ruff] line-length = 100`)
- Quote style: double quotes (`[tool.ruff.format] quote-style = "double"`)
- Target: Python 3.13 (`target-version = "py313"`)

**Linting:**
- Tool: `ruff check` with rule sets `["E", "F", "I", "W", "UP", "RUF"]`
  - `E/W` = pycodestyle errors/warnings
  - `F` = pyflakes
  - `I` = isort
  - `UP` = pyupgrade (modern Python idioms)
  - `RUF` = Ruff-specific rules
- `# noqa: UP047` used sparingly for intentional exceptions

**Type Checking:**
- `mypy --strict` with `warn_return_any = true`
- `pydantic.mypy` plugin enabled
- `from __future__ import annotations` at top of **every** source file (100% coverage)
- `TYPE_CHECKING` guard for heavy or circular imports: place in `if TYPE_CHECKING:` block
- Optional package imports guarded and annotated `# type: ignore[import-not-found]`
- MCP decorators annotated `# type: ignore[untyped-decorator]`
- `@staticmethod` must appear outside `@traced` decorator

## Import Organization

**Order (enforced by ruff/isort):**
1. `from __future__ import annotations` — always first
2. Standard library (`pathlib`, `dataclasses`, `typing`, etc.)
3. Third-party (`click`, `pydantic`, `sqlalchemy`, `structlog`)
4. Internal package (`ztlctl.domain`, `ztlctl.infrastructure`, etc.)

**`TYPE_CHECKING` Guard:**
```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy import Connection
    from ztlctl.infrastructure.vault import VaultTransaction
```

**Lazy Local Imports:**
Used inside methods for cross-service imports to avoid circular dependencies. Six established precedents in `session.py`, `context.py`, `upgrade.py`:
```python
def some_method(self) -> None:
    from ztlctl.services.reweave import ReweaveService  # lazy import
    ReweaveService(self._vault).reweave(...)
```

**Path Aliases:**
- None configured — all imports use full module paths from `src/ztlctl/`

## Service Layer Patterns

**Universal Return Type:**
All service methods return `ServiceResult` (never raise). Defined in `src/ztlctl/services/result.py`:
```python
class ServiceResult(BaseModel):
    model_config = {"frozen": True}
    ok: bool
    op: str
    data: dict[str, Any] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    error: ServiceError | None = None
    meta: dict[str, Any] | None = None
```

**Service Construction:**
All services receive a `Vault` at construction and store it as `self._vault`:
```python
class CreateService(BaseService):
    def create_note(self, title: str, ...) -> ServiceResult:
        with self._vault.transaction() as txn:
            ...
```

**Event Dispatch:**
Plugin failures are warnings, never errors. `BaseService._dispatch_event()` wraps all bus calls:
```python
INVARIANT: Plugin failures are warnings, never errors.
```

**Frozen Pydantic Model Updates:**
Use `model_copy(update=...)` since `ServiceResult` is frozen:
```python
return result.model_copy(update={"meta": merged_meta})
```

**Typed Payload Contracts:**
Service result `data` dicts are validated against Pydantic models in `src/ztlctl/services/contracts.py`:
```python
def dump_validated[T: BaseModel](model_cls: type[T], data: dict[str, Any]) -> dict[str, Any]:
    model = model_cls.model_validate(data)
    return model.model_dump(mode="python")
```

## Error Handling

**Strategy:** Never raise from service methods — return `ServiceResult(ok=False, error=ServiceError(...))`.

**Error codes:** `UPPER_SNAKE_CASE` strings: `"EMPTY_QUERY"`, `"COLLISION"`, `"E001"`.

**Plugin/event failures:** Caught at `BaseService._dispatch_event()` and converted to `warnings`, never propagated as errors.

**Optional packages:** Import failures for optional deps (`sqlite_vec`, `sentence_transformers`, `mcp`, `leidenalg`) are caught and degrade gracefully.

**AppContext.emit():** CLI command exit semantics — `ok=True` writes to stdout, `ok=False` writes to stderr and `raise SystemExit(1)`.

**Compensation-based rollback:** File operations in `Vault.transaction()` track writes and roll back on failure without raising from the caller.

## Logging

**Framework:** `structlog` with stdlib `logging` fallback.

**Patterns:**
- Module-level logger: `logger = logging.getLogger(__name__)` in every module that logs
- Structured events via `structlog.get_logger("ztlctl.telemetry")` with key=value pairs
- All log output goes to **stderr** — stdout is reserved for command output
- `logger.debug(...)` for diagnostic/trace-level events
- `logger.warning(...)` for recoverable issues (e.g., file rollback failures)
- Telemetry spans logged as `span.complete` events with `span_name`, `duration_ms`, `ok`, `children`

## Comments and Docstrings

**Module docstrings:** Every module has a one-paragraph docstring at the top explaining purpose and key invariants. Includes DESIGN.md section references where relevant.

**Class docstrings:** All public classes have a docstring. Internal `_` classes have brief inline comments.

**Method docstrings:** Public methods with non-obvious behavior get full docstrings with `Args:` and `Returns:` sections. Simple CRUD methods use one-liners.

**INVARIANT comments:** Used to document structural guarantees:
```python
# INVARIANT: All service-layer methods return ServiceResult.
# INVARIANT: Plugin failures are warnings, never errors.
```

**Section separators:** Long files use `# ---` or `# ──` banners to group related code:
```python
# ---------------------------------------------------------------------------
# Post-create automatic reweave (T-001)
# ---------------------------------------------------------------------------
```

## Module Design

**Exports:**
- `src/ztlctl/commands/__init__.py` exports `register_commands` and `load_plugin_commands`
- Most modules do not use `__all__` — imports are explicit

**Barrel files:**
- `__init__.py` files are mostly empty or contain minimal re-exports
- Each layer imports directly from the submodule, not from `__init__.py`

**Dependency direction (strictly enforced):**
```
commands → services, output, config
output   → services
services → domain, infrastructure, config
domain   → (no internal deps)
infrastructure → domain
config   → (no internal deps beyond pydantic)
```

---

*Convention analysis: 2026-03-19*
