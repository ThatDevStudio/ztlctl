---
phase: 28-plugin-foundation
plan: "01"
subsystem: plugin
tags: [claude-code-plugin, mcp, hooks, bash, pytest]

requires: []
provides:
  - "Plugin manifest (plugin.json) with all 8 required fields validated by automated tests"
  - "MCP transport config (.mcp.json) with PYTHONUNBUFFERED=1 for clean stdio"
  - "PreToolUse vault gate hook (vault-gate.sh) blocking mcp__ztlctl__ calls when no vault found"
  - "hooks.json with both SessionStart and PreToolUse entries using ${CLAUDE_PLUGIN_ROOT} paths"
  - "tests/plugin/ package with 11 automated structure and behavior tests"
affects: [28-02, skills, agents, commands]

tech-stack:
  added: []
  patterns:
    - "vault-gate.sh: walk CWD upward checking for ztlctl.toml, exit 2 with guidance message on miss"
    - "PreToolUse hook matcher: mcp__ztlctl__ prefix scopes gate to ztlctl tools only"
    - "test_stdio_no_stdout_pollution: skips when mcp extra absent, active when installed"

key-files:
  created:
    - plugin/hooks/scripts/vault-gate.sh
    - tests/plugin/__init__.py
    - tests/plugin/test_plugin_structure.py
  modified:
    - plugin/.mcp.json
    - plugin/hooks/hooks.json

key-decisions:
  - "vault-gate.sh walks CWD upward (not just CWD) so vault detection works from any subdirectory of a project"
  - "test_stdio_no_stdout_pollution uses pytest.mark.skipif on mcp spec absence — consistent with tests/mcp/test_stdio_integration.py pattern"
  - "plugin.json required no changes — scaffold from prior work already matched the spec exactly"

patterns-established:
  - "Hook exit codes: exit 0 = allow, exit 2 = block (user-facing error to stderr), exit 1 = warning-only (never use for gates)"
  - "All hook commands use ${CLAUDE_PLUGIN_ROOT} — not $HOME, ~/,  or relative paths"
  - "No plugin file contains ../ path traversals — plugin is a self-contained filesystem artifact"

requirements-completed: [PLGN-01, PLGN-02, PLGN-03]

duration: 18min
completed: 2026-03-22
---

# Phase 28 Plan 01: Plugin Foundation Hardening Summary

**Plugin manifest, MCP stdio config (PYTHONUNBUFFERED=1), and vault-gate.sh PreToolUse hook hardened; 11 automated tests validate structure, behavior, and exit codes**

## Performance

- **Duration:** 18 min
- **Started:** 2026-03-22T00:00:00Z
- **Completed:** 2026-03-22T00:18:00Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments

- Added `PYTHONUNBUFFERED=1` to `plugin/.mcp.json` env block to prevent stdio transport buffering stalls (PLGN-02)
- Created `plugin/hooks/scripts/vault-gate.sh`: PreToolUse hook that walks CWD upward checking for `ztlctl.toml`, blocks with `exit 2` and a user-friendly `ztlctl init` guidance message when no vault found (PLGN-03)
- Added `PreToolUse` entry to `plugin/hooks/hooks.json` scoped to `mcp__ztlctl__` matcher, referencing vault-gate.sh via `${CLAUDE_PLUGIN_ROOT}` (PLGN-03)
- Created `tests/plugin/test_plugin_structure.py` with 11 tests covering directory structure, manifest fields, kebab-case naming, PYTHONUNBUFFERED, hook permissions, vault gate registration, vault gate behavioral exit codes, path traversal safety, and CLAUDE_PLUGIN_ROOT usage (PLGN-01, PLGN-02, PLGN-03)

## Task Commits

Each task was committed atomically:

1. **Task 1: Harden plugin manifest, MCP transport config, and vault gate hook** - `d5ac85f` (feat)
2. **Task 2: Create automated plugin structure and stdout cleanliness tests** - `200ec10` (test)

## Files Created/Modified

- `plugin/.mcp.json` - Added `"PYTHONUNBUFFERED": "1"` to env block
- `plugin/hooks/hooks.json` - Added PreToolUse section with mcp__ztlctl__ matcher and vault-gate.sh command
- `plugin/hooks/scripts/vault-gate.sh` - New PreToolUse hook script; CWD-upward vault detection, exit 2 with guidance on miss, exit 0 on hit
- `tests/plugin/__init__.py` - New empty package init
- `tests/plugin/test_plugin_structure.py` - New 11-test automated validation suite

## Decisions Made

- vault-gate.sh walks CWD upward (not just checks CWD) so the gate works correctly from any subdirectory within a vault project. This matches how ztlctl itself discovers `ztlctl.toml`.
- `test_stdio_no_stdout_pollution` uses `@pytest.mark.skipif` on mcp package absence, consistent with the existing `tests/mcp/test_stdio_integration.py` module-level skip pattern. The test is active when the mcp extra is installed and verifies clean JSON-only stdout.
- `plugin.json` was already complete and correct from the prior scaffold — no changes were needed.

## Deviations from Plan

None — plan executed exactly as written. The only minor adaptation was adding `@pytest.mark.skipif` to `test_stdio_no_stdout_pollution` instead of failing when the mcp extra is absent; this matches the established test pattern and is consistent with the plan's intent (validate when mcp is present).

## Issues Encountered

None.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- Plugin foundation (manifest, MCP transport, vault gate) is production-ready and validated by automated tests
- Phase 28-02 (skill authoring) can begin — the PreToolUse gate ensures skills never call MCP tools against an uninitialized vault
- Skills must declare `disable-model-invocation: true` for all write-operation workflows (per PITFALLS #20 and STATE.md constraints)
- Test suite will catch regressions to plugin structure as skills and commands are added in subsequent plans

---
*Phase: 28-plugin-foundation*
*Completed: 2026-03-22*
