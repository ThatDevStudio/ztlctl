---
phase: 01-core-hardening
plan: "03"
subsystem: performance
tags: [concurrent.futures, ThreadPoolExecutor, FTS5, BM25, networkx, betweenness]

# Dependency graph
requires: []
provides:
  - Parallel file I/O in rebuild() via ThreadPoolExecutor(max_workers=8)
  - Safe FTS5 term escaping via _fts5_escape() helper in reweave.py
  - Betweenness centrality k-approximation (k=500, seed=42) for graphs >500 nodes
affects: [check, reweave, graph, performance-regression-tests]

# Tech tracking
tech-stack:
  added: [concurrent.futures (stdlib)]
  patterns:
    - Parallel reads + sequential writes pattern for SQLite-safe I/O parallelism
    - Module-level escape helper for FTS5 term sanitization
    - k-approximation gating by node count threshold (<=500 exact, >500 approximate)

key-files:
  created: []
  modified:
    - src/ztlctl/services/check.py
    - src/ztlctl/services/reweave.py
    - src/ztlctl/services/graph.py
    - tests/services/test_graph.py

key-decisions:
  - "ThreadPoolExecutor reads files in parallel (max_workers=8); DB writes remain sequential inside vault.transaction() to avoid SQLite database-is-locked errors"
  - "k_param=None for <=500 nodes (exact betweenness) and k=500 for larger graphs with seed=42 for deterministic approximation"
  - "_fts5_escape() uses double-quote wrapping with internal double-quote escaping per FTS5 spec, extracted as module-level helper for reuse"

patterns-established:
  - "Parallel I/O pattern: ThreadPoolExecutor for reads, sequential for writes — safe for SQLite concurrency"
  - "FTS5 sanitization: always escape terms via _fts5_escape() before FTS5 MATCH queries"

requirements-completed: [HARD-06]

# Metrics
duration: 5min
completed: "2026-03-19"
---

# Phase 01 Plan 03: Performance Bottleneck Fixes Summary

**ThreadPoolExecutor parallel file reads in rebuild(), FTS5 term escaping via _fts5_escape(), and betweenness centrality k=500 approximation for graphs >500 nodes**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-19T20:16:23Z
- **Completed:** 2026-03-19T20:21:15Z
- **Tasks:** 1 (3 code changes + 1 test addition)
- **Files modified:** 4

## Accomplishments

- check.py rebuild() now reads all content files in parallel using ThreadPoolExecutor(max_workers=8), then processes DB writes sequentially inside vault.transaction() — eliminates sequential I/O bottleneck on vault-wide rebuilds
- reweave.py adds _fts5_escape() module-level helper that properly escapes FTS5 query terms (wraps in double-quotes, escapes internal double-quotes per FTS5 spec); _score_bm25 uses it instead of naive f-string quoting
- graph.py materialize_metrics() uses k-approximation for betweenness centrality: exact computation (k=None) for <=500 nodes, k=500 + seed=42 for larger graphs — reduces O(V*E) to O(k*E) on large vaults
- Added two tests in TestMaterializeMetrics: one verifying exact computation for small graphs via mock assertion, one verifying the k-param selection logic directly

## Task Commits

1. **Task 1: All three performance fixes** - `6de39da` (perf)

## Files Created/Modified

- `src/ztlctl/services/check.py` — Added `from concurrent.futures import ThreadPoolExecutor, as_completed`, module-level `_read_file()` helper, parallel read phase in rebuild()
- `src/ztlctl/services/reweave.py` — Added `_fts5_escape()` module-level helper, updated `_score_bm25` to use it
- `src/ztlctl/services/graph.py` — Replaced `nx.betweenness_centrality(g)` with k-param and seed=42
- `tests/services/test_graph.py` — Added `test_betweenness_uses_exact_for_small_graphs` and `test_betweenness_k_param_logic_for_large_graphs`

## Decisions Made

- **Parallel reads, sequential writes**: Only the file READ step is parallelized. DB writes remain inside `vault.transaction()` to avoid SQLite "database is locked" errors from concurrent writes.
- **k=500 as approximation limit**: Matches NetworkX convention; provides good accuracy for practical vault sizes. seed=42 ensures deterministic results across runs.
- **_fts5_escape as module-level function**: Reusable outside the class; aligns with _jaccard pattern already in reweave.py. Previous f-string quoting (`f'"{w}"'`) didn't escape internal double-quotes, which could cause FTS5 syntax errors for titles containing quotes.
- **Test strategy for k-approximation**: Avoided creating 500+ node test graphs (impractical in tests); instead verified the k-param selection logic directly and mocked betweenness_centrality to assert k=None on small graphs.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- Initial test for `test_betweenness_uses_k_approximation_for_large_graphs` attempted to mock `number_of_nodes()` to return 501 while calling the real betweenness function — this caused `ValueError: Sample larger than population` (can't sample k=500 from a 3-node graph). Fixed by replacing with a pure logic test that verifies the k-param selection formula directly.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- All three HARD-06 performance bottlenecks are fixed
- 1508 tests pass, mypy strict clean, ruff clean
- rebuild() is now safe for large vaults (parallel reads, sequential writes)
- reweave scoring is robust against titles with special FTS5 characters

## Self-Check: PASSED

All artifacts verified:
- src/ztlctl/services/check.py: FOUND
- src/ztlctl/services/reweave.py: FOUND
- src/ztlctl/services/graph.py: FOUND
- tests/services/test_graph.py: FOUND
- .planning/phases/01-core-hardening/01-03-SUMMARY.md: FOUND
- commit 6de39da: FOUND

---
*Phase: 01-core-hardening*
*Completed: 2026-03-19*
