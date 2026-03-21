---
phase: 15-event-model-hardening
plan: "02"
subsystem: event-bus
tags: [event-model, refactoring, correctness, post-action, shutdown-drain]
dependency_graph:
  requires: [15-01]
  provides: [ARCH-01, ARCH-02, ARCH-03]
  affects: [services/base.py, plugins/event_bus.py, commands/_context.py, infrastructure/vault.py, controllers/*]
tech_stack:
  added: []
  patterns:
    - Service-side canonical post_action emission via WAL
    - Bounded shutdown drain with configurable timeout
    - Startup recovery drain for pending WAL events
    - Structural regression test using ast.parse
key_files:
  created:
    - tests/controllers/test_post_action_removal.py
  modified:
    - src/ztlctl/services/base.py
    - src/ztlctl/plugins/event_bus.py
    - src/ztlctl/commands/_context.py
    - src/ztlctl/infrastructure/vault.py
    - src/ztlctl/controllers/base.py
    - src/ztlctl/controllers/create.py
    - src/ztlctl/controllers/update.py
    - src/ztlctl/controllers/session.py
    - src/ztlctl/controllers/check.py
    - src/ztlctl/controllers/reweave.py
    - src/ztlctl/controllers/graph.py
    - src/ztlctl/controllers/query.py
    - src/ztlctl/controllers/export.py
    - src/ztlctl/controllers/discovery.py
    - src/ztlctl/controllers/workflow.py
    - src/ztlctl/controllers/upgrade.py
    - src/ztlctl/controllers/vector.py
    - src/ztlctl/controllers/ingest.py
    - src/ztlctl/controllers/init_ctrl.py
    - tests/plugins/test_event_bus.py
    - tests/controllers/test_hook_wiring.py
    - tests/plugins/test_plugin_config.py
decisions:
  - "Single-step cutover: all 64 controller _dispatch_post_action calls removed atomically with no deprecation window"
  - "Bounded shutdown drain uses EventBusConfig.shutdown_timeout_seconds (default 5s), not zero"
  - "Startup drain is best-effort: failure logs warning and continues (never blocks startup)"
  - "post_action special path in _execute_hook handles ActionEvent dict payload differently from per-event hooks"
  - "Bridge code (per-event hook → post_action) kept for backward compat until Phase 16"
metrics:
  duration_minutes: 60
  completed_date: "2026-03-21"
  tasks_completed: 2
  files_changed: 22
requirements_satisfied: [ARCH-01, ARCH-02, ARCH-03]
---

# Phase 15 Plan 02: Remove Controller post_action and Add Drain Infrastructure

Single-step removal of 64 controller-side `_dispatch_post_action` call sites plus canonical service-side `post_action` emission through the WAL, bounded shutdown drain, and startup recovery drain.

## Summary

Service-side post_action emission via `BaseService._dispatch_post_action_event()` replacing 64 controller-side sync calls with WAL-backed async dispatch; bounded shutdown drain with configurable timeout; startup drain retrying pending WAL rows from interrupted prior runs.

## Tasks Completed

| Task | Description | Commit |
|------|-------------|--------|
| 1 | Service-side emission + shutdown/startup drain | 1d449a7 |
| 2 | Remove 64 controller _dispatch_post_action calls | f659920 |

## What Was Built

### Task 1: Service-Side Emission and Drain Infrastructure

**`BaseService._dispatch_post_action_event()`** — new method that:
- Creates an `ActionEvent` (from `domain/events.py`) with action_name, side_effect="write", payload, warnings, result
- Dispatches to `"post_action"` hook via EventBus WAL
- Catches exceptions and appends to warnings (never raises)

**`EventBus._execute_hook()` post_action path** — new special case:
- When `hook_name == "post_action"`: payload IS an ActionEvent dict
- Calls `pm.hook.post_action(action_name=payload["action_name"], kwargs=payload["payload"], result=payload.get("result"))`
- Returns early without running the bridge
- All other hooks: use the existing per-event path + bridge (backward compat)

**`AppContext.close()` shutdown drain**:
- Changed from `wait_for_events=False` to `wait_for_events=True`
- Uses `self.settings.eventbus.shutdown_timeout_seconds` as the per-future timeout
- On timeout: pending WAL rows stay as `pending` (not cancelled or deleted)

**`Vault.init_event_bus()` startup drain**:
- Calls `self._event_bus.drain()` after EventBus construction
- Any failure logs a warning and continues — never blocks startup

### Task 2: Remove Controller-Side _dispatch_post_action

**64 call sites removed** across 14 controllers:
- create.py: 4, update.py: 3, session.py: 9, check.py: 4, reweave.py: 3
- graph.py: 8, query.py: 10, export.py: 4, discovery.py: 3, workflow.py: 4
- upgrade.py: 3, vector.py: 2, ingest.py: 4, init_ctrl.py: 3

**`BaseController._dispatch_post_action` method deleted** — method no longer exists. `_dispatch_pre_action` and `_dispatch_event` remain intact.

**Structural regression test** — `tests/controllers/test_post_action_removal.py`:
- Uses `ast.parse` to scan all controller `.py` files
- Asserts no `self._dispatch_post_action(...)` call nodes exist
- Asserts `_dispatch_post_action` not defined in `base.py`
- Asserts `_dispatch_pre_action` and `_dispatch_event` still present

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] pre-existing test_verbose_telemetry.py failure**
- **Found during:** Task 2 full suite run
- **Issue:** `test_verbose_json_includes_telemetry_in_meta` was already failing before any Plan 02 changes (confirmed by stash test)
- **Fix:** Out of scope — not caused by Plan 02 changes, not fixed
- **Status:** Pre-existing, documented in deferred items

**2. [Rule 2 - Test Update] test_hook_wiring.py used patch.object on removed method**
- **Found during:** Task 2 full suite run
- **Issue:** Tests patched `_dispatch_post_action` which no longer exists
- **Fix:** Updated 8 test cases to remove post_action patches; assertions now verify pre_action only
- **Files modified:** `tests/controllers/test_hook_wiring.py`
- **Commit:** f659920

**3. [Rule 2 - Test Update] test_plugin_config.py tested BaseController._dispatch_post_action**
- **Found during:** Task 2 full suite run
- **Issue:** Two tests directly called `controller._dispatch_post_action()` on the deleted method
- **Fix:** Replaced with equivalent tests for `BaseService._dispatch_post_action_event()` (the new service-side equivalent)
- **Files modified:** `tests/plugins/test_plugin_config.py`
- **Commit:** f659920

## Verification

```
grep -r "_dispatch_post_action" src/ztlctl/controllers/  # 0 matches (ARCH-03)
uv run pytest tests/plugins/test_event_bus.py -k "drain or startup or post_action"  # 7 passed
uv run pytest tests/ -q  # 1842 passed, 2 skipped (1 pre-existing failure excluded)
uv run ruff check src/ztlctl/controllers/ src/ztlctl/services/base.py  # clean
uv run mypy src/ztlctl/controllers/ src/ztlctl/services/base.py  # clean
```

## Known Stubs

None — all implementations are complete and wired.

## Self-Check: PASSED
