# Technology Stack

**Analysis Date:** 2026-03-19

## Languages

**Primary:**
- Python 3.13 - All source code under `src/ztlctl/` and `tests/`

**Secondary:**
- TOML - Configuration files (`pyproject.toml`, user `ztlctl.toml`)
- Jinja2 templates - Content generation under `src/ztlctl/templates/`
- SQL - SQLite/FTS5 queries in `src/ztlctl/infrastructure/`

## Runtime

**Environment:**
- CPython 3.13 (minimum `>=3.13`, uses Python 3.13 type alias syntax `type X = ...`)

**Package Manager:**
- uv (Astral) — required for all dependency operations
- Lockfile: `uv.lock` (present and committed)
- Never use `uv pip install`; always use `uv add` or `uv add --group <group>`

## Frameworks

**Core:**
- Click `>=8.1` - CLI framework; entry point `ztlctl.cli:cli` in `src/ztlctl/cli.py`
- Pydantic `>=2.0` - Domain models, config models, ServiceResult types
- pydantic-settings `>=2.13.1` - `ZtlSettings` in `src/ztlctl/config/settings.py`; env prefix `ZTLCTL_`

**Data:**
- SQLAlchemy `>=2.0` (Core only, not ORM) - SQLite persistence in `src/ztlctl/infrastructure/database/`
- Alembic `>=1.13` - Schema migrations in `src/ztlctl/infrastructure/database/migrations/`
- NetworkX `>=3.0` - Graph algorithms (PageRank, Louvain, betweenness, paths) in `src/ztlctl/infrastructure/graph/engine.py`

**Content:**
- Jinja2 `>=3.1` - Template rendering in `src/ztlctl/infrastructure/templates.py` and `src/ztlctl/templates/`
- ruamel.yaml `>=0.18` - YAML frontmatter parsing (preserves comments/formatting) in `src/ztlctl/domain/content.py`

**Extension:**
- pluggy `>=1.4` - Plugin system hook specs and manager in `src/ztlctl/plugins/`
- mcp `>=1.0` (optional extra) - FastMCP server in `src/ztlctl/mcp/`; requires `ztlctl[mcp]`
- anyio `>=4.0` (optional extra, bundled with mcp extra) - Async transport for MCP

**Output:**
- Rich `>=13.0` - Terminal output formatting in `src/ztlctl/output/`
- structlog `>=24.0` - Structured logging (console + JSON) in `src/ztlctl/config/logging.py`

**Workflow Templates:**
- Copier `>=9.12.0` - Workflow scaffold generation in `src/ztlctl/services/workflow.py`

**Semantic Search (optional extra `ztlctl[semantic]`):**
- sqlite-vec `>=0.1` - Vector similarity search via SQLite extension
- sentence-transformers `>=2.2` - Local embedding generation (`all-MiniLM-L6-v2`, 384-dim) in `src/ztlctl/infrastructure/embeddings.py`

**Community Detection (optional extra `ztlctl[community]`):**
- leidenalg - Leiden algorithm for higher-quality community detection; falls back to NetworkX Louvain if not installed

**Build:**
- hatchling - Build backend (`[build-system]` in `pyproject.toml`)
- uv build - Produces wheel/sdist in `dist/`

**Testing:**
- pytest `>=8.3` - Test runner; config in `[tool.pytest.ini_options]`; testpaths `["tests"]`
- pytest-cov `>=6.0` - Coverage reporting; `fail_under = 80`

**Linting/Formatting:**
- ruff `>=0.8` - Lint (`E`, `F`, `I`, `W`, `UP`, `RUF`) and format; line-length 100; `quote-style = "double"`
- mypy `>=1.13` - Type checking; strict mode; pydantic plugin enabled

**Commit/Versioning:**
- Commitizen `>=4.1` - Conventional commits enforcement; version provider `pep621`; tag format `v$version`
- pre-commit `>=4.0` - Git hooks for ruff, commitizen commit-msg lint

## Key Dependencies

**Critical:**
- `click>=8.1` - All CLI commands and AppContext pattern (`src/ztlctl/commands/_base.py`)
- `pydantic>=2.0` - ServiceResult frozen models, domain types, all config sections
- `sqlalchemy>=2.0` - SQLite Core queries; `PRAGMA journal_mode=WAL`, `PRAGMA foreign_keys=ON`
- `networkx>=3.0` - Graph engine rebuilt per invocation from DB; PageRank, betweenness, Louvain
- `pluggy>=1.4` - Entry-point plugin discovery; hookspecs in `src/ztlctl/plugins/contracts.py`
- `rich>=13.0` - All terminal output renderers in `src/ztlctl/output/renderers.py`
- `structlog>=24.0` - Hierarchical telemetry spans via `@traced` decorator and `trace_span()` context manager
- `ruamel.yaml>=0.18` - Per-call `_new_yaml()` factory to avoid stateful YAML emitter corruption
- `copier>=9.12.0` - Workflow template scaffolding via `workflow init` / `workflow update` commands

**Infrastructure:**
- `alembic>=1.13` - Migration versions in `src/ztlctl/infrastructure/database/migrations/versions/`
- `scipy>=1.17.1` - Listed as dependency; pulled transitively (not directly imported in source as of analysis)
- `jinja2>=3.1` - Self-description generation (`ztlctl agent regenerate`), content templates
- `pydantic-settings>=2.13.1` - TOML walk-up config discovery + env var override chain

## Configuration

**Environment:**
- Env prefix `ZTLCTL_` maps to `ZtlSettings` fields
- Priority chain: CLI flags > `ZTLCTL_*` env vars > `ztlctl.toml` (walk-up discovery) > code defaults
- Config file: `ztlctl.toml` discovered by walking up from cwd (`src/ztlctl/config/discovery.py`)

**Build:**
- `pyproject.toml` - Single source of truth for version, deps, tool config
- `[tool.hatch.build.targets.wheel]` packages `src/ztlctl`
- Release script: `scripts/build_release_manifest.py`, `scripts/update_homebrew_formula.py`

## Platform Requirements

**Development:**
- Python 3.13+
- uv (Astral) package manager
- pre-commit installed for git hooks
- git binary (GitPlugin silent-fails if missing)

**Production:**
- Python 3.13+ (no server/daemon; pure CLI process)
- SQLite 3 with FTS5 support (standard in Python 3.13)
- Optional: `ztlctl[mcp]` for MCP stdio/HTTP server mode
- Optional: `ztlctl[semantic]` for vector search
- Optional: `ztlctl[community]` for Leiden community detection

---

*Stack analysis: 2026-03-19*
