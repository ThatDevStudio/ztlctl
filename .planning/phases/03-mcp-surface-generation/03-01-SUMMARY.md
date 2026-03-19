---
phase: 03-mcp-surface-generation
plan: 01
subsystem: mcp
tags: [mcp, generator, action-registry, refactor]
dependency_graph:
  requires: [02-04-SUMMARY.md]
  provides: [mcp/response.py, mcp/generator.py]
  affects: [mcp/server.py, mcp/resources.py, mcp/prompts.py, catalogs.py, manifest.json]
tech_stack:
  added: []
  patterns: [ActionRegistry-driven tool registration, Pydantic MCP response model, compatibility shim pattern]
key_files:
  created:
    - src/ztlctl/mcp/response.py
    - src/ztlctl/mcp/generator.py
    - tests/mcp/test_response.py
    - tests/mcp/test_generator.py
  modified:
    - src/ztlctl/mcp/server.py
    - src/ztlctl/catalogs.py
    - src/ztlctl/mcp/resources.py
    - src/ztlctl/mcp/prompts.py
    - src/ztlctl/templates/agent_workflow/manifest.json
    - tests/mcp/test_server.py
    - tests/mcp/test_prompts.py
    - tests/mcp/test_resources.py
    - tests/services/test_contracts.py
  deleted:
    - src/ztlctl/mcp/tools.py
    - tests/mcp/test_tools.py
    - tests/mcp/test_tools_impl.py
decisions:
  - "McpResponse.warnings is list[str] | None (not list[str]) so model_dump(exclude_none=True) omits empty warnings — matching old _to_mcp_response() behavior"
  - "tool_catalog() and common_error_recovery() added to generator.py as compatibility shims for resources.py, prompts.py, catalogs.py"
  - "manifest.json tool names updated to registry names (session_status->status, create_log->start, graph_themes->themes, etc.)"
  - "agent_reference_impl workflow_examples updated to use registry action names"
  - "test_resources.py updated to drop 'discovery'/'analysis' category assertions (not in new registry)"
metrics:
  duration: 15 min
  completed: 2026-03-19
  tasks: 2
  files: 16
---

# Phase 3 Plan 1: MCP Tool Generator Summary

Replace the hand-written 1499-line `mcp/tools.py` with ActionRegistry-driven tool auto-generation via `McpResponse` Pydantic model and `generate_tools()` in `mcp/generator.py`.

## What Was Built

### McpResponse model (`src/ztlctl/mcp/response.py`)
- `McpError(BaseModel)` and `McpResponse(BaseModel)` with `model_config = {"frozen": True}`
- `McpResponse.from_result(result)` converts any `ServiceResult` into a validated MCP response dict
- Explicitly drops `result.meta` (internal diagnostic data not intended for MCP consumers)
- `warnings: list[str] | None = None` — `None` when empty so `model_dump(exclude_none=True)` omits the key
- `COMMON_ERROR_RECOVERY` dict moved from `tools.py` to `response.py`

### MCP tool generator (`src/ztlctl/mcp/generator.py`)
- `generate_tools(server, vault)` iterates `get_action_registry().list_actions()` (59 actions) and registers each via `server.tool()(fn)`
- `_make_tool_fn(action, vault)` creates a wrapper function with correct `__name__`, `__doc__`, `__annotations__`, `__kwdefaults__`
- `_build_annotations(params)` maps ActionParam types to Python types — supports `Literal[...]` for choices, `list[Any]`, `dict[str, Any]`, union types
- `_render_action_doc(action)` builds rich docstrings with "What it does:", "When to use:", "Avoid when:", "Side effects:", "Args:", "Common errors:"
- `set_vault(vault)` / module-level `_vault_ref` pattern (not closure binding) per locked decision
- No top-level MCP package import (guarded)
- `_register_plugin_tools(server, vault)` compatibility shim for future plugin contributions
- `tool_catalog()` and `common_error_recovery()` compatibility shims for callers previously importing from `mcp/tools`

### server.py wired to generator
- Changed `from ztlctl.mcp.tools import register_tools` → `from ztlctl.mcp.generator import generate_tools`
- Changed `register_tools(server, vault)` → `generate_tools(server, vault)`

### tools.py deleted (1499 lines)
- 30 hand-written tool functions, `_TOOL_CATALOG`, `ToolCatalogEntry`, `register_tools()`, `_to_mcp_response()` all removed
- Coverage now via ActionRegistry + generator

### manifest.json updated
- All 25 tool name references updated from old catalog names to ActionRegistry names
- `session_status` → `status`, `create_log` → `start`, `session_close` → `close`, `graph_themes` → `themes`, etc.
- `garden_seed` and `ingest_source` replaced by `create_note` and `ingest_text` (no direct equivalents in registry)

## Test Coverage

| File | Tests | Purpose |
|------|-------|---------|
| tests/mcp/test_response.py | 5 | McpResponse.from_result() unit tests |
| tests/mcp/test_generator.py | 10 | Generator: count, annotations, DummyServer, doc, kwdefaults |
| tests/mcp/test_tools.py | DELETED | Replaced by test_generator.py |
| tests/mcp/test_tools_impl.py | DELETED | Replaced by controller unit tests |

Full suite: 1608 passed, 2 skipped.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] McpResponse.warnings type changed from list[str] to list[str] | None**
- **Found during:** Task 1 (GREEN phase)
- **Issue:** `model_dump(exclude_none=True)` doesn't exclude empty lists, causing `warnings: []` in output contrary to spec
- **Fix:** Changed field to `list[str] | None = None`; `from_result()` sets `None` when warnings is empty
- **Files modified:** `src/ztlctl/mcp/response.py`
- **Commit:** c4851aa

**2. [Rule 3 - Blocking] Multiple callers imported from deleted mcp/tools.py**
- **Found during:** Task 2 (deleting tools.py)
- **Issue:** `catalogs.py`, `resources.py`, `prompts.py`, `test_prompts.py`, `test_contracts.py` imported `tool_catalog`, `common_error_recovery`, `agent_context_impl`
- **Fix:** Added `tool_catalog()` and `common_error_recovery()` compatibility shims to `generator.py`; updated all callers; replaced `agent_context_impl` in test_contracts.py with direct QueryService calls
- **Files modified:** `generator.py`, `catalogs.py`, `resources.py`, `prompts.py`, `test_prompts.py`, `test_contracts.py`
- **Commit:** 0e8ba9f

**3. [Rule 1 - Bug] manifest.json tool names referenced old catalog names**
- **Found during:** Task 2 (running full test suite)
- **Issue:** `test_workflow_validate_passes_after_export` failed because `manifest.json` had old names (`session_status`, `graph_themes`, etc.) not present in new ActionRegistry
- **Fix:** Updated manifest.json to map all 25 tool references to new registry names
- **Files modified:** `src/ztlctl/templates/agent_workflow/manifest.json`
- **Commit:** 0e8ba9f

**4. [Rule 1 - Bug] agent_reference_impl workflow_examples used old tool names**
- **Found during:** Task 2 (test_resources.py failure)
- **Issue:** Hard-coded workflow examples in resources.py referenced `garden_seed`, `ingest_source`, `create_log`, `session_close`, `get_related`, `graph_gaps`, `graph_bridges`
- **Fix:** Updated all references to registry names; `garden_seed` → `create_note`, `ingest_source` → `ingest_text`, etc.
- **Files modified:** `src/ztlctl/mcp/resources.py`
- **Commit:** 0e8ba9f

**5. [Rule 1 - Bug] test_resources.py checked for 'discovery'/'analysis' categories**
- **Found during:** Task 2 (test_resources.py failure)
- **Issue:** Test expected `discovery` and `analysis` categories from old 30-tool catalog; new registry uses different category names
- **Fix:** Updated test to only assert categories that exist in the new registry (`creation`, `query`, `graph`, `session`, `lifecycle`)
- **Files modified:** `tests/mcp/test_resources.py`
- **Commit:** 0e8ba9f

## Self-Check: PASSED

All key files exist:
- FOUND: src/ztlctl/mcp/response.py
- FOUND: src/ztlctl/mcp/generator.py
- FOUND: tests/mcp/test_response.py
- FOUND: tests/mcp/test_generator.py
- CONFIRMED DELETED: src/ztlctl/mcp/tools.py

All task commits verified:
- FOUND: c4851aa (feat: McpResponse + generator)
- FOUND: 0e8ba9f (refactor: wire generator, delete tools.py)
