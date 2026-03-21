---
phase: 15-event-model-hardening
plan: 01
subsystem: plugins
tags: [pydantic, event-bus, config, domain-events, action-event]

# Dependency graph
requires: []
provides:
  - EventBusConfig frozen Pydantic model with 4 configurable timeout/retry fields
  - ActionEvent frozen Pydantic model with Literal side_effect constraint and JSON serialization
  - ZtlSettings.eventbus field wired to EventBusConfig with TOML [eventbus] section support
  - EventBus constructor accepts optional EventBusConfig parameter; stores per_future_timeout, shutdown_timeout, dead_letter_retention_days
  - Vault passes config=self._settings.eventbus to EventBus at construction
  - Vault.close() accepts optional timeout parameter passed through to EventBus.shutdown()
affects: [15-02-emission-drain, 15-03-dead-letter, plugins, vault]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "EventBusConfig: frozen Pydantic model in config/models.py, wired as ZtlSettings field via Field(default_factory)"
    - "ActionEvent: frozen Pydantic model in domain/events.py with Literal['write','read'] constraint and Any result field"
    - "EventBus config parameter: optional config=None for backward compat, falls back to legacy max_retries/max_workers kwargs"
    - "Vault.close() timeout pass-through: optional timeout param propagates from Vault -> EventBus.shutdown() -> _wait_futures()"

key-files:
  created:
    - src/ztlctl/domain/events.py
    - tests/domain/test_events.py
  modified:
    - src/ztlctl/config/models.py
    - src/ztlctl/config/settings.py
    - src/ztlctl/plugins/event_bus.py
    - src/ztlctl/infrastructure/vault.py
    - tests/config/test_models.py
    - tests/plugins/test_event_bus.py

key-decisions:
  - "EventBus config parameter is optional (config: EventBusConfig | None = None) — preserves backward compat with tests passing max_retries/max_workers as kwargs"
  - "ActionEvent.result: Any = None — allows full ServiceResult to be carried without coupling domain to services layer"
  - "shutdown_timeout_seconds stored on EventBus for future use in graceful shutdown logic (Plan 16)"
  - "dead_letter_retention_days stored on EventBus for dead-letter cleanup (Plan 15-03)"

patterns-established:
  - "Config section pattern: frozen BaseModel in config/models.py, Field(default_factory=X) in ZtlSettings, TOML [section] support automatic"
  - "Domain event pattern: ActionEvent in domain/events.py, frozen, Literal for constrained fields, Any result for loose coupling"

requirements-completed: [ARCH-04, DEBT-02]

# Metrics
duration: 18min
completed: 2026-03-21
---

# Phase 15 Plan 01: Event Model Hardening — Foundational Types Summary

**EventBusConfig frozen model with 4 configurable fields, ActionEvent domain event model, and EventBus refactored to use configurable timeouts from settings instead of hardcoded values**

## Performance

- **Duration:** ~18 min
- **Started:** 2026-03-21T00:00:00Z
- **Completed:** 2026-03-21T00:18:00Z
- **Tasks:** 2
- **Files modified:** 8

## Accomplishments

- Added `EventBusConfig` frozen Pydantic model with `shutdown_timeout_seconds`, `max_retries`, `dead_letter_retention_days`, `per_future_timeout_seconds` fields and correct defaults
- Added `ActionEvent` frozen Pydantic model in `domain/events.py` with `Literal["write", "read"]` constraint, `payload`, `warnings`, `result` fields and JSON serialization
- Wired `ZtlSettings.eventbus: EventBusConfig` with TOML `[eventbus]` section support
- Refactored `EventBus.__init__` to accept optional `config: EventBusConfig | None = None`; removed hardcoded `timeout=30` in `_wait_futures`
- Added `timeout` override parameter to `_wait_futures()` and `shutdown()`; Vault passes config through at construction and timeout through at close

## Task Commits

Each task was committed atomically:

1. **Task 1: EventBusConfig and ActionEvent models with tests** - `9bf04f5` (feat)
2. **Task 2: Refactor EventBus constructor to accept EventBusConfig** - `e7c7d0f` (refactor)

**Plan metadata:** (docs commit — see below)

_Note: Task 1 used TDD (RED test → GREEN implementation)._

## Files Created/Modified

- `src/ztlctl/domain/events.py` — New: ActionEvent frozen Pydantic domain event model
- `src/ztlctl/config/models.py` — Added: EventBusConfig frozen Pydantic model
- `src/ztlctl/config/settings.py` — Added: EventBusConfig import + ZtlSettings.eventbus field
- `src/ztlctl/plugins/event_bus.py` — Refactored: optional config param, _per_future_timeout/_shutdown_timeout/_dead_letter_retention_days fields, _wait_futures timeout param, shutdown timeout param
- `src/ztlctl/infrastructure/vault.py` — Updated: EventBus construction passes config, Vault.close() accepts timeout param
- `tests/domain/test_events.py` — New: 11 tests for ActionEvent validation, defaults, frozen, side_effect, JSON serialization
- `tests/config/test_models.py` — Appended: 9 tests for EventBusConfig defaults, overrides, frozen, ZtlSettings.eventbus TOML wiring
- `tests/plugins/test_event_bus.py` — Appended: 6 tests for config wiring, configurable timeout behavior

## Decisions Made

- **EventBus config parameter is optional** — `config: EventBusConfig | None = None` preserves backward compatibility with existing tests that pass `max_retries` as a kwarg. When `config` is provided it takes precedence; when `None`, legacy defaults apply.
- **ActionEvent.result: Any = None** — carries the full ServiceResult for plugins that need it, without coupling domain layer to services.
- **shutdown_timeout_seconds stored** — available for future graceful shutdown logic (Plan 16) without another refactor.
- **dead_letter_retention_days stored** — ready for dead-letter cleanup logic (Plan 15-03).

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

- `--timeout=30` pytest flag was not recognized (pytest-timeout not installed). Ran tests without the flag — no impact on test results.

## Next Phase Readiness

- Plan 15-02 (emission/drain) can now import `ActionEvent` from `domain/events.py` and use `EventBusConfig` for its tests
- Plan 15-03 (dead-letter) can use `self._dead_letter_retention_days` already stored on EventBus
- All contracts defined by this plan are in place for dependent plans

## Self-Check: PASSED

- FOUND: `src/ztlctl/domain/events.py`
- FOUND: `src/ztlctl/config/models.py` (with EventBusConfig)
- FOUND: `tests/domain/test_events.py`
- FOUND: commit `9bf04f5` (feat: EventBusConfig, ActionEvent models)
- FOUND: commit `e7c7d0f` (refactor: EventBus config parameter)
- All 45 targeted tests pass (13 config/test_models, 11 domain/test_events, 21 plugins/test_event_bus)
- Full suite: 1844 passed, 2 skipped, 0 failures

---
*Phase: 15-event-model-hardening*
*Completed: 2026-03-21*
