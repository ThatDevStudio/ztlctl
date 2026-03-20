---
phase: 04-cli-surface-generation
plan: "02"
subsystem: cli
tags: [click, actionregistry, generator, parity, testing]

requires:
  - phase: 04-cli-surface-generation/04-01
    provides: "CLI generator (generate_commands), ActionDefinition CLI metadata, _derive_cli_name"

provides:
  - "Generator-driven CLI command registration replaces all hand-written command files"
  - "Dynamic CLI catalog (catalogs.py) derived from ActionRegistry"
  - "Custom-presentation escape hatches wired: batch, init wizard, update, garden, serve, workflow"
  - "CLI parity test suite (tests/commands/test_cli_parity.py) proving 1:1 ActionRegistry -> CLI mapping"
  - "Cross-surface test confirming CLI and MCP both derive from ActionRegistry single source of truth"
  - "vector_status ActionDefinition + VectorController.status() method"
  - "ActionParam.cli_name field for option name overrides (e.g. content_type -> --type)"
  - "ExportController accepts str|Path for output_dir; supports output_file for export_graph"

affects:
  - future-phases
  - mcp-surface
  - testing

tech-stack:
  added: []
  patterns:
    - "ActionParam.cli_name: override Click flag name while keeping Python kwarg name unchanged"
    - "cli_is_argument=True: positional Click args instead of options (output_dir, topic, query)"
    - "_make_export_filters(): lazy import helper returning Any to avoid circular import + mypy"
    - "_render_export content key: renderer detects 'content' key and prints raw to stdout for export_graph"
    - "Two-class parity test structure: TestCliParity (generated surface) + TestCustomCommandsWired (hand-written)"
    - "cli_with_generated_commands fixture: builds isolated Click.Group from generate_commands() without full CLI"

key-files:
  created:
    - tests/commands/test_cli_parity.py
  modified:
    - src/ztlctl/commands/__init__.py
    - src/ztlctl/actions/_register_core.py
    - src/ztlctl/actions/definitions.py
    - src/ztlctl/commands/generator.py
    - src/ztlctl/controllers/export.py
    - src/ztlctl/controllers/ingest.py
    - src/ztlctl/controllers/vector.py
    - src/ztlctl/output/renderers.py
    - tests/mcp/test_parity.py
    - tests/commands/test_export.py
    - tests/commands/test_ingest.py
    - tests/commands/test_graph.py
    - tests/commands/test_query.py
    - tests/commands/test_help.py
    - tests/commands/test_vector.py
    - tests/actions/test_core_registrations.py

key-decisions:
  - "ActionParam.cli_name field added to definitions.py: cleanly separates Python kwarg name from CLI flag name without duplicating ActionParam entries"
  - "cli_is_argument=True used for output_dir, topic, and query: positional args for high-frequency parameters improve UX"
  - "choices removed from export_dashboard viewer param: service layer normalizes 'vanilla' alias; CLI choices restriction was too strict"
  - "ExportController.export_graph output_file param added at controller level rather than in generator: keeps generator generic, logic stays in controller"
  - "_render_export content-key detection: graph export prints raw DOT/JSON to stdout enabling shell piping"
  - "Custom-presentation wiring preserved via register_commands() harvest-and-reattach pattern for init group subcommands"

patterns-established:
  - "cli_name on ActionParam: use when CLI flag name must differ from Python kwarg (e.g. content_type -> --type)"
  - "str|Path controller signatures: all controller methods accepting file paths accept both types, wrapping with Path() internally"
  - "Parity test fixture isolation: cli_with_generated_commands builds a standalone group, decoupled from full CLI"

requirements-completed: [ACTN-04, ACTN-05]

duration: ~90min
completed: 2026-03-19
---

# Phase 04 Plan 02: CLI Generator Wiring and Parity Tests Summary

**Generator-driven CLI registration replaces all hand-written command files, with full ActionRegistry <-> CLI parity enforced by a 12-test suite and cross-surface MCP+CLI coverage test**

## Performance

- **Duration:** ~90 min
- **Started:** 2026-03-19T00:00:00Z
- **Completed:** 2026-03-19
- **Tasks:** 2
- **Files modified:** 16

## Accomplishments

- Wired `generate_commands()` into `register_commands()` as the primary registration mechanism; deleted all hand-written command files (query, graph, session, check, ingest, export, vector, upgrade, reweave)
- All custom-presentation commands (batch, init wizard, update, garden, serve, workflow) preserved via explicit wiring with harvest-and-reattach pattern for init subcommands
- Added `tests/commands/test_cli_parity.py` with 12 tests: ActionRegistry <-> CLI 1:1 mapping, help text coverage, hyphen naming, group count, category coverage, and hand-written custom command wiring
- Extended `tests/mcp/test_parity.py` with cross-surface `test_cli_and_mcp_cover_same_actions()` proving single source of truth

## Task Commits

Each task was committed atomically:

1. **Task 1: Wire generator, delete hand-written files, migrate tests** - `dc83893` (feat)
2. **Task 2: Add CLI parity test suite and extend MCP parity** - `220d4a6` (test)

## Files Created/Modified

- `tests/commands/test_cli_parity.py` — New 12-test CLI parity suite (TestCliParity + TestCustomCommandsWired)
- `src/ztlctl/commands/__init__.py` — Wired generate_commands() + custom presentation commands
- `src/ztlctl/actions/_register_core.py` — Added cli_name overrides, choices constraints, vector_status action, _make_export_filters helper
- `src/ztlctl/actions/definitions.py` — Added cli_name field to ActionParam
- `src/ztlctl/commands/generator.py` — Updated _param_to_click() to use cli_name with dual param_decls
- `src/ztlctl/controllers/export.py` — str|Path for output_dir params; output_file support in export_graph
- `src/ztlctl/controllers/ingest.py` — str|Path for path param in ingest_file
- `src/ztlctl/controllers/vector.py` — Added VectorController.status() method
- `src/ztlctl/output/renderers.py` — _render_export detects "content" key and prints raw to stdout
- `tests/mcp/test_parity.py` — Cross-surface test + count updated to >= 60
- `tests/commands/test_export.py` — Updated to match generated CLI surface (positional args, --type, --format)
- `tests/commands/test_ingest.py` — Updated --as -> --target-type, removed --stdin usage
- `tests/commands/test_graph.py` — Fixed --type flag usage in seed helper
- `tests/commands/test_query.py` — Fixed sort choices, space choices validation, positional topic
- `tests/commands/test_help.py` — Updated --content-type -> --type, --fmt -> --format
- `tests/commands/test_vector.py` — vector status command now works

## Decisions Made

- **ActionParam.cli_name field**: Separates CLI flag name from Python kwarg name cleanly; avoids duplicating ActionParam entries or special-casing in generator. When `cli_name` is set, generator uses `param_decls=[option_name, p.name]` so Click maps `--type` to `content_type` kwarg transparently.
- **choices removed from export_dashboard viewer**: Service layer normalizes `vanilla` → `none` with a deprecation warning; having `choices` at the CLI level blocked the alias. Validation responsibility belongs to the service, not the CLI.
- **export_graph output_file at controller level**: Generator stays generic (just maps params to kwargs); writing to file is business logic that belongs in the controller.
- **_render_export content-key pattern**: Detecting the `"content"` key in ServiceResult.data allows export_graph to print raw DOT/JSON to stdout enabling shell piping without a separate code path.
- **Harvest-and-reattach for init group**: Generated `init` group contains `regenerate` and `staleness` subcommands; wizard group replaces it but must retain those subcommands. Pattern: collect subcommands before overwrite, re-attach after.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] ExportController and IngestController rejected str paths from CLI**
- **Found during:** Task 1 (wire generator, run test suite)
- **Issue:** Controllers typed `output_dir: Path` / `path: Path` but generator passes str values from Click; calling `.resolve()` on str raised AttributeError
- **Fix:** Changed signatures to `Path | str` and wrapped with `Path()` internally
- **Files modified:** src/ztlctl/controllers/export.py, src/ztlctl/controllers/ingest.py
- **Verification:** export and ingest tests pass
- **Committed in:** dc83893 (Task 1 commit)

**2. [Rule 2 - Missing Critical] vector_status action absent from registry**
- **Found during:** Task 1 (test_vector.py failing on `vector status` command)
- **Issue:** VectorController had no `status()` method; no corresponding ActionDefinition existed; CLI had no `vector status` command
- **Fix:** Added VectorController.status(), added vector_status ActionDefinition to _register_core.py
- **Files modified:** src/ztlctl/controllers/vector.py, src/ztlctl/actions/_register_core.py
- **Verification:** test_vector.py and parity tests pass; vector_status in registry count
- **Committed in:** dc83893 (Task 1 commit)

**3. [Rule 1 - Bug] export graph stdout not printing content**
- **Found during:** Task 1 (test_export.py export_graph_stdout test)
- **Issue:** _render_export did not handle ServiceResult containing "content" key; graph DOT/JSON was silently swallowed
- **Fix:** Added content-key detection in _render_export to print raw content to stdout
- **Files modified:** src/ztlctl/output/renderers.py
- **Verification:** export graph test verifying stdout content passes
- **Committed in:** dc83893 (Task 1 commit)

**4. [Rule 1 - Bug] --type / --format / --output options not recognized**
- **Found during:** Task 1 (multiple test failures)
- **Issue:** content_type param generated `--content-type` (not `--type`); fmt param generated `--fmt` (not `--format`); output_file param not in registry
- **Fix:** Added cli_name="type" to content_type params; cli_name="format" to fmt param; cli_name="output" to output_file param; added output_file ActionParam
- **Files modified:** src/ztlctl/actions/_register_core.py, src/ztlctl/actions/definitions.py, src/ztlctl/commands/generator.py
- **Verification:** test_help.py, test_export.py, test_query.py all pass
- **Committed in:** dc83893 (Task 1 commit)

**5. [Rule 1 - Bug] --space and --sort not validating choices**
- **Found during:** Task 1 (test_query.py test_search_invalid_space expecting failure but command succeeded)
- **Issue:** space params had no choices restriction; sort param missing priority, title, type choices
- **Fix:** Added choices=("notes", "ops", "self") to all 4 space params; choices=("recency", "title", "type", "priority") to sort param
- **Files modified:** src/ztlctl/actions/_register_core.py
- **Verification:** test_query.py invalid space/sort tests pass
- **Committed in:** dc83893 (Task 1 commit)

**6. [Rule 3 - Blocking] Runtime click import missing in commands/__init__.py**
- **Found during:** Task 1 (RuntimeError at line 63 - click not defined)
- **Issue:** click was only imported under TYPE_CHECKING; register_commands() used click.Group at runtime; ruff reordered code placing usage before the runtime import
- **Fix:** Moved `import click as _click` to top of register_commands() before first usage; changed all isinstance checks to use _click
- **Files modified:** src/ztlctl/commands/__init__.py
- **Verification:** Full test suite passes; no import errors
- **Committed in:** dc83893 (Task 1 commit)

---

**Total deviations:** 6 auto-fixed (3 Rule 1 bugs, 1 Rule 2 missing critical, 1 Rule 3 blocking, 1 Rule 1 bug)
**Impact on plan:** All auto-fixes were necessary for correctness and test parity. No scope creep — each fix directly unblocked the generator wiring migration.

## Issues Encountered

- The `init` group required a harvest-and-reattach pattern because the generator creates subcommands (regenerate, staleness) that must survive the overwrite with the wizard group. Solved by collecting subcommands before `cli.add_command(init_wizard_group)` and re-adding them afterward.
- mypy strict: `_make_export_filters` return type required `Any` annotation because `ExportFilters` is lazily imported inside the function body to avoid circular imports.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Phase 4 complete: ActionRegistry is the single source of truth for both CLI and MCP surfaces
- 1633 tests passing (2 skipped), mypy strict clean, ruff clean
- Any new action requires only one registration in _register_core.py to appear on both CLI and MCP
- Custom-presentation pattern documented and tested for future escape hatches

---
*Phase: 04-cli-surface-generation*
*Completed: 2026-03-19*
