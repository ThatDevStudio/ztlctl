---
phase: 05-plugin-formalization
plan: "03"
subsystem: plugins
tags:
  - plugins
  - built-in-plugins
  - post-action
  - event-bus
  - tdd
dependency_graph:
  requires:
    - post_action hookspec (05-01)
    - PLUGIN_API_VERSION constant + check_plugin_api_version() (05-01)
    - EventBus WAL-backed dispatch (phase 6 baseline)
  provides:
    - GitPlugin.post_action — single method replacing 8 per-event hookimpls
    - GitPlugin.PLUGIN_API_VERSION = 1
    - ReweavePlugin.post_action — create_note/create_reference filter
    - ReweavePlugin.PLUGIN_API_VERSION = 1
    - EventBus._HOOK_TO_ACTION mapping (8 lifecycle hooks -> action names)
    - EventBus post_action bridge in _execute_hook
    - tests/plugins/test_event_bus_post_action_bridge.py (12 new tests)
  affects:
    - All callers of CreateService/UpdateService/SessionService/CheckService
      now reach migrated plugins via two paths: controller direct + EventBus bridge
tech_stack:
  added: []
  patterns:
    - TDD red-green for both tasks
    - Single post_action method with if/elif action_name routing
    - result=None passthrough (EventBus bridge); result.ok=False guard
    - _handle_* private methods for clean routing logic in GitPlugin
    - _HOOK_TO_ACTION module-level dict for bridge action name mapping
    - post_create content_type refinement: create_{content_type} from payload
    - Bridge exception isolation: post_action errors don't affect WAL status
key_files:
  created:
    - tests/plugins/test_event_bus_post_action_bridge.py
  modified:
    - src/ztlctl/plugins/builtins/git.py
    - src/ztlctl/plugins/builtins/reweave_plugin.py
    - src/ztlctl/plugins/event_bus.py
    - tests/plugins/test_git_plugin.py
    - tests/plugins/test_reweave_plugin.py
decisions:
  - "GitPlugin post_action uses _handle_* private methods for each action group instead of inlining — keeps the routing method short and each handler testable in isolation"
  - "result=None treated as pass-through (trust EventBus only dispatches on success) — result.ok=False guard only skips explicit failures from controller direct path"
  - "_handle_close handles both close and archive action names — they produce identical git side effects (stage + immediate commit if not batch)"
  - "EventBus bridge fires REGARDLESS of whether per-event hook had subscribers — ensures migrated plugins always receive lifecycle events"
  - "post_create content_type refinement in bridge: create_{content_type} from payload (create_note/create_reference/create_task) matching ActionRegistry action names"
  - "Bridge catches its own exceptions with separate try/except block — a post_action failure does not change the WAL event status (already marked completed/failed by per-event dispatch)"
metrics:
  duration_seconds: 900
  completed_date: "2026-03-20"
  tasks_completed: 2
  files_created: 1
  files_modified: 5
---

# Phase 05 Plan 03: Built-in Plugin Migration + EventBus Bridge Summary

**One-liner:** GitPlugin and ReweavePlugin ported to post_action with PLUGIN_API_VERSION=1; EventBus bridges all 8 legacy lifecycle hooks to post_action so migrated plugins receive service-layer events via both controller and event-bus dispatch paths.

## What Was Built

### Task 1: GitPlugin Migration

**`src/ztlctl/plugins/builtins/git.py`** — Complete lifecycle section rewrite:
- `PLUGIN_API_VERSION = 1` class attribute added
- 8 per-event hookimpl methods removed (post_create, post_update, post_close, post_reweave, post_session_start, post_session_close, post_check, post_init)
- Single `@hookimpl def post_action(self, action_name, kwargs, result)` added
- Action routing via if/elif to private handlers:
  - `_handle_create(action_name, kwargs)` — create_note, create_reference, create_task
  - `_handle_update(kwargs)` — update
  - `_handle_close(kwargs)` — close, archive
  - `_handle_session_close(kwargs)` — session_close
  - `_handle_init(kwargs)` — init
  - No-ops: reweave, session_start, check, check_rebuild
- Guard: `result is not None and (not hasattr(result, "ok") or not result.ok)` — skips on explicit failure, passes through on None (EventBus bridge path)
- All private git subprocess helpers unchanged

**`tests/plugins/test_git_plugin.py`** — Complete rewrite:
- All tests updated to call `plugin.post_action(action_name=..., kwargs={...}, result=...)` instead of per-event methods
- New tests: `test_plugin_api_version`, `test_post_action_skips_failed_result`, `test_post_action_none_result_proceeds`, `test_post_action_close_stages_file`, `test_post_action_archive_stages_file`, no-op action tests
- 28 tests total, all passing

### Task 2: ReweavePlugin Migration + EventBus Bridge

**`src/ztlctl/plugins/builtins/reweave_plugin.py`** — Rewritten:
- `PLUGIN_API_VERSION = 1` class attribute added
- `@hookimpl post_create` removed
- Single `@hookimpl def post_action(self, action_name, kwargs, result)` added:
  - Guards: action_name not in {"create_note", "create_reference"} → return
  - Guard: result.ok=False → return (None passes through)
  - Extracts content_id from kwargs.get("content_id")
  - Decision note exclusion preserved (DB subtype lookup)
  - no_reweave and reweave.enabled settings checks preserved
  - Calls ReweaveService(self._vault).reweave(content_id=content_id)

**`src/ztlctl/plugins/event_bus.py`** — Bridge added to `_execute_hook`:
- Module-level `_HOOK_TO_ACTION: dict[str, str]` mapping 8 lifecycle hooks to action names
- After per-event dispatch, bridge block fires `pm.hook.post_action(action_name=..., kwargs=payload, result=None)`
- post_create refined: `f"create_{payload.get('content_type', 'note')}"`
- Bridge runs regardless of per-event hook subscriber count
- Bridge exceptions caught independently (don't affect WAL status)
- `getattr(self._pm.hook, "post_action", None)` for graceful degradation

**`tests/plugins/test_reweave_plugin.py`** — Updated:
- All unit tests now call `plugin.post_action(action_name=..., kwargs={...}, result=...)`
- New: `test_plugin_api_version`, `test_post_action_create_reference_calls_reweave_service`, `test_post_action_create_task_skipped`, `test_post_action_update_skipped`, `test_post_action_skips_failed_result`, `test_post_action_none_result_proceeds`
- Integration tests preserved unchanged
- 15 tests total, all passing

**`tests/plugins/test_event_bus_post_action_bridge.py`** — New file (12 tests):
- `_RecordingPlugin` with `@_hookimpl post_action` records all calls
- Tests: post_create → create_note/reference/task, post_update → update, post_session_close → session_close, post_reweave → reweave, post_check → check, post_init → init
- Tests: non-lifecycle hook → no post_action, result=None always, bridge error doesn't break WAL, no post_action hookspec → no error

## Test Coverage

| File | Tests | Description |
|------|-------|-------------|
| `tests/plugins/test_git_plugin.py` | 28 | GitPlugin post_action routing, all action types, batch/immediate mode |
| `tests/plugins/test_reweave_plugin.py` | 15 | ReweavePlugin post_action, create filtering, settings guards |
| `tests/plugins/test_event_bus_post_action_bridge.py` | 12 | Bridge mapping, content_type refinement, error isolation |

Total new/updated tests: **55** — all passing.
Full suite: **1723 passed, 2 skipped** — no regressions.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] ruff RUF012: mutable class-level dict in test helper**
- **Found during:** Task 1, pre-commit hook
- **Issue:** `class _Result: data: dict = {}` triggers ruff RUF012 (mutable default class attribute)
- **Fix:** Added `__init__` to initialize `self.data = {}` per-instance
- **Files modified:** `tests/plugins/test_git_plugin.py`
- **Commit:** 4651be1

**2. [Rule 1 - Bug] pluggy hookimpl marker can't be applied to bound methods**
- **Found during:** Task 2, first test run of test_event_bus_post_action_bridge.py
- **Issue:** Dynamically applying `hookimpl(recording_plugin.post_action)` to a bound method raises `AttributeError: 'method' object has no attribute '__dict__'` — pluggy requires the marker at class-definition time on an unbound function
- **Fix:** Changed `_RecordingPlugin.post_action` to use `@_hookimpl` decorator at class definition; removed dynamic marker application in `_make_plugin_manager`
- **Files modified:** `tests/plugins/test_event_bus_post_action_bridge.py`
- **Commit:** 3849fd2

## Self-Check: PASSED
