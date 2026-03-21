---
phase: 16-plugin-bridge-and-action-executor
plan: 03
subsystem: controllers, actions, commands
tags: [arch-remediation, controller-migration, action-registry, garden-seed, ARCH-06, ARCH-09]
dependency_graph:
  requires: [16-01]
  provides: [all-controllers-use-_run_action, garden_seed-ActionDefinition]
  affects: [all-14-controllers, ActionRegistry, CLI-generator, commands/__init__.py]
tech_stack:
  added: []
  patterns: [_run_action delegation, ActionDefinition handler convention, inline _invoke closure]
key_files:
  created:
    - tests/actions/test_garden_seed_registration.py
  modified:
    - src/ztlctl/controllers/check.py
    - src/ztlctl/controllers/create.py
    - src/ztlctl/controllers/discovery.py
    - src/ztlctl/controllers/export.py
    - src/ztlctl/controllers/graph.py
    - src/ztlctl/controllers/ingest.py
    - src/ztlctl/controllers/init_ctrl.py
    - src/ztlctl/controllers/query.py
    - src/ztlctl/controllers/reweave.py
    - src/ztlctl/controllers/session.py
    - src/ztlctl/controllers/update.py
    - src/ztlctl/controllers/upgrade.py
    - src/ztlctl/controllers/vector.py
    - src/ztlctl/controllers/workflow.py
    - src/ztlctl/actions/_register_core.py
    - src/ztlctl/commands/__init__.py
    - src/ztlctl/commands/generator.py
    - tests/actions/test_core_registrations.py
  deleted:
    - src/ztlctl/commands/garden.py
decisions:
  - All 14 controllers migrated to _run_action; _dispatch_pre_action no longer called directly in any controller method outside base.py
  - garden_seed handler uses single-call lambda convention (vault, **kw) matching all other ActionDefinitions — the plan's two-level lambda pattern was incompatible with CLI/MCP generator calling convention
  - garden_seed registered in creation category, not a separate category
  - cli_examples added to garden_seed ActionDefinition for --examples flag compatibility
metrics:
  duration_minutes: 45
  completed_date: "2026-03-21T17:54:05Z"
  tasks_completed: 2
  files_modified: 19
---

# Phase 16 Plan 03: Controller Migration and garden_seed Registration Summary

Migrated all 14 controllers from inline _dispatch_pre_action boilerplate to _run_action delegation, and registered garden_seed as a first-class ActionDefinition routing through CreateController with maturity="seed" baked in.

## Tasks Completed

### Task 1: Migrate all 14 controllers to use _run_action (ARCH-06)

Replaced the repeated 8-line boilerplate pattern (dispatch + rejection check + ServiceResult/ServiceError construction) in every controller method with `_run_action("action_name", kwargs, _invoke)`. The `_invoke` inner function uses `kw` parameter to pick up plugin-modified kwargs.

**Controllers migrated (total ~63 methods):**
- check.py: 4 methods (check, fix, rebuild, rollback) — event_purge unchanged (no pre_action hook)
- create.py: 4 methods (create_note, create_reference, create_task, create_batch) — dispatch_post_create captured from outer scope
- discovery.py: 3 methods — inline logic moved into _invoke closures
- export.py: 4 methods — export_graph file-writing logic preserved inside _invoke
- graph.py: 8 methods
- ingest.py: 4 methods
- init_ctrl.py: 3 methods
- query.py: 10 methods
- reweave.py: 3 methods
- session.py: 9 methods
- update.py: 3 methods
- upgrade.py: 3 methods
- vector.py: 2 methods — ServiceResult construction for status() moved into _invoke
- workflow.py: 4 methods — read_answers, profile_choices, default_choices unchanged (no ServiceResult return)

Commit: 305836a

### Task 2: Register garden_seed as first-class ActionDefinition (ARCH-09)

- Added `garden_seed` ActionDefinition to `_register_core.py` in the creation category
- Handler: `lambda vault, **kw: CreateController(vault).create_note(kw["title"], tags=kw.get("tags"), topic=kw.get("topic"), maturity="seed")`
- Added "garden" to `_GROUP_HELP` in `generator.py` — generator now auto-creates the garden group with seed subcommand
- Removed manual garden import from `commands/__init__.py`
- Deleted hand-written `commands/garden.py`
- Added `tests/actions/test_garden_seed_registration.py`
- Updated `tests/actions/test_core_registrations.py` to include garden_seed in creation category set

Commit: adad52e

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] garden_seed handler calling convention**
- **Found during:** Task 2
- **Issue:** Plan specified a two-level lambda `lambda vault: (lambda title, ...: ...)` which is incompatible with the CLI/MCP generator that calls `action.handler(vault, **kwargs)` in a single call. All other core registrations use `lambda vault, **kw: ...`.
- **Fix:** Used single-call lambda matching all other ActionDefinitions: `lambda vault, **kw: CreateController(vault).create_note(kw["title"], ...)`
- **Files modified:** src/ztlctl/actions/_register_core.py, tests/actions/test_garden_seed_registration.py
- **Commit:** adad52e

**2. [Rule 2 - Missing] cli_examples missing from garden_seed**
- **Found during:** Task 2 test run
- **Issue:** test_examples.py asserts `ztlctl garden seed --examples` produces output containing "garden seed". Generated commands with empty cli_examples fail this test.
- **Fix:** Added cli_examples field to the garden_seed ActionDefinition with three example invocations.
- **Files modified:** src/ztlctl/actions/_register_core.py
- **Commit:** adad52e

**3. [Rule 1 - Bug] test_core_registrations.py creation category set**
- **Found during:** Task 2 test run
- **Issue:** TestCategoryIntegrity.test_category_exact_names had a hardcoded set `{"create_note", "create_reference", "create_task", "create_batch"}` that didn't include garden_seed.
- **Fix:** Updated expected set to include "garden_seed".
- **Files modified:** tests/actions/test_core_registrations.py
- **Commit:** adad52e

## Pre-existing Failures (Out of Scope)

4 tests were failing before this plan's changes (confirmed by checking on base commit 305836a):
- `tests/commands/test_serve.py::TestServeCommand::test_serve_invokes_create_server_with_transport_options`
- `tests/commands/test_git_missing_runtime.py::TestGitMissingRuntime::test_create_note_succeeds_when_git_missing`
- `tests/plugins/test_reweave_plugin.py::TestReweavePluginIntegration::test_reweave_creates_edges_for_related_content`
- `tests/services/test_create.py::TestPostCreateReweave::test_reweave_runs_via_post_create_plugin`

These are logged to `deferred-items.md` scope — out of scope for this plan.

## Known Stubs

None. All controller migrations are complete and functionally equivalent to before. garden_seed routes through CreateController which routes through CreateService.

## Self-Check: PASSED

All key files verified:
- src/ztlctl/controllers/create.py — FOUND
- src/ztlctl/actions/_register_core.py — FOUND
- src/ztlctl/commands/garden.py — DELETED (correct)
- tests/actions/test_garden_seed_registration.py — FOUND
- Commit 305836a (Task 1) — FOUND
- Commit adad52e (Task 2) — FOUND
