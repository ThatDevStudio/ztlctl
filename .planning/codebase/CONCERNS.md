# Codebase Concerns

**Analysis Date:** 2026-03-19

---

## Tech Debt

**Hardcoded embedding dimension in schema DDL:**
- Issue: `VEC_CREATE_SQL` in `src/ztlctl/infrastructure/database/schema.py` (line 153) hard-codes `FLOAT[384]`. The user-configurable `embedding_dim` setting in `src/ztlctl/config/models.py` (line 105) is only used when `VectorService.ensure_table()` creates the table at runtime. The schema-level constant is unused for creation but provides a false reference that can confuse readers and may cause divergence if the schema constant is ever used instead.
- Files: `src/ztlctl/infrastructure/database/schema.py`, `src/ztlctl/services/vector.py`, `src/ztlctl/config/models.py`
- Impact: Changing `embedding_dim` in config while an existing `vec_items` table exists with a different dimension silently produces incorrect similarity results or crashes. No migration path enforces consistency between the stored dimension and the configured dimension.
- Fix approach: Remove `VEC_CREATE_SQL` from schema.py (it is dead), or make `ensure_table()` validate the existing table dimension against config before use.

**`backup_retention_days` config setting is declared but never enforced:**
- Issue: `CheckConfig.backup_retention_days = 30` exists in `src/ztlctl/config/models.py` (line 145). The `_prune_backups()` method in `src/ztlctl/services/check.py` (line 309) only enforces `backup_max_count` (default 10) — it never reads `backup_retention_days` or deletes by age.
- Files: `src/ztlctl/services/check.py`, `src/ztlctl/config/models.py`
- Impact: The setting is misleading. Users who rely on time-based retention will accumulate stale backups beyond their intent once count exceeds `backup_max_count`. Backups are created before every `check`, `check --rebuild`, and `check --rollback`.
- Fix approach: Add age-based pruning in `_prune_backups()` that also deletes backups older than `backup_retention_days`.

**`graph materialize` is a required prerequisite not enforced automatically:**
- Issue: The `graph` search ranking mode in `QueryService.search()` (`src/ztlctl/services/query.py` line 392–399) requires persisted PageRank values in the `nodes` table. These are only written by `GraphService.materialize_metrics()` (`src/ztlctl/services/graph.py` line 569). A fresh vault returns all-zero PageRank scores with a warning. No command triggers `materialize_metrics` automatically after bulk content creation or `check --rebuild`.
- Files: `src/ztlctl/services/query.py`, `src/ztlctl/services/graph.py`, `src/ztlctl/commands/graph.py`
- Impact: `ztlctl search --rank graph` silently degrades to BM25-only with a warning. Users may not notice until they run `ztlctl graph materialize` explicitly.
- Fix approach: Call `materialize_metrics()` automatically at the end of `check --rebuild`, or add it to session close in `SessionService`.

**`betweenness_centrality` runs on full graph per materialize call:**
- Issue: `GraphService.materialize_metrics()` computes `nx.betweenness_centrality(g)` for every node on every invocation. Betweenness is O(V * E) and can take seconds on graphs > 1,000 nodes.
- Files: `src/ztlctl/services/graph.py` (line 587)
- Impact: `ztlctl graph materialize` will become noticeably slow as the vault grows. The graph engine comment says "< 10K nodes, full rebuild takes < 10ms" — that is true for the graph build but does not account for betweenness centrality.
- Fix approach: Make betweenness computation optional (behind a `--compute-betweenness` flag), or use approximation (`k` parameter to `nx.betweenness_centrality`).

**Local `import json` inside a hot loop in `check.rebuild()`:**
- Issue: In `src/ztlctl/services/check.py` (line 198), `import json` is placed inside the per-file loop body that processes every content file during `rebuild`. Python caches module imports, so there is no runtime cost, but it is a style violation that increases cognitive load and confuses readers about the import scope.
- Files: `src/ztlctl/services/check.py`
- Impact: Cosmetic only; no runtime overhead. However, it sets a precedent that can hide real deferred imports with actual cost.
- Fix approach: Move `import json` to the module top level.

---

## Known Bugs

**`backup_retention_days` silently ignored (see Tech Debt above).**

**FTS5 and `vec_items` can diverge after `check --rollback`:**
- Symptoms: After restoring an older DB backup via `check --rollback`, the FTS5 `nodes_fts` and (if present) `vec_items` tables may not match the restored `nodes` table because the backup is a raw file copy with `shutil.copy2`. If the FTS5 or vector tables were modified after the backup was taken they will be stale.
- Files: `src/ztlctl/services/check.py` (line 281), `src/ztlctl/infrastructure/vault.py`
- Trigger: Run `check --rollback` on a vault that has had content created since the backup.
- Workaround: Follow `check --rollback` with `check --rebuild` to re-sync FTS5 and re-embed vectors.

---

## Security Considerations

**`ztlctl workflow init/update` executes Copier templates from external URLs:**
- Risk: `WorkflowService` in `src/ztlctl/services/workflow.py` calls `copier.run_copy()` and `copier.run_update()` with user-provided template sources. Copier templates can execute arbitrary Python via Jinja2 hooks.
- Files: `src/ztlctl/services/workflow.py`
- Current mitigation: None beyond Copier's own trust model.
- Recommendations: Document the risk in user-facing help. Consider restricting `--src` to trusted domains or local paths. Copier 9.x requires explicit `--trust` flag for hook execution — verify this flag is not being set permissively.

**Git plugin commits titles and paths from user-supplied content:**
- Risk: The `GitPlugin` in `src/ztlctl/plugins/builtins/git.py` constructs commit messages using `content_id` and `title` fields directly (lines 72, 88). If a title contains shell metacharacters, these are passed as a string to `subprocess.run(["git", "commit", "-m", message])` with `shell=False` — so there is no shell injection. However, a title with `\n` or embedded null bytes can produce a misleading multi-line commit message.
- Files: `src/ztlctl/plugins/builtins/git.py` (lines 72, 88)
- Current mitigation: `shell=False` prevents shell injection. Subprocess list form is safe.
- Recommendations: Sanitize newlines in title before embedding in commit message.

**MCP server binds to configurable host without authentication:**
- Risk: `src/ztlctl/mcp/server.py` creates a FastMCP server bound to `host` and `port` parameters. Streamable HTTP transport has no authentication layer. Any process that can reach the bound address can read vault content and issue write operations.
- Files: `src/ztlctl/mcp/server.py`, `src/ztlctl/commands/serve.py`
- Current mitigation: Default bind is `127.0.0.1`; stdio transport (default for Claude Desktop integration) is not network-accessible.
- Recommendations: Document that HTTP transport is for trusted local use only. Add a warning in `ztlctl serve --transport http` output.

---

## Performance Bottlenecks

**`check --rebuild` reads every markdown file on disk — N file I/Os:**
- Problem: `CheckService.rebuild()` calls `self._vault.find_content()` then reads each file via `file_path.read_text()` in a sequential loop. For a vault with thousands of notes, this is O(N) disk reads with no batching or parallelism.
- Files: `src/ztlctl/services/check.py` (line 152–207), `src/ztlctl/infrastructure/filesystem.py` (line 115)
- Cause: Files are the source of truth, so a rebuild must re-parse them. No caching of parsed frontmatter exists.
- Improvement path: Use `concurrent.futures.ThreadPoolExecutor` to parallelize file reads; frontmatter is CPU-light so I/O dominates.

**Context assembly reads markdown files per-note for enrichment signals:**
- Problem: `QueryService._content_features()` in `src/ztlctl/services/query.py` (line 575) reads and parses each result file from disk to extract enrichment signals (key points, provenance, excerpts) during search result ranking. For a 10-result search, this is 10 synchronous `file.read_text()` + frontmatter parse calls.
- Files: `src/ztlctl/services/query.py` (line 575)
- Cause: Enrichment signals are not stored in the DB.
- Improvement path: Cache key enrichment fields (key_point_count, provenance_count, excerpt_count) in the `nodes` table and populate them during content creation and rebuild.

**`reweave` candidate scoring does per-candidate FTS5 queries:**
- Problem: `ReweaveService._score_candidates()` in `src/ztlctl/services/reweave.py` issues one FTS5 query per candidate note to compute BM25 similarity. For a vault with 200 candidates this is 200 individual SQL queries.
- Files: `src/ztlctl/services/reweave.py`
- Cause: BM25 scoring is done individually rather than via a single FTS5 ranking query.
- Improvement path: Reformulate as a single FTS5 MATCH query returning all candidates ranked by BM25, then merge with Jaccard/graph proximity signals in Python.

---

## Fragile Areas

**EventBus future timeout is a hard-coded 30 seconds:**
- Files: `src/ztlctl/plugins/event_bus.py` (line 229)
- Why fragile: A slow plugin (e.g., git push to a remote with latency) that runs over 30 seconds will have its future silently abandoned. The WAL record remains in `failed` state and will be retried at next drain. The retry behaviour is correct but the timeout is not configurable and produces no user-visible warning.
- Safe modification: Make `timeout` configurable via `EventBus.__init__()` parameter (and exposed via config). Log a warning when a future times out rather than silently passing.
- Test coverage: `tests/plugins/test_event_bus.py` tests the happy path; timeout edge case is not tested.

**`dead_letter` events in `event_wal` accumulate without cleanup:**
- Files: `src/ztlctl/plugins/event_bus.py`, `src/ztlctl/infrastructure/database/schema.py`
- Why fragile: Events that exhaust retries are marked `dead_letter` and never deleted. On a long-lived vault with flaky plugins, the `event_wal` table will grow unboundedly. No command exists to inspect or purge dead-letter events.
- Safe modification: Add a `drain_dead_letters()` method or include dead-letter pruning in `CheckService.scan()` output so users can act on them.
- Test coverage: Dead-letter accumulation is not tested.

**`GraphEngine` is lazy-per-process, not lazy-per-command:**
- Files: `src/ztlctl/infrastructure/graph/engine.py`
- Why fragile: The `GraphEngine._graph` cache is valid only within a single CLI invocation (processes are short-lived). It is invalidated correctly after writes via `vault.graph.invalidate()`. However, if any service bypasses invalidation after a graph-modifying operation, a stale in-process graph is used. Currently `invalidate()` is called manually; there is no automatic invalidation hook.
- Safe modification: Dispatch a graph-invalidation call inside `VaultTransaction.__exit__` to ensure it fires after every successful commit.
- Test coverage: Invalidation is not explicitly integration-tested; only unit-level tests exist.

**Copier update falls back to `recopy` silently:**
- Files: `src/ztlctl/services/workflow.py` (line 367–380)
- Why fragile: When `copier.run_update()` raises `CopierError` (missing `.copier-answers.yml`), the code falls back to `run_recopy()`, which overwrites local customizations without diff review. This is documented as a warning in `ServiceResult.warnings` but is not surfaced prominently to the user at the CLI level.
- Safe modification: Promote the recopy fallback to a structured error requiring `--force-recopy` flag acknowledgment.
- Test coverage: The fallback path is tested in `tests/test_workflows.py` but the user impact (overwritten files) is not asserted.

**MCP server has no graceful vault shutdown:**
- Files: `src/ztlctl/mcp/server.py`, `src/ztlctl/commands/serve.py`
- Why fragile: `create_server()` creates a `Vault` and calls `vault.init_event_bus()`. The `EventBus` holds a `ThreadPoolExecutor`. When the MCP server process exits (or receives SIGINT), the executor is not shut down cleanly — in-flight plugin futures may be abandoned. The CLI path (`AppContext`) calls `event_bus.drain()` + `event_bus.shutdown()` on exit, but the MCP server path does not register equivalent cleanup.
- Safe modification: Register an `atexit` handler or `contextlib.ExitStack` in `create_server()` that calls `vault.event_bus.drain()` and `vault.event_bus.shutdown()`.
- Test coverage: MCP module is excluded from coverage (`pyproject.toml` line 124).

---

## Scaling Limits

**FTS5 full-table BM25 queries with no result limit on large vaults:**
- Current capacity: Acceptable under ~5,000 notes.
- Limit: FTS5 `MATCH` with `ORDER BY bm25()` must score every matching row before limiting. With tens of thousands of notes and common search terms, query time grows linearly.
- Scaling path: Add a `LIMIT` to the inner FTS5 subquery before Python-side re-ranking fetches extra candidates.

**NetworkX graph held in memory per-process:**
- Current capacity: Acceptable under ~50,000 edges.
- Limit: `GraphEngine._build_from_db()` loads all nodes and edges into a NetworkX `DiGraph` in memory. A dense vault with 10,000 notes and 5 links each = 50,000 edges at ~200 bytes each ≈ 10 MB — acceptable. At 500,000 edges, memory pressure becomes significant.
- Scaling path: Lazy-load subgraphs for targeted graph operations rather than loading the full graph.

---

## Dependencies at Risk

**`leidenalg` / `igraph` are optional extras without version pins:**
- Risk: The `community` optional extra in `pyproject.toml` (line 64) specifies `leidenalg` with no version constraint. `leidenalg` has historically broken its Python API on minor version bumps. The `GraphService._leiden_communities()` method in `src/ztlctl/services/graph.py` (line 191) has a `# type: ignore[import-not-found]` suppressor, meaning mypy never validates the call.
- Impact: A `leidenalg` release with an API change will break `graph themes` and `graph materialize` community detection silently (falls through to Louvain fallback).
- Migration plan: Pin `leidenalg>=0.10` (tested version) in the `community` extra; add `igraph` stub types or suppress via `overrides` in mypy config.

**`sentence-transformers` and `sqlite-vec` are unversioned optional extras:**
- Risk: `pyproject.toml` line 65 specifies `sentence-transformers>=2.2` and `sqlite-vec>=0.1`. Both packages have released breaking API changes since those lower bounds. `sqlite-vec` extension loading (`VectorService._load_sqlite_vec()`) uses undocumented `enable_load_extension` which may differ by SQLite build.
- Impact: Semantic search silently fails with `is_available() → False` if extension loading breaks; user sees a fallback to BM25 with no indication of the root cause.
- Migration plan: Add a diagnostic `ztlctl vector status` output that distinguishes between "package not installed", "extension load failed", and "table not initialized".

**`copier>=9.12.0` is a core dependency (not optional):**
- Risk: Copier is imported unconditionally in `src/ztlctl/services/workflow.py` (line 12). Copier 9.x has a large dependency tree (including `rich`, `pydantic`, `jinja2` — all already used). However, Copier's own release cadence can pin or conflict with transitive dependencies, particularly `pydantic-settings`.
- Impact: A Copier upgrade that tightens a transitive constraint could block `uv lock` resolution.
- Migration plan: Consider making Copier an optional extra (`workflow = ["copier>=9.12"]`) and guard imports in `WorkflowService` so the rest of ztlctl works without it.

---

## Test Coverage Gaps

**`src/ztlctl/services/session.py`, `src/ztlctl/services/reweave.py`, `src/ztlctl/services/check.py` are explicitly excluded from coverage:**
- What's not tested: All session lifecycle paths (start, close, reopen, enrichment pipeline), all reweave pipeline stages (DISCOVER→SCORE→FILTER→CONNECT), full check scan and fix categories.
- Files: `pyproject.toml` (line 125–127)
- Risk: These are among the most complex services (696, 819, 905 lines respectively). Regressions in session close, reweave scoring weights, or integrity fix logic will not be caught by the coverage gate.
- Priority: High — these services contain the core lifecycle business logic. The exclusion was pragmatic (test complexity) but should be incrementally lifted.

**All plugin code is excluded from coverage:**
- What's not tested: `GitPlugin` hooks, `ReweavePlugin` post-create flow, `EventBus` retry/drain/dead-letter paths, `PluginManager` entry-point discovery.
- Files: `pyproject.toml` (line 128); `src/ztlctl/plugins/`
- Risk: Plugin failures are designed to be silent warnings, making regressions particularly hard to detect without tests. The EventBus timeout and dead-letter accumulation bugs described above have no coverage.
- Priority: Medium — add targeted tests for the `EventBus` state machine (pending→completed, pending→failed→dead_letter) and `GitPlugin` batch vs immediate commit modes.

**MCP layer has zero coverage:**
- What's not tested: All 12 MCP tools, 6 resources, 4 prompts, and the `_impl` functions.
- Files: `pyproject.toml` (line 124); `src/ztlctl/mcp/`
- Risk: The `_impl` functions were specifically designed to be testable without the `mcp` package, but no tests exercise them. Breaking changes in any `_impl` function will not be caught.
- Priority: Medium — the `_impl` pattern is wasted investment if the functions are never tested. Add unit tests for the most critical `_impl` functions (create, search, session operations).

**Token estimation in context assembly is untested:**
- What's not tested: `estimate_tokens()` in `src/ztlctl/services/_helpers.py` is a character-count heuristic (`len(text) // 4`). The context assembly budget enforcement in `ContextAssembler.assemble()` (`src/ztlctl/services/context.py`) relies entirely on this. If actual token counts diverge significantly from the estimate (e.g., for CJK text or dense JSON), budget overruns go undetected.
- Files: `src/ztlctl/services/_helpers.py`, `src/ztlctl/services/context.py`
- Risk: Low in English-only vaults; high if non-ASCII content is used. No integration test verifies that assembled context stays within the requested budget.
- Priority: Low for English vaults; medium if internationalization is planned.

---

## Missing Critical Features

**No `ztlctl vector status` or vector diagnostics command:**
- Problem: When semantic search is unavailable, `VectorService.is_available()` returns `False` and all vector operations silently no-op. There is no user-facing command to distinguish "sqlite-vec not installed", "extension load failed on this SQLite build", "vec_items table not initialized", or "embeddings stale".
- Blocks: Users cannot self-diagnose semantic search failures without reading source code.

**No `event_wal` inspection or dead-letter management command:**
- Problem: Dead-letter events accumulate in `event_wal` with no user-visible surface. There is no `ztlctl events` or `ztlctl check --events` command.
- Blocks: Silent plugin failure investigation requires direct SQLite inspection.

---

*Concerns audit: 2026-03-19*
