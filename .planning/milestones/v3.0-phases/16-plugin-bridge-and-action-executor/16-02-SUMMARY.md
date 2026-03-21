---
phase: 16-plugin-bridge-and-action-executor
plan: "02"
subsystem: mcp
tags: [mcp, shutdown, lifecycle, vault, eventbus, debt]
dependency_graph:
  requires: []
  provides: [ServerContext, vault-graceful-shutdown]
  affects: [src/ztlctl/mcp/server.py, src/ztlctl/commands/serve.py]
tech_stack:
  added: []
  patterns: [ServerContext dataclass, try/finally lifecycle pattern]
key_files:
  created:
    - tests/mcp/test_shutdown.py
  modified:
    - src/ztlctl/mcp/server.py
    - src/ztlctl/commands/serve.py
key_decisions:
  - "ServerContext dataclass wraps server+vault — clean ownership without polluting FastMCP with private attributes"
  - "try/finally in serve command (not signal handlers) — FastMCP handles signals before returning, so finally always runs"
  - "vault.close(wait_for_events=True) drains EventBus WAL before DB engine closes"
metrics:
  duration_minutes: 8
  completed_date: "2026-03-21"
  tasks_completed: 2
  files_modified: 3
requirements_satisfied: [DEBT-04]
---

# Phase 16 Plan 02: MCP Graceful Shutdown Summary

MCP server now returns a `ServerContext(server, vault)` from `create_server()`, and `serve.py` wraps `server.run()` in try/finally calling `vault.close(wait_for_events=True)` — ensuring EventBus WAL drains and DB engine closes on every exit path.

## What Was Built

**ServerContext dataclass** (`src/ztlctl/mcp/server.py`):
- New `@dataclass class ServerContext` with `server: Any` and `vault: Any` fields
- `create_server()` return type changed from `-> Any` to `-> ServerContext`
- `ServerContext` added to `__all__` (sorted per ruff RUF022)

**Graceful shutdown** (`src/ztlctl/commands/serve.py`):
- `server = create_server(...)` replaced with `ctx = create_server(...)`
- `server.run(transport=transport)` wrapped in `try/finally`
- `finally` block calls `ctx.vault.close(wait_for_events=True)`

**Shutdown tests** (`tests/mcp/test_shutdown.py`):
- 7 tests across 2 test classes
- `TestServerContextStructure`: dataclass check, field names, construction
- `TestVaultClosedOnShutdown`: normal return, SystemExit, RuntimeError, call-count assertions

## Verification

- `uv run pytest tests/mcp/ -x -q` — 119 passed, 1 skipped
- `uv run ruff check src/ztlctl/mcp/server.py src/ztlctl/commands/serve.py` — clean
- `uv run mypy src/ztlctl/mcp/server.py src/ztlctl/commands/serve.py` — clean

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Ruff RUF022 — `__all__` not sorted**
- **Found during:** Task 2 verification
- **Issue:** `["create_server", "mcp_available", "ServerContext"]` is not isort-sorted
- **Fix:** Reordered to `["ServerContext", "create_server", "mcp_available"]`
- **Files modified:** `src/ztlctl/mcp/server.py`
- **Commit:** 7cc337b (bundled into Task 2 commit)

**2. [Rule 1 - Bug] `create_server` is a lazy local import in serve.py — not patchable at module level**
- **Found during:** Task 2 test writing
- **Issue:** `patch("ztlctl.commands.serve.create_server")` fails because the import is inside the function body
- **Fix:** Tests directly replicate the try/finally logic (testing the pattern, not the Click wiring) — this is the plan's suggested "Alternative" approach
- **Impact:** Tests verify the logical contract of the shutdown pattern without needing CliRunner indirection

## Commits

| Hash | Message |
|------|---------|
| 36eec6f | fix(mcp): add ServerContext and graceful shutdown via try/finally (DEBT-04) |
| 7cc337b | test(mcp): add shutdown tests for vault cleanup on normal exit, SystemExit, and RuntimeError (DEBT-04) |

## Known Stubs

None — all paths fully wired.

## Self-Check: PASSED
