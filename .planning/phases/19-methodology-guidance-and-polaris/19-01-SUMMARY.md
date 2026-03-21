---
phase: 19-methodology-guidance-and-polaris
plan: "01"
subsystem: polaris-layer
tags: [polaris, init, mcp, context-assembly, priorities]
dependency_graph:
  requires: []
  provides: [polaris-template, polaris-mcp-resource, polaris-context-layer]
  affects: [init, mcp/resources, services/context, services/contracts]
tech_stack:
  added: []
  patterns: [jinja2-template, mcp-resource-impl, token-budgeted-layer]
key_files:
  created:
    - src/ztlctl/templates/self/polaris.md.j2
    - tests/services/test_context.py
  modified:
    - src/ztlctl/services/init.py
    - src/ztlctl/mcp/resources.py
    - src/ztlctl/services/context.py
    - src/ztlctl/services/contracts.py
    - tests/services/test_init.py
    - tests/mcp/test_resources.py
decisions:
  - "polaris scaffolded for all profiles (core + obsidian) — it is vault-level, not profile-specific"
  - "AgentContextLayers.polaris: str | None added to Pydantic contract between log_entries and topic_content"
  - "test_none_client_no_obsidian_dir updated: garden/ now always exists due to polaris scaffolding"
metrics:
  duration_seconds: 268
  completed: "2026-03-21"
  tasks_completed: 2
  files_modified: 8
---

# Phase 19 Plan 01: Polaris Layer Summary

Polaris priorities template, vault init scaffolding, MCP resource, and ContextAssembler Layer 1 integration with 500-token budget.

## What Was Built

**Task 1 — Template + Init + MCP resource:**

- Created `src/ztlctl/templates/self/polaris.md.j2` — Jinja2 template with frontmatter and three sections: Mission, Current Priorities (numbered 1-3), Decision Principles (3 bullets). Research-partner tone.
- Modified `init_vault` in `services/init.py` (step 5b): renders polaris template and writes `garden/groves/polaris.md` for all vault profiles.
- Modified `mcp/resources.py`: added `polaris_impl` function (file-read with guidance fallback) and registered `ztlctl://polaris` resource. Updated `_RESOURCE_CATALOG` from 17 to 18 entries.

**Task 2 — ContextAssembler Layer 1:**

- Modified `services/context.py` Layer 1 block: reads `garden/groves/polaris.md`, truncates to 500-token budget (~2000 chars) with `[... polaris truncated ...]` marker, sets `layers["polaris"] = None` when file absent.
- Modified `services/contracts.py`: added `polaris: str | None = None` field to `AgentContextLayers` Pydantic model.
- Created `tests/services/test_context.py` with 4 polaris-specific tests covering: present/absent file, token truncation, token counting.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed test_none_client_no_obsidian_dir conflicting assertion**
- **Found during:** Task 1 GREEN phase
- **Issue:** Pre-existing test asserted `assert not (tmp_path / "garden").exists()` for core profile, but polaris scaffolding now creates `garden/groves/` for all profiles.
- **Fix:** Updated assertion to verify polaris file is present instead of asserting garden absence.
- **Files modified:** `tests/services/test_init.py`
- **Commit:** cd72d4c

**2. [Rule 2 - Contract] Added polaris field to AgentContextLayers**
- **Found during:** Task 2 GREEN phase — `dump_validated(AgentContextResultData, ...)` would strip the polaris key from layers since the Pydantic model didn't define it.
- **Fix:** Added `polaris: str | None = None` to `AgentContextLayers` in `services/contracts.py`.
- **Files modified:** `src/ztlctl/services/contracts.py`
- **Commit:** 2a7d4b1

### Out-of-Scope Discovery

`tests/mcp/test_resources.py` was modified by a parallel executor adding `TestGardenBacklogTitleCandidates` tests for METH-03 (garden_backlog title quality). These tests currently fail because METH-03 implementation is incomplete. This is deferred to the plan that implements METH-03.

## Commits

| Task | Commit | Message |
|------|--------|---------|
| 1 | cd72d4c | feat(19-01): polaris template, init scaffolding, and MCP resource |
| 2 | 2a7d4b1 | feat(19-01): add polaris to ContextAssembler Layer 1 with 500-token budget |

## Verification

- `uv run pytest tests/services/test_init.py tests/mcp/test_resources.py tests/services/test_context.py -x -q` → 110 passed
- `uv run ruff check src/ztlctl/services/init.py src/ztlctl/mcp/resources.py src/ztlctl/services/context.py` → clean
- `uv run mypy src/ztlctl/services/init.py src/ztlctl/mcp/resources.py src/ztlctl/services/context.py` → clean

## Known Stubs

None — polaris is wired end-to-end: template → init scaffolding → MCP resource → context assembly.

## Self-Check: PASSED
