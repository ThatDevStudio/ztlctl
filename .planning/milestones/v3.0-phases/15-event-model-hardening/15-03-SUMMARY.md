---
phase: 15-event-model-hardening
plan: "03"
subsystem: event-model
tags: [event-bus, wal, dead-letter, check-service, action-registry, maintenance]

requires:
  - phase: 15-event-model-hardening/15-01
    provides: EventBusConfig with dead_letter_retention_days field
  - phase: 15-event-model-hardening/15-02
    provides: Startup drain in Vault.init_event_bus

provides:
  - SEVERITY_INFO constant in CheckService
  - Dead-letter count reporting in _check_structural_validation (info severity)
  - EventBus.purge_dead_letters() method with configurable retention
  - Auto-purge of old dead-letter events during startup drain (D-20)
  - event_purge ActionDefinition registered under maintenance category
  - CheckController.event_purge() method delegating to EventBus.purge_dead_letters

affects:
  - check-service
  - event-bus
  - action-registry
  - mcp-tools

tech-stack:
  added: []
  patterns:
    - SEVERITY_INFO for advisory/informational check issues (rank 0 in filter)
    - purge_dead_letters pattern for WAL cleanup with configurable retention
    - maintenance category in ActionRegistry for operational housekeeping actions

key-files:
  created: []
  modified:
    - src/ztlctl/services/check.py
    - src/ztlctl/services/contracts.py
    - src/ztlctl/plugins/event_bus.py
    - src/ztlctl/infrastructure/vault.py
    - src/ztlctl/controllers/check.py
    - src/ztlctl/actions/_register_core.py
    - tests/plugins/test_event_bus.py
    - tests/services/test_check.py
    - tests/controllers/test_check.py
    - tests/mcp/test_parity.py

key-decisions:
  - "SEVERITY_INFO rank=0 in _SEVERITY_RANK so dead-letter issues appear only at min_severity='info', not default 'warning'"
  - "CheckIssue severity Literal extended to include 'info' for contract consistency"
  - "event_purge placed in 'maintenance' category (not 'check') — operational housekeeping vs. integrity scanning"
  - "Auto-purge uses config retention_days by default; event_purge action allows override via older_than_days"

patterns-established:
  - "Informational (non-actionable) check findings use SEVERITY_INFO, filtered out at default warning threshold"
  - "WAL cleanup methods return deleted row count for observability"

requirements-completed: [DEBT-03]

duration: 20min
completed: "2026-03-21"
---

# Phase 15 Plan 03: Dead-Letter Event Observability Summary

**Dead-letter WAL events are now visible in `ztlctl check`, auto-purged at startup, and manually clearable via `event_purge` action registered under maintenance category**

## Performance

- **Duration:** ~20 min
- **Started:** 2026-03-21T16:40:00Z
- **Completed:** 2026-03-21T16:58:19Z
- **Tasks:** 2
- **Files modified:** 10

## Accomplishments

- Added `SEVERITY_INFO` constant to CheckService and extended `CheckIssue.severity` Literal to include "info"
- Dead-letter WAL count surfaces in `ztlctl check --min-severity info` as a structural issue with guidance to run `event purge`
- `EventBus.purge_dead_letters(older_than_days=N)` deletes stale dead-letter rows, defaulting to config's `dead_letter_retention_days`
- Startup drain in `Vault.init_event_bus()` now auto-purges old dead-letter events before processing pending events
- `event_purge` ActionDefinition registered in ActionRegistry under new `maintenance` category, wired to `CheckController.event_purge()`

## Task Commits

1. **Test: Dead-letter purge and check reporting (RED)** — `6a38895` (test)
2. **Task 1: Dead-letter observability implementation (GREEN)** — `17d9f2c` (feat)
3. **Task 2: event_purge action registration** — `57175fe` (feat)

## Files Created/Modified

- `src/ztlctl/services/check.py` — Added `SEVERITY_INFO`, event_wal import, dead-letter count query in `_check_structural_validation`
- `src/ztlctl/services/contracts.py` — Extended `CheckIssue.severity` Literal to include "info"
- `src/ztlctl/plugins/event_bus.py` — Added `purge_dead_letters()` method; added `delete`, `func` imports
- `src/ztlctl/infrastructure/vault.py` — Added auto-purge call before startup drain in `init_event_bus()`
- `src/ztlctl/controllers/check.py` — Added `event_purge()` method delegating to bus
- `src/ztlctl/actions/_register_core.py` — Registered `event_purge` ActionDefinition under `maintenance` category
- `tests/plugins/test_event_bus.py` — 4 new `TestDeadLetterPurge` tests
- `tests/services/test_check.py` — 3 new `TestDeadLetterCheckReporting` tests
- `tests/controllers/test_check.py` — 3 new `TestEventPurgeController` tests
- `tests/mcp/test_parity.py` — Updated category count 15 → 16 for new maintenance category

## Decisions Made

- `SEVERITY_INFO` gets rank 0 in `_SEVERITY_RANK` so dead-letter issues only appear when `min_severity="info"` is explicitly requested — users aren't flooded with advisory items by default
- `event_purge` placed in `maintenance` category rather than `check` category — it's operational housekeeping, not integrity scanning
- `CheckController.event_purge()` returns `ok=False` with `EVENT_BUS_NOT_INITIALIZED` error code when bus is None (handles CLI invocation before vault initialization)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] CheckIssue contract rejected "info" severity**
- **Found during:** Task 1 (implementing dead-letter check reporting)
- **Issue:** `CheckIssue.severity` was `Literal["warning", "error"]`; adding "info" severity to the structural check caused Pydantic validation to reject the issue dict
- **Fix:** Extended the Literal to `Literal["info", "warning", "error"]` in `src/ztlctl/services/contracts.py`
- **Files modified:** src/ztlctl/services/contracts.py
- **Verification:** check tests pass with info-severity issues serializing correctly
- **Committed in:** 17d9f2c (Task 1 GREEN commit)

**2. [Rule 1 - Bug] test_parity.py expected 15 categories, new maintenance category makes 16**
- **Found during:** Task 2 (full suite run after registering event_purge)
- **Issue:** `test_category_coverage` asserted `len(categories) == 15`; adding `maintenance` category made it 16
- **Fix:** Updated assertion to `== 16` and updated docstring
- **Files modified:** tests/mcp/test_parity.py
- **Verification:** All 7 parity tests pass
- **Committed in:** 57175fe (Task 2 commit)

**3. [Rule 2 - Missing Critical] Ruff lint violations in purge_dead_letters**
- **Found during:** Task 2 (ruff check before commit)
- **Issue:** Line-too-long (E501) and `timezone.utc` instead of `datetime.UTC` (UP017)
- **Fix:** Wrapped long line with parens, replaced `timezone.utc` with `UTC` alias import
- **Files modified:** src/ztlctl/plugins/event_bus.py
- **Verification:** `uv run ruff check src/` passes with no issues
- **Committed in:** 57175fe (Task 2 commit)

---

**Total deviations:** 3 auto-fixed (2 Rule 1 bugs, 1 Rule 2 missing critical)
**Impact on plan:** All fixes necessary for correctness and code quality. No scope creep.

## Issues Encountered

- Pre-existing test failure in `tests/integration/test_verbose_telemetry.py::TestVerboseTelemetry::test_verbose_json_includes_telemetry_in_meta` (JSONDecodeError: Extra data) — confirmed pre-existing via `git stash`. Logged to deferred-items, not caused by this plan.

## Known Stubs

None — all functionality fully implemented and wired.

## Next Phase Readiness

- DEBT-03 fully resolved: dead-letter events are observable, auto-managed, and manually clearable
- Phase 15 complete: all 3 plans executed (01: config/event model, 02: single producer + drain, 03: observability)
- Ready for Phase 16 (MCP graceful shutdown + deprecated per-event hook removal)

---
*Phase: 15-event-model-hardening*
*Completed: 2026-03-21*
