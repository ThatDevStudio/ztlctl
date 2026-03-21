---
phase: 19-methodology-guidance-and-polaris
plan: "02"
subsystem: methodology-guidance
tags: [methodology, check-service, mcp-resources, tdd, title-quality]
dependency_graph:
  requires: []
  provides: [prose-as-title-guidance, title-quality-check, garden-backlog-candidates]
  affects: [check.py, resources.py, methodology.md.j2]
tech_stack:
  added: []
  patterns: [frozenset-module-constants, info-severity-advisory, lazy-local-imports]
key_files:
  created: []
  modified:
    - src/ztlctl/templates/self/methodology.md.j2
    - src/ztlctl/services/check.py
    - src/ztlctl/mcp/resources.py
    - tests/services/test_check.py
    - tests/mcp/test_resources.py
decisions:
  - "_GENERIC_TITLE_PATTERNS is a module-level frozenset (not method-local) for reuse and clarity"
  - "Title quality check fires for word_count <= 3 OR is_generic — both conditions qualify independently"
  - "garden_backlog_impl imports CheckService locally (lazy import matching existing pattern) to avoid circular dependency"
  - "Empty vault short-circuits with title_improvement_candidates: [] on failed vault_review"
metrics:
  duration_minutes: 3
  completed_date: "2026-03-21"
  tasks_completed: 2
  files_changed: 5
---

# Phase 19 Plan 02: Methodology Guidance and Title Quality Summary

Prose-as-title convention documented in methodology template, title quality advisory check added to CheckService at info severity, and title improvement candidates surfaced in the garden backlog MCP resource.

## What Was Built

### Task 1: Methodology template + title quality check

- Added `### Prose-as-Title Convention` section to `methodology.md.j2` inside the `research-partner` tone block, with a 4-row example table and guidance to aim for 4+ words
- Added `_GENERIC_TITLE_PATTERNS` frozenset at module level in `check.py` (near severity/category constants)
- Extended `_check_structural_validation` to select the `title` column and append `SEVERITY_INFO` issues for notes with `word_count <= 3` or titles matching generic patterns
- Added `TestTitleQualityCheck` class (8 tests): single-word, two-word, three-word, "Untitled", "New Note", descriptive (not flagged), hidden at `warning` severity, correct category/severity

### Task 2: Garden backlog resource with title improvement candidates

- Modified `garden_backlog_impl` to call `CheckService(vault).check(min_severity="info")` after aggregating stale seeds and orphans
- Filters issues for `CAT_STRUCTURAL + SEVERITY_INFO + "Title quality"` message pattern
- Returns `title_improvement_candidates` list (each entry: `{id, message}`) alongside existing `items` and `count`
- Added `TestGardenBacklogTitleCandidates` class (7 tests): key presence, type, empty vault, short title, generic title, descriptive (not flagged), existing fields preserved

## Decisions Made

| Decision | Rationale |
|----------|-----------|
| `_GENERIC_TITLE_PATTERNS` as module-level frozenset | Reusable across future callers; avoids re-creating set on every check call |
| `word_count <= 3` threshold | Captures 1-, 2-, 3-word titles; 4+ words required for descriptive prose |
| `SEVERITY_INFO` only (never blocks) | Title quality is advisory guidance, not a correctness requirement |
| Lazy local import of `CheckService` in `resources.py` | Matches the established pattern for all 6 service imports in `resources.py`; avoids circular imports |
| `"Title quality"` string sentinel in message filter | Stable discriminator that distinguishes title issues from other `CAT_STRUCTURAL/SEVERITY_INFO` issues (dead-letter events) |

## Deviations from Plan

None — plan executed exactly as written.

## Commits

| Task | Commit | Description |
|------|--------|-------------|
| 1 | f091703 | feat(19-02): add prose-as-title methodology section and title quality check |
| 2 | 373a40f | feat(19-02): surface title improvement candidates in garden backlog resource |

## Verification

- `uv run pytest tests/services/test_check.py tests/mcp/test_resources.py -x -q` — 109/109 passed
- `uv run ruff check src/ztlctl/services/check.py src/ztlctl/mcp/resources.py` — clean
- `uv run mypy src/ztlctl/services/check.py src/ztlctl/mcp/resources.py` — clean
- `grep "Prose-as-Title" src/ztlctl/templates/self/methodology.md.j2` — found
- `grep "your search index" src/ztlctl/templates/self/methodology.md.j2` — found
- `grep "GENERIC_TITLE_PATTERNS" src/ztlctl/services/check.py` — found
- `grep "Title quality" src/ztlctl/services/check.py` — found
- `grep "title_improvement_candidates" src/ztlctl/mcp/resources.py` — found

## Self-Check: PASSED
