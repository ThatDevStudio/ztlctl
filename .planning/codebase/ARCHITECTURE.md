# Architecture

**Analysis Date:** 2026-03-19

## Pattern Overview

**Overall:** Layered Clean Architecture with Vault Repository Pattern

**Key Characteristics:**
- Strict unidirectional dependency flow: domain → infrastructure → config → services → output → commands
- `Vault` is the single dependency injected into every service (repository pattern)
- `ServiceResult` is the universal return type across all service boundaries — CLI, MCP, and plugins all consume it
- Event-driven side effects via WAL-backed async EventBus (pluggy + ThreadPoolExecutor)
- Telemetry injected via ContextVar-based span tracing with zero signature change

## Layers

**Domain Layer:**
- Purpose: Pure business types, enums, lifecycle rules, ID patterns — no external deps beyond pydantic
- Location: `src/ztlctl/domain/`
- Contains: `ContentType`, `NoteStatus`, `TaskStatus`, `GardenMaturity`, lifecycle transition maps, wikilink/tag parsers, frontmatter parsers
- Depends on: pydantic only
- Used by: infrastructure, services

**Infrastructure Layer:**
- Purpose: All data storage and retrieval — SQLite/SQLAlchemy Core, NetworkX graph, filesystem ops, embeddings
- Location: `src/ztlctl/infrastructure/`
- Contains: `Vault` repository, `VaultTransaction`, `GraphEngine`, `DatabaseEngine`, `FilesystemOps`, `EmbeddingStore`, `QueryRepository`, Alembic migrations
- Depends on: domain
- Used by: services (exclusively via Vault)

**Config Layer:**
- Purpose: Pydantic settings models, TOML walk-up discovery, structlog configuration
- Location: `src/ztlctl/config/`
- Contains: `ZtlSettings` (frozen, merges CLI flags + env vars + TOML + defaults), `VaultConfig`, `ReweaveConfig`, etc.
- Depends on: domain (for workspace profile helpers)
- Used by: infrastructure (Vault init), commands (AppContext)

**Services Layer:**
- Purpose: All business logic — implements domain operations using Vault for data access
- Location: `src/ztlctl/services/`
- Contains: `CreateService`, `QueryService`, `GraphService`, `UpdateService`, `ReweaveService`, `CheckService`, `SessionService`, `VectorService`, `IngestService`, `ExportService`, `InitService`, `WorkflowService`
- Depends on: domain, infrastructure (Vault only), config (via Vault.settings)
- Used by: commands, mcp

**Output Layer:**
- Purpose: Rich/JSON formatters that adapt `ServiceResult` for human or machine display
- Location: `src/ztlctl/output/`
- Contains: `format_result()`, `render_result()`, `render_quiet()`, Rich renderers
- Depends on: services (ServiceResult type only)
- Used by: commands (via AppContext.emit())

**Commands Layer:**
- Purpose: Click command groups and standalone commands — thin adapters that parse CLI args and delegate to services
- Location: `src/ztlctl/commands/`
- Contains: 9 command groups (create, query, graph, agent, garden, export, ingest, vector, workflow) + 9 standalone commands (check, init, upgrade, update, reweave, archive, extract, supersede, serve)
- Depends on: services, output, config
- Used by: CLI entrypoint (`cli.py`)

**Plugins Layer:**
- Purpose: pluggy hook specs, EventBus (WAL-backed async dispatch), PluginManager (entry-point discovery), built-in plugins
- Location: `src/ztlctl/plugins/`
- Contains: `ZtlctlHookSpec` (8 lifecycle hooks + 8 registration hooks), `EventBus`, `PluginManager`, `GitPlugin`, `ReweavePlugin`, `ObsidianPlugin`
- Depends on: services (for plugin implementations), infrastructure (EventBus needs DB engine)
- Used by: Vault (init_event_bus), services (BaseService._dispatch_event)

**MCP Layer:**
- Purpose: Optional FastMCP adapter exposing 12 tools, 6 resources, 4 prompts over stdio or HTTP
- Location: `src/ztlctl/mcp/`
- Contains: `create_server()`, `register_tools()`, `register_resources()`, `register_prompts()`
- Depends on: services (directly, via separate Vault instance), infrastructure
- Used by: `commands/serve.py` (ztlctl serve)
- Note: guarded behind `try/except ImportError` — mcp package is an optional extra

## Data Flow

**Standard CLI Command:**

1. User invokes `ztlctl <command> <args>` — entrypoint: `src/ztlctl/cli.py`
2. Click root group (`RootZtlGroup`) instantiates `ZtlSettings.from_cli()` — discovers `ztlctl.toml` via directory walk-up
3. `AppContext` is created and stored on `ctx.obj` — configures logging, enables telemetry if `--verbose`
4. Subcommand handler receives `AppContext` via `@click.pass_obj`
5. Handler constructs a service (e.g., `CreateService(app.vault)`) — Vault is lazily initialized on first access
6. Service executes within `vault.transaction()` context manager — coordinates SQLite + filesystem + graph atomically
7. Service returns `ServiceResult` (frozen Pydantic model)
8. Command calls `app.emit(result)` — formats for stdout (success) or stderr (failure, exit 1)
9. AppContext.close() drains EventBus on exit

**Create Content Pipeline (CreateService):**

1. VALIDATE — domain model validates inputs via `get_content_model()`
2. GENERATE — `_generate_id()` calls `next_sequential_id()` for sequential ID (e.g., `ztl_abc12345`)
3. PERSIST — insert node row + write markdown file within `vault.transaction()`
4. INDEX — `txn.upsert_fts()` for FTS5, `txn.index_tags()`, `txn.index_links()` for edges
5. EVENT — `_dispatch_event("post_create", ...)` via EventBus (async by default)
6. VECTOR INDEX — embed content if semantic search enabled
7. RESPOND — return `ServiceResult(ok=True, op="create_note", data={...})`

**State Management:**
- No global mutable state — `ZtlSettings` and `Vault` are per-invocation
- Graph cache (`GraphEngine`) is per-`Vault` instance, invalidated after each transaction
- Telemetry uses `ContextVar` — safe in async/threaded contexts, zero overhead when disabled

## Key Abstractions

**Vault (Repository):**
- Purpose: Single point of access to database, filesystem, and graph — injected into every service
- Examples: `src/ztlctl/infrastructure/vault.py`
- Pattern: Repository pattern; `vault.transaction()` yields `VaultTransaction` with coordinated ACID semantics

**VaultTransaction:**
- Purpose: Active transaction context; tracks file writes for compensation-based rollback
- Examples: `src/ztlctl/infrastructure/vault.py` (`VaultTransaction` dataclass)
- Pattern: Context manager; `txn.write_file()` registers rollback; `txn.conn` for SQLAlchemy Core

**ServiceResult:**
- Purpose: Universal return type for all service operations — carries ok/error, op name, data payload, warnings, meta
- Examples: `src/ztlctl/services/result.py`
- Pattern: Frozen Pydantic model; telemetry injected via `model_copy(update={"meta": merged})` to avoid mutation

**AppContext:**
- Purpose: Shared Click context flowing through command hierarchy — lazy Vault + centralized emit()
- Examples: `src/ztlctl/commands/_context.py`
- Pattern: Stored on `ctx.obj`; accessed via `@click.pass_obj`; `app.vault` triggers lazy init

**BaseService:**
- Purpose: Abstract base providing `self._vault` access and `_dispatch_event()` helper
- Examples: `src/ztlctl/services/base.py`
- Pattern: Constructor injection; all services subclass this; plugin failures are warnings, never errors

**@traced decorator + trace_span():**
- Purpose: Hierarchical performance span tracing injected into `ServiceResult.meta["telemetry"]`
- Examples: `src/ztlctl/services/telemetry.py`; applied on 45 service methods
- Pattern: ContextVar-based — ~10ns overhead when disabled, activated by `--verbose`

**ZtlctlHookSpec (pluggy):**
- Purpose: Defines 16 hookspecs — 8 lifecycle events (post_create, post_update, etc.) + 8 registration hooks (CLI commands, MCP tools, etc.)
- Examples: `src/ztlctl/plugins/hookspecs.py`
- Pattern: pluggy hookspecs; `EventBus` dispatches lifecycle events async via `event_wal` WAL table

## Entry Points

**CLI Entrypoint:**
- Location: `src/ztlctl/cli.py` (defines `cli` Click group)
- Invoked as: `ztlctl` (pyproject.toml scripts entry point)
- Triggers: `ZtlSettings.from_cli()` → `AppContext` → subcommand dispatch

**Python Module Entrypoint:**
- Location: `src/ztlctl/__main__.py`
- Triggers: `python -m ztlctl` runs the same `cli` group

**MCP Server Entrypoint:**
- Location: `src/ztlctl/commands/serve.py` → `src/ztlctl/mcp/server.py`
- Triggers: `ztlctl serve` creates a separate Vault instance and mounts FastMCP server

**Plugin Entrypoint:**
- Location: `src/ztlctl/plugins/manager.py` (`PluginManager.discover_and_load()`)
- Triggers: On vault lazy init; loads entry-point plugins + local plugins from `<vault>/.ztlctl/plugins/`

## Error Handling

**Strategy:** Return-based with `ServiceResult` — services never raise to callers; all errors are captured in `ServiceResult(ok=False, error=ServiceError(...))`

**Patterns:**
- Service failures → `ServiceResult(ok=False, error=ServiceError(code=..., message=...))`
- Plugin/event failures → demoted to `warnings` list, never error; logged at DEBUG level
- Click-level failures → `raise SystemExit(1)` via `AppContext.emit()` on failed result
- Transaction failures → SQLAlchemy rolls back DB; `VaultTransaction` compensates file writes on exception
- Missing optional deps (mcp, sqlite-vec, sentence-transformers) → `ImportError` caught at import time with clear user message

## Cross-Cutting Concerns

**Logging:** structlog (dual-output: Rich console + JSON to stderr); configured once by `AppContext` via `configure_logging()` in `src/ztlctl/config/logging.py`; all service spans logged via `structlog.get_logger("ztlctl.telemetry")`

**Validation:** Pydantic throughout — `ZtlSettings` (frozen), `ServiceResult` (frozen), `ServiceError` (frozen), payload contracts in `src/ztlctl/services/contracts.py`; `dump_validated()` validates service payloads at boundary

**Authentication:** None — local file system tool; no auth layer

**Config Discovery:** `src/ztlctl/config/discovery.py` `find_config()` walks directories upward from CWD to find `ztlctl.toml`; vault root is set to the config file's parent directory

---

*Architecture analysis: 2026-03-19*
