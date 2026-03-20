---
phase: 04-cli-surface-generation
verified: 2026-03-19T00:00:00Z
status: passed
score: 12/12 must-haves verified
re_verification: false
---

# Phase 4: CLI Surface Generation Verification Report

**Phase Goal:** CLI commands are auto-generated from the ActionRegistry, eliminating hand-crafted Click command duplication while preserving interactive and complex command behaviors
**Verified:** 2026-03-19
**Status:** passed
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths (Plan 01)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | ActionDefinition has a cli_name field for explicit CLI name override | VERIFIED | `cli_name: str | None = None` present at line 146 of `definitions.py` |
| 2 | Every ActionDefinition has a non-None cli_group assignment | VERIFIED | 54 explicit `cli_group=` assignments in `_register_core.py`; custom_presentation actions optionally omit it |
| 3 | update ActionDefinition is marked custom_presentation=True | VERIFIED | AST scan confirms `update` is one of 6 actions with `custom_presentation=True` |
| 4 | generator.py can create Click commands from ActionDefinitions | VERIFIED | `generate_commands`, `_make_command`, `_param_to_click`, `_derive_cli_name` all present and substantive |
| 5 | _param_to_click maps all ActionParam varieties (argument, flag, choice, multiple, dict, int, float, str) | VERIFIED | All 7 branches present in `generator.py` lines 50-108 |
| 6 | Generated callbacks call action.handler(app.vault, **kwargs) then app.emit(result) | VERIFIED | Lines 147-148 of `generator.py` confirm exact pattern |
| 7 | cli_multiple params are normalized from tuple to list or None in callbacks | VERIFIED | Lines 137-141 of `generator.py` confirm normalization logic |

### Observable Truths (Plan 02)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 8 | ztlctl --help shows command groups matching ActionRegistry cli_group values | VERIFIED | `register_commands()` calls `generate_commands(cli)` which creates ZtlGroups for each distinct cli_group; 13 hand-written files deleted |
| 9 | Generated CLI commands invoke action handlers and emit results identically to hand-written predecessors | VERIFIED | 1633 tests pass (including all command-layer tests); `_make_command` callback pattern verified |
| 10 | custom_presentation commands (create_batch, init wizard, serve, workflow, update, init_vault) still work via hand-written implementations | VERIFIED | `__init__.py` explicitly wires batch, update, garden, init_wizard_group, serve, workflow; 6 actions confirmed `custom_presentation=True` |
| 11 | Every non-custom_presentation ActionDefinition has a corresponding CLI command | VERIFIED | 12 parity tests pass including `test_all_non_custom_actions_have_cli_commands` |
| 12 | cli_command_catalog() returns a dynamic catalog derived from ActionRegistry | VERIFIED | `catalogs.py` calls `get_action_registry()` dynamically; static `_CLI_COMMAND_CATALOG` tuple absent (grep returns 0 matches) |

**Score:** 12/12 truths verified

---

## Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/ztlctl/actions/definitions.py` | cli_name field on ActionDefinition | VERIFIED | `cli_name: str | None = None` at line 146 with full docstring |
| `src/ztlctl/actions/_register_core.py` | All ActionDefinitions with cli_group and cli_name | VERIFIED | 54 `cli_group=` assignments, 37 `cli_name=` assignments, 6 `custom_presentation=True` |
| `src/ztlctl/commands/generator.py` | CLI command factory and group registration | VERIFIED | Exports `generate_commands`, `_make_command`, `_param_to_click`, `_derive_cli_name`; 215 lines, substantive |
| `tests/commands/test_generator.py` | Unit tests for generator | VERIFIED | 31 test functions confirmed |
| `src/ztlctl/commands/__init__.py` | Generator-driven command registration + custom command wiring | VERIFIED | `generate_commands(cli)` called; all 6 custom-presentation paths wired |
| `src/ztlctl/catalogs.py` | Dynamic CLI catalog from ActionRegistry | VERIFIED | `get_action_registry()` used; no static `_CLI_COMMAND_CATALOG` |
| `tests/commands/test_cli_parity.py` | CLI parity test suite | VERIFIED | 12 test functions confirmed |

### Deleted Hand-written Command Files (Expected Gone)

| File | Status |
|------|--------|
| `src/ztlctl/commands/query.py` | DELETED |
| `src/ztlctl/commands/graph.py` | DELETED |
| `src/ztlctl/commands/agent.py` | DELETED |
| `src/ztlctl/commands/archive.py` | DELETED |
| `src/ztlctl/commands/supersede.py` | DELETED |
| `src/ztlctl/commands/extract.py` | DELETED |
| `src/ztlctl/commands/reweave.py` | DELETED |
| `src/ztlctl/commands/check.py` | DELETED |
| `src/ztlctl/commands/upgrade.py` | DELETED |
| `src/ztlctl/commands/export.py` | DELETED |
| `src/ztlctl/commands/ingest.py` | DELETED |
| `src/ztlctl/commands/vector.py` | DELETED |
| `src/ztlctl/commands/session.py` | DELETED |

---

## Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `commands/generator.py` | `actions/registry.py` | `get_action_registry().list_actions(custom_presentation=False)` | WIRED | Line 201: `registry.list_actions(custom_presentation=False)` confirmed |
| `commands/generator.py` | `commands/_base.py` | `ZtlCommand` and `ZtlGroup` constructors | WIRED | 9 grep matches for ZtlCommand/ZtlGroup in generator.py |
| `commands/__init__.py` | `commands/generator.py` | `generate_commands(cli)` call | WIRED | Line 55: `generate_commands(cli)` confirmed |
| `commands/__init__.py` | `commands/create.py` | batch subcommand added to generated create group | WIRED | Lines 62-66: imports `batch`, adds to create_group |
| `catalogs.py` | `actions/registry.py` | Dynamic catalog derivation | WIRED | `get_action_registry()` called inside `cli_command_catalog()` |

---

## Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| ACTN-04 | 04-01, 04-02 | Auto-generated CLI commands from ActionDefinitions — replaces hand-crafted Click command files; handles interactive prompts, AppContext.emit(), exit codes, --verbose/--json flags, progressive disclosure | SATISFIED | `generator.py` creates commands from registry; all 13 hand-written files deleted; `app.emit(result)` in callback; 43 parity+generator tests pass |
| ACTN-05 | 04-01, 04-02 | Escape hatch preservation — batch operations, init wizard, serve command, and other complex commands retain hand-written implementations | SATISFIED | 6 actions with `custom_presentation=True` (create_batch, update, init_workflow, update_workflow, export_assets, init_vault); `__init__.py` explicitly wires all custom commands; create.py/update.py/garden.py/init_cmd.py/serve.py/workflow.py all exist |

No orphaned requirements found — all ACTN-04 and ACTN-05 mappings accounted for.

---

## Anti-Patterns Found

No blockers or significant anti-patterns detected.

Scan of `generator.py`, `commands/__init__.py`, `catalogs.py`, `actions/definitions.py`:
- No TODO/FIXME/HACK/PLACEHOLDER comments
- No empty implementations (`return null`, `return {}`, empty lambdas)
- No stub callbacks

---

## Human Verification Required

### 1. CLI Help Output Structure

**Test:** Run `uv run ztlctl --help` in a vault directory
**Expected:** Shows command groups (query, graph, session, create, check, ingest, export, vector, upgrade, reweave, init) plus standalone commands and custom ones (update, garden, serve, workflow)
**Why human:** Visual output verification; automated tests use CliRunner which may mask cosmetic issues

### 2. init Group Harvest-and-Reattach

**Test:** Run `uv run ztlctl init --help` and verify both the wizard subcommands (from init_cmd.py) and the generated subcommands (regenerate, staleness) appear
**Expected:** `init --help` shows the interactive wizard flags AND the regenerate/staleness subcommands
**Why human:** The harvest-and-reattach pattern for the init group is complex wiring that parity tests verify structurally but not visually

---

## Gaps Summary

No gaps found. All must-haves verified at all three levels (exists, substantive, wired).

Both requirement IDs (ACTN-04, ACTN-05) are fully satisfied:
- ACTN-04: The generator module creates Click commands from ActionRegistry, replaces 13 hand-written files, and uses `app.emit(result)` for consistent exit code and output handling
- ACTN-05: Six actions are protected by `custom_presentation=True`; hand-written files preserved for batch, update, garden, init wizard, serve, and workflow

Full test suite: **1633 passed, 2 skipped** — no regressions.

---

_Verified: 2026-03-19_
_Verifier: Claude (gsd-verifier)_
