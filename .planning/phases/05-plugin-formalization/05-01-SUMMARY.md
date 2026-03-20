---
phase: 05-plugin-formalization
plan: "01"
subsystem: plugins
tags:
  - plugins
  - api-versioning
  - action-hooks
  - config-injection
  - tdd
dependency_graph:
  requires: []
  provides:
    - PLUGIN_API_VERSION constant + check_plugin_api_version() in plugins/_version.py
    - PluginLoadError exception for compatibility failures
    - ActionRejection frozen dataclass for pre-action abort
    - pre_action (firstresult=True) and post_action hookspecs
    - get_config_schema and initialize hookspecs
    - warn_on_impl deprecation markers on all 9 per-event hookspecs
    - PluginsConfig extra=allow + get_plugin_config() accessor
    - PluginManager.inject_configs() for TOML-based config injection
    - BaseController._dispatch_pre_action() and _dispatch_post_action()
  affects:
    - 05-02 (plugin lifecycle callbacks build on pre/post-action dispatch)
    - 05-03 (EventBus bridges post_create etc. to post_action)
tech_stack:
  added: []
  patterns:
    - TDD red-green for both tasks
    - _version.py private module to break circular import between __init__.py and manager.py
    - firstresult=True hookspec for pre_action (first non-None wins)
    - warn_on_impl=DeprecationWarning on deprecated hookspecs (pluggy native)
    - extra="allow" on PluginsConfig Pydantic model for arbitrary plugin sections
key_files:
  created:
    - src/ztlctl/plugins/_version.py
    - tests/plugins/test_api_version.py
    - tests/plugins/test_pre_action_hooks.py
    - tests/plugins/test_plugin_config.py
  modified:
    - src/ztlctl/plugins/__init__.py
    - src/ztlctl/plugins/hookspecs.py
    - src/ztlctl/plugins/contracts.py
    - src/ztlctl/plugins/manager.py
    - src/ztlctl/controllers/base.py
    - src/ztlctl/config/models.py
    - tests/config/test_settings.py
decisions:
  - "Plugin versioning helpers extracted to plugins/_version.py to prevent circular import: __init__.py imports manager, manager now imports _version directly"
  - "Compatibility window logic: declared == current = clean; declared in (min_supported, current) = warn; declared <= min_supported = raise; declared > current = raise"
  - "Legacy plugins (no PLUGIN_API_VERSION attr) pass silently — backward compatible"
  - "ActionRejection returned as (original_kwargs, rejection) tuple from _dispatch_pre_action so caller can emit error ServiceResult without modifying kwargs"
  - "test_legacy_plugins_obsidian_key_is_ignored renamed and updated: extra=allow intentionally stores plugin sections for PLUG-03"
metrics:
  duration_seconds: 470
  completed_date: "2026-03-20"
  tasks_completed: 2
  files_created: 4
  files_modified: 7
---

# Phase 05 Plan 01: Plugin API Versioning, Pre/Post-Action Hooks, and Config Injection Summary

**One-liner:** PLUG-01/02/03 foundation — API versioning with 2-version compatibility window, firstresult pre_action/post_action hookspecs with ActionRejection abort, and Pydantic-validated plugin config injection from TOML sections.

## What Was Built

### Task 1: Plugin API Versioning + ActionRejection + Hookspecs

**`src/ztlctl/plugins/_version.py`** (new) — Private module to avoid circular imports:
- `PLUGIN_API_VERSION = 1` integer constant
- `_COMPATIBILITY_WINDOW = 2` — plugins at version `current - window + 1` through `current - 1` load with a deprecation warning; older versions are rejected
- `PluginLoadError` exception for incompatible plugins
- `check_plugin_api_version(plugin, name)` — returns `list[str]` warnings or raises `PluginLoadError`

**`src/ztlctl/plugins/__init__.py`** — Re-exports all version symbols from `_version.py`

**`src/ztlctl/plugins/contracts.py`** — Added `ActionRejection` frozen dataclass:
```python
@dataclass(frozen=True)
class ActionRejection:
    reason: str
    code: str = "plugin_rejected"
    detail: dict[str, Any] = field(default_factory=dict)
```

**`src/ztlctl/plugins/hookspecs.py`** — Major additions:
- `pre_action(action_name, kwargs)` — `firstresult=True`, returns `ActionRejection | dict | None`
- `post_action(action_name, kwargs, result)` — fires for all plugins
- `get_config_schema()` — `firstresult=True`, returns `type[BaseModel] | None`
- `initialize(config)` — receives validated config at load time
- All 9 per-event hookspecs (`post_create` through `post_init_profile`) annotated with `warn_on_impl=DeprecationWarning(...)` pointing to `post_action`

### Task 2: PluginManager Version Checking + Config Injection + BaseController Dispatch

**`src/ztlctl/plugins/manager.py`** — Added:
- Import `check_plugin_api_version`, `PluginLoadError` from `_version`
- `register_plugin()` — version checks before accepting; incompatible plugins unregistered + warning logged; deprecated versions get warning
- `_normalize_plugin_instances()` — same version check after instantiation
- `inject_configs(settings)` / `_inject_plugin_configs(settings)` — iterates all plugins, calls `get_config_schema()`, looks up `settings.plugins.get_plugin_config(name)`, validates with Pydantic, calls `initialize(config=validated_or_None)`

**`src/ztlctl/config/models.py`** — `PluginsConfig` changes:
- `model_config = {"frozen": True, "extra": "allow"}` — accepts `[plugins.<name>]` TOML sections
- `get_plugin_config(name: str) -> dict[str, Any]` — accessor for extra plugin config

**`src/ztlctl/controllers/base.py`** — Added:
- `_dispatch_pre_action(action_name, kwargs) -> tuple[dict, ActionRejection | None]`
  - Returns `(modified_kwargs, None)` if plugin returns dict
  - Returns `(original_kwargs, ActionRejection)` if plugin rejects
  - Returns `(original_kwargs, None)` on None result or exception
- `_dispatch_post_action(action_name, kwargs, result) -> None`
  - Fires `pm.hook.post_action(...)`, swallows exceptions at DEBUG level

## Test Coverage

| File | Tests | Description |
|------|-------|-------------|
| `tests/plugins/test_api_version.py` | 9 | PLUGIN_API_VERSION constant, compatibility logic, warn_on_impl |
| `tests/plugins/test_pre_action_hooks.py` | 11 | ActionRejection, pre_action firstresult, post_action multi-plugin |
| `tests/plugins/test_plugin_config.py` | 18 | PluginsConfig extra, inject_configs, BaseController dispatch |

Total new tests: **38** — all passing.
Full suite: **1671 passed, 2 skipped** — no regressions.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Circular Import] Extracted versioning helpers to `_version.py`**
- **Found during:** Task 2, when adding `from ztlctl.plugins import check_plugin_api_version` to `manager.py`
- **Issue:** `plugins/__init__.py` imports `PluginManager` from `manager.py`; `manager.py` importing from `plugins/__init__.py` creates a circular import
- **Fix:** Created `plugins/_version.py` as a private module with no imports from the `plugins` package. `manager.py` imports from `_version` directly. `__init__.py` re-exports from `_version` for public API consumers.
- **Files modified:** `src/ztlctl/plugins/_version.py` (new), `src/ztlctl/plugins/__init__.py`, `src/ztlctl/plugins/manager.py`
- **Commit:** 901c522, eb11019

**2. [Rule 1 - Bug] Updated `test_legacy_plugins_obsidian_key_is_ignored` in `test_settings.py`**
- **Found during:** Task 2 full test suite run
- **Issue:** The test asserted that unknown `[plugins.obsidian]` keys were silently dropped by `PluginsConfig`. With `extra="allow"`, they are now intentionally stored for PLUG-03 config injection — the old behavior was no longer correct.
- **Fix:** Renamed test to `test_plugins_extra_keys_stored_for_config_injection` and updated assertion to verify the new intended behavior (extra keys stored in `model_extra`, accessible via `get_plugin_config`).
- **Files modified:** `tests/config/test_settings.py`
- **Commit:** eb11019

## Self-Check: PASSED

All created files exist on disk. Both task commits verified in git log.
