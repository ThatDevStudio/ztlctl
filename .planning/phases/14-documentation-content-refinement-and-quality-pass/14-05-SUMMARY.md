---
phase: 14-documentation-content-refinement-and-quality-pass
plan: "05"
subsystem: docs
tags: [documentation, quality-pass, developer-guide, nav-wiring, llms-txt]
dependency_graph:
  requires: ["14-02", "14-03", "14-04"]
  provides: ["complete-docs-site", "agent-corpus-updated", "nav-wired"]
  affects: ["mkdocs.yml", "docs/llms.txt", "docs/llms-full.txt"]
tech_stack:
  added: []
  patterns: ["source-verified docs", "mkdocstrings auto-gen", "agent corpus regeneration"]
key_files:
  created: []
  modified:
    - docs/dev/index.md
    - docs/development.md
    - docs/plugin-guide.md
    - docs/api-reference.md
    - docs/mcp.md
    - mkdocs.yml
    - docs/llms.txt
    - scripts/gen_llms_full_txt.py
    - docs/llms-full.txt
decisions:
  - "17 MCP resources verified from resources.py (docs had 11) — updated to full list"
  - "9 MCP prompts verified from prompts.py — count added to mcp.md"
  - "plugin-guide.md deprecated section upgraded to !!! warning admonition for visibility"
  - "ZtlctlHookSpec class name added to hookspec reference intro (source-verified)"
metrics:
  duration_minutes: 10
  completed_date: "2026-03-20"
  tasks_completed: 2
  files_modified: 9
---

# Phase 14 Plan 05: Developer-Guide Quality Pass and Nav Wiring Summary

**One-liner:** Source-verified Developer Guide pages (hookspecs, ActionRegistry, MCP resources/prompts) + best-practices.md and agents.md wired into mkdocs.yml nav, llms.txt, gen script, and regenerated llms-full.txt.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Enhance Developer Guide pages | be2bdaf | docs/dev/index.md, docs/development.md, docs/plugin-guide.md, docs/api-reference.md, docs/mcp.md |
| 2 | Wire new pages into mkdocs.yml, llms.txt, gen script, regenerate llms-full.txt | 4c5ba0d | mkdocs.yml, docs/llms.txt, scripts/gen_llms_full_txt.py, docs/llms-full.txt |

## What Was Built

### Task 1: Developer Guide Pages Enhanced

**docs/dev/index.md** (12 → 13 lines): Added Agent System Manual row to the In This Guide table.

**docs/development.md** (154 → 160 lines): Added "Further Reading" section with cross-links to plugin-guide.md and api-reference.md. Architecture and Action Model sections were already source-verified from prior plans.

**docs/plugin-guide.md** (719 → 728 lines): Three targeted changes:
- ToC entry: "16 hookspecs" → "16 active hookspecs" (source: 25 total - 9 deprecated = 16 active)
- Hookspec Reference intro: added `ZtlctlHookSpec` class name and cross-link to api-reference.md
- Deprecated Per-Event Hooks section: upgraded to `!!! warning "Deprecated Hookspecs"` admonition with bulleted hook list

**docs/api-reference.md** (69 → 71 lines): Added intro paragraph explaining auto-generation and cross-link to plugin-guide.md for usage examples.

**docs/mcp.md** (105 → 149 lines): Three targeted changes:
- Resources table updated from 11 to all 17 resources (source-verified from resources.py)
- Prompts table annotated with count (9) source-verified from prompts.py
- Added concrete create_note tool call/response example
- Added Agent Integration section with cross-link to agents.md

### Task 2: Nav Wiring and Corpus Regeneration

**mkdocs.yml**: Added two nav entries — `Best Practices: best-practices.md` in User Guide section, `Agent System Manual: agents.md` in Developer Guide section. `mkdocs build --strict` passes with 0 errors and 0 warnings.

**docs/llms.txt**: Added Best Practices entry (after Troubleshooting) and Agent System Manual entry (after MCP Server) with full URLs.

**scripts/gen_llms_full_txt.py**: Added `best-practices.md` to User Guide NAV_ORDER and `agents.md` to Developer Guide NAV_ORDER (reformatted by ruff to stay within 100-char line limit).

**docs/llms-full.txt**: Regenerated — now includes content from best-practices.md and agents.md. File grew substantially (2244 insertions).

## Verification Results

```
mkdocs build --strict: PASSED (1.54s, no errors, no warnings)
grep "best-practices" mkdocs.yml: FOUND
grep "agents.md" mkdocs.yml: FOUND
grep "Best Practices" docs/llms-full.txt: FOUND
grep "Agent System Manual" docs/llms-full.txt: FOUND
total lines (5 dev guide pages): 1120 (>= 1080 threshold)
docs/development.md: 160 lines (>= 160 threshold)
docs/plugin-guide.md: 728 lines (>= 720 threshold)
docs/api-reference.md: 71 lines (>= 70 threshold)
docs/mcp.md: 149 lines (>= 110 threshold)
```

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] MCP resources table was incomplete**
- **Found during:** Task 1 (mcp.md source verification)
- **Issue:** docs/mcp.md listed 11 resources; resources.py defines 17 (includes recipe resources and docs/* resources added in Phases 12-13)
- **Fix:** Updated Available Resources table to list all 17 resources with accurate descriptions
- **Files modified:** docs/mcp.md
- **Commit:** be2bdaf

**2. [Rule 3 - Blocking] ruff E501 line-too-long in gen_llms_full_txt.py**
- **Found during:** Task 2 commit (pre-commit hook)
- **Issue:** New Developer Guide list exceeded 100-char line limit
- **Fix:** Pre-commit ruff-format hook auto-reformatted to multi-line list; re-staged and committed
- **Files modified:** scripts/gen_llms_full_txt.py
- **Commit:** 4c5ba0d

## Decisions Made

| Decision | Rationale |
|----------|-----------|
| Resources table updated from 11 to 17 | Source verification found 6 undocumented resources added in Phases 12-13 (recipes/* and docs/*) |
| Prompt count (9) added to mcp.md | Explicit count aids agents consuming the MCP docs for planning |
| !!! warning admonition over plain-text deprecated section | Higher visual prominence for breaking-change-adjacent information |

## Self-Check: PASSED

All files found. All commits verified.

| Check | Result |
|-------|--------|
| docs/development.md | FOUND |
| docs/plugin-guide.md | FOUND |
| docs/api-reference.md | FOUND |
| docs/mcp.md | FOUND |
| docs/dev/index.md | FOUND |
| docs/llms-full.txt | FOUND |
| commit be2bdaf | FOUND |
| commit 4c5ba0d | FOUND |
