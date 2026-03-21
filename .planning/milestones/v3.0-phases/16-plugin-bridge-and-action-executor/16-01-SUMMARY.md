---
phase: 16-plugin-bridge-and-action-executor
plan: "01"
subsystem: plugins, controllers
tags: [arch, event-bus, controller, bridge-removal, action-executor]
dependency_graph:
  requires: [Phase 15 — services emit post_action directly via _dispatch_post_action_event]
  provides: [No-bridge EventBus (ARCH-05), _run_action executor on BaseController (ARCH-06)]
  affects: [EventBus._execute_hook, BaseController, all controllers migrating in Plan 03]
tech_stack:
  added: []
  patterns: [collections.abc.Callable for invoke type hint, local import pattern for ServiceError/ServiceResult inside _run_action]
key_files:
  created:
    - tests/plugins/test_event_bus_post_action_bridge.py (rewritten — TestEventBusBridgeRemoved)
  modified:
    - src/ztlctl/plugins/event_bus.py
    - src/ztlctl/controllers/base.py
    - tests/controllers/test_base.py
decisions:
  - "_HOOK_TO_ACTION dict removed entirely — dead code once services own post_action via _dispatch_post_action_event (Phase 15)"
  - "ActionRejection.detail is dict[str, Any] (not str | None) — plan interface section was stale; used isinstance guard in _run_action"
  - "_run_action uses local imports for ServiceError/ServiceResult to match existing controller pattern and avoid circular imports"
metrics:
  duration_seconds: 249
  completed: "2026-03-21T17:41:42Z"
  tasks_completed: 2
  files_modified: 4
---

# Phase 16 Plan 01: Remove Bridge and Add Action Executor Summary

Bridge code removed from EventBus (ARCH-05) and generic `_run_action` executor added to BaseController (ARCH-06) as the foundation for controller migration in Plan 03.

## What Was Built

**Task 1 — Remove post_action bridge from EventBus (ARCH-05)**

Removed `_HOOK_TO_ACTION` dict and the bridge block in `_execute_hook` that fired a second `post_action` when a per-event hook ran. After Phase 15, services emit `post_action` directly via `_dispatch_post_action_event`, so the bridge caused duplicate delivery. Per-event hooks (post_create, post_update, etc.) now dispatch ONLY their own hookspec — no secondary `post_action` call follows.

**Task 2 — Add _run_action to BaseController (ARCH-06)**

Added `_run_action(action_name, kwargs, invoke)` to `BaseController`. This method encapsulates the complete pre-action pipeline:
1. Dispatches `pre_action` hook via `_dispatch_pre_action`
2. On rejection: returns `ServiceResult(ok=False, error=ServiceError(code="ACTION_REJECTED", ...))`
3. On success (possibly with plugin-modified kwargs): calls `invoke(kwargs)` and returns its result

All controller methods will migrate to use `_run_action` in Plan 03.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] ActionRejection.detail is dict[str, Any], not str | None**
- **Found during:** Task 2 (test failure during initial run)
- **Issue:** Plan's interface section showed `detail: str | None` for ActionRejection, but the actual dataclass definition uses `detail: dict[str, Any] = field(default_factory=dict)`
- **Fix:** Used `rejection.detail if isinstance(rejection.detail, dict) else {}` in `_run_action` to match ServiceError.detail type
- **Files modified:** src/ztlctl/controllers/base.py
- **Commit:** fa3e258

**2. [Rule 3 - Blocking] ruff import sort fix**
- **Found during:** Task 2 post-commit lint check
- **Issue:** `from ztlctl.services.result import ServiceError, ServiceResult as SR` was flagged as unsorted by ruff (I001)
- **Fix:** `uv run ruff check --fix` split into two separate import lines
- **Files modified:** src/ztlctl/controllers/base.py
- **Commit:** fa3e258 (included in same task commit)

## Known Stubs

None.

## Verification Results

```
uv run pytest tests/plugins/ tests/controllers/ -q (excl. pre-existing failure)
263 passed, 53 warnings

uv run ruff check src/ztlctl/plugins/event_bus.py src/ztlctl/controllers/base.py
All checks passed!

uv run mypy src/ztlctl/plugins/event_bus.py src/ztlctl/controllers/base.py
Success: no issues found in 2 source files

grep -r "_HOOK_TO_ACTION" src/
(no output — completely removed)
```

**Pre-existing failure (out of scope):**
- `tests/plugins/test_reweave_plugin.py::TestReweavePluginIntegration::test_reweave_creates_edges_for_related_content` — fails before and after this plan's changes; documented in deferred-items.

## Commits

| Task | Commit | Files |
|------|--------|-------|
| 1: Remove bridge (ARCH-05) | dc6e5af | event_bus.py, test_event_bus_post_action_bridge.py |
| 2: Add _run_action (ARCH-06) | fa3e258 | base.py (controller), test_base.py |

## Self-Check: PASSED
