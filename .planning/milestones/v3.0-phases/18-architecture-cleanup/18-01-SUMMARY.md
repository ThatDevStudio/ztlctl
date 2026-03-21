---
phase: 18-architecture-cleanup
plan: "01"
subsystem: services
tags: [python, pydantic, pluggy, mcp, import-cleanup]

# Dependency graph
requires:
  - phase: 17-registry-decomposition-and-plugin-runtime
    provides: centralized plugin runtime discovery and decomposed action registrations
provides:
  - workspace_modes.py compatibility wrapper removed; export.py uses direct workspace_profiles import
  - Phantom mutation category removed from _DEFAULT_ACTIVE_CATEGORIES
  - Custom note type update/close actions aligned to lifecycle category
  - ServiceError.recovery field documented with Pydantic Field description
  - ARCH-10, DEBT-05, DEBT-06 marked complete
affects: [phase-19-polaris, phase-20-recall, mcp-generator, plugins-manager, services-result]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Direct import over compatibility wrapper: workspace_profiles.normalize_dashboard_viewer imported directly"
    - "Pydantic Field description for self-documenting optional fields with production usage context"

key-files:
  created: []
  modified:
    - src/ztlctl/services/export.py
    - src/ztlctl/mcp/generator.py
    - src/ztlctl/plugins/manager.py
    - src/ztlctl/services/result.py
    - tests/mcp/test_generator.py
    - .planning/REQUIREMENTS.md
  deleted:
    - src/ztlctl/workspace_modes.py

key-decisions:
  - "ServiceError.recovery IS actively used (controllers/base.py, controllers/discovery.py, mcp/response.py) — kept with Field description documenting its purpose"
  - "Custom note type update/close actions use lifecycle category matching core _lifecycle.py actions — not mutation"

patterns-established:
  - "Direct imports over compatibility wrappers: remove indirection as soon as the wrapper's only consumer is updated"

requirements-completed: [ARCH-10, DEBT-05, DEBT-06]

# Metrics
duration: 12min
completed: 2026-03-21
---

# Phase 18 Plan 01: Architecture Cleanup (Compatibility Residue) Summary

**Dead workspace_modes.py wrapper removed, phantom mutation category purged from MCP generator and plugin manager, and ServiceError.recovery self-documented via Pydantic Field**

## Performance

- **Duration:** ~12 min
- **Started:** 2026-03-21T18:40:00Z
- **Completed:** 2026-03-21T18:52:00Z
- **Tasks:** 2
- **Files modified:** 6 (+ 1 deleted)

## Accomplishments

- Deleted `workspace_modes.py` compatibility wrapper; `export.py` now imports `normalize_dashboard_viewer` directly from `workspace_profiles`
- Removed `mutation` from `_DEFAULT_ACTIVE_CATEGORIES` in `mcp/generator.py`; custom note type update/close actions in `plugins/manager.py` changed to `lifecycle` category
- `ServiceError.recovery` documented with `Field(description=...)` clarifying it is actively populated by controllers and consumed by `mcp/response.py`
- REQUIREMENTS.md: ARCH-10, DEBT-05, DEBT-06 marked complete

## Task Commits

Each task was committed atomically:

1. **Task 1: Remove workspace_modes.py and fix mutation category** - `2639f70` (refactor)
2. **Task 2: Resolve DEBT-06 and update REQUIREMENTS.md** - `2071114` (fix)

**Deviation fix:** `69ee24e` (style: ruff E501 fix on Field description line length)

## Files Created/Modified

- `src/ztlctl/services/export.py` - Direct import from workspace_profiles instead of workspace_modes
- `src/ztlctl/mcp/generator.py` - _DEFAULT_ACTIVE_CATEGORIES no longer contains "mutation"
- `src/ztlctl/plugins/manager.py` - Custom note type update/close use category="lifecycle"
- `src/ztlctl/services/result.py` - ServiceError.recovery uses Pydantic Field with description
- `tests/mcp/test_generator.py` - Assertion updated to 5-category default set
- `.planning/REQUIREMENTS.md` - ARCH-10, DEBT-05, DEBT-06 marked complete and traceability updated
- ~~`src/ztlctl/workspace_modes.py`~~ - Deleted

## Decisions Made

- ServiceError.recovery is kept (not removed) — confirmed actively used by controllers/base.py (plugin rejection path), controllers/discovery.py (category error path), and mcp/response.py (MCP error response builder). Field description documents this so the "unused" tech debt perception is resolved.
- Mutation category never existed in the actual action registry — it was a phantom leftover in defaults. Removing it aligns defaults to the real category set.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed ruff E501 line too long in ServiceError.recovery Field description**
- **Found during:** Task 2 (post-task verification)
- **Issue:** Field description string exceeded 100-char line limit
- **Fix:** Split description into two concatenated string literals using parentheses
- **Files modified:** src/ztlctl/services/result.py
- **Verification:** `uv run ruff check` passes with 0 errors
- **Committed in:** `69ee24e` (follow-up style fix)

---

**Total deviations:** 1 auto-fixed (Rule 1 — style/lint)
**Impact on plan:** Trivial line-length fix. No scope creep.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Phase 18 Plan 02 can proceed — ARCH-10, DEBT-05, DEBT-06 are complete
- Remaining Phase 18 items: DEBT-01 (embedding dims), DEBT-08 (bridges k-approximation)
- Import graph is clean: no workspace_modes references anywhere in src/

---
*Phase: 18-architecture-cleanup*
*Completed: 2026-03-21*
