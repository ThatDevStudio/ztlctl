---
phase: 15-event-model-hardening
plan: 04
subsystem: services
tags: [event-model, post-action, services, gap-closure]
dependency_graph:
  requires: [15-02]
  provides: [post-action-service-dispatch]
  affects: [create, update, session, reweave, check, graph]
tech_stack:
  added: []
  patterns: [post-action-dispatch-pattern, service-side-emission]
key_files:
  created:
    - tests/services/test_post_action_dispatch.py
  modified:
    - src/ztlctl/services/create.py
    - src/ztlctl/services/update.py
    - src/ztlctl/services/session.py
    - src/ztlctl/services/reweave.py
    - src/ztlctl/services/check.py
    - src/ztlctl/services/graph.py
    - .planning/REQUIREMENTS.md
decisions:
  - "_dispatch_post_action_event placed after _dispatch_event and before return in all write methods"
  - "reopen() warnings list added (was previously empty result) to pass to _dispatch_post_action_event"
  - "graph.py unlink uses unlink_result variable name to avoid collision with CursorResult<Any> named result"
  - "prune() and undo() use empty warnings list since they have no warning accumulator"
metrics:
  duration_seconds: 371
  completed_date: "2026-03-21"
  tasks_completed: 2
  files_modified: 7
---

# Phase 15 Plan 04: Wire Post-Action Dispatch into All Write Services — Summary

Wire `_dispatch_post_action_event` into all 14 write-side service methods across 6 files, and update REQUIREMENTS.md to reflect ARCH-04 and DEBT-02 as Complete — closing three verification blockers from the Phase 15 gap analysis.

## What Was Built

### Task 1: Add _dispatch_post_action_event to all write services

Added `self._dispatch_post_action_event(...)` calls at each successful write commit path across all 6 write service files, covering 14 method call sites:

**create.py (2 sites):**
- `_create_content`: dispatches after `_vector_index_created`, using `action_name=final.op` (which is `create_note`, `create_reference`, or `create_task`)
- `create_batch`: dispatches after the per-item `post_create` event loop, using `action_name="create_batch"`

**update.py (2 sites):**
- `update`: dispatches after vector re-index, before RESPOND return, using `action_name=op` (`update_note`/`update_reference`/`update_task`)
- `archive`: dispatches after `_dispatch_event("post_close", ...)`, using `action_name="archive"`

**session.py (4 sites):**
- `start`: dispatches after `_dispatch_event("post_session_start", ...)`, using `action_name=op` with `session_id` kwarg
- `close`: dispatches after bus drain barrier (end of REPORT step), using `action_name=op` with `session_id` kwarg
- `reopen`: dispatches after transaction, using `action_name=op` with `session_id` kwarg (added empty `warnings` list)
- `extract_decision`: dispatches after `_dispatch_event("post_extract_decision", ...)`, using `action_name=op` with `session_id` kwarg

**reweave.py (3 sites):**
- `reweave`: dispatches after `_dispatch_event("post_reweave", ...)`, using `action_name=op`
- `prune` (non-dry-run path only): dispatches after `_prune_links`, using empty warnings list
- `undo`: dispatches after `_apply_undo`, using empty warnings list

**check.py (2 sites):**
- `fix`: dispatches after the transaction block, using empty warnings list
- `rebuild`: dispatches at end of method after graph metric materialization, passing the accumulated warnings

**graph.py (1 site):**
- `unlink`: dispatches after the transaction, using `unlink_result` variable name to avoid type collision with the CursorResult named `result` inside the transaction block

**Structural regression test (`tests/services/test_post_action_dispatch.py`):**
- AST-based scan of all 6 service files
- Identifies methods with `self._vault.transaction()` calls (write indicator)
- Verifies each has a `_dispatch_post_action_event` call
- 18 methods in EXEMPT_METHODS set: private helpers, read-only ops, and known exceptions

### Task 2: Update REQUIREMENTS.md

- `ARCH-04`: Changed from `[ ]` to `[x]` in requirements list
- `DEBT-02`: Changed from `[ ]` to `[x]` in requirements list
- Traceability table row for ARCH-04: `Pending` → `Complete`
- Traceability table row for DEBT-02: `Pending` → `Complete`

## Verification Results

- `uv run pytest tests/services/test_post_action_dispatch.py`: 1 passed
- `uv run pytest tests/ --ignore=tests/integration/test_verbose_telemetry.py`: 1853 passed, 2 skipped
- `uv run ruff check src/ztlctl/services/`: All checks passed
- `uv run mypy src/ztlctl/services/`: Success: no issues found in 22 source files
- Pre-existing failure in `test_verbose_json_includes_telemetry_in_meta` confirmed pre-existing (reproducible without this plan's changes)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Variable name collision in graph.py**
- **Found during:** Task 1, mypy check
- **Issue:** `result = txn.conn.execute(edges.delete()...)` inside the `with self._vault.transaction()` block set `result` to `CursorResult[Any]`. Adding `result = ServiceResult(...)` after the block failed mypy with `Incompatible types in assignment`
- **Fix:** Used `unlink_result` as the variable name for the ServiceResult in `unlink()` method
- **Files modified:** src/ztlctl/services/graph.py
- **Commit:** d21fa08

**2. [Rule 2 - Missing] reopen() had no warnings list**
- **Found during:** Task 1, implementing session.py reopen dispatch
- **Issue:** The `reopen()` method returned an empty `ServiceResult` with no warnings list — the plan noted `_dispatch_post_action_event` should receive `warnings`
- **Fix:** Added `warnings: list[str] = []` before building the result, passed to dispatch call
- **Files modified:** src/ztlctl/services/session.py
- **Commit:** d21fa08

## Known Stubs

None.

## Commits

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Wire _dispatch_post_action_event into all write services | d21fa08 | create.py, update.py, session.py, reweave.py, check.py, graph.py, test_post_action_dispatch.py |
| 2 | Mark ARCH-04 and DEBT-02 as Complete in REQUIREMENTS.md | 25cf223 | .planning/REQUIREMENTS.md |

## Self-Check: PASSED

- tests/services/test_post_action_dispatch.py: FOUND
- src/ztlctl/services/create.py: FOUND
- src/ztlctl/services/update.py: FOUND
- src/ztlctl/services/session.py: FOUND
- src/ztlctl/services/reweave.py: FOUND
- src/ztlctl/services/check.py: FOUND
- src/ztlctl/services/graph.py: FOUND
- Commit d21fa08: FOUND (feat(15-04): wire _dispatch_post_action_event into all write services)
- Commit 25cf223: FOUND (docs(15-04): mark ARCH-04 and DEBT-02 as Complete in REQUIREMENTS.md)
