---
phase: 03-mcp-surface-generation
plan: 02
subsystem: mcp
tags: [mcp, generator, token-budget, parity, action-registry, testing]
dependency_graph:
  requires:
    - phase: 03-01
      provides: "generate_tools(), _make_tool_fn(), McpResponse, ActionRegistry-driven tool registration"
  provides:
    - "BUDGET_AWARE_ACTIONS frozenset and _apply_token_budget() in generator.py"
    - "token_budget: int | None param injected into list_items, search, vault_review, decision_support tools"
    - "tests/mcp/test_parity.py: 6 parity tests proving 59/59 ActionDefinitions have MCP tools"
  affects: [mcp/server.py, future agent consumers, CLI/MCP parity docs]
tech-stack:
  added: []
  patterns:
    - "Budget-aware tool injection: BUDGET_AWARE_ACTIONS set + _apply_token_budget() in _make_tool_fn() conditionally injects token_budget kwarg"
    - "Parity testing via DummyServer: generate_tools() on DummyServer captures all registered fns for structural assertions"
    - "Token estimation: len(json.dumps(data)) // 4 as char-to-token heuristic"
key-files:
  created:
    - tests/mcp/test_parity.py
  modified:
    - src/ztlctl/mcp/generator.py
    - tests/mcp/test_generator.py
key-decisions:
  - "PREVIOUSLY_MISSING set in test_parity.py uses actual registry names (apply, check_pending, stamp_current, check) not plan-doc names (upgrade_apply, etc.) — discovered at test time"
  - "Budget truncation iterates from tail of first list field — simple, predictable, correct for MCP list responses"
  - "_apply_token_budget returns same object when budget is None (identity, not copy) for zero-cost passthrough"
patterns-established:
  - "Budget-aware MCP tools: BUDGET_AWARE_ACTIONS frozenset as gating mechanism, _apply_token_budget() as pure function"
  - "Parity tests: DummyServer fixture, registry_names <= tool_names subset check proves no gaps"
requirements-completed: [AGNT-02, PLUG-04]
duration: 4min
completed: 2026-03-19
---

# Phase 3 Plan 2: Token Budget + MCP Parity Test Suite Summary

**Token-budget truncation for 4 high-volume MCP tools (list_items, search, vault_review, decision_support) plus a 6-test parity suite proving all 59 ActionDefinitions have registered MCP tools.**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-19T23:24:20Z
- **Completed:** 2026-03-19T23:28:00Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments

- `BUDGET_AWARE_ACTIONS` frozenset and `_apply_token_budget()` added to `generator.py` — 4 tools now accept `token_budget: int | None`
- Budget-aware `_make_tool_fn()` branch injects `token_budget` into `__annotations__` and `__kwdefaults__` at generation time
- 8 new tests in `test_generator.py` prove truncation behavior, annotation injection, and BUDGET_AWARE_ACTIONS membership
- `tests/mcp/test_parity.py` with 6 tests verifies complete CLI/MCP parity: 59/59 actions covered, 13 categories covered, all tools have docstrings and `return` annotation
- Full suite: 1622 passed, 2 skipped — mypy strict clean, ruff clean

## Task Commits

Each task was committed atomically:

1. **Task 1: Add token-budget truncation for high-volume MCP tools** - `efbac86` (feat)
2. **Task 2: Create parity test suite verifying all ActionDefinitions have MCP tools** - `4e3dbff` (test)

**Plan metadata:** (docs commit follows)

_Note: TDD tasks — RED phase (import error confirmed), GREEN phase (all tests pass)_

## Files Created/Modified

- `src/ztlctl/mcp/generator.py` — Added `BUDGET_AWARE_ACTIONS`, `_apply_token_budget()`, conditional budget branch in `_make_tool_fn()`
- `tests/mcp/test_generator.py` — 8 new budget tests added
- `tests/mcp/test_parity.py` — Created: 6 parity tests proving 59/59 registry coverage

## Decisions Made

- `PREVIOUSLY_MISSING` set in `test_parity.py` uses actual ActionRegistry names (`apply`, `check_pending`, `stamp_current`, `check`) not the plan-doc names (`upgrade_apply`, `upgrade_check_pending`, etc.) — corrected at test time after running and seeing failures
- `_apply_token_budget` returns the same dict object (identity) when `budget is None` for zero-cost passthrough — no unnecessary allocation
- Budget truncation operates on the first list-valued field found — simple, predictable, handles all current MCP list responses correctly

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] PREVIOUSLY_MISSING tool names corrected to match actual registry names**
- **Found during:** Task 2 (test execution)
- **Issue:** Plan specified `upgrade_apply`, `upgrade_check_pending`, `upgrade_stamp_current`, `check_integrity` but the actual ActionRegistry uses `apply`, `check_pending`, `stamp_current`, `check`
- **Fix:** Updated `PREVIOUSLY_MISSING` set in `test_parity.py` to use correct registry names with inline comments explaining the mapping
- **Files modified:** `tests/mcp/test_parity.py`
- **Verification:** All 6 parity tests pass
- **Committed in:** `4e3dbff` (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 - Bug)
**Impact on plan:** Trivial naming correction — the tools ARE present, the test just needed correct names. No scope change.

## Issues Encountered

None beyond the naming deviation above.

## Next Phase Readiness

- Phase 03 complete: MCP surface is fully auto-generated from ActionRegistry, token-budget aware for high-volume tools, and parity-tested
- Ready for Phase 04 or any downstream consumer of the MCP surface
- AGNT-02 and PLUG-04 requirements satisfied

---
*Phase: 03-mcp-surface-generation*
*Completed: 2026-03-19*

## Self-Check: PASSED

All key files exist:
- FOUND: src/ztlctl/mcp/generator.py
- FOUND: tests/mcp/test_generator.py
- FOUND: tests/mcp/test_parity.py

All task commits verified:
- FOUND: efbac86 (feat(03-02): add token-budget truncation)
- FOUND: 4e3dbff (test(03-02): create parity test suite)
