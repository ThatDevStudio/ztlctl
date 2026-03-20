---
phase: 04-cli-surface-generation
plan: 01
subsystem: actions
tags: [click, actiondefinition, cli-generator, actionparam, tdd]

requires:
  - phase: 03-mcp-surface-generation
    provides: mcp/generator.py pattern and ActionRegistry with all 59 ActionDefinitions
provides:
  - cli_name field on ActionDefinition for explicit CLI command name overrides
  - All 59 ActionDefinitions with correct cli_group and cli_name metadata
  - src/ztlctl/commands/generator.py with generate_commands, _make_command, _param_to_click, _derive_cli_name
  - Unit tests for all generator functions (31 tests)
affects:
  - 04-02 (CLI surface wiring - will call generate_commands to register auto-generated groups)

tech-stack:
  added: []
  patterns:
    - "cli_name override: explicit > group-prefix-strip > underscore-to-hyphen derivation"
    - "_param_to_click: ActionParam -> click.Argument | click.Option with full type mapping"
    - "_make_command: ZtlCommand factory with @click.pass_obj, cli_multiple tuple normalization, dict JSON parsing"
    - "generate_commands: lazily creates ZtlGroup per distinct cli_group, top-level for cli_group=None"

key-files:
  created:
    - src/ztlctl/commands/generator.py
    - tests/commands/test_generator.py
  modified:
    - src/ztlctl/actions/definitions.py
    - src/ztlctl/actions/_register_core.py
    - tests/actions/test_definitions.py

key-decisions:
  - "update action marked custom_presentation=True — keeps hand-written update.py which decomposes changes dict into individual flags"
  - "reweave/prune/undo grouped under cli_group='reweave' subgroup (new structure, not top-level standalone)"
  - "archive and supersede stay top-level (cli_group=None) to preserve existing CLI UX"
  - "cli_name positional-only param pattern for @click.pass_obj callbacks (mypy arg-type fix)"

patterns-established:
  - "TDD for CLI generator: write tests against expected behavior, then implement to pass"
  - "ActionParam -> click.Parameter: argument > flag > choices > multiple > dict(JSON) > typed option"
  - "Callback pattern: @click.pass_obj with positional-only app param (/) to satisfy mypy strict"

requirements-completed: [ACTN-04, ACTN-05]

duration: 9min
completed: 2026-03-19
---

# Phase 4 Plan 1: ActionDefinition CLI Metadata and Generator Summary

**ActionDefinition.cli_name field + all 59 registrations updated with CLI metadata + generator.py creating Click commands from ActionRegistry with full type mapping and TDD test coverage**

## Performance

- **Duration:** 9 min
- **Started:** 2026-03-19T23:59:10Z
- **Completed:** 2026-03-19T23:09:10Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments

- Added `cli_name: str | None = None` field to `ActionDefinition` frozen dataclass with backward compatibility
- Updated all 59 ActionDefinitions in `_register_core.py` with correct `cli_group` and `cli_name` values; `update` marked `custom_presentation=True`
- Built `src/ztlctl/commands/generator.py` mirroring `mcp/generator.py` with four exported functions: `generate_commands`, `_make_command`, `_param_to_click`, `_derive_cli_name`
- 31 unit tests in `tests/commands/test_generator.py` covering all ActionParam type mappings, name derivation, callback normalization, and group registration

## Task Commits

1. **Task 1: Add cli_name field and update all registrations** - `f92a137` (feat)
2. **Task 2: Build CLI command generator module with unit tests** - `78f20be` (feat)

## Files Created/Modified

- `src/ztlctl/actions/definitions.py` - Added `cli_name: str | None = None` field with docstring
- `src/ztlctl/actions/_register_core.py` - 53 explicit `cli_group=` assignments + 29 `cli_name=` overrides; `update` marked `custom_presentation=True`
- `tests/actions/test_definitions.py` - 4 new tests for `cli_name` field
- `src/ztlctl/commands/generator.py` - New: CLI command factory module
- `tests/commands/test_generator.py` - New: 31 unit tests for generator

## Decisions Made

- `update` action marked `custom_presentation=True` to skip auto-generation — the existing hand-written `update.py` decomposes the `changes` dict into individual `--title/--status/--tags` flags that the generic generator cannot replicate
- `reweave`, `prune`, `undo` grouped under `cli_group="reweave"` (as subcommands `run`, `prune`, `undo`) rather than keeping them as top-level standalone commands — more consistent structure
- `archive` and `supersede` kept as top-level (`cli_group=None`) to match existing CLI UX
- `@click.pass_obj` callback uses positional-only `app` parameter (`def callback(app, /, **kwargs)`) to satisfy mypy strict `arg-type` check

## Deviations from Plan

None - plan executed exactly as written. The one minor adaptation was fixing test invocation command names when `_derive_cli_name` strips group prefix (e.g., `"test_cmd"` with `cli_group="test"` derives to `"cmd"`, not `"test-cmd"`). Fixed by using `cli_name=` override in affected tests.

## Issues Encountered

- `@click.pass_obj` callback: mypy strict flagged `app` as named parameter; resolved by marking it positional-only with `/` syntax (Python 3.8+ positional-only syntax)
- Test callback assertions failed because `_derive_cli_name` correctly stripped group prefix in test helpers — fixed by using explicit `cli_name=` in tests requiring predictable command names

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- `generator.py` is fully functional and tested — ready for Plan 02 to wire `generate_commands()` into the main CLI entry point
- All 59 ActionDefinitions have correct CLI metadata for group registration
- Existing hand-written commands (`update`, `init_vault`, etc.) remain unaffected via `custom_presentation=True` gate
- 1657 total tests pass, mypy strict, ruff clean

---
*Phase: 04-cli-surface-generation*
*Completed: 2026-03-19*
