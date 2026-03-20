---
phase: 07-plugin-agentic-wiring-fixes
plan: "01"
subsystem: plugins, mcp
tags: [plug-03, agnt-01, agnt-04, wiring, micro-fix]
dependency_graph:
  requires: []
  provides: [inject_configs-vault-wiring, mcp-error-detail-forwarding, advisory-category-docs]
  affects: [vault.init_event_bus, mcp.response.from_result, mcp.generator.category-state]
tech_stack:
  added: []
  patterns: [inject_configs-wiring, error-detail-forwarding, advisory-metadata-comment]
key_files:
  created: []
  modified:
    - src/ztlctl/infrastructure/vault.py
    - src/ztlctl/mcp/response.py
    - src/ztlctl/mcp/generator.py
    - .planning/REQUIREMENTS.md
    - tests/mcp/test_response.py
    - tests/plugins/test_plugin_config.py
decisions:
  - PLUG-03 wired via pm.inject_configs(self._settings) immediately after discover_and_load() and before built-in plugin registration
  - ACTION_REJECTED inserted alphabetically in COMMON_ERROR_RECOVERY between ACTIVE_SESSION_EXISTS and INVALID_TRANSITION
  - Advisory comment placed directly after _active_categories assignment for co-location with the code it documents
  - test_init_event_bus_calls_inject_configs uses patch.object on PluginManager.inject_configs to avoid full event bus startup
metrics:
  duration: 4
  completed_date: "2026-03-20"
  tasks_completed: 2
  files_modified: 6
---

# Phase 7 Plan 1: Plugin Agentic Wiring Fixes Summary

Wire plugin config injection into vault initialization, forward ServiceError.detail to McpError.detail in MCP responses, and document category activation as advisory-only metadata.

## What Was Built

Three single-line or comment-level micro-fixes that complete the wiring between fully-implemented components that were never connected in the production path:

1. **PLUG-03 (vault.py):** `pm.inject_configs(self._settings)` inserted into `init_event_bus()` after `discover_and_load()`. Third-party plugins loaded from entry points now receive validated TOML `[plugins.<name>]` config during vault initialization.

2. **AGNT-01 (response.py):** `detail=result.error.detail` added to the `McpError(...)` constructor in `from_result()`. `ACTION_REJECTED` entry added to `COMMON_ERROR_RECOVERY` with plugin rejection guidance. Full structured error detail from `ServiceError` is now surfaced to MCP consumers.

3. **AGNT-04 (generator.py + REQUIREMENTS.md):** Multi-line advisory comment added after `_active_categories` explaining that FastMCP does not support dynamic tool deregistration, so category activation is metadata for agent tool-selection decisions, not dynamic tool gating. REQUIREMENTS.md description updated to match.

## Tasks

| Task | Description | Commit |
|------|-------------|--------|
| 1 | Apply three micro-fixes (PLUG-03 + AGNT-01 + AGNT-04) | 243a9fb |
| 2 | Tests for micro-fixes (PLUG-03 + AGNT-01) | 0526e4d |

## Tests Added

- `test_from_result_forwards_error_detail`: verifies `ServiceError.detail` with data is forwarded to `McpError.detail`
- `test_from_result_forwards_empty_detail`: verifies default empty `detail={}` is forwarded correctly
- `test_action_rejected_in_common_error_recovery`: verifies `ACTION_REJECTED` entry exists and references "plugin"
- `test_init_event_bus_calls_inject_configs`: verifies `vault.init_event_bus()` calls `pm.inject_configs(settings)` with the vault settings instance

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing]: Updated REQUIREMENTS.md traceability table entries**
- **Found during:** Task 1
- **Issue:** AGNT-01 and AGNT-04 entries in the traceability table were still marked "Pending"; PLUG-03 checkbox was `[ ]` in both requirement list and table
- **Fix:** Marked PLUG-03, AGNT-01, AGNT-04 as `[x]` and "Complete" in traceability table
- **Files modified:** .planning/REQUIREMENTS.md
- **Commit:** 243a9fb

**2. [Rule 1 - Bug]: Fixed line-too-long in ACTION_REJECTED recovery string**
- **Found during:** Task 1 ruff check
- **Issue:** `ACTION_REJECTED` recovery string had 101-char line exceeding 100-char limit
- **Fix:** Rewrapped string to break at 100 chars
- **Files modified:** src/ztlctl/mcp/response.py
- **Commit:** 243a9fb

**3. [Rule 2 - Missing]: Added ACTION_REJECTED to test_all_codes_have_recovery set**
- **Found during:** Task 2
- **Issue:** The regression guard test `test_all_codes_have_recovery` would fail if ACTION_REJECTED was added to COMMON_ERROR_RECOVERY but not to the known-codes set
- **Fix:** Added "ACTION_REJECTED" to the `all_known_codes` set in the test
- **Files modified:** tests/mcp/test_response.py
- **Commit:** 0526e4d

## Self-Check: PASSED

All source files verified present. Both task commits (243a9fb, 0526e4d) verified in git history.
