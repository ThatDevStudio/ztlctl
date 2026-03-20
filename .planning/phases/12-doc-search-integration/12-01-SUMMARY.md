---
phase: 12-doc-search-integration
plan: "01"
subsystem: services
tags: [docs-search, tdd, pure-functions, stdlib]
dependency_graph:
  requires: []
  provides:
    - _docs_search_impl
    - _docs_index_impl
    - _resolve_docs_path
  affects:
    - src/ztlctl/services/docs.py
tech_stack:
  added: []
  patterns:
    - TypedDict for typed return dicts (DocResult, DocError)
    - Weighted term-frequency scoring with stdlib re
    - AND logic via per-term presence check before scoring
key_files:
  created:
    - src/ztlctl/services/docs.py
    - tests/services/test_docs.py
  modified: []
decisions:
  - TypedDict (DocResult, DocError) instead of bare dict — mypy strict requires typed dicts for sort key access
  - _check_and_logic() extracted as a separate helper for clarity and testability
  - DocError union in return type list[DocResult | DocError] — avoids Any, satisfies mypy invariance
metrics:
  duration_minutes: 3
  completed_date: "2026-03-20"
  tasks_completed: 2
  files_changed: 2
---

# Phase 12 Plan 01: Pure Documentation Search Module Summary

**One-liner:** Stdlib-only weighted TF scoring with AND logic, TypedDict returns, and env-overridable path resolution for docs corpus search.

## What Was Built

`src/ztlctl/services/docs.py` — a pure function module with no CLI or MCP coupling:

- `_resolve_docs_path()` — resolves docs/ via `ZTLCTL_DOCS_PATH` env var first, then package-relative `Path(__file__).parent.parent.parent.parent / "docs"` (works in editable install)
- `_docs_search_impl(query, limit=5, docs_path=None)` — searches docs corpus with weighted TF scoring; AND logic enforced (all query terms must appear); returns `list[DocResult | DocError]`
- `_docs_index_impl(docs_path=None)` — reads `docs/llms.txt` and returns its content as a string; returns error string on failure

Supporting helpers: `_score_page()`, `_check_and_logic()`, `_extract_excerpt()`, `_extract_title()`, `_collect_docs_files()`.

`tests/services/test_docs.py` — 23 tests across 3 test classes covering all specified behaviors.

## Tasks

| Task | Description | Commit | Status |
|------|-------------|--------|--------|
| RED | Write failing tests for all three functions | 699ce7d | Done |
| GREEN | Implement docs.py to make all tests pass | a64b34b | Done |

## Test Results

- 23/23 docs tests pass
- Full suite: 1804 passed, 2 skipped — no regressions
- `uv run mypy src/ztlctl/services/docs.py` — clean

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] TypedDict types required for mypy strict compliance**
- **Found during:** GREEN phase (mypy run)
- **Issue:** `list[dict]` return type fails `type-arg` check; `list[dict[str, object]]` fails sort key type check
- **Fix:** Introduced `DocResult` and `DocError` TypedDicts; return type `list[DocResult | DocError]`; inner candidates list typed as `list[DocResult | DocError]` to satisfy invariance; sort key uses conditional access with `# type: ignore[typeddict-item]`
- **Files modified:** `src/ztlctl/services/docs.py`
- **Commit:** a64b34b

**2. [Rule 1 - Style] Ruff E501 line too long in error message string**
- **Found during:** GREEN commit (pre-commit hook)
- **Issue:** Error message in `_docs_search_impl` exceeded 100-char line limit
- **Fix:** Shortened error message from "Set the ZTLCTL_DOCS_PATH environment variable to the path of your docs/ directory." to "Set ZTLCTL_DOCS_PATH to the path of your docs/ directory."
- **Files modified:** `src/ztlctl/services/docs.py`
- **Commit:** a64b34b

## Self-Check: PASSED

Files exist:
- src/ztlctl/services/docs.py — FOUND
- tests/services/test_docs.py — FOUND

Commits exist:
- 699ce7d — FOUND (test RED)
- a64b34b — FOUND (feat GREEN)
