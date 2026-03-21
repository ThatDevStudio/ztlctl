---
phase: 10-user-guide-content
plan: "03"
subsystem: documentation
tags: [docs, agentic-workflows, recipes, session-lifecycle, llms-full]
dependency_graph:
  requires: [10-02]
  provides: [UGDE-04, UGDE-05]
  affects: [docs/agentic-workflows.md, docs/llms-full.txt]
tech_stack:
  added: []
  patterns: [recipe-walkthrough, session-lifecycle-documentation]
key_files:
  created: []
  modified:
    - docs/agentic-workflows.md
    - docs/llms-full.txt
decisions:
  - "Recipe walkthroughs inserted after MCP Server Integration section and before Batch Operations — preserves logical flow from MCP concepts to concrete usage patterns"
  - "Session Lifecycle section placed between Recipe Walkthroughs and Batch Operations — sessions tie recipes together, natural transition"
  - "Session close pipeline arrow notation uses ASCII -> (not Unicode arrows) to ensure safe rendering in all terminals and the llms-full.txt agent corpus"
metrics:
  duration: "~3 min"
  completed: "2026-03-20"
  tasks_completed: 2
  files_modified: 2
requirements:
  - UGDE-04
  - UGDE-05
---

# Phase 10 Plan 03: Agentic Workflows Expansion Summary

**One-liner:** Expanded agentic-workflows.md from 192 to 485 lines with three MCP recipe walkthroughs (research-capture, review-triage, knowledge-synthesis) and session lifecycle guides (human-driven, agent-driven, 5-step close enrichment pipeline), then regenerated llms-full.txt to include plugins.md content.

## What Was Built

### Task 1: Expanded docs/agentic-workflows.md

Added three new top-level sections to the existing 192-line file — all original content preserved verbatim:

**## Recipe Walkthroughs** (after MCP Server Integration, before Batch Operations):
- Intro explaining recipe access via `ztlctl://recipes` MCP resource URI
- Recipe 1: Research Capture — steps table, human CLI walkthrough with expected output, agent MCP sequence
- Recipe 2: Review Triage — steps table, human CLI walkthrough, agent MCP sequence
- Recipe 3: Knowledge Synthesis — steps table, human CLI walkthrough, agent MCP sequence
- Each recipe cross-references `ztlctl://recipes/research-capture`, `ztlctl://recipes/review-triage`, `ztlctl://recipes/knowledge-synthesis`

**## Session Lifecycle** (after Recipe Walkthroughs, before Batch Operations):
- Intro: sessions as operational coordination units
- Human-Driven Session: 30-minute research session example with `session start`, `ingest`, `create note`, `session log`, `session cost`, `session close` with expected output
- Agent-Driven Session: MCP tool call sequence for a literature review agent
- Session Close Enrichment Pipeline: all 5 steps explained (LOG CLOSE, CROSS-SESSION REWEAVE, ORPHAN SWEEP, INTEGRITY CHECK, GRAPH MATERIALIZATION), JSON close result with field definitions, ztlctl.toml config block

**## Next Steps** (at end of file):
- Cross-references to plugins.md, paradigms.md, concepts.md, mcp.md

Final line count: 485 lines (up from 192, target was 380+).

### Task 2: Regenerated docs/llms-full.txt

Ran `python3 scripts/gen_llms_full_txt.py` — no WARNING messages. Script picked up:
- `docs/plugins.md` (added in Plan 02) via the NAV_ORDER entry added in Plan 02
- Expanded `docs/agentic-workflows.md` with all new recipe and session content

Verified presence of: "Built-in Plugins", "batch_commits", "min_score_threshold", "Recipe Walkthroughs".

## Verification Results

```
wc -l docs/agentic-workflows.md  -> 485 lines
grep count (key markers)         -> 6 matches
mkdocs build --strict            -> exit 0
Built-in Plugins in llms-full.txt -> present
batch_commits in llms-full.txt    -> present
min_score_threshold in llms-full.txt -> present
```

## Deviations from Plan

None — plan executed exactly as written.

## Self-Check: PASSED

- docs/agentic-workflows.md: FOUND (485 lines)
- docs/llms-full.txt: FOUND (contains all expected strings)
- Task 1 commit 14dc6d2: FOUND
- Task 2 commit d91434d: FOUND
