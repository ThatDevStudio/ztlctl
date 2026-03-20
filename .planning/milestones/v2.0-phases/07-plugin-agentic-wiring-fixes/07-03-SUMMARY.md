---
phase: 07-plugin-agentic-wiring-fixes
plan: 03
subsystem: plugins
tags: [pluggy, hooks, controllers, pre_action, post_action, ActionRejection]

# Dependency graph
requires:
  - phase: 07-plugin-agentic-wiring-fixes
    provides: BaseController with _dispatch_pre_action and _dispatch_post_action methods (Plan 01); batch-1 controllers wired (Plan 02)
provides:
  - Hook-wired QueryController (10 methods)
  - Hook-wired ReweaveController (3 methods)
  - Hook-wired SessionController (9 methods)
  - Hook-wired UpdateController (3 methods)
  - Hook-wired UpgradeController (3 methods)
  - Hook-wired VectorController (2 methods, vector_status action name)
  - Hook-wired WorkflowController (4 ServiceResult methods; 3 non-ServiceResult helpers left unwired)
  - 9 spot-check tests for batch-2 controller hook wiring
affects:
  - Plugin system integration tests
  - MCP tool invocations that go through controllers
  - CLI command execution that goes through controllers

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "4-step hook wiring: kwargs dict -> _dispatch_pre_action -> rejection check -> service call -> _dispatch_post_action"
    - "Action name disambiguation: vector_status (not status) to avoid collision with SessionController.status"
    - "Non-ServiceResult controller helpers left unwired (WorkflowController: read_answers, profile_choices, default_choices)"

key-files:
  created:
    - tests/controllers/test_hook_wiring_batch2.py
  modified:
    - src/ztlctl/controllers/query.py
    - src/ztlctl/controllers/reweave.py
    - src/ztlctl/controllers/session.py
    - src/ztlctl/controllers/update.py
    - src/ztlctl/controllers/upgrade.py
    - src/ztlctl/controllers/vector.py
    - src/ztlctl/controllers/workflow.py

key-decisions:
  - "VectorController.status() uses action name 'vector_status' (not 'status') to avoid action name collision with SessionController.status"
  - "WorkflowController read_answers/profile_choices/default_choices are NOT wired — they return non-ServiceResult types and are helper methods, not actions"

patterns-established:
  - "All ServiceResult-returning controller methods follow the 4-step hook wiring pattern established in Plan 02"
  - "Batch-2 hook wiring spot-checks use spy_pre pattern (captures args while delegating to original) instead of full mocks"

requirements-completed: [PLUG-02]

# Metrics
duration: 8min
completed: 2026-03-20
---

# Phase 7 Plan 03: Plugin Agentic Wiring Fixes (Batch 2) Summary

**Pre/post-action hook wiring completed for all 7 batch-2 controllers covering 33 ServiceResult methods, with vector_status action name disambiguation and WorkflowController non-ServiceResult helper methods correctly excluded**

## Performance

- **Duration:** ~8 min
- **Started:** 2026-03-20T05:41:00Z
- **Completed:** 2026-03-20T05:49:51Z
- **Tasks:** 2
- **Files modified:** 8 (7 controllers + 1 test file)

## Accomplishments
- Wired 33 ServiceResult methods across 7 controllers with _dispatch_pre_action / _dispatch_post_action hook pattern
- VectorController.status() correctly uses "vector_status" action name (not "status") to prevent collision with SessionController.status
- WorkflowController helpers (read_answers, profile_choices, default_choices) correctly left unwired since they return non-ServiceResult types
- 9 spot-check tests confirm hook wiring correctness including action names, kwargs completeness, and non-ServiceResult skip behavior
- Full test suite: 1781 passed, 0 failed, 2 skipped (no regressions)

## Task Commits

Each task was committed atomically:

1. **Task 1: Wire hooks into 7 controllers (query, reweave, session, update, upgrade, vector, workflow)** - `4bd50a3` (feat)
2. **Task 2: Spot-check tests + full regression for batch 2 controllers** - `3f089d4` (test)

## Files Created/Modified
- `src/ztlctl/controllers/query.py` - 10 methods wired: count_items, search, get, list_items, work_queue, list_tags, decision_support, topic_packet, draft_from_topic, vault_review
- `src/ztlctl/controllers/reweave.py` - 3 methods wired: reweave, prune, undo
- `src/ztlctl/controllers/session.py` - 9 methods wired: start, close, reopen, status, log_entry, cost, context, brief, extract_decision
- `src/ztlctl/controllers/update.py` - 3 methods wired: update, archive, supersede
- `src/ztlctl/controllers/upgrade.py` - 3 methods wired: check_pending, apply, stamp_current
- `src/ztlctl/controllers/vector.py` - 2 methods wired: status (as vector_status), reindex_all
- `src/ztlctl/controllers/workflow.py` - 4 ServiceResult methods wired: init_workflow, update_workflow, export_assets, validate_assets; 3 non-ServiceResult helpers left unwired
- `tests/controllers/test_hook_wiring_batch2.py` - 9 spot-check tests for batch-2 hook wiring

## Decisions Made
- VectorController.status() must use "vector_status" as the action name — the ActionDefinition registered in _register_core.py uses "vector_status" to avoid collision with SessionController's "status" action
- WorkflowController read_answers, profile_choices, default_choices are helper methods returning WorkflowChoices/list[str]/Any, not ServiceResult — they correctly remain unwired per plan specification

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- Ruff pre-commit hook reformatted 2 files on first commit attempt and failed on long docstrings in test file; both resolved by re-staging after auto-format and shortening docstrings.

## Next Phase Readiness
- PLUG-02 requirement fully satisfied: all 59+ controller ServiceResult methods wired with pre/post-action hooks across both batches (Plans 02 + 03)
- Plugin system can now intercept, modify, or reject any action dispatched through any controller
- Phase 07 plan execution complete

---
*Phase: 07-plugin-agentic-wiring-fixes*
*Completed: 2026-03-20*
