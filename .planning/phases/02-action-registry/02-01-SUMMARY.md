---
phase: 02-action-registry
plan: "01"
subsystem: actions
tags: [dataclasses, registry, frozen, singleton, actions]

# Dependency graph
requires: []
provides:
  - ActionParam frozen dataclass — 10-field parameter descriptor for CLI/MCP auto-generation
  - ActionDefinition frozen dataclass — 13-field operation descriptor (core, MCP, CLI, presentation metadata)
  - ActionRegistry class — register/get/list_actions with name-uniqueness enforcement
  - get_action_registry() — module-level singleton accessor
  - src/ztlctl/actions/ package with public __all__
affects:
  - 02-action-registry plans 2-4 (controllers, CLI adapter, MCP adapter)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Frozen dataclass pattern: @dataclass(frozen=True) for thread safety and hashability — mirrors NoteTypeDefinition in domain/registry.py"
    - "Module-level singleton: _REGISTRY = ActionRegistry() at bottom of registry.py, exposed via get_action_registry()"
    - "TDD Red-Green pattern: write failing tests, commit, then implement, then verify"

key-files:
  created:
    - src/ztlctl/actions/__init__.py
    - src/ztlctl/actions/definitions.py
    - src/ztlctl/actions/registry.py
    - tests/actions/__init__.py
    - tests/actions/test_definitions.py
    - tests/actions/test_registry.py
  modified: []

key-decisions:
  - "ActionParam.handler typed as Callable[..., Any] instead of Callable[..., ServiceResult] to avoid circular import — handler is runtime-safe"
  - "ActionRegistry list_actions() uses AND logic for combined filters — most selective default matches user intent"
  - "No built-in action registrations in plan 02-01 — controllers register their own definitions in plan 02-02"

patterns-established:
  - "actions/ package mirrors domain/ structure: definitions.py + registry.py + __init__.py re-exports"
  - "Test isolation: always use fresh ActionRegistry() instances in tests, never the singleton"
  - "Filter combinatorics: list_actions() supports category, side_effect, and custom_presentation independently"

requirements-completed:
  - ACTN-01
  - ACTN-02

# Metrics
duration: 3min
completed: "2026-03-19"
---

# Phase 2 Plan 01: Action Registry Foundation Summary

**ActionParam (10 fields) and ActionDefinition (13 fields) frozen dataclasses plus ActionRegistry with singleton, establishing the define-once action model foundation for auto-generated CLI and MCP surfaces**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-19T21:25:51Z
- **Completed:** 2026-03-19T21:28:51Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments

- ActionParam frozen dataclass with 10 fields covering all CLI/MCP/prompt metadata
- ActionDefinition frozen dataclass with 13 fields (core identity, MCP guidance, CLI metadata, presentation escape hatch)
- ActionRegistry with register/get/list_actions (name-uniqueness, multi-filter), module-level singleton via get_action_registry()
- 28 unit tests — all green, mypy strict clean, ruff clean

## Task Commits

Each task was committed atomically using TDD (RED then GREEN):

1. **Task 1: ActionParam + ActionDefinition (RED)** — `7b80241` (test)
2. **Task 1: ActionParam + ActionDefinition (GREEN)** — `718a545` (feat)
3. **Task 2: ActionRegistry (RED)** — `0e41ca2` (test)
4. **Task 2: ActionRegistry (GREEN)** — `6b2c5b0` (feat)

_Note: TDD tasks have separate test and feat commits (RED + GREEN)._

## Files Created/Modified

- `src/ztlctl/actions/__init__.py` — package root, re-exports all 4 public symbols
- `src/ztlctl/actions/definitions.py` — ActionParam and ActionDefinition frozen dataclasses
- `src/ztlctl/actions/registry.py` — ActionRegistry class with module-level singleton
- `tests/actions/__init__.py` — empty test package marker
- `tests/actions/test_definitions.py` — 18 tests for ActionParam and ActionDefinition
- `tests/actions/test_registry.py` — 10 tests for ActionRegistry and singleton

## Decisions Made

- `handler` field typed as `Callable[..., Any]` (not `Callable[..., ServiceResult]`) to avoid circular import — type is documented in docstring
- No built-in registrations in this plan; controllers register their own definitions in plan 02-02
- `list_actions()` multi-filter uses AND logic — most selective behavior matching expected usage

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

None — ruff auto-fixed import ordering (I001) and line length (E501) via pre-commit hooks on first commit attempt. No logic changes.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- actions/ package is importable; all 4 symbols available via `from ztlctl.actions import ...`
- Plan 02-02 can immediately import ActionParam, ActionDefinition, ActionRegistry to register controller methods
- Full test suite green (1597 passed, 2 skipped) — no regressions

---
*Phase: 02-action-registry*
*Completed: 2026-03-19*

## Self-Check: PASSED

- FOUND: src/ztlctl/actions/__init__.py
- FOUND: src/ztlctl/actions/definitions.py
- FOUND: src/ztlctl/actions/registry.py
- FOUND: tests/actions/test_definitions.py
- FOUND: tests/actions/test_registry.py
- FOUND commit: 7b80241 (test RED definitions)
- FOUND commit: 718a545 (feat GREEN definitions)
- FOUND commit: 0e41ca2 (test RED registry)
- FOUND commit: 6b2c5b0 (feat GREEN registry)
