---
phase: 02-action-registry
plan: 04
subsystem: actions
tags: [actions, registry, controllers, capstone]
dependency_graph:
  requires: [02-01, 02-02, 02-03]
  provides: [core-action-registry]
  affects: [mcp, cli, actions]
tech_stack:
  added: []
  patterns: [factory-lambda-handlers, lazy-controller-imports]
key_files:
  created:
    - src/ztlctl/actions/_register_core.py
    - tests/actions/test_core_registrations.py
  modified:
    - src/ztlctl/actions/__init__.py
    - tests/actions/test_definitions.py
    - tests/actions/test_registry.py
decisions:
  - Handler factory pattern: lambda vault, **kw: Controller(vault).method(**kw) — creates controller per call to avoid stale state
  - Lazy controller imports inside _register_core_actions() body — avoids circular imports and expensive startup cost
  - Module-load-time registration via __init__.py — mirrors domain/registry.py builtin registration pattern
  - 5 custom_presentation=True actions: create_batch, init_vault, init_workflow, update_workflow, export_assets
  - MCP metadata strings shortened to fit ruff E501 (100 char) limit — content preserved
  - Side-effect for reindex_all set to "read" per plan spec (scanning and writing vector embeddings is idempotent)
metrics:
  duration: 10
  completed_date: "2026-03-19"
  tasks: 3
  files: 5
---

# Phase 02 Plan 04: Core Action Registrations Summary

59 ActionDefinitions registered across 13 categories via factory lambda handlers, completing the define-once action model for the entire controller layer.

## What Was Built

### _register_core.py

`_register_core_actions()` function registering 59 ActionDefinitions into the singleton registry. Organized into 13 sections matching the category taxonomy:

- **creation** (4): create_note, create_reference, create_task, create_batch
- **query** (10): count_items, search, get, list_items, work_queue, list_tags, decision_support, topic_packet, draft_from_topic, vault_review
- **graph** (8): related, themes, rank, path, gaps, bridges, unlink, materialize_metrics
- **lifecycle** (3): update, archive, supersede
- **reweave** (3): reweave, prune, undo
- **session** (9): start, close, reopen, status, log_entry, cost, context, brief, extract_decision
- **check** (4): check, fix, rebuild, rollback
- **ingest** (4): list_providers, ingest_text, ingest_file, ingest_url
- **export** (4): export_markdown, export_indexes, export_graph, export_dashboard
- **vector** (1): reindex_all
- **upgrade** (3): check_pending, apply, stamp_current
- **workflow** (3): init_workflow, update_workflow, export_assets
- **init** (3): init_vault, regenerate_self, check_staleness

Read: 29, Write: 30. Custom presentation: 5.

### __init__.py update

Added `_register_core_actions()` call at module load time, mirroring the `_register_builtins()` pattern from `domain/registry.py`.

### test_core_registrations.py

33 integration tests across 4 test classes:
- `TestCoreRegistrationCount`: minimum count (>=45), unique names, all 13 categories covered
- `TestActionLookup`: lookup by name with correct category/side_effect/params for 7 key actions; custom_presentation set
- `TestFilteringConsistency`: read/write filter correctness, spot-checks for 22 read + 30 write actions, subset invariant
- `TestHandlerSignatureParity`: callable check, vault+kwargs signature, param descriptions, required param defaults, param coverage for 8 actions
- `TestCategoryIntegrity`: parametrized exact-match for 8 fixed-size categories, content checks for 5 variable-size categories

## Decisions Made

- **Factory lambda handlers**: `lambda vault, **kw: Controller(vault).method(**kw)` — constructs controller per call to avoid stale vault state across calls. Controllers construct services per-call themselves (decision from plan 02-02).
- **Lazy controller imports**: All 13 controller imports are inside the `_register_core_actions()` function body to avoid module-level cross-layer imports that could cause circular import chains.
- **Module-load registration**: `__init__.py` calls `_register_core_actions()` once on import. The singleton registry rejects duplicate registrations (raises ValueError), so double-import is safe.
- **custom_presentation=True**: Applied to create_batch, init_vault, init_workflow, update_workflow, export_assets — these have complex I/O that can't be handled by a generic presenter.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Pre-existing ruff I001 in test files**
- **Found during:** Task 3 full validation
- **Issue:** tests/actions/test_definitions.py and test_registry.py had unsorted import blocks (ruff I001), causing `ruff check .` to fail
- **Fix:** `uv run ruff check --fix` on both files
- **Files modified:** tests/actions/test_definitions.py, tests/actions/test_registry.py
- **Commit:** 573287c

## Final Validation

- 1665 tests pass (33 new + 1632 pre-existing)
- `uv run mypy src/` — 0 errors (117 files)
- `uv run ruff check .` — 0 errors
- `uv run ruff format --check .` — all 230 files already formatted
- Registry loads at import time with 59 actions (plan required >=45)

## Self-Check: PASSED

All created files exist. All commit hashes verified in git log.
