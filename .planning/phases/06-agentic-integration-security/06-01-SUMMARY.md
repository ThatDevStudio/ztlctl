---
phase: 06-agentic-integration-security
plan: 01
subsystem: api
tags: [pydantic, mcp, error-handling, agent-recovery]

# Dependency graph
requires:
  - phase: 03-mcp-surface-generation
    provides: McpResponse, McpError, COMMON_ERROR_RECOVERY, from_result() converter
provides:
  - ServiceError.recovery field (str | None) — machine-readable agent guidance per error
  - McpError.recovery field propagated by from_result() with ServiceError.recovery > dict fallback
  - COMMON_ERROR_RECOVERY extended from 9 to 36 entries covering all service error codes
affects: [06-02, 06-03, mcp-surface-generation, agent-consumers]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "ServiceError.recovery overrides COMMON_ERROR_RECOVERY dict in from_result()"
    - "COMMON_ERROR_RECOVERY as exhaustive error-code-to-guidance registry"

key-files:
  created: []
  modified:
    - src/ztlctl/services/result.py
    - src/ztlctl/mcp/response.py
    - tests/services/test_result.py
    - tests/mcp/test_response.py

key-decisions:
  - "ServiceError.recovery is optional (default None) — zero impact on 30+ existing construction sites"
  - "from_result() uses result.error.recovery or COMMON_ERROR_RECOVERY.get(code) — explicit override wins"
  - "COMMON_ERROR_RECOVERY is a module-level dict; agents can import it directly for static inspection"

patterns-established:
  - "ServiceError.recovery overrides COMMON_ERROR_RECOVERY: per-call specificity beats generic guidance"
  - "model_dump(exclude_none=True) omits recovery when None — clean MCP payload for success paths"

requirements-completed: [AGNT-01]

# Metrics
duration: 10min
completed: 2026-03-20
---

# Phase 06 Plan 01: Agent Error Recovery Summary

**ServiceError and McpError gain a recovery field; COMMON_ERROR_RECOVERY extended to 36 entries covering all service error codes with programmatic next-step guidance for agents**

## Performance

- **Duration:** 10 min
- **Started:** 2026-03-20T04:24:00Z
- **Completed:** 2026-03-20T04:34:51Z
- **Tasks:** 1
- **Files modified:** 4

## Accomplishments

- Added `recovery: str | None = None` to `ServiceError` with zero impact on all existing construction sites
- Added `recovery: str | None = None` to `McpError` with priority propagation in `from_result()`: explicit `ServiceError.recovery` overrides `COMMON_ERROR_RECOVERY` dict fallback
- Extended `COMMON_ERROR_RECOVERY` from 9 to 36 entries covering every error code emitted by all 13 services (create, query, graph, update, reweave, session, check, upgrade, export, init, workflow, ingest, vector)
- Added 9 new tests: field defaults, propagation, override priority, dump exclusion/inclusion, and full-coverage assertion via `test_all_codes_have_recovery`

## Task Commits

Each task was committed atomically:

1. **Task 1: Add recovery field to ServiceError and McpError, extend COMMON_ERROR_RECOVERY** - `7884834` (feat)

**Plan metadata:** committed with docs/state update

## Files Created/Modified

- `src/ztlctl/services/result.py` — Added `recovery: str | None = None` field to `ServiceError`
- `src/ztlctl/mcp/response.py` — Added `recovery: str | None = None` to `McpError`; extended `COMMON_ERROR_RECOVERY` to 36 entries; wired `from_result()` with recovery propagation
- `tests/services/test_result.py` — Added 2 tests for `ServiceError.recovery` field behavior
- `tests/mcp/test_response.py` — Added 7 tests: McpError field, propagation, override, dump behavior, full-coverage assertion

## Decisions Made

- `ServiceError.recovery` is `str | None = None` — existing callers pass zero changes
- `from_result()` uses `result.error.recovery or COMMON_ERROR_RECOVERY.get(result.error.code)` — explicit per-call recovery overrides the generic fallback; `None` result means no guidance available for that code
- All 36 error code strings were determined by grepping `code="..."` across the full `src/ztlctl/services/` tree; `test_all_codes_have_recovery` provides ongoing regression guard

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed line-length violations in COMMON_ERROR_RECOVERY entries**
- **Found during:** Task 1 (full-suite ruff check)
- **Issue:** 17 new dict entries exceeded the 100-char ruff line limit
- **Fix:** Wrapped long string values in parenthesized implicit concatenation, consistent with the 3 existing long entries already using that pattern
- **Files modified:** `src/ztlctl/mcp/response.py`, `tests/mcp/test_response.py`
- **Verification:** `ruff check` passes on all modified files
- **Committed in:** `7884834` (task commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 — line length)
**Impact on plan:** Cosmetic formatting fix only. No semantic changes.

## Issues Encountered

- Pre-commit hook stash/restore cycle temporarily appeared to fail the commit but the commit was created successfully (`7884834`). The exit code 1 was a pre-commit warning about unstaged files in other plan's uncommitted changes, not a commit failure.
- Pre-existing ruff and mypy errors in `tests/services/test_workflow.py`, `tests/plugins/test_manager.py`, and `src/ztlctl/plugins/manager.py` (from earlier phase work in-progress) were identified as out-of-scope and logged to deferred items.

## Next Phase Readiness

- `ServiceError.recovery` field is available for all services to populate on specific error sites if needed
- `McpError.recovery` is automatically populated for all 36 codes via `from_result()` — agents receive guidance without any service-layer changes
- Plan 06-02 (MCP orchestration resources) was already committed alongside this work and is ready

---
*Phase: 06-agentic-integration-security*
*Completed: 2026-03-20*

## Self-Check: PASSED

- FOUND: src/ztlctl/services/result.py
- FOUND: src/ztlctl/mcp/response.py
- FOUND: .planning/phases/06-agentic-integration-security/06-01-SUMMARY.md
- FOUND: commit 7884834
