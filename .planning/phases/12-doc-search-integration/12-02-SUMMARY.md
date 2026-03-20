---
phase: 12-doc-search-integration
plan: "02"
subsystem: cli-surface
tags: [docs, controller, cli, action-registry, custom-presentation]
dependency_graph:
  requires: [12-01]
  provides: [docs_search CLI command, DocsController, docs_search ActionDefinition]
  affects: [commands/__init__.py, actions/_register_core.py, mcp tool surface]
tech_stack:
  added: []
  patterns: [custom_presentation CLI command, lazy import controller pattern]
key_files:
  created:
    - src/ztlctl/controllers/docs.py
    - src/ztlctl/commands/docs.py
    - tests/controllers/test_docs_controller.py
  modified:
    - src/ztlctl/actions/_register_core.py
    - src/ztlctl/commands/__init__.py
    - tests/mcp/test_parity.py
decisions:
  - "DocsController.search() accepts docs_path kwarg for testability — not in ActionDefinition params (tests mock _resolve_docs_path instead)"
  - "docs_group exported as docs_group (not docs) to avoid shadowing stdlib/builtin names"
  - "test_parity.py category count updated from 14 to 15 — docs category is a new first-class category"
metrics:
  duration: 4 min
  completed: "2026-03-20"
  tasks_completed: 2
  files_modified: 6
---

# Phase 12 Plan 02: CLI Surface Wiring for Docs Search Summary

**One-liner:** `ztlctl docs search <query>` with `--limit`/`--json` flags via custom_presentation DocsController + ActionDefinition registered in MCP tool surface.

## What Was Built

### Task 1: DocsController and docs_group Click command

- `src/ztlctl/controllers/docs.py`: `DocsController.search(query, limit, docs_path)` wraps `_docs_search_impl`, never accesses vault methods. Returns `{"results": [...]}` dict.
- `src/ztlctl/commands/docs.py`: `docs_group` Click group with `search` subcommand. Supports `--limit` (default 5) and `--json` flags. Rich table output in default mode; `{"results": [...]}` JSON in `--json` mode. Handles error sentinel (no docs path) gracefully.
- `tests/controllers/test_docs_controller.py`: 9 TDD tests covering return structure, limit, AND logic, vault isolation (mock_vault accessed zero methods), and `_resolve_docs_path` delegation.

### Task 2: ActionDefinition registration and CLI wiring

- `src/ztlctl/actions/_register_core.py`: Added `docs_search` ActionDefinition with `custom_presentation=True`, `mcp_when_to_use`/`mcp_avoid_when` for MCP tool generation. DocsController lazy-imported (alphabetical order maintained).
- `src/ztlctl/commands/__init__.py`: `docs_group` added to `register_commands()` after `workflow` command.
- `tests/mcp/test_parity.py`: Updated `test_category_coverage` from 14 to 15 categories — auto-fix for test asserting wrong count after new `docs` category was added.

## Verification

- `ztlctl docs search "session"` — Rich table with Title/Score/Excerpt columns
- `ztlctl docs search "session" --json` — JSON `{"results": [...]}` to stdout
- `ztlctl docs search "session" --limit 2` — caps at 2 results
- `ztlctl docs search --help` — shows QUERY argument, `--limit`, `--json` options
- `docs_search` in ActionRegistry with `custom_presentation=True`
- 1821 tests pass, mypy strict clean, ruff clean

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] mypy errors in commands/docs.py for TypedDict union access**
- **Found during:** Task 1 GREEN phase
- **Issue:** Iterating `list[DocResult | DocError]` and accessing `DocResult`-only keys (`title`, `score`, `excerpt`) caused mypy to complain about missing keys on `DocError`.
- **Fix:** Added list comprehension `[r for r in results if "score" in r]` with explicit `list[DocResult]` annotation to narrow the union after the error guard.
- **Files modified:** `src/ztlctl/commands/docs.py`
- **Commit:** bf2dcec

**2. [Rule 1 - Bug] test_parity.py test_category_coverage hardcoded count**
- **Found during:** Task 2 full test run
- **Issue:** `test_category_coverage` asserted `len(categories) == 14` but registering `docs_search` with category `"docs"` added a 15th category.
- **Fix:** Updated assertion to `== 15` and updated docstring.
- **Files modified:** `tests/mcp/test_parity.py`
- **Commit:** 85f8794

## Self-Check: PASSED

- `src/ztlctl/controllers/docs.py` — FOUND
- `src/ztlctl/commands/docs.py` — FOUND
- `tests/controllers/test_docs_controller.py` — FOUND
- Commit `bf2dcec` (Task 1) — FOUND
- Commit `85f8794` (Task 2) — FOUND
