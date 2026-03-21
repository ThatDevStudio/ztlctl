---
phase: 17-registry-decomposition-and-plugin-runtime
verified: 2026-03-21T00:00:00Z
status: passed
score: 7/7 must-haves verified
re_verification: false
---

# Phase 17: Registry Decomposition and Plugin Runtime Verification Report

**Phase Goal:** Action registrations live in feature-local modules, plugin/profile/workflow discovery is handled by a single coherent runtime owner, and load_plugin_commands participates in config injection
**Verified:** 2026-03-21
**Status:** passed
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| #  | Truth | Status | Evidence |
|----|-------|--------|----------|
| 1  | Each feature area owns its ActionDefinitions in a local module inside `src/ztlctl/actions/` | VERIFIED | 9 modules exist: `_creation.py`, `_query.py`, `_graph.py`, `_lifecycle.py`, `_session.py`, `_check.py`, `_ingest.py`, `_export.py`, `_admin.py` — each with a single `_register_*_actions()` function |
| 2  | `_register_core.py` is deleted (decomposed) | VERIFIED | `ls src/ztlctl/actions/_register_core.py` returns NOT_FOUND; `test_register_core_deleted` test asserts absence |
| 3  | All 66 existing ActionDefinitions remain registered — no regressions | VERIFIED | `from ztlctl.actions import get_action_registry; len(r.list_actions())` returns 66; `test_total_registration_count_at_least_66` passes |
| 4  | Module-load-time registration still works via `import ztlctl.actions` | VERIFIED | `__init__.py` imports and calls all 9 `_register_*_actions()` functions at module load time |
| 5  | PluginManager is not independently constructed outside `manager.py`/`runtime.py` | VERIFIED | `grep -rn "PluginManager()" src/ztlctl/ --include="*.py" | grep -v manager.py | grep -v runtime.py` returns empty |
| 6  | `load_plugin_commands` uses the centralized factory with `inject_configs` | VERIFIED | `commands/__init__.py` calls `get_plugin_manager(local_dir=..., settings=settings)` — `settings=settings` triggers `inject_configs(settings)` inside the factory |
| 7  | Plugin discovery caches by scope; repeated calls return the same PM instance | VERIFIED | `runtime.py` maintains `_cache: dict[tuple[Path | None, bool], PluginManager]`; `test_get_plugin_manager_caches_by_scope` confirms identity; `cache=False` path available for vault.py mutation site |

**Score:** 7/7 truths verified

---

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/ztlctl/actions/_creation.py` | `_register_creation_actions()` | VERIFIED | Exists, line 6: `def _register_creation_actions() -> None`, lazy controller imports, `from __future__ import annotations` at line 3 |
| `src/ztlctl/actions/_query.py` | `_register_query_actions()` | VERIFIED | Exists, line 6, pattern confirmed |
| `src/ztlctl/actions/_graph.py` | `_register_graph_actions()` | VERIFIED | Exists, line 6, pattern confirmed |
| `src/ztlctl/actions/_lifecycle.py` | `_register_lifecycle_actions()` | VERIFIED | Exists, line 6, pattern confirmed |
| `src/ztlctl/actions/_session.py` | `_register_session_actions()` | VERIFIED | Exists, line 6, pattern confirmed |
| `src/ztlctl/actions/_check.py` | `_register_check_actions()` | VERIFIED | Exists, line 6, pattern confirmed |
| `src/ztlctl/actions/_ingest.py` | `_register_ingest_actions()` | VERIFIED | Exists, line 6, pattern confirmed |
| `src/ztlctl/actions/_export.py` | `_register_export_actions()` | VERIFIED | Exists, line 8, pattern confirmed |
| `src/ztlctl/actions/_admin.py` | `_register_admin_actions()` | VERIFIED | Exists, line 6, pattern confirmed |
| `src/ztlctl/actions/__init__.py` | Calls all 9 functions at load time, no `_register_core` reference | VERIFIED | All 9 `_register_*_actions()` calls present, no `_register_core` import, `__all__` exports correct symbols |
| `src/ztlctl/plugins/runtime.py` | `get_plugin_manager()` factory with scope-aware caching | VERIFIED | `def get_plugin_manager`, `_cache: dict`, `pm.inject_configs(settings)`, `cache: bool = True` param, `reset_plugin_manager_cache()` all present |
| `src/ztlctl/commands/__init__.py` | `load_plugin_commands` uses `get_plugin_manager` with `inject_configs` | VERIFIED | Line 19 imports `get_plugin_manager` from `ztlctl.plugins.runtime`; line 37 passes `settings=settings` |
| `tests/plugins/test_plugin_runtime.py` | Tests for centralized factory | VERIFIED | 9 test functions including `test_get_plugin_manager_caches_by_scope` and `test_inject_configs_called_when_settings_provided` |
| `tests/actions/test_core_registrations.py` | `TestDecomposedModules` class with decomposition assertions | VERIFIED | `test_register_core_deleted`, `test_all_feature_modules_exist`, `test_total_registration_count_at_least_66` all present |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `src/ztlctl/actions/__init__.py` | all `_register_*_actions` functions | import + call at module load time | VERIFIED | Lines 3–23: imports all 9 then calls all 9 at module scope |
| `src/ztlctl/commands/__init__.py` | `src/ztlctl/plugins/runtime.py` | `get_plugin_manager` call | VERIFIED | Lazy import at line 19, call at line 35 with `settings=settings` |
| `src/ztlctl/infrastructure/vault.py` | `src/ztlctl/plugins/runtime.py` | `get_plugin_manager` call | VERIFIED | Line 378: lazy import; line 384: `get_plugin_manager(local_dir=local_plugins, settings=self._settings, cache=False)` |
| `src/ztlctl/services/init.py` | `src/ztlctl/plugins/runtime.py` | `get_plugin_manager` call | VERIFIED | Line 157: lazy import; line 159: `get_plugin_manager(local_dir=None, include_entrypoints=True)` |
| `src/ztlctl/services/workflow.py` | `src/ztlctl/plugins/runtime.py` | `get_plugin_manager` call | VERIFIED | Line 198: lazy import; line 200: `get_plugin_manager(local_dir=vault_root / ".ztlctl" / "plugins")` |
| `src/ztlctl/workspace_profiles.py` | `src/ztlctl/plugins/runtime.py` | `get_plugin_manager` call | VERIFIED | Line 161: lazy import; line 163: `get_plugin_manager(local_dir=..., include_entrypoints=...)` |

---

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| ARCH-07 | 17-01-PLAN.md | Action registrations decomposed into feature-local modules | SATISFIED | 9 `_*.py` modules in `src/ztlctl/actions/`, `_register_core.py` deleted, 66 actions still registered |
| ARCH-08 | 17-02-PLAN.md | Centralized plugin runtime discovery — single coherent owner per scope | SATISFIED | `runtime.py` factory with `_cache` keyed on `(local_dir, include_entrypoints)`; all 5 former independent construction sites replaced |
| DEBT-07 | 17-02-PLAN.md | `load_plugin_commands` creates PluginManager with `inject_configs` support | SATISFIED | `commands/__init__.py` passes `settings=settings` to `get_plugin_manager()`, which calls `pm.inject_configs(settings)` when settings is not None |

All 3 requirement IDs from plan frontmatter accounted for. No orphaned phase-17 requirements in REQUIREMENTS.md (all three explicitly map to Phase 17 and show `Complete`).

---

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `src/ztlctl/commands/generator.py` | 196 | Stale comment: `# noqa: F401 — triggers _register_core_actions()` | INFO | Comment describes the old monolith function name; the import itself is correct and still works — `import ztlctl.actions` triggers registration via `__init__.py` which now calls all 9 decomposed functions. No behavioral impact. |

No blocker or warning anti-patterns found. The stale comment in `generator.py` is informational only — the import mechanism is functionally correct.

---

### Human Verification Required

None. All phase goals are verifiable programmatically.

---

### Gaps Summary

No gaps. All must-haves are satisfied:

- ARCH-07: The 2303-line `_register_core.py` monolith is gone. Its 66 ActionDefinitions are distributed across 9 feature-local modules, each owning a single `_register_*_actions()` function with lazy controller imports. Module-load-time behavior is preserved via `__init__.py` calling all 9 at import time.

- ARCH-08: `src/ztlctl/plugins/runtime.py` provides the single coherent runtime owner. All 5 former independent `PluginManager()` construction sites delegate to `get_plugin_manager()`. Scope-aware caching by `(local_dir, include_entrypoints)` key prevents redundant discovery. The `cache=False` escape hatch handles vault.py's mutation pattern correctly.

- DEBT-07: `load_plugin_commands` in `commands/__init__.py` now passes `settings=settings` to the factory, which calls `inject_configs(settings)` — closing the longstanding config injection gap.

Test coverage: 45 registration + runtime tests pass (36 registration, 9 plugin runtime). Full suite reported 1868 passed per SUMMARY.

---

_Verified: 2026-03-21_
_Verifier: Claude (gsd-verifier)_
