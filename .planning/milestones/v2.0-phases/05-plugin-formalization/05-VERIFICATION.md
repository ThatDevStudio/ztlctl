---
phase: 05-plugin-formalization
verified: 2026-03-19T00:00:00Z
status: passed
score: 10/10 must-haves verified
re_verification: false
---

# Phase 05: Plugin Formalization Verification Report

**Phase Goal:** Third-party plugin authors have a stable, versioned API to register custom note types, actions, hooks, and configuration
**Verified:** 2026-03-19
**Status:** passed
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| #  | Truth | Status | Evidence |
|----|-------|--------|----------|
| 1  | Plugins that declare a PLUGIN_API_VERSION too new or too old are rejected at load time with clear error messages | VERIFIED | `_version.py`: `check_plugin_api_version()` raises `PluginLoadError` for declared > host or declared <= min_supported; called in `manager.py` `_normalize_plugin_instances()` and `register_plugin()` |
| 2  | Plugins that declare a deprecated API version emit a warning but still load | VERIFIED | `_version.py` lines 57-61: declared < PLUGIN_API_VERSION (but within window) returns warning list; `manager.py` logs each warning |
| 3  | A plugin pre_action hook can return modified kwargs that replace the originals before handler execution | VERIFIED | `controllers/base.py` `_dispatch_pre_action()`: `isinstance(result, dict)` branch returns `(result, None)`; `hookspecs.py` `pre_action` is `firstresult=True` |
| 4  | A plugin pre_action hook can return an ActionRejection to abort action execution | VERIFIED | `controllers/base.py` `_dispatch_pre_action()`: `isinstance(result, ActionRejection)` branch returns `(kwargs, result)`; `contracts.py` `ActionRejection` frozen dataclass with reason/code/detail |
| 5  | Plugin configuration from [plugins.<name>] TOML sections is validated against plugin-declared Pydantic schemas at load time | VERIFIED | `config/models.py` `PluginsConfig`: `extra="allow"`, `get_plugin_config()`; `manager.py` `_inject_plugin_configs()` calls `get_config_schema()`, validates via `schema_cls(**raw_config)`, passes to `initialize()` |
| 6  | Deprecated per-event hookspecs emit DeprecationWarning at plugin registration time via pluggy warn_on_impl | VERIFIED | `hookspecs.py`: all 9 per-event specs (post_create, post_update, post_close, post_reweave, post_session_start, post_session_close, post_check, post_init, post_init_profile) carry `warn_on_impl=DeprecationWarning(...)` |
| 7  | A plugin that registers a NoteTypeDefinition automatically gets create/update/close CLI and MCP actions | VERIFIED | `manager.py` `_register_note_type_actions()`: creates 3 `ActionDefinition` objects (`create_{ntd_name}`, `update_{ntd_name}`, `close_{ntd_name}`) with `cli_group`, `cli_name`, `mcp_when_to_use` set; registered into `ActionRegistry` |
| 8  | A plugin can provide custom Rich output and MCP response formatting via RenderContribution | VERIFIED | `contracts.py` `RenderContribution` frozen dataclass (note_type, rich_formatter, mcp_formatter); `manager.py` `render_contributions()` collects via `_collect_contributions`; `hookspecs.py` `register_render_contributions` hookspec |
| 9  | GitPlugin and ReweavePlugin use post_action instead of per-event hookimpl methods and declare PLUGIN_API_VERSION = 1 | VERIFIED | `builtins/git.py`: `PLUGIN_API_VERSION = 1`, single `@hookimpl post_action()` method, no `def post_create/update/close` methods; `builtins/reweave_plugin.py`: same pattern |
| 10 | Service-layer _dispatch_event calls reach migrated plugins through the EventBus post_action bridge | VERIFIED | `event_bus.py`: `_HOOK_TO_ACTION` dict maps 8 per-event names; `_execute_hook()` calls `post_action_fn(action_name=action_name, kwargs=payload, result=None)` after per-event dispatch; `post_create` refined to `create_{content_type}` |

**Score:** 10/10 truths verified

---

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/ztlctl/plugins/_version.py` | PLUGIN_API_VERSION constant, check_plugin_api_version(), PluginLoadError | VERIFIED | All three present; compatibility window logic complete |
| `src/ztlctl/plugins/__init__.py` | Re-exports PLUGIN_API_VERSION, PluginLoadError, check_plugin_api_version | VERIFIED | All exported via `__all__` from `_version.py` |
| `src/ztlctl/plugins/hookspecs.py` | pre_action (firstresult), post_action, get_config_schema, initialize, register_note_types, register_render_contributions, 9 deprecated hookspecs with warn_on_impl | VERIFIED | All present; TYPE_CHECKING guards for ActionRejection, NoteTypeDefinition, RenderContribution imports |
| `src/ztlctl/plugins/contracts.py` | ActionRejection, RenderContribution, PluginMetadata frozen dataclasses | VERIFIED | All three present with correct fields |
| `src/ztlctl/plugins/manager.py` | check_plugin_api_version() in load path, _inject_plugin_configs(), _register_note_types(), _register_note_type_actions(), render_contributions() | VERIFIED | All present; version check in both _normalize_plugin_instances() and register_plugin() |
| `src/ztlctl/controllers/base.py` | _dispatch_pre_action(), _dispatch_post_action() wired to vault.plugin_manager | VERIFIED | Both methods present; pm = self._vault.plugin_manager; None guard; ActionRejection/dict routing |
| `src/ztlctl/config/models.py` | PluginsConfig with extra="allow" and get_plugin_config() | VERIFIED | model_config = {"frozen": True, "extra": "allow"}; get_plugin_config() returns model_extra.get(name, {}) |
| `src/ztlctl/plugins/event_bus.py` | _HOOK_TO_ACTION dict; _execute_hook bridges to post_action | VERIFIED | Module-level _HOOK_TO_ACTION with 8 entries; bridge block in _execute_hook fires post_action after per-event dispatch |
| `src/ztlctl/plugins/metadata.py` | read_plugin_metadata(pyproject_path) reads [tool.ztlctl-plugin] | VERIFIED | Full implementation; tomllib/tomli fallback; returns PluginMetadata or None on error |
| `src/ztlctl/plugins/builtins/git.py` | PLUGIN_API_VERSION = 1, single post_action, no per-event methods | VERIFIED | Class attr set; single @hookimpl post_action; 8 old methods absent |
| `src/ztlctl/plugins/builtins/reweave_plugin.py` | PLUGIN_API_VERSION = 1, post_action, no post_create | VERIFIED | Class attr set; @hookimpl post_action with action_name filtering; post_create absent |
| `src/ztlctl/infrastructure/vault.py` | plugin_manager property | VERIFIED | Line 337: `@property def plugin_manager(self) -> Any | None` |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `plugins/manager.py` | `plugins/_version.py` | `check_plugin_api_version()` called during load | WIRED | Called in `_normalize_plugin_instances()` (line 387) and `register_plugin()` (line 78) |
| `controllers/base.py` | `plugins/hookspecs.py` | `pm.hook.pre_action()` called before handler | WIRED | `_dispatch_pre_action()` calls `pm.hook.pre_action(action_name=action_name, kwargs=kwargs)` |
| `plugins/manager.py` | `config/models.py` | Plugin config injection from PluginsConfig extra fields | WIRED | `_inject_plugin_configs()` calls `plugins_cfg.get_plugin_config(plugin_name)` |
| `plugins/manager.py` | `domain/registry.py` | `get_note_type_registry().register()` for plugin NoteTypeDefinitions | WIRED | `_register_note_types()` imports and calls `get_note_type_registry().register(item)` |
| `plugins/manager.py` | `actions/registry.py` | `get_action_registry().register()` for auto-generated ActionDefinitions | WIRED | `_register_note_type_actions()` imports and calls `action_registry.register(action)` |
| `plugins/builtins/git.py` | `plugins/hookspecs.py` | `@hookimpl post_action` replaces 8 per-event methods | WIRED | Single `@hookimpl def post_action()` method present; no old per-event methods |
| `plugins/builtins/reweave_plugin.py` | `plugins/hookspecs.py` | `@hookimpl post_action` replaces post_create | WIRED | `@hookimpl def post_action()` with `action_name in {"create_note", "create_reference"}` guard |
| `plugins/event_bus.py` | `plugins/hookspecs.py` | `_execute_hook` bridges per-event dispatch to post_action | WIRED | `_HOOK_TO_ACTION` dict + `post_action_fn(action_name=..., kwargs=payload, result=None)` |

---

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| PLUG-01 | 05-01, 05-03 | Plugin API versioning with deprecation helpers — explicit PLUGIN_API_VERSION constant; compatibility checks at load time | SATISFIED | `_version.py`: PLUGIN_API_VERSION=1, _COMPATIBILITY_WINDOW=2, check_plugin_api_version(), PluginLoadError; 9 hookspecs with warn_on_impl; GitPlugin + ReweavePlugin declare PLUGIN_API_VERSION=1 |
| PLUG-02 | 05-01, 05-03 | Pre-action hooks with modification and cancellation — synchronous firstresult dispatch; plugins can modify inputs or return rejection | SATISFIED | `hookspecs.py`: pre_action (firstresult=True), post_action; `contracts.py`: ActionRejection; `controllers/base.py`: _dispatch_pre_action/_dispatch_post_action; EventBus bridge |
| PLUG-03 | 05-01 | Plugin configuration via [plugins.<name>] sections in ztlctl.toml — validated against plugin-declared schema | SATISFIED | `config/models.py`: PluginsConfig extra="allow", get_plugin_config(); `manager.py`: _inject_plugin_configs() with ValidationError handling; get_config_schema + initialize hookspecs |
| PLUG-05 | 05-02 | Custom note types with custom lifecycles — plugins register NoteTypeDefinitions gaining CLI and MCP surfaces automatically | SATISFIED | `hookspecs.py`: register_note_types; `manager.py`: _register_note_types() + _register_note_type_actions() creating 3 ActionDefinitions with cli_group, cli_name, mcp_when_to_use |
| PLUG-06 | 05-02 | Plugin-contributed content type rendering — custom output for Rich CLI and MCP responses | SATISFIED | `contracts.py`: RenderContribution (note_type, rich_formatter, mcp_formatter); `hookspecs.py`: register_render_contributions; `manager.py`: render_contributions() collection method |
| PLUG-07 | 05-02 | Plugin marketplace metadata convention — [tool.ztlctl-plugin] in pyproject.toml | SATISFIED | `contracts.py`: PluginMetadata frozen dataclass; `plugins/metadata.py`: read_plugin_metadata() with tomllib/tomli fallback; documented in module docstring with example |

No orphaned requirements. PLUG-04 is assigned to Phase 3 (not this phase) and is not claimed by any plan here.

---

### Anti-Patterns Found

No blockers or warnings detected in phase artifacts.

- No TODO/FIXME/PLACEHOLDER comments in any artifact file
- No `return null` / empty stub implementations
- All hookspecs have real signatures and docstrings
- Both built-in plugins have substantive post_action routing logic
- EventBus bridge has independent exception handling that cannot break per-event dispatch

---

### Human Verification Required

None. All observable truths are verifiable from static code analysis. The plugin system is tested by 174 passing unit tests covering:

- API version acceptance/rejection edge cases
- pre_action ActionRejection and kwargs-modification paths
- Plugin config validation and injection
- NoteTypeDefinition auto-action registration
- RenderContribution collection
- Marketplace metadata reading
- GitPlugin and ReweavePlugin post_action routing
- EventBus post_action bridge with content_type mapping

---

### Summary

Phase 05 goal is fully achieved. Third-party plugin authors have a stable, versioned API surface:

**PLUG-01 (API versioning):** `PLUGIN_API_VERSION = 1` is exported from the plugins package. `check_plugin_api_version()` enforces a 2-version compatibility window with distinct error/warning paths. All 9 per-event hookspecs carry `warn_on_impl=DeprecationWarning(...)`. Both built-in plugins declare `PLUGIN_API_VERSION = 1`.

**PLUG-02 (Pre/post-action hooks):** `pre_action` (firstresult) and `post_action` hookspecs are defined. `BaseController._dispatch_pre_action()` and `_dispatch_post_action()` are wired to `vault.plugin_manager`. The EventBus bridges all 8 per-event lifecycle dispatches to `post_action` so migrated plugins receive events from both paths.

**PLUG-03 (Plugin config):** `PluginsConfig` accepts arbitrary `[plugins.<name>]` TOML sections via `extra="allow"`. `PluginManager._inject_plugin_configs()` validates against plugin-declared Pydantic schemas and calls `initialize()`.

**PLUG-05 (Custom note types):** `register_note_types` hookspec + `_register_note_types()` pipeline auto-creates `create_*`, `update_*`, `close_*` ActionDefinitions with correct `cli_group` and `mcp_when_to_use` metadata.

**PLUG-06 (Custom rendering):** `RenderContribution` frozen dataclass and `register_render_contributions` hookspec with `render_contributions()` collection method.

**PLUG-07 (Marketplace metadata):** `PluginMetadata` frozen dataclass and `read_plugin_metadata()` helper reading `[tool.ztlctl-plugin]` from pyproject.toml.

All 174 plugin tests pass. No regressions.

---

_Verified: 2026-03-19_
_Verifier: Claude (gsd-verifier)_
