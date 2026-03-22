---
phase: 29-mvp-skills
plan: "01"
subsystem: plugin/skills
tags: [skills, orient, capture, align, mcp, claude-code-plugin]
dependency_graph:
  requires: []
  provides:
    - plugin/skills/orient — vault orientation workflow skill
    - plugin/skills/capture — research capture workflow skill
    - plugin/skills/align — polaris alignment check workflow skill
  affects:
    - plugin/skills/ — three new skill directories added
tech_stack:
  added: []
  patterns:
    - SKILL.md frontmatter (name, description, version, disable-model-invocation)
    - Lean skill body (<200 lines) with progressive disclosure to references/
    - Unique action verb descriptions to prevent activation overlap
    - Read-only skills omit disable-model-invocation; write-side-effect skills include it
key_files:
  created:
    - plugin/skills/orient/SKILL.md
    - plugin/skills/orient/references/context-assembly.md
    - plugin/skills/capture/SKILL.md
    - plugin/skills/capture/references/capture-workflow.md
    - plugin/skills/align/SKILL.md
    - plugin/skills/align/references/polaris-workflow.md
  modified: []
decisions:
  - "orient and align have no disable-model-invocation: read-only, safe for auto-invocation"
  - "capture has disable-model-invocation: true due to ingest_source and create_note write side-effects"
  - "align is standalone: other skills mention polaris but do NOT invoke align (prevents skill-chaining cascades)"
  - "capture Iron Law: always search before creating; check result.success after every write"
metrics:
  duration: "3m 4s"
  completed_date: "2026-03-22"
  tasks_completed: 3
  tasks_total: 3
  files_created: 6
  files_modified: 0
---

# Phase 29 Plan 01: MVP Skills (Orient, Capture, Align) Summary

Three LOW-complexity Claude Code plugin skills that compose read-heavy MCP tool
sequences into guided vault orientation, research capture, and polaris alignment
workflows.

## What was built

### ztl:orient — Vault orientation

4-step workflow: read `ztlctl://self/identity` → read `ztlctl://polaris` →
call `agent_context(topic, budget=8000)` → report structured summary. Read-only,
safe for auto-invocation. No `disable-model-invocation`. References file documents
the 5-layer context payload (polaris, related notes, graph neighbors, session
history, methodology) and budget tuning (4k/8k/16k).

### ztl:capture — Research capture

5-step workflow: `search` (duplicate detection) → lightweight orientation →
`ingest_source` for external sources → `create_note` for synthesis → report.
Includes Iron Law ("always search before creating; check result.success after
every write") and Anti-Patterns section (no double-reweave, no generic tags).
Has `disable-model-invocation: true` due to write side-effects. References file
provides expanded content type decision tree and session integration guidance.

### ztl:align — Polaris alignment check

4-step workflow: read `ztlctl://polaris` → `check_alignment(decision)` →
present result (match/no-match) → optional decision note suggestion (never
auto-created). Read-only, safe for auto-invocation. Documents standalone design:
other skills do not chain into align. References file covers polaris document
structure, `check_alignment` response fields, and the decision audit trail
pattern.

## Skill catalog after this plan

| Skill | Lines | disable-model-invocation | Interaction | MCP calls |
|-------|-------|--------------------------|-------------|-----------|
| vault-methodology | 73 | no | Autonomous | Reference only |
| graph-intelligence | existing | no | Autonomous | Reference only |
| session-workflow | 73 | no | Autonomous | Reference only |
| orient | 55 | no | Autonomous | 3 reads |
| capture | 73 | yes | Autonomous + dup warning | 3-5 calls |
| align | 56 | no | Autonomous | 2-4 reads |

## Commits

| Task | Commit | Files |
|------|--------|-------|
| Task 1: ztl:orient | 6563c36 | plugin/skills/orient/SKILL.md, references/context-assembly.md |
| Task 2: ztl:capture | 7957384 | plugin/skills/capture/SKILL.md, references/capture-workflow.md |
| Task 3: ztl:align | 7bb5406 | plugin/skills/align/SKILL.md, references/polaris-workflow.md |

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None — all six files are complete. No placeholder text, no hardcoded empty
values, no "TODO" or "coming soon" content.

## Self-Check: PASSED

Files verified to exist:
- plugin/skills/orient/SKILL.md — FOUND (55 lines)
- plugin/skills/orient/references/context-assembly.md — FOUND
- plugin/skills/capture/SKILL.md — FOUND (73 lines)
- plugin/skills/capture/references/capture-workflow.md — FOUND
- plugin/skills/align/SKILL.md — FOUND (56 lines)
- plugin/skills/align/references/polaris-workflow.md — FOUND

Commits verified:
- 6563c36 — FOUND
- 7957384 — FOUND
- 7bb5406 — FOUND

Must-have truths verified:
- ztl:orient exists with identity, polaris, and agent_context — PASS
- ztl:capture exists with search, ingest_source, create_note — PASS
- ztl:align exists with polaris resource and check_alignment — PASS
- orient has no disable-model-invocation — PASS
- align has no disable-model-invocation — PASS
- capture has disable-model-invocation: true — PASS
- Descriptions use unique action verbs (orient/context vs capture/ingest vs align/priorities) — PASS
