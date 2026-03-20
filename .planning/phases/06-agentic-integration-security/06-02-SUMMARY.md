---
phase: 06-agentic-integration-security
plan: 02
subsystem: mcp
tags: [mcp, resources, recipes, progressive-disclosure, category-activation, agnt-03, agnt-04]
dependency_graph:
  requires: []
  provides: [recipe-resources, category-activation-state, discover-categories-tool]
  affects: [mcp-server, action-registry, mcp-resources, mcp-generator]
tech_stack:
  added: []
  patterns: [impl-function-testability, category-activation-state, progressive-disclosure]
key_files:
  created:
    - src/ztlctl/controllers/discovery.py
  modified:
    - src/ztlctl/mcp/resources.py
    - src/ztlctl/mcp/generator.py
    - src/ztlctl/actions/_register_core.py
    - tests/mcp/test_resources.py
    - tests/mcp/test_generator.py
    - tests/mcp/test_parity.py
decisions:
  - "_DEFAULT_ACTIVE_CATEGORIES frozenset guards deactivate_category -- core categories cannot be deactivated by agents"
  - "DiscoveryController uses lazy imports matching established controller pattern -- avoids circular imports and startup cost"
  - "Category activation state is module-level in generator.py (server-scoped) -- single MCP server process = single session"
  - "deactivate_category returns False for unknown non-active category (NOT_FOUND) and for core category (VALIDATION_FAILED) -- separate error codes"
metrics:
  duration_minutes: 12
  completed_date: "2026-03-20T04:45:26Z"
  tasks_completed: 2
  files_modified: 7
  files_created: 1
requirements: [AGNT-03, AGNT-04]
---

# Phase 6 Plan 2: Agent Orchestration Recipes and Progressive Tool Disclosure Summary

**One-liner:** Recipe MCP resources (ztlctl://recipes/*) provide structured step-by-step orchestration guidance; generator.py category activation lets agents manage the tool surface via discover_categories/activate_category/deactivate_category.

## What Was Built

### Task 1: Orchestration Recipe Resources (AGNT-03)

Added four new `_impl` functions to `src/ztlctl/mcp/resources.py`:

- `recipe_research_capture_impl()` — 3-step recipe: search → create_note → reweave
- `recipe_review_triage_impl()` — 4-step recipe: work_queue → get_document → update → archive
- `recipe_knowledge_synthesis_impl()` — 4-step recipe: search → gaps → draft_from_topic → reweave
- `recipe_index_impl()` — index listing all three recipes with URIs

Each recipe step has structured `step`, `action`, `params`, `description`, and `conditions` fields. All four URIs (`ztlctl://recipes`, `ztlctl://recipes/research-capture`, `ztlctl://recipes/review-triage`, `ztlctl://recipes/knowledge-synthesis`) are registered in `_RESOURCE_CATALOG` and exposed as server resources via `register_resources()`.

### Task 2: Progressive Tool Disclosure (AGNT-04)

Added category activation state to `src/ztlctl/mcp/generator.py`:

- `_DEFAULT_ACTIVE_CATEGORIES` — frozenset with creation, mutation, query, graph, lifecycle, session
- `_active_categories` — mutable session-scoped set initialized from defaults
- `get_active_categories()` — returns a copy (not reference)
- `activate_category(cat)` — validates against registry, adds to active set, returns bool
- `deactivate_category(cat)` — guards core categories, returns False on attempt
- `reset_active_categories()` — restores to defaults
- `_get_all_categories()` — helper that queries ActionRegistry for all known categories

Created `src/ztlctl/controllers/discovery.py` with `DiscoveryController`:

- `discover_categories()` — groups registry actions by category, annotates active/core/tool status
- `activate_category(category)` — delegates to generator, returns tool list on success
- `deactivate_category(category)` — guards core categories with informative error recovery

Registered three ActionDefinitions in the new "discovery" category in `_register_core.py`.

## Test Coverage

- 6 new tests in `TestRecipeResources` (test_resources.py) covering all recipe impls, index, catalog URIs, and server registration
- 7 new tests in test_generator.py covering default categories, copy semantics, activate/deactivate/reset lifecycle
- Updated `test_catalog_has_15_resources` (was 11, now 15 with 4 recipe URIs)
- Updated `test_category_coverage` category count from 13 to 14 in test_parity.py

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Updated stale catalog count test**
- **Found during:** Task 1
- **Issue:** `test_catalog_has_11_resources` expected 11 but now there are 15 (4 recipe URIs added)
- **Fix:** Renamed and updated assertion to `test_catalog_has_15_resources`
- **Files modified:** tests/mcp/test_resources.py
- **Commit:** 7884834

**2. [Rule 1 - Bug] Updated stale category count in test_parity.py**
- **Found during:** Task 2
- **Issue:** `test_category_coverage` expected 13 categories but discovery category added a 14th
- **Fix:** Updated docstring and assertion from 13 to 14
- **Files modified:** tests/mcp/test_parity.py
- **Commit:** ed7dd03

## Commits

| Commit | Message | Task |
|--------|---------|------|
| 7884834 | feat(06-02): add orchestration recipe MCP resources (AGNT-03) | Task 1 |
| ed7dd03 | feat(06-02): add progressive tool disclosure -- category activation (AGNT-04) | Task 2 |

## Self-Check

- [x] `src/ztlctl/mcp/resources.py` — recipe_research_capture_impl exists
- [x] `src/ztlctl/mcp/generator.py` — _DEFAULT_ACTIVE_CATEGORIES, get/activate/deactivate/reset exist
- [x] `src/ztlctl/controllers/discovery.py` — DiscoveryController created
- [x] `src/ztlctl/actions/_register_core.py` — discover_categories, activate_category, deactivate_category registered
- [x] `tests/mcp/test_resources.py` — TestRecipeResources with 6 tests
- [x] `tests/mcp/test_generator.py` — 7 category activation tests
- [x] All 1760 tests pass, mypy strict, ruff clean
