# Codebase Structure

**Analysis Date:** 2026-03-19

## Directory Layout

```
ztlctl/
├── src/
│   └── ztlctl/              # Package root
│       ├── cli.py           # Root Click group, global flags, command registration
│       ├── __main__.py      # python -m ztlctl entrypoint
│       ├── __init__.py      # Package version
│       ├── catalogs.py      # Public surface catalogs (CLI, MCP, workflow metadata)
│       ├── workspace_modes.py       # Workspace mode definitions
│       ├── workspace_ownership.py   # Ownership/identity metadata
│       ├── workspace_profiles.py    # Profile discovery and normalization
│       ├── domain/          # Types, enums, lifecycle rules (no external deps)
│       ├── infrastructure/  # SQLite, graph engine, filesystem, embeddings
│       │   ├── database/    # SQLAlchemy Core schema + engine + migrations
│       │   ├── graph/       # NetworkX graph engine
│       │   └── repositories/ # Query repository (complex read queries)
│       ├── config/          # Pydantic settings, TOML discovery, logging config
│       ├── services/        # Business logic (all public methods return ServiceResult)
│       ├── output/          # Rich/JSON formatters
│       ├── commands/        # Click command groups + standalone commands
│       ├── plugins/         # pluggy hookspecs, EventBus, PluginManager, builtins
│       └── mcp/             # Optional FastMCP adapter (guarded imports)
├── tests/                   # Mirrors src/ztlctl/ structure + integration/
│   ├── conftest.py          # Shared fixtures (tmp_vault, db, etc.)
│   ├── domain/
│   ├── infrastructure/
│   ├── config/
│   ├── services/
│   ├── commands/
│   ├── output/
│   ├── plugins/
│   ├── mcp/
│   └── integration/         # End-to-end performance and telemetry tests
├── docs/                    # Jekyll/GitHub Pages documentation
├── plugin/                  # External plugin development reference
│   ├── agents/
│   ├── commands/
│   ├── hooks/
│   └── skills/
├── scripts/                 # Release and utility scripts
├── pyproject.toml           # Package metadata, deps, tool config
├── uv.lock                  # Pinned dependency lockfile
├── DESIGN.md                # Canonical design specification (~97KB)
└── .ztlctl/                 # Local vault used for development (ztlctl.db, backups, plugins)
```

## Directory Purposes

**`src/ztlctl/domain/`:**
- Purpose: Pure business vocabulary — no I/O, no external deps beyond pydantic
- Contains: `ContentType`, `NoteSubtype`, `RefSubtype`, `Space` enums; `NoteStatus`, `TaskStatus`, `LogStatus`, `GardenMaturity` lifecycle enums; transition maps; wikilink/tag/frontmatter parsers; ID generation logic
- Key files: `src/ztlctl/domain/types.py`, `src/ztlctl/domain/lifecycle.py`, `src/ztlctl/domain/content.py`, `src/ztlctl/domain/ids.py`, `src/ztlctl/domain/links.py`, `src/ztlctl/domain/tags.py`

**`src/ztlctl/infrastructure/`:**
- Purpose: All data persistence and retrieval
- Contains: `Vault` repository + `VaultTransaction`; SQLAlchemy Core table definitions; Alembic migrations; `GraphEngine` (NetworkX DiGraph, lazy-built); filesystem helpers; embedding store (sqlite-vec); `QueryRepository` for complex reads
- Key files: `src/ztlctl/infrastructure/vault.py`, `src/ztlctl/infrastructure/database/schema.py`, `src/ztlctl/infrastructure/database/engine.py`, `src/ztlctl/infrastructure/graph/engine.py`, `src/ztlctl/infrastructure/filesystem.py`, `src/ztlctl/infrastructure/embeddings.py`, `src/ztlctl/infrastructure/repositories/query.py`

**`src/ztlctl/config/`:**
- Purpose: Settings resolution and logging setup
- Contains: `ZtlSettings` (frozen Pydantic BaseSettings; merges CLI → env → TOML → defaults); section config models; `find_config()` walk-up discovery; `configure_logging()` (structlog dual-output)
- Key files: `src/ztlctl/config/settings.py`, `src/ztlctl/config/models.py`, `src/ztlctl/config/discovery.py`, `src/ztlctl/config/logging.py`

**`src/ztlctl/services/`:**
- Purpose: All business logic; every public method returns `ServiceResult`
- Contains: One service class per domain operation; `BaseService` abstract base; `ServiceResult` + `ServiceError`; typed payload contracts; `@traced` + `trace_span()` telemetry primitives; shared helpers
- Key files: `src/ztlctl/services/base.py`, `src/ztlctl/services/result.py`, `src/ztlctl/services/contracts.py`, `src/ztlctl/services/telemetry.py`, `src/ztlctl/services/create.py`, `src/ztlctl/services/query.py`, `src/ztlctl/services/graph.py`, `src/ztlctl/services/update.py`, `src/ztlctl/services/reweave.py`, `src/ztlctl/services/check.py`, `src/ztlctl/services/session.py`, `src/ztlctl/services/vector.py`, `src/ztlctl/services/ingest.py`, `src/ztlctl/services/export.py`, `src/ztlctl/services/init.py`, `src/ztlctl/services/workflow.py`, `src/ztlctl/services/upgrade.py`

**`src/ztlctl/output/`:**
- Purpose: Adapt `ServiceResult` for human (Rich) or machine (`--json`) display
- Contains: `format_result()` dispatcher; Rich renderers by operation type; quiet (minimal) renderers; telemetry tree renderer
- Key files: `src/ztlctl/output/formatters.py`, `src/ztlctl/output/renderers.py`, `src/ztlctl/output/console.py`

**`src/ztlctl/commands/`:**
- Purpose: Click command groups and standalone commands — thin adapters that call services
- Contains: `AppContext` (shared ctx.obj); `RootZtlGroup` (dynamic plugin commands); `ZtlCommand`/`ZtlGroup` (--examples flag); per-operation command modules
- Key files: `src/ztlctl/commands/_context.py`, `src/ztlctl/commands/_base.py`, `src/ztlctl/commands/__init__.py`

**`src/ztlctl/plugins/`:**
- Purpose: Extension system — lifecycle hooks, async dispatch, plugin discovery
- Contains: `ZtlctlHookSpec` (pluggy hookspecs); `EventBus` (WAL-backed, ThreadPoolExecutor); `PluginManager` (entry-point discovery + local dir); built-in plugins (GitPlugin, ReweavePlugin, ObsidianPlugin); `contracts.py` (contribution types)
- Key files: `src/ztlctl/plugins/hookspecs.py`, `src/ztlctl/plugins/event_bus.py`, `src/ztlctl/plugins/manager.py`, `src/ztlctl/plugins/contracts.py`, `src/ztlctl/plugins/builtins/git.py`, `src/ztlctl/plugins/builtins/reweave_plugin.py`, `src/ztlctl/plugins/builtins/obsidian.py`

**`src/ztlctl/mcp/`:**
- Purpose: Optional FastMCP adapter; guarded behind `try/except ImportError`
- Contains: `create_server()` factory; `register_tools()` (12 tools); `register_resources()` (6 resources); `register_prompts()` (4 prompts)
- Key files: `src/ztlctl/mcp/server.py`, `src/ztlctl/mcp/tools.py`, `src/ztlctl/mcp/resources.py`, `src/ztlctl/mcp/prompts.py`

**`tests/`:**
- Purpose: Mirrors `src/ztlctl/` structure; `integration/` holds end-to-end/performance tests
- Key files: `tests/conftest.py` (shared fixtures), `tests/integration/test_performance.py`, `tests/integration/test_verbose_telemetry.py`

**`plugin/`:**
- Purpose: External plugin development reference material (agents, hooks, skills, commands docs/examples)

**`.ztlctl/`:**
- Purpose: Local development vault (SQLite DB, backups, local plugins)
- Generated: Yes (by `ztlctl init`)
- Committed: Yes (the dev vault's DB and backups are present)

## Key File Locations

**Entry Points:**
- `src/ztlctl/cli.py`: Root `cli` Click group; global flags; `register_commands()` call
- `src/ztlctl/__main__.py`: `python -m ztlctl` runs `cli`

**Configuration:**
- `pyproject.toml`: Package metadata, dependencies, ruff/mypy/pytest/commitizen config
- `src/ztlctl/config/settings.py`: `ZtlSettings.from_cli()` — the settings constructor
- `src/ztlctl/config/models.py`: All section config models (`VaultConfig`, `ReweaveConfig`, etc.)
- `src/ztlctl/config/discovery.py`: `find_config()` walk-up TOML discovery

**Core Logic:**
- `src/ztlctl/infrastructure/vault.py`: `Vault` (repository) + `VaultTransaction`
- `src/ztlctl/services/base.py`: `BaseService` + `_dispatch_event()`
- `src/ztlctl/services/result.py`: `ServiceResult` + `ServiceError`
- `src/ztlctl/services/contracts.py`: All typed payload contracts (SearchResultData, ListItemsResultData, etc.)
- `src/ztlctl/commands/_context.py`: `AppContext` — `emit()`, `vault` (lazy), `log_action_cost()`

**Database:**
- `src/ztlctl/infrastructure/database/schema.py`: All SQLAlchemy table definitions (nodes, edges, tags_registry, node_tags, id_counters, reweave_log, event_wal, session_logs)
- `src/ztlctl/infrastructure/database/engine.py`: `init_database()` — SQLite engine creation + Alembic migrations
- `src/ztlctl/infrastructure/database/migrations/versions/`: Migration scripts (001_baseline, 002_node_timestamps)

**Testing:**
- `tests/conftest.py`: Shared fixtures for temp vault, in-memory DB, etc.
- `tests/integration/`: End-to-end and performance regression tests

## Naming Conventions

**Files:**
- Service files: `<domain>.py` — matches the class name without `Service` suffix (e.g., `create.py` → `CreateService`)
- Command files: `<command>.py` — matches the CLI command name (e.g., `graph.py` → `graph` group)
- Private helpers: `_<name>.py` — underscore prefix (e.g., `_base.py`, `_context.py`, `_helpers.py`)
- Test files: `test_<module>.py` — mirror of source module name

**Directories:**
- Lowercase snake_case for all packages
- Test directories mirror source packages exactly

**Classes:**
- Services: `<Domain>Service` (e.g., `CreateService`, `QueryService`, `GraphService`)
- Domain enums: `<Domain><Concept>` (e.g., `NoteStatus`, `ContentType`, `GardenMaturity`)
- Click commands: lowercase verb/noun (e.g., `create`, `query`, `graph`)
- Config models: `<Section>Config` (e.g., `VaultConfig`, `ReweaveConfig`)
- Pydantic contracts: `<Operation>ResultData`, `<Entity>Item` (e.g., `SearchResultData`, `SearchItem`)

## Where to Add New Code

**New Service (business operation):**
- Primary code: `src/ztlctl/services/<domain>.py` — subclass `BaseService`, return `ServiceResult`
- Payload contracts: `src/ztlctl/services/contracts.py` — add `<Operation>ResultData` Pydantic model
- Tests: `tests/services/test_<domain>.py`
- Export from: `src/ztlctl/services/__init__.py` (if needed)

**New CLI Command:**
- Single command: `src/ztlctl/commands/<command>.py`
- Register in: `src/ztlctl/commands/__init__.py` `register_commands()`
- Tests: `tests/commands/test_<command>.py`
- Use `ZtlCommand` (cls= parameter) or `ZtlGroup` for --examples support

**New Command Group:**
- Implementation: `src/ztlctl/commands/<group>.py`
- Register group in: `src/ztlctl/commands/__init__.py` `register_commands()`

**New Domain Type/Rule:**
- Types/enums: `src/ztlctl/domain/types.py`
- Lifecycle rules: `src/ztlctl/domain/lifecycle.py`
- Tests: `tests/domain/test_<module>.py`

**New Config Section:**
- Model: `src/ztlctl/config/models.py` — add frozen Pydantic model
- Add field: `src/ztlctl/config/settings.py` `ZtlSettings` class

**New Plugin Hook:**
- Hookspec: `src/ztlctl/plugins/hookspecs.py` — add `@hookspec` method to `ZtlctlHookSpec`
- Built-in implementation: `src/ztlctl/plugins/builtins/<plugin>.py`

**New MCP Tool/Resource/Prompt:**
- Tools: `src/ztlctl/mcp/tools.py` — add `_impl_<name>()` function + register in `register_tools()`
- Resources: `src/ztlctl/mcp/resources.py`
- Prompts: `src/ztlctl/mcp/prompts.py`
- Add catalog entry: `src/ztlctl/catalogs.py`

**New Output Renderer:**
- Renderer: `src/ztlctl/output/renderers.py` — add `render_<operation>()` function
- Tests: `tests/output/test_<renderer>.py`

**Utilities / Shared Helpers:**
- Service-level helpers: `src/ztlctl/services/_helpers.py`
- Infrastructure helpers: appropriate `src/ztlctl/infrastructure/` module

## Special Directories

**`.ztlctl/`:**
- Purpose: Active local development vault (ztlctl.db, backups/, plugins/)
- Generated: Yes (by `ztlctl init`)
- Committed: Yes (dev vault committed to repo for testing)

**`src/ztlctl/infrastructure/database/migrations/`:**
- Purpose: Alembic migration scripts managed by `alembic`
- Generated: No (manually authored)
- Committed: Yes

**`dist/`:**
- Purpose: Built wheel and sdist artifacts from `uv build`
- Generated: Yes
- Committed: No (but currently present from prior builds)

**`docs/`:**
- Purpose: Jekyll-based GitHub Pages documentation site
- Generated: No
- Committed: Yes

**`plugin/`:**
- Purpose: External plugin development reference — agents, hooks, skills, commands
- Generated: No
- Committed: Yes

---

*Structure analysis: 2026-03-19*
