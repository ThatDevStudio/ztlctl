---
phase: 01-core-hardening
verified: 2026-03-19T21:00:00Z
status: passed
score: 21/21 must-haves verified
re_verification: null
gaps: []
human_verification:
  - test: "Run 'ztlctl serve --transport http' and observe stderr"
    expected: "WARNING: HTTP transport has no authentication. Only use on trusted local networks. appears before server starts"
    why_human: "Requires a live CLI invocation with optional MCP dependency; not exercisable in grep/static analysis"
  - test: "Run 'ztlctl --help' and compare against README CLI Command Reference table"
    expected: "All 18 commands listed in README match actual help output; no undocumented commands and no missing commands"
    why_human: "CLI help accuracy is a documentation quality judgment; VALIDATION.md flags this as manual-only"
---

# Phase 01: Core Hardening Verification Report

**Phase Goal:** The existing codebase is stable, well-tested, performant, and has a formalized extensible data model ready for the action registry

**Verified:** 2026-03-19T21:00:00Z
**Status:** passed
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | All 4 content types and 5 subtypes have registered NoteTypeDefinitions | VERIFIED | registry.py lines 185-295: 9 built-in types registered via `_register_builtins()` |
| 2 | NoteTypeDefinition is a frozen dataclass with all 9 fields | VERIFIED | registry.py lines 43-88: `@dataclass(frozen=True)` with name, content_type, model_cls, transitions, template_name, required_sections, initial_status, is_subtype, parent_type |
| 3 | NoteTypeRegistry validates transitions and plugin registration | VERIFIED | registry.py lines 90-183: register/get/list_types/_validate_transitions methods |
| 4 | backup_retention_days config is enforced via age-based pruning | VERIFIED | check.py line 346-347: `retention_days = config.backup_retention_days` in `_prune_backups()` |
| 5 | VEC_CREATE_SQL dead code is removed from schema.py | VERIFIED | grep returns NOT_FOUND for VEC_CREATE_SQL in schema.py |
| 6 | import json is at module level in check.py | VERIFIED | check.py line 10: `import json` at module level (not inside loop) |
| 7 | Graph materialize is called after check --rebuild | VERIFIED | check.py line 257: `GraphService(self._vault).materialize_metrics()` |
| 8 | Git commit messages are sanitized (newlines/null bytes stripped) | VERIFIED | git.py lines 28-31: `def _sanitize_for_commit(text: str)`, applied at lines 79-80, 97, 113 |
| 9 | MCP HTTP transport emits warning before server starts | VERIFIED | serve.py line 45: `"WARNING: HTTP transport has no authentication. Only use on trusted local networks."` |
| 10 | Copier trust/unsafe behavior documented | VERIFIED | workflow.py lines 340, 359, 375: SECURITY comments on all three Copier call sites |
| 11 | rebuild() uses ThreadPoolExecutor for parallel file reads | VERIFIED | check.py lines 12, 62-63, 175-176: import, `_read_file()` helper, `ThreadPoolExecutor(max_workers=8)` |
| 12 | reweave batch FTS5 BM25 scoring (single query, not per-candidate) | VERIFIED | reweave.py line 443-470: `_score_bm25()` with `_fts5_escape()` building one query, `bm25(nodes_fts)` |
| 13 | betweenness centrality uses k-approximation for graphs > 500 nodes | VERIFIED | graph.py lines 587-589: `k_param = None if node_count <= 500 else min(500, node_count)`, `betweenness_centrality(g, k=k_param, seed=42)` |
| 14 | All coverage exclusions removed except __main__.py | VERIFIED | pyproject.toml omit contains only `"src/ztlctl/__main__.py"` |
| 15 | EventBus dead_letter state machine path is tested | VERIFIED | test_event_bus.py lines 325-360: `test_event_transitions_to_dead_letter_after_max_retries` |
| 16 | MCP _impl functions tested without mcp package | VERIFIED | tests/mcp/test_tools_impl.py: 6 test functions (create_note, search, get_document) |
| 17 | Session, reweave, check service tests meet coverage | VERIFIED | test_session.py: TestSessionNamedAcceptanceCriteria; test_reweave.py: TestReweaveNamedAcceptanceCriteria; test_check.py: test_backup_retention_days_prunes_old_backups, TestRebuildCompleteness |
| 18 | Vault._check_schema_current() detects stale schema | VERIFIED | vault.py line 390: `def _check_schema_current(self) -> bool:`, line 407: `ctx.get_current_revision()` |
| 19 | Stale schema warning is non-fatal and goes to stderr | VERIFIED | _context.py lines 53-55: `if not self._vault._check_schema_current():` then `click.echo(..., err=True)` |
| 20 | CheckService has schema_version error category | VERIFIED | check.py lines 50, 83-84, 378-385: `CAT_SCHEMA_VERSION`, `_check_schema_version()` called in `check()` |
| 21 | README documents all key commands and --log-json | VERIFIED | README.md lines 95, 108-113: `--log-json`, `ztlctl check`, `ztlctl upgrade`, `ztlctl serve`, CLI Command Reference table |

**Score:** 21/21 truths verified

---

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/ztlctl/domain/registry.py` | NoteTypeDefinition frozen dataclass + NoteTypeRegistry + 9 built-ins | VERIFIED | @dataclass(frozen=True), 9 types in _register_builtins(), get_note_type_registry() accessor |
| `tests/domain/test_registry.py` | Unit tests for all registry behaviors | VERIFIED | 23 test functions |
| `src/ztlctl/services/check.py` | backup_retention_days enforcement, import json, ThreadPoolExecutor, materialize after rebuild, schema check | VERIFIED | All 5 items confirmed via grep |
| `src/ztlctl/infrastructure/database/schema.py` | VEC_CREATE_SQL removed | VERIFIED | grep returns NOT_FOUND |
| `src/ztlctl/plugins/builtins/git.py` | _sanitize_for_commit helper applied to all commit messages | VERIFIED | Lines 28-31 define helper; applied at 79-80, 97, 113 |
| `src/ztlctl/commands/serve.py` | WARNING on HTTP transports | VERIFIED | Line 45 |
| `src/ztlctl/services/workflow.py` | Copier unsafe=False documented | VERIFIED | SECURITY comments on all three Copier call sites |
| `src/ztlctl/services/reweave.py` | Batch FTS5 BM25 scoring | VERIFIED | _fts5_escape() + single bm25(nodes_fts) query in _score_bm25() |
| `src/ztlctl/services/graph.py` | k-approximation for betweenness centrality in materialize_metrics | VERIFIED | Lines 587-589 |
| `pyproject.toml` | Coverage omit = only __main__.py | VERIFIED | Single entry confirmed |
| `tests/plugins/test_event_bus.py` | dead_letter state machine test | VERIFIED | test_event_transitions_to_dead_letter_after_max_retries |
| `tests/mcp/test_tools_impl.py` | MCP _impl tests | VERIFIED | 6 test functions |
| `tests/services/test_check.py` | backup_retention test, rebuild test | VERIFIED | Lines 855, 888-891 |
| `tests/services/test_session.py` | Session lifecycle named tests | VERIFIED | TestSessionNamedAcceptanceCriteria with 2 tests |
| `tests/services/test_reweave.py` | Reweave pipeline named tests | VERIFIED | TestReweaveNamedAcceptanceCriteria with 6 tests |
| `src/ztlctl/infrastructure/vault.py` | _check_schema_current() with pre-Alembic handling | VERIFIED | Lines 390-411 |
| `src/ztlctl/commands/_context.py` | Stale warning on lazy vault init | VERIFIED | Lines 53-55 |
| `tests/services/test_upgrade.py` | TestCheckSchemaCurrent with 4 tests | VERIFIED | Lines 117-143+ |
| `README.md` | CLI Command Reference with all commands | VERIFIED | Lines 95, 108-113 |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `src/ztlctl/domain/registry.py` | `src/ztlctl/domain/content.py` | `from ztlctl.domain.content import` | WIRED | Line 18 confirms import |
| `src/ztlctl/domain/registry.py` | `src/ztlctl/domain/lifecycle.py` | `from ztlctl.domain.lifecycle import` | WIRED | Line 26 confirms import |
| `src/ztlctl/services/check.py` | `src/ztlctl/config/models.py` | reads `backup_retention_days` from CheckConfig | WIRED | Line 347 reads `config.backup_retention_days` |
| `src/ztlctl/services/check.py` | `src/ztlctl/services/graph.py` | `GraphService.materialize_metrics()` after rebuild | WIRED | Line 257 |
| `src/ztlctl/services/check.py` | `concurrent.futures` | ThreadPoolExecutor for parallel reads | WIRED | Line 12 top-level import |
| `src/ztlctl/infrastructure/vault.py` | `alembic` | `MigrationContext.get_current_revision()` vs head | WIRED | Line 407 |
| `src/ztlctl/commands/_context.py` | `src/ztlctl/infrastructure/vault.py` | `_check_schema_current()` on lazy vault init | WIRED | Line 53 |
| `pyproject.toml` | `src/ztlctl/services/session.py` | coverage omit removal (session now measured) | WIRED | session.py absent from omit list |

---

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| HARD-01 | 01-02-PLAN | Tech debt cleanup: backup_retention_days enforced, VEC_CREATE_SQL removed, import json moved, post-rebuild graph materialize | SATISFIED | All 4 items verified in check.py and schema.py |
| HARD-02 | 01-01-PLAN | Data model consistency: NoteTypeDefinition as canonical lifecycle + type descriptor | SATISFIED | registry.py with 9 built-in types, transition integrity validation |
| HARD-03 | 01-05-PLAN | UX polish: CLI rough edges, progressive disclosure consistency | SATISFIED | serve.py HTTP warning; Copier fallback surfaced; README accurate |
| HARD-04 | 01-05-PLAN | Documentation audit: README and help text accuracy | SATISFIED | README CLI Command Reference table with 18 commands and --log-json |
| HARD-05 | 01-04-PLAN | Test coverage gaps closed: session, reweave, check, plugins, MCP lifted from exclusion | SATISFIED | pyproject.toml omit = only __main__.py; 1553 tests at 87.66% coverage |
| HARD-06 | 01-03-PLAN | Performance bottleneck fixes: rebuild parallelization, FTS5 batch, betweenness k-approx | SATISFIED | ThreadPoolExecutor in check.py, _fts5_escape + batch bm25 in reweave.py, k_param in graph.py |
| HARD-07 | 01-02-PLAN | Security: git sanitization, HTTP transport warning, Copier trust audit | SATISFIED | _sanitize_for_commit in git.py, WARNING in serve.py, SECURITY comments in workflow.py |
| HARD-08 | 01-05-PLAN | Vault schema versioning: stale detection, upgrade path, forward-compatible markers | SATISFIED | _check_schema_current() in vault.py, stale warning in _context.py, _check_schema_version() in check.py |
| HARD-09 | 01-01-PLAN | NoteTypeDefinition as extensible primitive: formalizes type + transitions + template as registrable unit | SATISFIED | NoteTypeDefinition frozen dataclass + NoteTypeRegistry with plugin registration support |

All 9 requirements from REQUIREMENTS.md Phase 1 mapping are SATISFIED. No orphaned requirements detected.

---

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `src/ztlctl/services/graph.py` | 385 | `nx.betweenness_centrality(g)` in `bridges()` method — no k-approximation | INFO | `bridges()` is a user-invoked query method, not a periodic metric. The k-approximation plan (HARD-06) targeted only `materialize_metrics()`. Out of scope but worth noting for large-vault performance. |

No blocker anti-patterns found. The `bridges()` betweenness call is a pre-existing pattern in a different method context than what the plan addressed; it does not block any phase requirement.

---

### Human Verification Required

#### 1. HTTP Transport Warning — Live Invocation

**Test:** Run `ztlctl serve --transport http` (or `--transport sse`) in a terminal with the `ztlctl[mcp]` extra installed
**Expected:** The string "WARNING: HTTP transport has no authentication. Only use on trusted local networks." appears on stderr before the server starts
**Why human:** Requires the optional MCP dependency; not statically verifiable; VALIDATION.md flags this as manual-only (HARD-07)

#### 2. CLI Help Text Accuracy

**Test:** Run `ztlctl --help` and compare every command group against the README CLI Command Reference table (18 commands listed)
**Expected:** All 18 commands in README match the actual CLI help output; no command missing from README; no command in help output absent from README
**Why human:** Documentation quality judgment; VALIDATION.md explicitly flags this as manual-only (HARD-04)

---

### Summary

Phase 01 goal is achieved. All 9 requirements (HARD-01 through HARD-09) are satisfied with concrete implementation evidence:

- **NoteTypeDefinition registry** (HARD-02, HARD-09): `domain/registry.py` is a substantive frozen dataclass with 9 built-in types, full transition validation, and plugin registration — wired to content.py and lifecycle.py.
- **Tech debt cleanup** (HARD-01): 4 of 4 items confirmed — backup_retention_days enforced, VEC_CREATE_SQL removed, import json at module level, graph materialized post-rebuild.
- **Security hardening** (HARD-07): All 3 items confirmed — git sanitization applied to all commit message fields, HTTP warning in serve.py, Copier unsafe=False documented.
- **Performance** (HARD-06): All 3 bottlenecks fixed — ThreadPoolExecutor parallel reads (writes sequential), single batch FTS5 query with proper escaping, betweenness k-approximation in materialize_metrics.
- **Coverage** (HARD-05): pyproject.toml omit reduced to __main__.py only; 1553 tests at 87.66% coverage (threshold 80%).
- **Schema versioning** (HARD-08): _check_schema_current() in vault with pre-Alembic handling, non-fatal warning in AppContext, schema_version error category in CheckService.
- **Documentation** (HARD-03, HARD-04): README CLI Command Reference section added with all 18 commands and --log-json; Copier UX warnings surfaced.

One notable info-level finding: `graph.py bridges()` at line 385 uses `nx.betweenness_centrality(g)` without the k-approximation that `materialize_metrics()` received. This is outside the scope of HARD-06 (which targeted only materialize_metrics) but may warrant future attention for large-vault invocations of `ztlctl graph bridges`.

Two items flagged for human verification (HTTP warning live test, CLI help accuracy) per VALIDATION.md's manual-only classification — automated checks passed for all other behaviors.

---

_Verified: 2026-03-19T21:00:00Z_
_Verifier: Claude (gsd-verifier)_
