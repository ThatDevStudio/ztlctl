# External Integrations

**Analysis Date:** 2026-03-19

## APIs & External Services

**Model Context Protocol (MCP):**
- FastMCP server - Exposes ztlctl as an MCP tool server for AI agent consumption
  - SDK/Client: `mcp>=1.0` (optional extra `ztlctl[mcp]`)
  - Transport: stdio (default, sub-ms latency) or streamable HTTP (`--host`, `--port`)
  - Entry: `ztlctl serve` command → `src/ztlctl/commands/serve.py`
  - Server setup: `src/ztlctl/mcp/server.py` via `create_server()`
  - Tools: `src/ztlctl/mcp/tools.py` (12 tools)
  - Resources: `src/ztlctl/mcp/resources.py` (6 resources)
  - Prompts: `src/ztlctl/mcp/prompts.py` (4 prompts)
  - Guard: all MCP imports wrapped in `try/except ImportError`; `mcp_available` flag gates usage

**PyPI:**
- Package published to `https://pypi.org/project/ztlctl/`
- Auth: OIDC trusted publisher (no stored token); `id-token: write` permission in `release-pipeline.yml`
- Environment gate: `pypi` GitHub Actions environment requires manual approval

**Homebrew (ThatDev/homebrew-ztlctl tap):**
- Formula auto-generated post-publish via `scripts/update_homebrew_formula.py`
- Auth: `HOMEBREW_TAP_TOKEN` secret (PAT); optional — tap sync skipped if token missing
- Repository: `ThatDev/homebrew-ztlctl` (external tap repo)
- Triggered after PyPI publish succeeds in `release-pipeline.yml`

**GitHub:**
- GitHub Releases: auto-created by release pipeline via `gh release create`
- Auth: `RELEASE_PAT` secret (PAT with `contents: write`)
- Release assets: wheel artifact + `dist/release-manifest.json`
- Release manifest: built by `scripts/build_release_manifest.py`

## Data Storage

**Databases:**
- SQLite 3 (FTS5 + WAL mode)
  - Location: `{vault_root}/.ztlctl/ztlctl.db`
  - Client: SQLAlchemy Core `>=2.0` (not ORM); `src/ztlctl/infrastructure/database/engine.py`
  - Migrations: Alembic `>=1.13`; env in `src/ztlctl/infrastructure/database/migrations/`
  - Pragmas set on connect: `PRAGMA journal_mode=WAL`, `PRAGMA foreign_keys=ON`
  - FTS5 virtual table (`nodes_fts`) for BM25 full-text search
  - Vector table via sqlite-vec extension (optional `ztlctl[semantic]`)

**File Storage:**
- Local filesystem only — vault is a directory tree of markdown files
  - Vault root: user-supplied or CWD
  - Metadata dir: `{vault_root}/.ztlctl/` (db, backups, plugins)
  - Content files: `.md` files throughout vault directory
  - Backup dir: `{vault_root}/.ztlctl/backups/` for rollback on transaction failure
  - Filesystem ops: `src/ztlctl/infrastructure/filesystem.py`

**Caching:**
- None — graph is rebuilt per invocation from SQLite (< 10ms at vault scale < 10K nodes)
- No Redis, Memcached, or in-process persistent cache

## Authentication & Identity

**Auth Provider:**
- None — ztlctl is a local CLI tool with no user authentication
- Vault access is filesystem-permission-based

## Monitoring & Observability

**Error Tracking:**
- None — no external error tracking service (Sentry, Datadog, etc.)

**Logs:**
- structlog `>=24.0` - dual output modes:
  - Human (default): Rich console renderer to stderr
  - JSON (`--log-json`): Structured JSON lines to stderr
  - Config: `src/ztlctl/config/logging.py` → `configure_logging()`
  - Telemetry: `@traced` decorator (45 service methods) + `trace_span()` context manager
  - Level: DEBUG when `--verbose`; WARNING otherwise

**Security Auditing:**
- `pip-audit` (via uvx) runs on every PR and release pipeline to scan for known vulnerabilities

## CI/CD & Deployment

**Hosting:**
- PyPI - Primary distribution (`https://pypi.org/project/ztlctl/`)
- Homebrew tap - `ThatDev/homebrew-ztlctl` (secondary install method)
- GitHub Releases - Source of truth for release artifacts

**CI Pipeline:**
- GitHub Actions on `ubuntu-latest`
- PR validation: `pr-ci.yml` — ruff check, ruff format, mypy, pytest, build, pip-audit, MCP extra tests, commit lint
- Release pipeline: `release-pipeline.yml` — same gates + semantic CI tests, then `cz bump --changelog`, tag, GitHub Release, PyPI publish, Homebrew tap sync
- Secrets required:
  - `RELEASE_PAT` - GitHub PAT for pushing tags and creating releases
  - `HOMEBREW_TAP_TOKEN` - PAT for pushing to Homebrew tap repo (optional)
- CI uses `astral-sh/setup-uv@v3` with cache enabled
- MCP tests run separately with `uv sync --group test --extra mcp`
- Semantic tests run separately with `uv sync --group test --group semantic-ci`

## Plugin System

**pluggy-based plugin architecture:**
- Hook specs: `src/ztlctl/plugins/contracts.py`
- Built-in plugins registered via `[project.entry-points."ztlctl.plugins"]` in `pyproject.toml`:
  - `git` → `ztlctl.plugins.builtins.git:GitPlugin` — git lifecycle integration
  - `obsidian` → `ztlctl.plugins.builtins.obsidian:ObsidianProfilePlugin` — Obsidian workspace init
  - `reweave` → `ztlctl.plugins.builtins.reweave_plugin:ReweavePlugin` — post-create reweave
- Local plugins: discovered from `{vault_root}/.ztlctl/plugins/` directory
- All plugin hook calls wrapped in try/except; failures are warnings, never errors

**Git Plugin (`src/ztlctl/plugins/builtins/git.py`):**
- Integration: subprocess git (no library dependency)
- 8 hookspecs: stage/commit on lifecycle events (create, update, close, etc.)
- Batch mode (default): stage on each operation, commit once at session close
- Immediate mode: commit after every operation
- Silent failure if git binary missing or directory is not a repo

**Obsidian Plugin (`src/ztlctl/plugins/builtins/obsidian.py`):**
- No external API calls — generates `.obsidian/` config files (JSON) at vault init
- Configures core plugins, community plugin manifest, and recommended settings
- Community plugins referenced by ID (not installed): dataview, templater-obsidian, folder-notes, omnisearch, obsidian-book-search-plugin

## Workflow Templates

**Copier (`>=9.12.0`):**
- `ztlctl workflow init` / `ztlctl workflow update` scaffold from templates
- Implementation: `src/ztlctl/services/workflow.py`
- Templates: `src/ztlctl/templates/workflow/` (Copier-based)
- No external template registry; templates bundled with package

## Webhooks & Callbacks

**Incoming:**
- None — no webhook endpoints; ztlctl is a CLI tool

**Outgoing:**
- None in core; EventBus dispatches to local pluggy plugins only (WAL-backed async)

## Environment Configuration

**Required env vars:**
- None strictly required — all settings have defaults
- `ZTLCTL_VAULT_ROOT` - Override vault root path
- `ZTLCTL_SYNC` - Force synchronous event bus mode
- All settings mapped from `ZTLCTL_` prefix via pydantic-settings

**Secrets location:**
- GitHub Actions secrets: `RELEASE_PAT`, `HOMEBREW_TAP_TOKEN`
- No application-level secrets (no API keys, no auth tokens in user config)

---

*Integration audit: 2026-03-19*
