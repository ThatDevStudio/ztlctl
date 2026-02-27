# ztlctl — Remaining Tasks

> Comprehensive audit of DESIGN.md vs current implementation (Phase 0–8 complete, ~1095 tests).
> Generated 2026-02-26 from codebase analysis.

## Legend

**Effort:** S (< 1 hour), M (1–4 hours), L (4–8 hours), XL (1–2 days)
**Impact:** Critical (blocks users), High (meaningful capability), Medium (polish/completeness), Low (nice-to-have)

---

## 1. Feature Gaps (Designed but Not Implemented)

### T-001: Post-Create Automatic Reweave ✅

**Effort:** M | **Impact:** High | **Status:** Done (PR #53)

DESIGN.md Section 4 states: "Reweave runs unless `--no-reweave` is passed." Currently, reweave is only triggered manually via `ztlctl reweave` or automatically at session close. The `--no-reweave` global CLI flag is parsed into `ZtlSettings.no_reweave` but never consulted by any code.

**What to do:**

- Option A (plugin approach): Create `src/ztlctl/plugins/builtins/reweave_plugin.py` with a `post_create` hookimpl that calls `ReweaveService.reweave(content_id=...)`. Check `no_reweave` setting before triggering. Register in `Vault.init_event_bus()`.
- Option B (service approach): Add a reweave call directly in `CreateService._create_content()` after the INDEX stage, gated by `self._vault.settings.no_reweave`.
- Wire `--no-reweave` flag to skip the automatic reweave.
- Update tests to verify post-create reweave runs (and is skipped with `--no-reweave`).

**Files:**

- Create: `src/ztlctl/plugins/builtins/reweave_plugin.py` (Option A)
- Modify: `src/ztlctl/services/create.py` (Option B)
- Modify: `src/ztlctl/infrastructure/vault.py` (register plugin, Option A)
- Test: `tests/services/test_create.py`, `tests/test_workflows.py`

---

### T-002: `graph unlink` Command

**Effort:** M | **Impact:** Medium

DESIGN.md Section 5 specifies: "`ztlctl graph unlink ztl_source ztl_target` removes specific links." This command does not exist. Currently the only way to remove links is via `reweave --prune`.

**What to do:**

- Add `unlink` subcommand to graph command group.
- Accept `source_id` and `target_id` positional arguments.
- Remove edge from `edges` table, remove body wikilink (if present, respecting garden note protection), remove frontmatter `links.relates` entry.
- Re-index FTS5 for affected notes.
- Return ServiceResult with details of what was removed.

**Files:**

- Modify: `src/ztlctl/commands/graph.py` (add subcommand)
- Modify: `src/ztlctl/services/graph.py` (add `unlink()` method)
- Test: `tests/services/test_graph.py`, `tests/commands/test_graph_cmd.py`

---

### T-003: `--ignore-checkpoints` Flag on `agent context` ✅

**Effort:** S | **Impact:** Medium | **Status:** Done — CLI → SessionService → ContextAssembler fully wired

DESIGN.md Section 8 specifies: "The `--ignore-checkpoints` flag reads full history when needed." The checkpoint-based retrieval is implemented, but the override flag is missing.

**What to do:**

- Add `ignore_checkpoints: bool = False` parameter to `ContextAssembler.assemble()`.
- Thread through `SessionService.context()`.
- Add `@click.option("--ignore-checkpoints", is_flag=True)` to `agent context` CLI command.
- In `context.py:_log_entries()`, skip the checkpoint query when flag is True.

**Files:**

- Modify: `src/ztlctl/services/context.py` (assembler + `_log_entries`)
- Modify: `src/ztlctl/services/session.py` (pass-through)
- Modify: `src/ztlctl/commands/agent.py` (CLI flag)
- Test: `tests/services/test_context.py`

---

### T-004: `orphan_reweave_threshold` Config Usage ✅

**Effort:** S | **Impact:** Low | **Status:** Done — used in `_orphan_sweep()` via `min_score_override`

`SessionConfig.orphan_reweave_threshold = 0.2` is defined in `config/models.py:91` but never referenced. The orphan sweep in `SessionService.close()` should use this as a lowered threshold when re-attempting reweave on orphan notes (notes with zero links).

**What to do:**

- In `SessionService.close()` orphan sweep section, pass `min_score_threshold=self._vault.settings.session.orphan_reweave_threshold` to `ReweaveService.reweave()`.
- Add test verifying lower threshold is used for orphans.

**Files:**

- Modify: `src/ztlctl/services/session.py` (orphan sweep)
- Test: `tests/services/test_session.py`

---

### T-005: Garden Advisory Features

**Effort:** L | **Impact:** Medium

`GardenConfig` defines three criteria that are never used:

- `seed_age_warning_days: int = 7` — warn about aging seeds
- `evergreen_min_key_points: int = 5` — evergreen readiness threshold
- `evergreen_min_bidirectional_links: int = 3` — evergreen readiness threshold

**What to do:**

- Add a `garden_health` check category to `CheckService.check()`:
  - Scan for notes with `maturity="seed"` created > `seed_age_warning_days` ago.
  - Scan for notes meeting evergreen criteria (key_points count from frontmatter, bidirectional link count from edges) that are still `seed` or `budding`.
  - Return advisory warnings (not errors) in the check report.
- Optionally add `garden status` subcommand showing maturity distribution and readiness candidates.

**Files:**

- Modify: `src/ztlctl/services/check.py` (new check category)
- Optionally modify: `src/ztlctl/commands/garden.py` (new subcommand)
- Test: `tests/services/test_check.py`

---

### T-006: Interactive Create Prompts

**Effort:** M | **Impact:** Medium

DESIGN.md Section 4 mentions three interaction profiles: Interactive (prompts for missing fields), Auto, and Non-interactive. Currently `create` commands accept flags only — no interactive prompting. The `init` command has interactive prompts, but `create` does not.

**What to do:**

- In interactive mode (when `--no-interact` is not set and stdin is a TTY), prompt for optional fields:
  - `create note`: prompt for tags if not provided, suggest related content from recent session.
  - `create reference`: prompt for URL if not provided.
  - `create task`: prompt for priority/impact/effort if not provided.
- Skip prompts when `--no-interact` or `--json` is set.
- Use `click.prompt()` / `click.confirm()` following the same pattern as `init_cmd.py`.

**Files:**

- Modify: `src/ztlctl/commands/create.py`
- Test: `tests/commands/test_create_cmd.py`

---

### T-007: Bidirectional Edge Materialization

**Effort:** M | **Impact:** Low

The `edges.bidirectional` column exists in the schema (reserved since Phase 1) but is never written. DESIGN.md notes it as reserved for future use.

**What to do:**

- In `GraphService.materialize_metrics()`, compute bidirectional flag: for each edge (A→B), check if (B→A) exists, and set `bidirectional=1`.
- Update `ztlctl check` graph health category to report bidirectional edge stats.
- Consider using bidirectional links in `GardenConfig.evergreen_min_bidirectional_links` check (T-005).

**Files:**

- Modify: `src/ztlctl/services/graph.py` (`materialize_metrics`)
- Modify: `src/ztlctl/services/check.py` (graph health reporting)
- Test: `tests/services/test_graph.py`

---

### T-008: `cluster_id` Materialization ✅

**Effort:** S | **Impact:** Low | **Status:** Done — computed in `materialize_metrics()` via Leiden→Louvain

The `nodes.cluster_id` column exists in the schema but is never written. `GraphService.materialize_metrics()` computes degree, pagerank, and betweenness — but not cluster assignments from community detection.

**What to do:**

- In `GraphService.materialize_metrics()`, run community detection (same Leiden → Louvain fallback used in `themes()`) and write `cluster_id` to each node.
- This enables cluster-based queries and filtering in future.

**Files:**

- Modify: `src/ztlctl/services/graph.py` (`materialize_metrics`)
- Test: `tests/services/test_graph.py`

---

## 2. Deferred Features (Explicitly Deferred in DESIGN.md)

### T-009: Local Directory Plugin Discovery

**Effort:** M | **Impact:** Medium

DESIGN.md Section 15: "Discovery: entry_points (pip-installed) + `.ztlctl/plugins/` (local)." Currently only entry-point discovery is implemented. Local plugins would enable per-vault customization without packaging.

**What to do:**

- In `PluginManager.discover_and_load()`, scan `.ztlctl/plugins/` for Python modules.
- Load via `importlib.import_module()` or `importlib.util.spec_from_file_location()`.
- Register each discovered plugin class via `register_plugin()`.
- Validate plugin classes implement the hookspec interface.
- Handle load errors gracefully (warning, not failure — per invariant).

**Files:**

- Modify: `src/ztlctl/plugins/manager.py`
- Test: `tests/plugins/test_manager.py`

---

### T-010: Copier Workflow Templates

**Effort:** XL | **Impact:** Medium

DESIGN.md Section 15: "`ztlctl workflow init` — interactive, CRA-style: source control, viewer, workflow, skill set. Powered by Copier."

The `workflow` command group exists but is empty (no subcommands). This feature adds composable template layers for different workflow configurations.

**What to do:**

- Add `copier` dependency.
- Create template directory structure with composable layers (git, obsidian, claude-driven, agent-generic, manual, research, engineering, minimal).
- Implement `workflow init` subcommand: interactive prompts for source control, viewer, workflow, skill set. Invoke Copier to scaffold.
- Implement `workflow update` subcommand: merge template improvements into existing vault.
- Store answers in `.ztlctl/workflow-answers.yml`.

**Files:**

- Modify: `pyproject.toml` (add `copier` dependency)
- Create: `src/ztlctl/templates/workflow/` (Copier template layers)
- Modify: `src/ztlctl/commands/workflow.py` (add `init`, `update` subcommands)
- Create: `src/ztlctl/services/workflow.py` (if needed)
- Test: `tests/commands/test_workflow_cmd.py`

---

### T-011: MCP Tool Proliferation Guard

**Effort:** M | **Impact:** Low

DESIGN.md Section 16: "At 15+ tools (from plugin registration), activate `discover_tools` meta-tool for progressive discovery by category."

Currently all 12 tools are registered unconditionally. Plugin-contributed tools could push the count past the usability threshold.

**What to do:**

- Track total registered tool count in `register_tools()`.
- If count >= 15, replace individual tool registrations with a single `discover_tools` meta-tool that lists tools by category and a `use_tool` proxy that forwards calls.
- Alternatively, register all tools but add a `discover_tools` tool that returns a categorized listing regardless of count.

**Files:**

- Modify: `src/ztlctl/mcp/tools.py`
- Test: `tests/mcp/test_tools.py`

---

### T-012: MCP Streamable HTTP Transport

**Effort:** L | **Impact:** Medium

DESIGN.md Section 16: "stdio default. Streamable HTTP optional for remote access." Currently `ztlctl serve --transport` only accepts `stdio`.

**What to do:**

- Add `http` as a transport option in `commands/serve.py` (`click.Choice(["stdio", "http"])`).
- Use FastMCP's streamable HTTP transport (if supported) or implement SSE-based transport.
- Add `--host` and `--port` options for HTTP mode.
- Consider authentication for remote access.

**Files:**

- Modify: `src/ztlctl/commands/serve.py`
- Modify: `src/ztlctl/mcp/server.py`
- Test: `tests/mcp/test_server.py`

---

### T-013: User-Provided Jinja2 Templates

**Effort:** M | **Impact:** Low

DESIGN.md Section 2: "User-provided templates supported in future versions." Currently only bundled templates in `src/ztlctl/templates/` are used.

**What to do:**

- Check for user templates in `.ztlctl/templates/` before falling back to bundled templates.
- Use Jinja2 `ChoiceLoader` with `FileSystemLoader(.ztlctl/templates/)` first, `PackageLoader` second.
- Apply to both `self/` templates (identity, methodology) and `content/` templates (note bodies).
- Document template override mechanism.

**Files:**

- Modify: `src/ztlctl/services/init.py` (self/ templates)
- Modify: `src/ztlctl/domain/content.py` (body templates)
- Test: `tests/services/test_init.py`, `tests/domain/test_content.py`

---

### T-014: Custom Subtypes (Plugin-Registered Content Models)

**Effort:** L | **Impact:** Low

DESIGN.md Section 2: "No custom subtypes in v1 — shipped subtypes use the same extensibility mechanism, allowing us to tune before opening to users."

`CONTENT_REGISTRY` is a module-level dict populated by `register_built_in_models()`. No external registration mechanism exists.

**What to do:**

- Add a pluggy hookspec `register_content_models()` that returns a dict of `{name: ContentModel subclass}`.
- Call during plugin discovery to extend `CONTENT_REGISTRY`.
- Validate custom models implement required classmethods (validate_create, validate_update, etc.).
- Handle conflicts (custom model name collides with built-in) with a warning.

**Files:**

- Modify: `src/ztlctl/plugins/hookspecs.py` (new hookspec)
- Modify: `src/ztlctl/domain/content.py` (registration API)
- Modify: `src/ztlctl/plugins/manager.py` (call hook during discovery)
- Test: `tests/plugins/test_manager.py`, `tests/domain/test_content.py`

---

### T-015: Semantic Search

**Effort:** XL | **Impact:** High

DESIGN.md Section 8 and config reference: `SearchConfig` has `semantic_enabled`, `embedding_model`, `embedding_dim` fields — all defined but unused. The optional `[semantic]` extra lists `sqlite-vec`.

**What to do:**

- Add `sqlite-vec` integration for vector storage.
- Create embedding pipeline: content → embedding model → vector insert.
- Add `--rank-by semantic` mode to `query search`.
- Hybrid ranking: combine BM25 with cosine similarity scores.
- Gate behind `search.semantic_enabled = true` config flag.
- Support `embedding_model = "local"` (e.g., sentence-transformers) and potentially API-based models.
- Import-guard like MCP (`try/except ImportError`).

**Files:**

- Create: `src/ztlctl/infrastructure/database/vectors.py`
- Modify: `src/ztlctl/services/query.py` (semantic ranking)
- Modify: `src/ztlctl/services/create.py` (embed on create)
- Modify: `src/ztlctl/services/update.py` (re-embed on update)
- Test: `tests/services/test_query.py`, integration tests

---

## 3. CLI Completeness

### T-016: `extract` Command Naming ✅

**Effort:** S | **Impact:** Low | **Status:** Done — accepted current naming, DESIGN.md updated

DESIGN.md shows `ztlctl extract decision LOG-0042` as the invocation. The current CLI is `ztlctl extract LOG-0042` — a standalone command, not a subcommand of an `extract` group. While functional, the naming diverges from design.

**What to do:**

- Either: Convert `extract` to a command group with `decision` as a subcommand (allows future `extract summary`, `extract timeline`, etc.).
- Or: Accept the current naming and update DESIGN.md to match.

**Files:**

- Modify: `src/ztlctl/commands/extract.py`
- Test: `tests/commands/test_extract_cmd.py`

---

### T-017: `--examples` Flag Coverage Audit ✅

**Effort:** S | **Impact:** Low | **Status:** Done — all commands/groups now have `examples=`

DESIGN.md Section 12 states `--examples` should be on every command. All commands use `ZtlCommand`/`ZtlGroup` base classes which support `examples=`, but not all commands may have examples defined.

**What to do:**

- Audit all commands and groups for `examples=` kwargs.
- Add example text to any commands missing it.
- Verify examples are accurate and render correctly.

**Files:**

- Modify: Various `src/ztlctl/commands/*.py` files as needed

---

## 4. Code Quality and Technical Debt

### T-018: Stale Plan Documents ✅

**Effort:** S | **Impact:** Low | **Status:** Done — moved to `docs/plans/archive/`

Three plan documents in `docs/plans/` reference completed work:

- `2026-02-25-session-stubs.md` — all three stubs (log_entry, cost, context) are fully implemented.
- `2026-02-26-verbose-telemetry-design.md` — merged as PR #50.
- `2026-02-26-verbose-telemetry-impl.md` — merged as PR #50.

**What to do:**

- Archive or delete stale plans. Options:
  - Move to `docs/plans/archive/`
  - Delete and rely on git history
  - Add "COMPLETED" header to each

**Files:**

- `docs/plans/2026-02-25-session-stubs.md`
- `docs/plans/2026-02-26-verbose-telemetry-design.md`
- `docs/plans/2026-02-26-verbose-telemetry-impl.md`

---

### T-019: `type: ignore` Comment Audit

**Effort:** S | **Impact:** Low

22 `# type: ignore` comments across the codebase. Most are justified (MCP untyped decorators, optional imports, test type narrowing), but should be periodically reviewed as dependencies update.

- 17 in `src/ztlctl/mcp/` — FastMCP decorator typing
- 2 in `src/ztlctl/services/graph.py` — optional `igraph`/`leidenalg` imports
- 1 in `src/ztlctl/mcp/server.py` — conditional MCP import
- 2 in `src/ztlctl/services/telemetry.py` — assignment narrowing

**What to do:**

- No action needed now. Revisit when FastMCP adds type stubs (would eliminate 17 ignores).
- Track as technical debt; check on dependency updates.

---

### T-020: DESIGN.md Implementation Notes Refresh

**Effort:** M | **Impact:** Low

DESIGN.md contains implementation notes from Phase 1–7 that reference line numbers, which may have drifted. The Phase 8 (verbose telemetry) addition is not yet documented in DESIGN.md.

**What to do:**

- Add Phase 8 implementation notes (telemetry, structlog, `@traced`, `trace_span`, `--log-json`, `--verbose` span tree rendering).
- Remove stale line number references or convert to section references.
- Update the backlog table (Section 20) with Phase 8 entry and test count.

**Files:**

- Modify: `DESIGN.md` (Sections 10, 17, 20)

---

### T-021: `docs/` Directory in Git Status ✅

**Effort:** S | **Impact:** Low | **Status:** Done — `docs/` tracked in git

`git status` shows `docs/` as untracked. The `docs/plans/` subdirectory contains plan documents that should be tracked.

**What to do:**

- `git add docs/` and commit the plan documents (or add to `.gitignore` if not desired in repo).
- Decide on policy: plans in repo or external.

---

## 5. Robustness and Polish

### T-022: `--no-reweave` Flag Wiring (Prerequisite for T-001) ✅

**Effort:** S | **Impact:** Medium | **Status:** Done (PR #53, wired with T-001)

Even if T-001 (post-create reweave) is not immediately implemented, the `--no-reweave` flag should at minimum be documented as a no-op or removed from the CLI to avoid user confusion.

**What to do:**

- If T-001 is planned: implement T-001 which naturally wires the flag.
- If T-001 is deferred: either remove the flag from `cli.py` and `ZtlSettings`, or add a comment documenting it as reserved.

**Files:**

- Modify: `src/ztlctl/cli.py`, `src/ztlctl/config/settings.py`

---

### T-023: Session Close Event WAL Drain Verification ✅

**Effort:** S | **Impact:** Medium | **Status:** Done — `bus.drain()` called in `session.py:192`

DESIGN.md Section 6 specifies session close drains the event WAL as the final step: "Drain event WAL: Sync barrier for async workflow events (wait for in-flight, retry failures, report)." Verify this is correctly implemented and add integration test if missing.

**What to do:**

- Verify `SessionService.close()` calls `EventBus.drain()` after the enrichment pipeline.
- Add integration test that creates content during a session, closes session, and verifies all events are processed (no pending/failed in event_wal).

**Files:**

- Check: `src/ztlctl/services/session.py`
- Test: `tests/integration/test_session_lifecycle.py` or similar

---

### T-024: Alembic Migration Testing

**Effort:** M | **Impact:** Medium

The upgrade pipeline (BACKUP → MIGRATE → VALIDATE → REPORT) is implemented, but migration testing could be more robust. Consider adding tests that:

- Create a vault with an older schema version, run upgrade, verify schema matches current.
- Test the pre-Alembic detection path (tables exist but no `alembic_version`).
- Test backup + rollback across a migration.

**What to do:**

- Add integration tests for the migration path.
- Test forward migration and rollback scenarios.

**Files:**

- Test: `tests/integration/test_upgrade.py` or `tests/services/test_upgrade.py`

---

### T-025: `--cost` Flag on All Actions ✅

**Effort:** M | **Impact:** Low | **Status:** Done (PR #52)

DESIGN.md Section 8: "All actions accept a `--cost` argument. Token cost is pre-computed per log entry and stored in the DB."

Currently only `agent session log --cost N` accepts a cost argument. Other commands (create, update, etc.) do not pass cost to session logging.

**What to do:**

- Add `--cost` option to commands that modify content (create, update, archive, supersede, reweave).
- When a session is active, automatically create a log entry with the provided cost.
- Or: decide this is a workflow-layer concern (the agent calls `log_entry --cost` separately) and update DESIGN.md to clarify.

**Files:**

- Modify: Various `src/ztlctl/commands/*.py`
- Modify: `src/ztlctl/services/session.py` (auto-log with cost)

---

## Summary Table

| ID | Task | Effort | Impact | Category | Status |
|----|------|--------|--------|----------|--------|
| T-001 | Post-create automatic reweave | M | High | Feature gap | ✅ Done |
| T-002 | `graph unlink` command | M | Medium | Feature gap | |
| T-003 | `--ignore-checkpoints` flag | S | Medium | Feature gap | ✅ Done |
| T-004 | `orphan_reweave_threshold` usage | S | Low | Feature gap | ✅ Done |
| T-005 | Garden advisory features | L | Medium | Feature gap | |
| T-006 | Interactive create prompts | M | Medium | Feature gap | |
| T-007 | Bidirectional edge materialization | M | Low | Feature gap | |
| T-008 | `cluster_id` materialization | S | Low | Feature gap | ✅ Done |
| T-009 | Local directory plugin discovery | M | Medium | Deferred | |
| T-010 | Copier workflow templates | XL | Medium | Deferred | |
| T-011 | MCP tool proliferation guard | M | Low | Deferred | |
| T-012 | MCP streamable HTTP transport | L | Medium | Deferred | |
| T-013 | User-provided Jinja2 templates | M | Low | Deferred | |
| T-014 | Custom subtypes (plugin-registered) | L | Low | Deferred | |
| T-015 | Semantic search | XL | High | Deferred | |
| T-016 | `extract` command naming | S | Low | CLI | ✅ Done |
| T-017 | `--examples` flag coverage audit | S | Low | CLI | ✅ Done |
| T-018 | Stale plan documents | S | Low | Code quality | ✅ Done |
| T-019 | `type: ignore` comment audit | S | Low | Code quality | |
| T-020 | DESIGN.md Phase 8 update | M | Low | Code quality | |
| T-021 | `docs/` directory git tracking | S | Low | Code quality | ✅ Done |
| T-022 | `--no-reweave` flag wiring | S | Medium | Robustness | ✅ Done |
| T-023 | Session close WAL drain verification | S | Medium | Robustness | ✅ Done |
| T-024 | Alembic migration testing | M | Medium | Robustness | |
| T-025 | `--cost` flag on all actions | M | Low | Robustness | ✅ Done |
