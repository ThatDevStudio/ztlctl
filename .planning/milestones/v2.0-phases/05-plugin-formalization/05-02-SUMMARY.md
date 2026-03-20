---
phase: 05-plugin-formalization
plan: "02"
subsystem: plugins
tags:
  - plugins
  - note-types
  - render-contributions
  - marketplace-metadata
  - tdd
dependency_graph:
  requires:
    - PLUGIN_API_VERSION constant + check_plugin_api_version() (05-01)
    - pre_action/post_action hookspecs (05-01)
    - NoteTypeDefinition + NoteTypeRegistry in domain/registry.py
    - ActionDefinition + ActionRegistry in actions/
    - CreateController.create_note/create_reference/create_task
    - UpdateController.update/archive
  provides:
    - register_note_types hookspec on ZtlctlHookSpec
    - register_render_contributions hookspec on ZtlctlHookSpec
    - RenderContribution frozen dataclass in contracts.py
    - PluginMetadata frozen dataclass in contracts.py
    - PluginManager._register_note_types() with injectable registry overrides
    - PluginManager._register_note_type_actions() auto-creating create/update/close ActionDefinitions
    - PluginManager.render_contributions() public method
    - src/ztlctl/plugins/metadata.py with read_plugin_metadata()
  affects:
    - 05-03 (EventBus can now bridge post_create etc. to plugin note type actions)
    - CLI generator (Phase 4) auto-picks up plugin-contributed ActionDefinitions
    - MCP generator (Phase 3) auto-picks up plugin-contributed ActionDefinitions
tech_stack:
  added: []
  patterns:
    - TDD red-green for both tasks
    - Injectable registry overrides (note_registry/action_registry params) for test isolation without monkeypatching singletons
    - _collect_contributions pattern reused for render_contributions()
    - Closure-captured variables (_note_type, _content_type) for correct lambda capture in action handlers
    - content_type dispatch in create handler (task -> create_task, reference -> create_reference, else -> create_note)
key_files:
  created:
    - src/ztlctl/plugins/metadata.py
    - tests/plugins/test_custom_note_types.py
    - tests/plugins/test_render_contributions.py
    - tests/plugins/test_marketplace_metadata.py
  modified:
    - src/ztlctl/plugins/hookspecs.py
    - src/ztlctl/plugins/contracts.py
    - src/ztlctl/plugins/manager.py
decisions:
  - "Injectable note_registry/action_registry params on _register_note_types() for test isolation — avoids monkeypatching module-level singletons, which would leak between tests"
  - "content_type dispatch in create handler routes to create_task/create_reference/create_note based on NoteTypeDefinition.content_type — each controller method has distinct signatures"
  - "close handler maps to UpdateController.archive() not close() — the actual method name in UpdateController"
  - "PluginMetadata added to contracts.py (not a separate file) for cohesion with other contract types"
  - "render_contributions() is NOT called in discover_and_load() — it is lazy (on-demand via _collect_contributions), consistent with all other contribution collectors"
  - "_register_note_types() IS called eagerly in discover_and_load() after _register_content_models() — note types and their ActionDefinitions must be registered at load time for CLI/MCP generators"
metrics:
  duration_seconds: 442
  completed_date: "2026-03-20"
  tasks_completed: 2
  files_created: 4
  files_modified: 3
---

# Phase 05 Plan 02: Custom Note Types, Render Contributions, and Marketplace Metadata Summary

**One-liner:** PLUG-05/06/07 payoff — plugins register NoteTypeDefinitions that auto-generate create/update/close ActionDefinitions picked up by CLI+MCP generators, plus RenderContribution for custom output formatting and PluginMetadata convention for discoverability.

## What Was Built

### Task 1: Custom Note Type Registration Pipeline + RenderContribution + Hookspecs

**`src/ztlctl/plugins/hookspecs.py`** — Added to ZtlctlHookSpec:
- `register_note_types()` — plugins return `list[NoteTypeDefinition] | None`; PluginManager auto-creates 3 ActionDefinitions per type
- `register_render_contributions()` — plugins return `list[RenderContribution] | None`; enables custom Rich/MCP output

**`src/ztlctl/plugins/contracts.py`** — Added two new frozen dataclasses:
- `RenderContribution`: `note_type (str)`, `rich_formatter (Callable[[dict], str])`, `mcp_formatter (Callable[[dict], dict])`
- `PluginMetadata`: `name, version, author, capabilities (tuple[str,...]), ztlctl_api_version (int), description (str="")`

**`src/ztlctl/plugins/manager.py`** — Auto-registration pipeline:
- `_register_note_types(note_registry=None, action_registry=None)` — iterates `register_note_types` hook results, registers each NoteTypeDefinition into NoteTypeRegistry (duplicate = warning+skip), calls `_register_note_type_actions()` for each
- `_register_note_type_actions(ntd, action_registry=None)` — creates 3 ActionDefinitions:
  - `create_{name}`: category="creation", side_effect="write", cli_group=content_type, params=(title, tags, links, body)
  - `update_{name}`: category="mutation", side_effect="write", params=(content_id, title, tags, body, status)
  - `close_{name}`: category="mutation", side_effect="write", params=(content_id, summary)
  - Create handler routes by content_type: task→create_task, reference→create_reference, else→create_note
  - Update handler calls UpdateController.update(); close handler calls UpdateController.archive()
- `render_contributions(reserved_types=None)` — uses `_collect_contributions` pattern, key=note_type
- `discover_and_load()` now calls `_register_note_types()` after `_register_content_models()`

### Task 2: Marketplace Metadata Convention + Helper

**`src/ztlctl/plugins/metadata.py`** (new):
- `read_plugin_metadata(pyproject_path: Path) -> PluginMetadata | None`
- Reads `[tool.ztlctl-plugin]` from pyproject.toml using stdlib `tomllib` (Python 3.11+) with `tomli` fallback
- Returns `None` on: missing section, invalid TOML, missing required fields — all with warning log
- No runtime enforcement — convention-based for future discoverability

## Test Coverage

| File | Tests | Description |
|------|-------|-------------|
| `tests/plugins/test_custom_note_types.py` | 8 | NoteTypeDefinition registration, auto-ActionDefinitions, metadata, duplicate handling |
| `tests/plugins/test_render_contributions.py` | 9 | RenderContribution frozen, formatters callable, collection, duplicate skip |
| `tests/plugins/test_marketplace_metadata.py` | 9 | PluginMetadata frozen, read_plugin_metadata happy path + error cases |

Total new tests: **26** — all passing.
Full suite: **1697 passed, 2 skipped** — no regressions.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Incorrect controller module names in action handlers**
- **Found during:** Task 1, mypy verification
- **Issue:** Plan suggested `create_ctrl` and `update_ctrl` as module names; actual modules are `create.py` and `update.py`
- **Fix:** Corrected imports to `ztlctl.controllers.create` and `ztlctl.controllers.update`
- **Files modified:** `src/ztlctl/plugins/manager.py`
- **Commit:** 43bc857

**2. [Rule 1 - Bug] Incorrect close handler method name**
- **Found during:** Task 1, mypy verification (`attr-defined` error)
- **Issue:** Plan said `UpdateController.close()`; actual method is `UpdateController.archive()`
- **Fix:** Changed close handler to call `UpdateController(vault).archive(**kwargs)`
- **Files modified:** `src/ztlctl/plugins/manager.py`
- **Commit:** 43bc857

**3. [Rule 1 - Bug] create handler incorrectly passed content_type to create_note**
- **Found during:** Task 1, mypy verification (`call-arg` error)
- **Issue:** Plan suggested `create_note(content_type=ct, subtype=nt, ...)` but `create_note` has no `content_type` param
- **Fix:** Dispatch by content_type: `task` → `create_task(title, **kwargs)`, `reference` → `create_reference(title, subtype=nt, **kwargs)`, else → `create_note(title, subtype=nt, **kwargs)`
- **Files modified:** `src/ztlctl/plugins/manager.py`
- **Commit:** 43bc857

**4. [Rule 1 - Bug] tomli fallback needed both import-not-found and no-redef type: ignore codes**
- **Found during:** Task 2, mypy verification
- **Issue:** `import tomli as tomllib  # type: ignore[no-redef]` alone caused `import-not-found` mypy error
- **Fix:** Added both codes: `# type: ignore[import-not-found,no-redef]`
- **Files modified:** `src/ztlctl/plugins/metadata.py`
- **Commit:** e2c56ff

## Self-Check: PASSED

All created files exist on disk. All four commits verified in git log.
