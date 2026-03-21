---
phase: 20-session-recall
plan: 02
subsystem: services
tags: [recall, session, topology, mcp, action-registry, sqlalchemy]

requires:
  - phase: 20-01
    provides: RecallService with recall_temporal and recall_topic, RecallController with all 3 method stubs

provides:
  - recall_topology: session pairs sharing referenced notes or tags (via session_logs.references JSON + node_tags)
  - sessions_recent_impl: last 5 sessions as MCP resource ztlctl://sessions/recent
  - 3 recall ActionDefinitions registered (recall_temporal, recall_topic, recall_topology) in session category
  - RECL-03, RECL-04, RECL-05 all complete

affects:
  - Phase 21 (contradiction detection) — recall infrastructure provides topology awareness for semantic checks
  - MCP session workflow — agents can now query ztlctl://sessions/recent for orientation

tech-stack:
  added: [itertools.combinations (stdlib)]
  patterns:
    - session_logs.references JSON array parsed for cross-session note reference tracking
    - node_tags JOIN used to compute per-session tag sets for topology analysis

key-files:
  created: []
  modified:
    - src/ztlctl/services/recall.py
    - src/ztlctl/actions/_session.py
    - src/ztlctl/mcp/resources.py
    - tests/services/test_recall.py
    - tests/mcp/test_resources.py
    - tests/controllers/test_recall.py

key-decisions:
  - "recall_topology uses session_logs.references JSON array (not nodes.session column) for cross-session shared note detection — a note has one session column but can be referenced in multiple sessions' log entries"
  - "sessions_recent_impl delegates to recall_temporal() and takes first 5 (already ordered by created_at desc)"
  - "Pre-existing flaky test (test_verbose_json_includes_telemetry_in_meta) confirmed pre-existing on HEAD before this plan; logged to deferred-items, not fixed here"

patterns-established:
  - "sessions_recent_impl follows all existing resource impl conventions: lazy service import, graceful fallback on failure"
  - "RecallController.recall_topology already wired in Plan 01 stub — Plan 02 only replaces the service implementation"

requirements-completed: [RECL-03, RECL-04, RECL-05]

duration: 5min
completed: 2026-03-21
---

# Phase 20 Plan 02: Session Recall Completion Summary

**recall_topology discovers session pairs sharing log-referenced notes or tags; ztlctl://sessions/recent MCP resource; all 3 recall actions registered in ActionRegistry**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-21T19:27:21Z
- **Completed:** 2026-03-21T19:32:22Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments

- `recall_topology` queries session_logs.references JSON arrays and node_tags to find sessions sharing notes or tags, sorted by shared-item count, capped to limit
- `sessions_recent_impl` returns last 5 sessions by delegating to `recall_temporal()` and slicing the ordered result
- `ztlctl://sessions/recent` added to `_RESOURCE_CATALOG` and registered in `register_resources`
- 3 recall ActionDefinitions (`recall_temporal`, `recall_topic`, `recall_topology`) registered in `_session.py` under session category, each wired to `RecallController`
- 7 topology tests + 5 sessions/recent MCP tests added and passing
- Full suite: 1948 passed (excluding known pre-existing flaky telemetry test)
- ruff, mypy, format all clean

## Task Commits

1. **Task 1: recall_topology, sessions_recent MCP resource, 3 recall ActionDefinitions** - `e479f44` (feat)
2. **Task 2: Full validation and REQUIREMENTS.md update** - `84f6df0` (fix + docs)

**Plan metadata:** (docs commit follows)

## Files Created/Modified

- `src/ztlctl/services/recall.py` - recall_topology implementation replacing stub
- `src/ztlctl/actions/_session.py` - 3 recall ActionDefinitions added at end of _register_session_actions
- `src/ztlctl/mcp/resources.py` - sessions_recent_impl + ztlctl://sessions/recent catalog entry + registration
- `tests/services/test_recall.py` - 7 TestRecallTopology tests added
- `tests/mcp/test_resources.py` - 5 TestSessionsRecentResource tests added; catalog count updated 18→19
- `tests/controllers/test_recall.py` - stub test renamed/updated for real implementation (checks 'pairs' key)

## Decisions Made

- `recall_topology` uses `session_logs.references` JSON array for shared note detection — `nodes.session` only tracks the session where a note was *created*, but `session_logs.references` captures notes referenced across multiple sessions' log entries
- `sessions_recent_impl` delegates to `recall_temporal()` and takes `[:5]` since results are already ordered by `created_at` desc
- Catalog size assertion in `test_catalog_has_18_resources` updated to 19 — correct behavior since we added one resource

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Updated controller test for real recall_topology implementation**

- **Found during:** Task 2 (full test suite run)
- **Issue:** `test_recall_topology_stub_returns_ok` checked for `"nodes"` key in result.data — the old stub shape. Real implementation returns `"pairs"` key.
- **Fix:** Renamed test to `test_recall_topology_returns_ok`, updated assertion to `assert "pairs" in result.data`
- **Files modified:** `tests/controllers/test_recall.py`
- **Verification:** Full suite passes with the corrected assertion
- **Committed in:** `84f6df0` (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 - stale test from Plan 01 stub)
**Impact on plan:** Necessary correctness fix. No scope creep.

## Issues Encountered

- Pre-existing flaky test `test_verbose_json_includes_telemetry_in_meta` fails in isolation and was failing on HEAD before this plan began. Confirmed pre-existing, out of scope — logged to deferred-items.

## Known Stubs

None — all three recall methods are fully implemented.

## Next Phase Readiness

- All 5 RECL requirements complete
- Phase 20 (session-recall) fully complete
- Phase 21 (contradiction detection) can begin — recall infrastructure provides session topology awareness

## Self-Check: PASSED

- FOUND: src/ztlctl/services/recall.py
- FOUND: src/ztlctl/actions/_session.py
- FOUND: src/ztlctl/mcp/resources.py
- FOUND: .planning/phases/20-session-recall/20-02-SUMMARY.md
- FOUND: e479f44 (Task 1 commit)
- FOUND: 84f6df0 (Task 2 commit)
- PASS: recall_topology defined in RecallService
- PASS: sessions_recent_impl defined in resources.py
- PASS: ztlctl://sessions/recent URI present in catalog and registered
- PASS: recall_temporal, recall_topic, recall_topology registered in _session.py
- PASS: RecallController imported in _session.py
- PASS: RECL-03 and RECL-04 marked complete in REQUIREMENTS.md

---
*Phase: 20-session-recall*
*Completed: 2026-03-21*
