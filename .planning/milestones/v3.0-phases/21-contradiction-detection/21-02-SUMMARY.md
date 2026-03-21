---
phase: 21-contradiction-detection
plan: "02"
subsystem: services/check, services/contradiction, mcp/resources, actions/_check
tags: [contradiction-detection, check-service, semantic-analysis, mcp-resource, action-registry]
dependency_graph:
  requires: ["21-01"]
  provides: [CAT_SEMANTIC, confirm_contradiction, ztlctl://review/contradictions, check_contradictions, confirm_contradiction_action]
  affects: [CheckService, ContradictionService, MCP resources, ActionRegistry]
tech_stack:
  added: []
  patterns:
    - TDD red-green: failing tests first, then implementation
    - trace_span for semantic analysis in CheckService.check()
    - Bidirectional graph edge insertion via VaultTransaction.insert_edge with check_duplicate
    - Lazy import pattern for cross-service ContradictionService usage in CheckService
    - MCP _impl function pattern (testable without mcp package) for contradictions_review_impl
key_files:
  created:
    - tests/test_contradiction_integration.py
    - tests/test_contradiction_resource.py
    - tests/test_contradiction_actions.py
  modified:
    - src/ztlctl/services/check.py
    - src/ztlctl/services/contradiction.py
    - src/ztlctl/mcp/resources.py
    - src/ztlctl/actions/_check.py
    - tests/controllers/test_contradiction.py
    - tests/mcp/test_resources.py
    - tests/mcp/test_parity.py
decisions:
  - CAT_SEMANTIC category wired outside the vault.engine.connect() block — _check_semantic() opens its own connection internally via ContradictionService
  - confirm_contradiction validates both notes exist before opening transaction (fail-fast before mutation)
  - _check_semantic called with trace_span("semantic_analysis") after garden_health span — consistent with existing span pattern
  - Category count 16->17 (analysis category now active with check_contradictions and confirm_contradiction)
  - Resource catalog count 19->20 (ztlctl://review/contradictions added)
metrics:
  duration: "~8 minutes"
  completed: "2026-03-21"
  tasks: 2
  files: 8
---

# Phase 21 Plan 02: Platform Integration Summary

**One-liner:** Contradiction detection wired into CheckService (CAT_SEMANTIC), confirmed as bidirectional graph edges, exposed as MCP resource, and registered in ActionRegistry as two analysis-category actions.

## What Was Built

### Task 1: CheckService CAT_SEMANTIC + confirm_contradiction + MCP resource (TDD)

**CheckService integration (CNTR-03):**
- Added `CAT_SEMANTIC = "semantic_analysis"` constant alongside existing CAT_* constants
- Added `_check_semantic()` private method: lazy-imports ContradictionService, calls `find_candidates()`, converts candidates to `SEVERITY_INFO` CheckIssue dicts
- Wired into `check()` with `trace_span("semantic_analysis")` after garden_health span
- Gracefully skips (returns `[]`) when VectorService unavailable — ContradictionService already handles this path

**ContradictionService.confirm_contradiction (CNTR-04):**
- Replaced stub (NOT_IMPLEMENTED) with full implementation
- Validates both note IDs exist via SELECT before opening transaction
- Inserts two bidirectional edges (`A->B` and `B->A`) with `edge_type="contradicts"`, `source_layer="user"`
- Uses `check_duplicate=True` so repeat calls skip silently and report `edges_created=0`
- Returns `{"note_a", "note_b", "edges_created"}` in ServiceResult
- Dispatches `post_action` event via `_dispatch_post_action_event`

**MCP resource (CNTR-05):**
- Added `ztlctl://review/contradictions` to `_RESOURCE_CATALOG`
- Added `contradictions_review_impl(vault)` function — returns `{"candidates": [...], "count": N}`
- Registered in `register_resources()` as `@server.resource("ztlctl://review/contradictions")`

### Task 2: ActionRegistry registration (CNTR-06)

Added two ActionDefinitions to `_register_check_actions()` in `src/ztlctl/actions/_check.py`:

- **`check_contradictions`** — category `analysis`, side_effect `read`, `cli_group=check`, `cli_name=contradictions`, params: `similarity_threshold (float, default=0.85)`, `max_pairs (int, default=20)`, handler delegates to `ContradictionController.check_contradictions`
- **`confirm_contradiction`** — category `analysis`, side_effect `write`, `cli_group=check`, `cli_name=confirm-contradiction`, params: `note_a (str, required, cli_is_argument)`, `note_b (str, required, cli_is_argument)`, handler delegates to `ContradictionController.confirm_contradiction`, `mcp_common_errors=("NOT_FOUND",)`

Both auto-generate CLI commands under `ztlctl check` and MCP tools in the analysis category.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Controller tests expected NOT_IMPLEMENTED stub**
- **Found during:** Task 2 full test suite regression
- **Issue:** `tests/controllers/test_contradiction.py` had two tests asserting `result.error.code == "NOT_IMPLEMENTED"` — written for Plan 01's stub
- **Fix:** Updated assertions to expect `NOT_FOUND` (the correct behavior when note IDs don't exist in the vault), removed stale "Plan 02" message check
- **Files modified:** `tests/controllers/test_contradiction.py`
- **Commit:** c3ce2eb

**2. [Rule 1 - Bug] Category/resource count tests hardcoded for pre-Plan-02 values**
- **Found during:** Task 2 full test suite regression
- **Issue:** `test_category_coverage` expected 16 categories; `test_catalog_has_19_resources` expected 19 resources
- **Fix:** Updated to 17 categories (analysis category now active) and 20 resources (contradictions resource added)
- **Files modified:** `tests/mcp/test_parity.py`, `tests/mcp/test_resources.py`
- **Commit:** c3ce2eb

## Known Stubs

None — all methods fully implemented. `confirm_contradiction` stub from Plan 01 replaced with working implementation.

## Pre-existing Failures (Out of Scope)

`tests/integration/test_verbose_telemetry.py::TestVerboseTelemetry::test_verbose_json_includes_telemetry_in_meta` — pre-existing JSON parsing failure confirmed present before this plan's changes (verified via git stash). Logged in `deferred-items.md`.

## Self-Check: PASSED

Files created/modified exist:
- src/ztlctl/services/check.py — FOUND (CAT_SEMANTIC constant + _check_semantic method)
- src/ztlctl/services/contradiction.py — FOUND (confirm_contradiction implementation)
- src/ztlctl/mcp/resources.py — FOUND (contradictions_review_impl + registration)
- src/ztlctl/actions/_check.py — FOUND (check_contradictions + confirm_contradiction)
- tests/test_contradiction_integration.py — FOUND (15 tests)
- tests/test_contradiction_resource.py — FOUND (6 tests)
- tests/test_contradiction_actions.py — FOUND (19 tests)

Commits:
- abdcd48: feat(21-02): CAT_SEMANTIC check integration, confirm_contradiction edges, MCP resource
- c3ce2eb: feat(21-02): register check_contradictions and confirm_contradiction in ActionRegistry

Test suite: 2011 passed, 1 pre-existing failure (unrelated), 2 skipped
