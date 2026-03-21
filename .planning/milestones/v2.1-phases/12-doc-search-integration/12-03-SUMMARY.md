---
phase: 12-doc-search-integration
plan: "03"
subsystem: mcp
tags: [mcp, resources, docs, llms-txt, agent-tooling]

requires:
  - phase: 12-01
    provides: _docs_index_impl and _docs_search_impl in services/docs.py

provides:
  - docs_index_impl() in mcp/resources.py — exposes llms.txt content as ztlctl://docs/index resource
  - docs_search_resource_impl() in mcp/resources.py — returns agent guidance dict for docs_search tool
  - Two new entries in _RESOURCE_CATALOG (ztlctl://docs/index, ztlctl://docs/search)
  - Both resources registered in register_resources() via @server.resource decorators

affects: [mcp-server, agent-workflows, resource-catalog]

tech-stack:
  added: []
  patterns:
    - "Static MCP resource calling lazy-imported _impl from services/ (pattern consistent with all existing resources)"
    - "Vault-independent _impl functions: take _vault=None but don't use it, for pattern consistency"

key-files:
  created: []
  modified:
    - src/ztlctl/mcp/resources.py
    - tests/mcp/test_resources.py

key-decisions:
  - "docs_search resource is static guidance (not parameterized) — directs agents to use docs_search MCP tool for actual queries"
  - "docs_index_impl uses lazy import of _docs_index_impl from services/docs.py — consistent with six other cross-service lazy import precedents"

patterns-established:
  - "Vault-independent resource impl: take _vault=None for signature consistency even when not needed"

requirements-completed: [AGNT-04]

duration: 4min
completed: "2026-03-20"
---

# Phase 12 Plan 03: MCP Resources for Documentation Summary

**Two new MCP resources wired: ztlctl://docs/index serves llms.txt content and ztlctl://docs/search returns agent guidance directing to the docs_search tool**

## Performance

- **Duration:** ~4 min
- **Started:** 2026-03-20T20:05:08Z
- **Completed:** 2026-03-20T20:08:57Z
- **Tasks:** 1
- **Files modified:** 2

## Accomplishments

- Added `ztlctl://docs/index` and `ztlctl://docs/search` to `_RESOURCE_CATALOG` (catalog grows from 15 to 17 entries)
- Implemented `docs_index_impl()` as a vault-independent function that returns llms.txt content via lazy import of `_docs_index_impl` from `services/docs.py`
- Implemented `docs_search_resource_impl()` returning a guidance dict with `tool: "docs_search"` directing agents to the correct MCP tool for search
- Registered both resources in `register_resources()` before the plugin_manager section
- Added `TestDocsResources` class with 6 tests; updated catalog count assertion to 17

## Task Commits

1. **Task 1: Add docs_index_impl and docs_search_resource_impl to resources.py** - `5895ae9` (feat)

**Plan metadata:** (pending — final docs commit)

## Files Created/Modified

- `src/ztlctl/mcp/resources.py` - Added two catalog entries, two _impl functions, two resource registrations in register_resources()
- `tests/mcp/test_resources.py` - Updated catalog count to 17, added TestDocsResources class with 6 tests

## Decisions Made

- `ztlctl://docs/search` is a static guidance resource (not parameterized) because mcp>=1.0 in this codebase uses only static `@server.resource` decorators — actual search handled by `docs_search` MCP tool auto-generated from ActionDefinition in Plan 02
- `docs_index_impl` uses lazy import pattern (`from ztlctl.services.docs import _docs_index_impl` inside function body) consistent with all other cross-service imports in this codebase

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Phase 12 complete: docs search and index fully integrated (Plan 01: service layer, Plan 02: MCP tool, Plan 03: MCP resources)
- All three plans of phase 12-doc-search-integration are done
- Resource catalog now has 17 entries; agents can access llms.txt via ztlctl://docs/index and get search guidance via ztlctl://docs/search

## Self-Check: PASSED

- `src/ztlctl/mcp/resources.py` - FOUND
- `tests/mcp/test_resources.py` - FOUND
- Commit `5895ae9` - FOUND

---
*Phase: 12-doc-search-integration*
*Completed: 2026-03-20*
