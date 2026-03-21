---
phase: 17-registry-decomposition-and-plugin-runtime
plan: "01"
subsystem: actions
tags: [refactor, architecture, registry, decomposition]
dependency_graph:
  requires: []
  provides: [feature-local-registration-modules, decomposed-action-registry]
  affects: [src/ztlctl/actions/__init__.py, src/ztlctl/actions/_*.py]
tech_stack:
  added: []
  patterns: [feature-local-registration-modules, lazy-controller-imports]
key_files:
  created:
    - src/ztlctl/actions/_creation.py
    - src/ztlctl/actions/_query.py
    - src/ztlctl/actions/_graph.py
    - src/ztlctl/actions/_lifecycle.py
    - src/ztlctl/actions/_session.py
    - src/ztlctl/actions/_check.py
    - src/ztlctl/actions/_ingest.py
    - src/ztlctl/actions/_export.py
    - src/ztlctl/actions/_admin.py
  modified:
    - src/ztlctl/actions/__init__.py
    - tests/actions/test_core_registrations.py
  deleted:
    - src/ztlctl/actions/_register_core.py
decisions:
  - "_register_core.py decomposed into 9 feature-local modules; each owns one registration function; __init__.py calls all 9 at module load time"
  - "Unused `from typing import Any` removed from 8 of 9 modules (linter auto-restored them); _export.py retains Any for _make_export_filters return type"
metrics:
  duration: "~15 min"
  completed_date: "2026-03-21"
  tasks: 2
  files_changed: 11
---

# Phase 17 Plan 01: Registry Decomposition Summary

Decomposed the monolithic `_register_core.py` (2303 lines, 66 ActionDefinitions) into 9 feature-local registration modules colocated in `src/ztlctl/actions/`, satisfying ARCH-07.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Extract 9 feature-local registration modules | dc134ca | 9 new `_*.py` files |
| 2 | Wire `__init__.py`, delete `_register_core.py`, update tests | cad76df | `__init__.py`, `_register_core.py` (deleted), `test_core_registrations.py` |

## What Was Built

**9 feature-local registration modules** in `src/ztlctl/actions/`:

| Module | Function | Actions |
|--------|----------|---------|
| `_creation.py` | `_register_creation_actions()` | 5 (create_note, create_reference, create_task, create_batch, garden_seed) |
| `_query.py` | `_register_query_actions()` | 10 (count_items, search, get, list_items, work_queue, list_tags, decision_support, topic_packet, draft_from_topic, vault_review) |
| `_graph.py` | `_register_graph_actions()` | 8 (related, themes, rank, path, gaps, bridges, unlink, materialize_metrics) |
| `_lifecycle.py` | `_register_lifecycle_actions()` | 6 (update, archive, supersede, reweave, prune, undo) |
| `_session.py` | `_register_session_actions()` | 9 (start, close, reopen, status, log_entry, cost, context, brief, extract_decision) |
| `_check.py` | `_register_check_actions()` | 5 (check, fix, rebuild, rollback, event_purge) |
| `_ingest.py` | `_register_ingest_actions()` | 4 (list_providers, ingest_text, ingest_file, ingest_url) |
| `_export.py` | `_register_export_actions()` | 4 (export_markdown, export_indexes, export_graph, export_dashboard) |
| `_admin.py` | `_register_admin_actions()` | 15 (vector_status, reindex_all, check_pending, apply, stamp_current, init_workflow, update_workflow, export_assets, init_vault, regenerate_self, check_staleness, discover_categories, activate_category, deactivate_category, docs_search) |

**`__init__.py`** updated to call all 9 functions at module load time; `_register_core.py` deleted.

**`tests/actions/test_core_registrations.py`** updated:
- Docstring updated to reflect decomposition
- `test_minimum_action_count` threshold raised from 45 to 60
- Added `TestDecomposedModules` class with 3 tests verifying the decomposition

## Verification

- 36/36 registration tests pass
- `uv run ruff check src/ztlctl/actions/` — clean
- `uv run mypy src/` — 122 files, no issues
- 66 actions still registered (zero regressions)
- `_register_core.py` does not exist

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Lint] Unused `from typing import Any` imports**
- **Found during:** Task 2 (ruff check)
- **Issue:** All 9 new modules included `from typing import Any` in module header (copied from `_register_core.py` template), but 8 of them don't use `Any` at module level
- **Fix:** Removed unused `from typing import Any` from 8 modules; retained in `_export.py` where `Any` is used in `_make_export_filters()` return annotation
- **Files modified:** `_creation.py`, `_query.py`, `_graph.py`, `_lifecycle.py`, `_session.py`, `_check.py`, `_ingest.py`, `_admin.py`
- **Commit:** cad76df

## Known Stubs

None.

## Self-Check: PASSED
