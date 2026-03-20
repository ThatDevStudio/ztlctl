---
phase: 06-agentic-integration-security
plan: 03
subsystem: plugins
tags: [security, plugins, copier, capabilities, audit-logging]
dependency_graph:
  requires:
    - 05-plugin-formalization
  provides:
    - SECU-01: force_trust Copier plugin template trust enforcement
    - SECU-02: declare_capabilities hookspec and audit logging
  affects:
    - src/ztlctl/services/workflow.py
    - src/ztlctl/controllers/workflow.py
    - src/ztlctl/actions/_register_core.py
    - src/ztlctl/plugins/hookspecs.py
    - src/ztlctl/plugins/manager.py
    - src/ztlctl/plugins/builtins/*.py
tech_stack:
  added: []
  patterns:
    - force_trust flag gates plugin Copier hook execution (unsafe=force_trust)
    - declare_capabilities hookspec for plugin capability audit
    - VALID_CAPABILITIES frozenset for capability allowlist validation
key_files:
  created:
    - .planning/phases/06-agentic-integration-security/06-03-SUMMARY.md
  modified:
    - src/ztlctl/services/workflow.py
    - src/ztlctl/controllers/workflow.py
    - src/ztlctl/actions/_register_core.py
    - src/ztlctl/plugins/hookspecs.py
    - src/ztlctl/plugins/manager.py
    - src/ztlctl/plugins/builtins/git.py
    - src/ztlctl/plugins/builtins/obsidian.py
    - src/ztlctl/plugins/builtins/reweave_plugin.py
    - tests/services/test_workflow.py
    - tests/plugins/test_manager.py
decisions:
  - "force_trust applies only to _run_plugin_copy; built-in _run_copy and _run_update always use unsafe=False regardless"
  - "Missing capability declarations logged at DEBUG (not WARNING) in plugin API v2 — advisory only; invalid declarations logged at WARNING"
  - "Built-in plugins (git, obsidian, reweave) now implement declare_capabilities to avoid noisy test output and document their access surface"
metrics:
  duration_minutes: 17
  completed_date: "2026-03-20"
  tasks_completed: 2
  files_modified: 10
requirements_satisfied:
  - SECU-01
  - SECU-02
---

# Phase 6 Plan 3: Plugin Security Hardening Summary

Plugin security hardening adding Copier trust enforcement for plugin-contributed workflow templates and plugin capability declarations with audit logging.

## Tasks Completed

### Task 1: Add Copier --force-trust flag and plugin template trust enforcement (SECU-01)

Added `force_trust: bool = False` parameter to `WorkflowService.init_workflow()` and `update_workflow()`. Added `_run_plugin_copy()` static method that passes `unsafe=force_trust` to Copier — plugin templates default to `unsafe=False` (no hook execution) unless `--force-trust` is explicitly set.

Built-in `_run_copy()` and `_run_update()` are unchanged and always use `unsafe=False`. The `force_trust` parameter is threaded through `WorkflowController` and exposed as a `cli_flag=True` `ActionParam` in both `init_workflow` and `update_workflow` ActionDefinitions.

**Commits:** `bd3b7b5` (RED tests), `7d3b8d3` (GREEN impl)

### Task 2: Add plugin capability declarations hookspec + validation + audit logging (SECU-02)

Added `declare_capabilities` hookspec to `ZtlctlHookSpec` (not firstresult — all plugins called). Added `VALID_CAPABILITIES: frozenset[str] = frozenset({"filesystem", "network", "database", "git"})` constant to `manager.py`. Added `_validate_capabilities()` method called at end of `discover_and_load()`.

Missing declarations are logged at DEBUG (advisory in plugin API v2). Invalid capability names are logged at WARNING. Valid declarations are logged at INFO as audit entries. All three built-in plugins (`GitPlugin`, `ObsidianProfilePlugin`, `ReweavePlugin`) now implement `declare_capabilities` with appropriate capability sets.

**Commits:** `07cf5ab` (RED tests), `53ebb3d` (GREEN impl)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Built-in plugins caused capability warning log bleed into test output**

- **Found during:** Task 2 full suite run
- **Issue:** `_validate_capabilities()` emitted `logger.warning()` for every registered plugin that didn't implement `declare_capabilities`. The built-in plugins (GitPlugin, ObsidianProfilePlugin, ReweavePlugin) didn't implement it. Click's CliRunner captures both stdout and stderr into `result.output`, causing warning log text to appear before JSON output in `--json` mode tests (specifically `test_regenerate_json` and `test_create_note_with_plugin_subtype`).
- **Fix 1:** Added `declare_capabilities` hookimpl to all three built-in plugins with correct capability sets.
- **Fix 2:** Lowered `no_capabilities_declared` from `logger.warning` to `logger.debug` — plugin API v2 treats missing declarations as advisory (consistent with plan's "warning, not hard error" language), while `invalid_capabilities` (unknown capability names) remains at `logger.warning` since it indicates a plugin authoring error.
- **Files modified:** `git.py`, `obsidian.py`, `reweave_plugin.py`, `manager.py`
- **Commits:** included in `53ebb3d`

## Self-Check: PASSED

All modified files verified to exist on disk. All 4 task commits verified in git history.
