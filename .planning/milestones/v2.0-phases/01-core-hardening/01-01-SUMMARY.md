---
phase: 01-core-hardening
plan: "01"
subsystem: domain
tags: [python, dataclass, registry, type-system, lifecycle, tdd]

requires: []
provides:
  - NoteTypeDefinition frozen dataclass with 9 fields as the canonical type descriptor
  - NoteTypeRegistry with register/get/list_types and transition integrity validation
  - 9 built-in type registrations (note, knowledge, decision, reference, article, tool, spec, task, log)
  - get_note_type_registry() public accessor for the module-level singleton
affects:
  - 02-action-registry
  - 03-service-hardening
  - 04-cli-mcp-consolidation

tech-stack:
  added: []
  patterns:
    - "Frozen dataclass as immutable type descriptor (NoteTypeDefinition)"
    - "Module-level singleton with _register_builtins() called at import time"
    - "Registry validates constraints on registration (not at construction)"

key-files:
  created:
    - src/ztlctl/domain/registry.py
    - tests/domain/test_registry.py
  modified: []

key-decisions:
  - "NoteTypeDefinition lives in domain/ (no infrastructure imports) per 6-layer architecture rules"
  - "log type uses base ContentModel since no LogModel class exists (sessions are DB-only)"
  - "Transition validation enforces all target states must be map keys (no orphaned states)"
  - "Subtypes inherit parent transitions by value — no runtime indirection needed"

patterns-established:
  - "NoteTypeDefinition: single source of truth for type metadata, transitions, and template"
  - "NoteTypeRegistry: register-validate-store pattern with descriptive ValueError messages"

requirements-completed: [HARD-02, HARD-09]

duration: 3min
completed: "2026-03-19"
---

# Phase 01 Plan 01: NoteTypeDefinition and NoteTypeRegistry Summary

**Frozen NoteTypeDefinition dataclass + NoteTypeRegistry singleton with 9 built-in types (note, knowledge, decision, reference, article, tool, spec, task, log) as the extensible type primitive for Phase 2 ActionRegistry**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-19T20:15:47Z
- **Completed:** 2026-03-19T20:18:31Z
- **Tasks:** 1 (TDD: 2 commits — test RED + feat GREEN)
- **Files modified:** 2

## Accomplishments

- `NoteTypeDefinition` frozen dataclass with all 9 fields including embedded transition maps, template names, required sections, and is_subtype/parent_type for subtype relationships
- `NoteTypeRegistry` with `register()` (validates duplicate names, subtype parent, transition integrity), `get()`, and `list_types(content_type=...)` filter
- All 9 built-in types registered at import: note, knowledge, decision, reference, article, tool, spec, task, log — covering all 4 content types and 5 subtypes
- 23 tests passing, mypy strict clean, ruff clean, full 1506-test suite green (no regressions)

## Task Commits

TDD cycle — two atomic commits:

1. **Task 1 RED: Failing tests** - `95a582a` (test)
2. **Task 1 GREEN: Implementation** - `0bbf064` (feat)

## Files Created/Modified

- `src/ztlctl/domain/registry.py` — NoteTypeDefinition dataclass, NoteTypeRegistry class, _register_builtins(), get_note_type_registry() singleton accessor
- `tests/domain/test_registry.py` — 23 tests covering all fields, validation errors, all 9 built-in types, filtering, and custom plugin registration

## Decisions Made

- `NoteTypeDefinition` lives in `domain/` (no infrastructure imports) — follows 6-layer architecture rules; template paths are strings resolved by services at runtime
- `log` type uses base `ContentModel` since no `LogModel` class exists (sessions are DB-only)
- `_validate_transitions()` enforces that all target states in transition lists also appear as keys — prevents orphaned states that could never be exited
- Subtypes (knowledge, article, tool, spec) inherit parent transition maps by value, not by reference — keeps definitions self-contained

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- `get_note_type_registry()` is ready for Phase 2 ActionRegistry to consume
- Plugin authors can register custom `NoteTypeDefinition` entries via `get_note_type_registry().register()`
- All 9 built-in type descriptors are stable and tested

---
*Phase: 01-core-hardening*
*Completed: 2026-03-19*
