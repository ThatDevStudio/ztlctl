---
phase: 17-registry-decomposition-and-plugin-runtime
plan: "02"
subsystem: plugins
tags: [arch, plugin-runtime, refactor, debt]
dependency_graph:
  requires: []
  provides: [centralized-plugin-manager-factory]
  affects: [commands/__init__.py, services/init.py, services/workflow.py, workspace_profiles.py, infrastructure/vault.py]
tech_stack:
  added: []
  patterns: [scope-aware-cache, lazy-local-import, cache-opt-out]
key_files:
  created:
    - src/ztlctl/plugins/runtime.py
    - tests/plugins/test_plugin_runtime.py
  modified:
    - src/ztlctl/commands/__init__.py
    - src/ztlctl/services/init.py
    - src/ztlctl/services/workflow.py
    - src/ztlctl/workspace_profiles.py
    - src/ztlctl/infrastructure/vault.py
decisions:
  - "vault.py uses cache=False because it mutates the PM with instance-specific built-ins (git-builtin, reweave-builtin) — caching would cause 'Plugin name already registered' on second Vault construction"
  - "inject_configs runs on every call even for cached instances (settings may differ per invocation)"
  - "All 4 non-vault sites use default cache=True — safe because they don't mutate the PM after discovery"
metrics:
  duration_minutes: 6
  tasks_completed: 2
  files_changed: 7
  completed_date: "2026-03-21"
requirements: [ARCH-08, DEBT-07]
---

# Phase 17 Plan 02: Centralized PluginManager Factory Summary

**One-liner:** Centralized `get_plugin_manager()` factory with scope-aware caching in `runtime.py`, replacing 5 independent `PluginManager()` constructions and fixing `load_plugin_commands` to call `inject_configs` (DEBT-07).

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Create centralized PluginManager factory in runtime.py | f2a0136 | src/ztlctl/plugins/runtime.py, tests/plugins/test_plugin_runtime.py |
| 2 | Replace all 5 PluginManager() constructions with get_plugin_manager() | 34e80fc | commands/__init__.py, services/init.py, services/workflow.py, workspace_profiles.py, infrastructure/vault.py |

## What Was Built

A new `src/ztlctl/plugins/runtime.py` module providing:

- `get_plugin_manager(*, local_dir, include_entrypoints, settings, cache)` — creates a `PluginManager`, calls `discover_and_load()`, optionally calls `inject_configs()`, and caches by `(local_dir, include_entrypoints)` key
- `reset_plugin_manager_cache()` — clears module-level cache for test teardown
- `cache=False` parameter for mutation sites (vault.py) that register instance-specific plugins after discovery

All 5 previously-independent `PluginManager()` construction sites now delegate to the factory. `load_plugin_commands` now passes `settings=settings`, fixing DEBT-07 (config injection gap).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] vault.py uses cache=False to prevent re-registration of built-in plugins**

- **Found during:** Task 2 verification (full test suite run)
- **Issue:** `vault.init_event_bus()` registers vault-instance-specific `git-builtin` and `reweave-builtin` plugins into the PM after discovery. With caching, the second Vault construction (e.g., two `ztlctl init` calls in the same process) retrieves the cached PM and tries to re-register the built-in plugins, causing `ValueError: Plugin name already registered`.
- **Fix:** Added `cache: bool = True` parameter to `get_plugin_manager()`. vault.py calls with `cache=False`. The `runtime.py` plan spec was extended with `cache` parameter (additive, backward-compatible). 2 additional tests added for `cache=False` behavior.
- **Files modified:** src/ztlctl/plugins/runtime.py, src/ztlctl/infrastructure/vault.py, tests/plugins/test_plugin_runtime.py
- **Commits:** f2a0136 (Task 1), 34e80fc (Task 2)

## Verification

```
grep "PluginManager()" src/ztlctl/ --include="*.py" -r | grep -v manager.py | grep -v runtime.py
# → empty (only runtime.py creates PluginManager())

grep "inject_configs\|settings=" src/ztlctl/commands/__init__.py
# → settings=settings,  # DEBT-07: inject_configs support

uv run pytest -q --ignore=tests/integration/test_verbose_telemetry.py
# → 1868 passed, 2 skipped

uv run mypy src/
# → Success: no issues found in 122 source files
```

Note: `tests/integration/test_verbose_telemetry.py::test_verbose_json_includes_telemetry_in_meta` is a pre-existing flaky test (JSON multi-line parsing) that was failing before this plan's changes. Confirmed via `git stash` regression test.

## Known Stubs

None.

## Self-Check: PASSED

- src/ztlctl/plugins/runtime.py: FOUND
- tests/plugins/test_plugin_runtime.py: FOUND
- Commit f2a0136: FOUND
- Commit 34e80fc: FOUND
- No remaining PluginManager() outside manager.py/runtime.py: CONFIRMED
