---
phase: 30-differentiator-skills
plan: "01"
subsystem: plugin-skills
tags: [skills, synthesize, decision-support, orient-session, mcp, claude-code-plugin]
dependency_graph:
  requires: [29-mvp-skills/29-02-PLAN.md]
  provides:
    - plugin/skills/synthesize/SKILL.md
    - plugin/skills/synthesize/references/synthesis-workflow.md
    - plugin/skills/decision-support/SKILL.md
    - plugin/skills/decision-support/references/decision-workflow.md
    - plugin/skills/orient-session/SKILL.md
    - plugin/skills/orient-session/references/recall-workflow.md
  affects: [Claude Code plugin skill index, agent workflow orchestration]
tech_stack:
  added: []
  patterns:
    - "SKILL.md frontmatter: name, description, version, disable-model-invocation"
    - "Iron Laws pattern (1-2 critical invariants at top of skill)"
    - "Progressive disclosure: SKILL.md (55-80 lines) + references/ (supplementary detail)"
    - "Unique trigger verbs per skill to prevent overlap"
key_files:
  created:
    - plugin/skills/synthesize/SKILL.md
    - plugin/skills/synthesize/references/synthesis-workflow.md
    - plugin/skills/decision-support/SKILL.md
    - plugin/skills/decision-support/references/decision-workflow.md
    - plugin/skills/orient-session/SKILL.md
    - plugin/skills/orient-session/references/recall-workflow.md
  modified: []
decisions:
  - "All 3 differentiator skills have disable-model-invocation: true (all have write side-effects or session starts)"
  - "synthesize uses 7-step workflow with mandatory draft approval checkpoint before create_note"
  - "decision-support is read-only by default — optional decision note only on explicit user request"
  - "orient-session uses ' — continued' topic suffix for session lineage tracing"
  - "Reference files use bullet lists (not numbered steps) — numbered sequences belong in SKILL.md only"
metrics:
  duration: "3m 30s"
  completed_date: "2026-03-22"
  tasks_completed: 2
  files_created: 6
---

# Phase 30 Plan 01: Differentiator Skills (Synthesize, Decision-Support, Orient-Session) Summary

Three differentiator Claude Code plugin skills created: knowledge synthesis pipeline with draft approval gate, multi-source decision briefing assembler, and recall-driven session start that loads prior session context before opening a new session.

## What Was Built

### ztl:synthesize (SKIL-06)

7-step synthesis workflow: survey existing notes → find structural graph gaps → get comprehensive topic context → generate draft → present for user approval → create note → report. The mandatory checkpoint (step 5) ensures no synthesis note is ever auto-written without user review. Trigger verbs: "synthesize", "consolidate", "connect notes on X".

Key reference: `synthesis-workflow.md` documents `graph_gaps` isolation scores, `topic_packet` field structure across `mode="learn"` vs `mode="decision"`, draft payload format, checkpoint presentation pattern, and empty-result fallbacks.

### ztl:decision-support (SKIL-07)

6-step read-only briefing pipeline: aggregate decisions/tasks/refs → load decision-queue → load polaris → advisory alignment check → decision-mode topic packet → synthesize structured briefing. No vault writes by default; optional decision note only on explicit user request. Clearly distinguished from `ztl:align` (quick pass/fail vs comprehensive multi-source briefing). Trigger verbs: "help me decide", "evaluate options", "decision context".

Key reference: `decision-workflow.md` documents `decision_support` output fields, `ztlctl://decision-queue` two-section format, `mode="decision"` topic packet differences, briefing structure order, and decision audit trail pattern.

### ztl:orient-session (SKIL-08)

6-step recall-driven session start: scan recent sessions → topic recall query → fetch key notes from prior sessions → summarize prior context → confirmation checkpoint → `session_start` with " — continued" suffix. The " — continued" convention creates a queryable session lineage for future recall. Trigger verbs: "continue work on X", "resume research", "pick up where I left off".

Key reference: `recall-workflow.md` documents `ztlctl://sessions/recent` resource fields, `recall_topic` output format, note selection priority for `get_document` calls, the continuation naming convention, and empty-result handling paths.

## Style Conformance

All three SKILL.md files follow Phase 29 patterns exactly:
- Frontmatter with name, description, version, disable-model-invocation
- Iron Laws block (1-2 critical invariants) before the workflow
- Numbered workflow steps with bold tool name — em-dash — explanation
- "When NOT to use" or "Path detection" section
- Reference link at the bottom
- Line counts: synthesize (72), decision-support (71), orient-session (65) — all within 55-80 range

## Deviations from Plan

### Auto-fixed Issues

None — plan executed exactly as written.

### Notes

Reference files were 79-90 lines (plan specified "approximately 40-60"). The extra depth was required to fully document tool output formats, empty-result handling, and the continuation pattern — all of which are referenced by SKILL.md and needed for correct agent use. The plan's CONTEXT.md says "progressive disclosure via references/ subdirectory" with no hard line limit for reference files.

## Known Stubs

None — all skills are fully specified with complete workflows, Iron Laws, and reference links.

## Self-Check: PASSED

All 6 created files verified present on disk. Both task commits (5b37bdc, ab9cc5a) verified in git log.
