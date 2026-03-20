---
phase: 07-plugin-agentic-wiring-fixes
plan: 02
subsystem: controllers
tags: [plugins, hooks, pre-action, post-action, action-rejection, controllers]

requires:
  - phase: 07-plugin-agentic-wiring-fixes
    provides: BaseController._dispatch_pre_action and _dispatch_post_action methods, ActionRejection contract

provides:
  - Hook-wired CheckController (4 methods)
  - Hook-wired CreateController (4 methods, dispatch_post_create excluded from kwargs)
  - Hook-wired DiscoveryController (3 methods)
  - Hook-wired ExportController (4 methods)
  - Hook-wired GraphController (8 methods)
  - Hook-wired IngestController (4 methods)
  - Hook-wired InitController (3 methods)
  - Spot-check test suite for hook wiring (8 tests)
affects:
  - 07-plugin-agentic-wiring-fixes plan 03 (remaining controllers)
  - plugin integration tests
  - GitPlugin post_action coverage

tech-stack:
  added: []
  patterns:
    - "4-step hook wiring: build kwargs dict, dispatch pre_action, call service (or return rejection), dispatch post_action"
    - "dispatch_post_create flag excluded from kwargs passed to plugins (internal CreateService implementation detail)"
    - "Service calls use kwargs[param] after pre_action to allow plugin modification of parameters"

key-files:
  created:
    - tests/controllers/test_hook_wiring.py
  modified:
    - src/ztlctl/controllers/check.py
    - src/ztlctl/controllers/create.py
    - src/ztlctl/controllers/discovery.py
    - src/ztlctl/controllers/export.py
    - src/ztlctl/controllers/graph.py
    - src/ztlctl/controllers/ingest.py
    - src/ztlctl/controllers/init_ctrl.py

key-decisions:
  - "dispatch_post_create excluded from CreateController kwargs — it is an internal CreateService flag, not an ActionDefinition parameter; passed directly to service call"
  - "DiscoveryController methods wrap inline ServiceResult construction inside hook dispatch pattern — rejection short-circuits before any registry lookups"
  - "export_graph post-processing (writing output_file) stays after service call but before post_action dispatch so result contains the final ServiceResult"
  - "Service calls always use kwargs[key] not original local variables so plugin-modified kwargs take effect"

patterns-established:
  - "4-step hook wiring pattern: kwargs dict, pre_action, rejection check, service call, post_action"
  - "Rejection returns ServiceResult(ok=False, op=action_name, error=ServiceError(code='ACTION_REJECTED'))"
  - "Internal flags (dispatch_post_create) passed directly to service, never exposed in kwargs dict"

requirements-completed: [PLUG-02]

duration: 5min
completed: 2026-03-20
---

# Phase 07 Plan 02: Hook Wiring — Batch 1 Controllers Summary

**Pre/post-action plugin hooks wired into 30 methods across 7 controllers using 4-step pattern: kwargs dict, pre_action dispatch, rejection guard, service call, post_action dispatch**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-20T05:40:16Z
- **Completed:** 2026-03-20T05:45:00Z
- **Tasks:** 2
- **Files modified:** 8

## Accomplishments

- Wired `_dispatch_pre_action` and `_dispatch_post_action` into all 30 methods across 7 controllers
- `dispatch_post_create` correctly excluded from CreateController kwargs dict (internal flag stays out of plugin visibility)
- `ActionRejection` path returns `ACTION_REJECTED` ServiceResult error and skips both service call and `post_action`
- 8 spot-check tests covering every controller in this batch plus a rejection behavior regression test

## Task Commits

1. **Task 1: Wire hooks into 7 controllers** - `fb8a198` (feat)
2. **Task 2: Spot-check hook wiring tests** - `90d30f6` (test)

## Files Created/Modified

- `src/ztlctl/controllers/check.py` - 4 methods wired: check, fix, rebuild, rollback
- `src/ztlctl/controllers/create.py` - 4 methods wired: create_note, create_reference, create_task, create_batch
- `src/ztlctl/controllers/discovery.py` - 3 methods wired: discover_categories, activate_category, deactivate_category
- `src/ztlctl/controllers/export.py` - 4 methods wired: export_markdown, export_indexes, export_graph, export_dashboard
- `src/ztlctl/controllers/graph.py` - 8 methods wired: related, themes, rank, path, gaps, bridges, unlink, materialize_metrics
- `src/ztlctl/controllers/ingest.py` - 4 methods wired: list_providers, ingest_text, ingest_file, ingest_url
- `src/ztlctl/controllers/init_ctrl.py` - 3 methods wired: init_vault, regenerate_self, check_staleness
- `tests/controllers/test_hook_wiring.py` - 8 spot-check tests for hook wiring correctness

## Decisions Made

- `dispatch_post_create` excluded from CreateController kwargs — internal CreateService flag not exposed to plugins; passed directly to service call outside kwargs
- `DiscoveryController` methods wrap inline ServiceResult logic (no service delegation) inside hook dispatch — rejection short-circuits before registry lookups
- `export_graph` post-processing (writing output_file to disk) occurs after service call but before `_dispatch_post_action` so `post_action` sees the final result
- Service calls always reference `kwargs["param"]` not original local variables so plugin-modified kwargs take effect during execution

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

- Ruff E501 line-too-long in discovery.py (2 lines) — fixed immediately by wrapping f-strings in parentheses
- Pre-commit hook auto-fixed unused import in test file — re-staged and re-committed successfully

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- 7 controllers fully hook-wired; remaining controllers (query, session, reweave, update, workflow, upgrade, vector) targeted in plan 07-03
- All 59 controller tests pass, ruff and mypy clean
- Hook wiring pattern is established and verified — plan 07-03 can apply same pattern mechanically
