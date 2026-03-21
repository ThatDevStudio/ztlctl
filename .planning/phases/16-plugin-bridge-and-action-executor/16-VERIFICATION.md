---
phase: 16-plugin-bridge-and-action-executor
verified: 2026-03-21T18:30:00Z
status: gaps_found
score: 7/8 must-haves verified
gaps:
  - truth: "DEBT-04 marked complete in REQUIREMENTS.md"
    status: failed
    reason: "REQUIREMENTS.md line 28 still shows '[ ] DEBT-04' (unchecked) and the traceability table at line 115 shows 'Pending'. The code fully implements DEBT-04 but the requirements document was not updated."
    artifacts:
      - path: ".planning/REQUIREMENTS.md"
        issue: "Line 28: '- [ ] **DEBT-04**' should be '- [x] **DEBT-04**'; line 115 traceability table shows 'Pending' instead of 'Complete'"
    missing:
      - "Update REQUIREMENTS.md: change '- [ ] **DEBT-04**' to '- [x] **DEBT-04**'"
      - "Update REQUIREMENTS.md traceability table: change DEBT-04 row from 'Pending' to 'Complete'"
---

# Phase 16: Plugin Bridge and Action Executor Verification Report

**Phase Goal:** The compatibility bridge is reversed so stable events drive legacy hooks, a generic action executor eliminates controller boilerplate, and MCP server shuts down cleanly
**Verified:** 2026-03-21T18:30:00Z
**Status:** gaps_found
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Per-event hooks (post_create, etc.) do NOT fire a second post_action — services own all post_action emission | VERIFIED | `_HOOK_TO_ACTION` dict and bridge block completely absent from event_bus.py (grep returns 0); docstring in `_execute_hook` explicitly states "Services own all post_action emission; no bridge is fired from here (ARCH-05)" |
| 2 | Legacy per-event hooks still fire for backward compatibility (just without the bridge to post_action) | VERIFIED | `test_per_event_hook_still_fires_normally` confirms post_create fires; `test_post_create_does_not_trigger_post_action` confirms post_action does not; test file has 5 tests in TestEventBusBridgeRemoved |
| 3 | BaseController._run_action encapsulates pre_action dispatch + rejection-to-ServiceResult in one method | VERIFIED | `_run_action` present at line 86 of base.py; accepts `action_name`, `kwargs`, `invoke: Callable`; returns SERVICE_REJECTED ServiceResult on rejection; calls `invoke(kwargs)` on success |
| 4 | When ztlctl serve exits, vault is closed and EventBus drains pending WAL events | VERIFIED | serve.py lines 50-53: `try: ctx.server.run(transport=transport) finally: ctx.vault.close(wait_for_events=True)` |
| 5 | vault.close(wait_for_events=True) runs even if server.run() raises SystemExit | VERIFIED | `test_vault_closed_on_system_exit` in tests/mcp/test_shutdown.py confirms this; Python's try/finally semantics guarantee it |
| 6 | create_server returns both the FastMCP server and the Vault (ServerContext) | VERIFIED | `ServerContext` dataclass defined in server.py lines 29-34; `create_server()` return type is `-> ServerContext`; returns `ServerContext(server=server, vault=vault)` at line 74 |
| 7 | Every controller method that had pre_action boilerplate now delegates to _run_action | VERIFIED | All 14 controllers show _run_action usage (check:4, create:4, discovery:3, export:4, graph:8, ingest:4, init_ctrl:3, query:10, reweave:3, session:9, update:3, upgrade:3, vector:2, workflow:4); grep for `_dispatch_pre_action` in .py controller files outside base.py returns 0 matches |
| 8 | garden seed is a registered ActionDefinition routing through CreateController, not CreateService directly | VERIFIED | `garden_seed` ActionDefinition in _register_core.py lines 273-318; handler: `lambda vault, **kw: CreateController(vault).create_note(kw["title"], ..., maturity="seed")`; cli_group="garden", cli_name="seed", side_effect="write", category="creation" |

**Score:** 7/8 truths verified (1 gap: DEBT-04 not marked complete in REQUIREMENTS.md)

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/ztlctl/plugins/event_bus.py` | Bridge code removed, `_HOOK_TO_ACTION` dict removed | VERIFIED | File exists, 320 lines, no `_HOOK_TO_ACTION` reference, `_execute_hook` docstring confirms ARCH-05 |
| `src/ztlctl/controllers/base.py` | `_run_action` utility method on BaseController | VERIFIED | File exists, 117 lines, `_run_action` at line 86 with full implementation |
| `src/ztlctl/mcp/server.py` | ServerContext dataclass returned from create_server | VERIFIED | File exists, 75 lines, `ServerContext` dataclass at line 29, `create_server()` returns `ServerContext` |
| `src/ztlctl/commands/serve.py` | try/finally block around server.run() calling vault.close() | VERIFIED | File exists, 53 lines, try/finally at lines 50-53 with `vault.close(wait_for_events=True)` |
| `src/ztlctl/controllers/create.py` | Controller methods using `_run_action` | VERIFIED | 4 occurrences of `_run_action` |
| `src/ztlctl/controllers/query.py` | Controller methods using `_run_action` | VERIFIED | 10 occurrences of `_run_action` |
| `src/ztlctl/actions/_register_core.py` | garden_seed ActionDefinition | VERIFIED | `garden_seed` registered at line 273 with all required fields |
| `src/ztlctl/commands/__init__.py` | No manual garden import | VERIFIED | grep for "garden" in __init__.py returns 0 matches |
| `src/ztlctl/commands/generator.py` | garden group help text in `_GROUP_HELP` | VERIFIED | Line 178: `"garden": "Cultivate knowledge with the garden persona."` |
| `src/ztlctl/commands/garden.py` | File deleted | VERIFIED | File does not exist (`test -f` returns non-zero) |
| `tests/plugins/test_event_bus_post_action_bridge.py` | Tests asserting bridge removal (TestEventBusBridgeRemoved) | VERIFIED | 5 tests including 3 `does_not_trigger_post_action` patterns |
| `tests/controllers/test_base.py` | Tests for `_run_action` | VERIFIED | 4 `test_run_action` tests |
| `tests/mcp/test_shutdown.py` | Tests for graceful shutdown | VERIFIED | 7 tests: 4 `test_vault_closed` variants plus 3 structure tests |
| `tests/actions/test_garden_seed_registration.py` | Tests for garden_seed registration | VERIFIED | 2 tests: registry presence and controller routing |
| `.planning/REQUIREMENTS.md` | DEBT-04 marked complete | FAILED | Line 28 shows `[ ]` (unchecked); traceability table line 115 shows "Pending" |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `event_bus.py` | `services/base.py _dispatch_post_action_event` | Services own all post_action dispatch; EventBus no longer bridges | VERIFIED | No `_HOOK_TO_ACTION` in event_bus.py (0 matches); `_execute_hook` dispatches per-event hooks directly without post_action bridge |
| `controllers/base.py` | `controllers/*.py` | `_run_action` available for all controller methods | VERIFIED | All 14 controllers import/call `self._run_action`; 63 total usages across the controller layer |
| `commands/serve.py` | `mcp/server.py` | ServerContext.server and ServerContext.vault | VERIFIED | `ctx = create_server(...)` then `ctx.server.run(...)` and `ctx.vault.close(...)` |
| `commands/serve.py` | `infrastructure/vault.py` | `vault.close(wait_for_events=True)` drains EventBus | VERIFIED | Line 53: `ctx.vault.close(wait_for_events=True)` — pattern `wait_for_events=True` confirmed |
| `actions/_register_core.py` | `controllers/create.py` | garden_seed handler calls CreateController.create_note | VERIFIED | Handler: `lambda vault, **kw: CreateController(vault).create_note(kw["title"], ..., maturity="seed")` |
| `commands/__init__.py` | `commands/generator.py` | generate_commands handles garden group automatically | VERIFIED | No `garden` import in `__init__.py`; `_GROUP_HELP["garden"]` present in generator.py |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| ARCH-05 | 16-01-PLAN.md | Compatibility bridge reversed — stable events adapt into legacy hooks | SATISFIED | `_HOOK_TO_ACTION` removed from event_bus.py; bridge block in `_execute_hook` removed; REQUIREMENTS.md line 16 shows `[x]` |
| ARCH-06 | 16-01-PLAN.md, 16-03-PLAN.md | Generic action executor replaces pre/post hook boilerplate in controllers | SATISFIED | `_run_action` on BaseController; all 14 controllers migrated (63 total method migrations); REQUIREMENTS.md line 17 shows `[x]` |
| ARCH-09 | 16-03-PLAN.md | Command surface convergence — garden seed is a first-class action | SATISFIED | `garden_seed` in ActionRegistry; cli_group="garden"; garden.py deleted; generator handles group; REQUIREMENTS.md line 20 shows `[x]` |
| DEBT-04 | 16-02-PLAN.md | MCP server graceful shutdown implemented | SATISFIED IN CODE, NOT IN DOCS | ServerContext + try/finally in serve.py verified; but REQUIREMENTS.md line 28 still shows `[ ]` (unchecked) and traceability table line 115 shows "Pending" |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `.planning/REQUIREMENTS.md` | 28, 115 | DEBT-04 checkbox unchecked and status "Pending" despite code completion | Warning | Requirements document does not accurately reflect delivered state; could mislead future planning |

No code-level anti-patterns (TODO, FIXME, stub returns, placeholder comments) found in any of the modified source files.

### Human Verification Required

None — all phase goals are verifiable programmatically.

### Gaps Summary

**One gap found:** REQUIREMENTS.md was not updated to reflect DEBT-04 completion after Plan 16-02 was executed.

The code fully implements DEBT-04:
- `ServerContext` dataclass exists in `src/ztlctl/mcp/server.py`
- `create_server()` returns `ServerContext(server=server, vault=vault)`
- `serve.py` wraps `server.run()` in try/finally calling `vault.close(wait_for_events=True)`
- 7 shutdown tests verify all exit paths

However, `.planning/REQUIREMENTS.md` has two inconsistencies:
1. Line 28: `- [ ] **DEBT-04**: MCP server graceful shutdown implemented` — checkbox not checked
2. Line 115 (traceability table): `| DEBT-04 | Phase 16 | Pending |` — status not updated to "Complete"

This is a documentation gap only — no code changes are required. The fix is two edits to REQUIREMENTS.md.

---

_Verified: 2026-03-21T18:30:00Z_
_Verifier: Claude (gsd-verifier)_
