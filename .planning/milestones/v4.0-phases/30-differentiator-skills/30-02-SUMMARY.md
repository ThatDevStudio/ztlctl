---
phase: 30-differentiator-skills
plan: "02"
subsystem: plugin-skills
tags: [claude-code-plugin, skills, zettelkasten, garden-health, contradictions, mcp]

requires:
  - phase: 29-mvp-skills
    provides: Phase 29 skill patterns (SKILL.md format, Iron Laws, reference file structure, batch confirmation)
  - phase: 30-01
    provides: synthesize, decision-support, orient-session skills (peer differentiator skills)

provides:
  - "ztl:garden-health skill — Fan-Out audit pattern composing vault_review + graph_gaps + graph_bridges + garden/backlog + review/dashboard"
  - "ztl:review-contradictions skill — Loop per-pair evaluation with never-auto-confirm Iron Law and sqlite-vec graceful degradation"
  - "garden-audit.md reference — tool output schemas, gap/bridge scoring, remediation options"
  - "contradiction-review.md reference — scoring interpretation, evaluation criteria, permanent edge semantics"

affects:
  - 30-differentiator-skills (completes phase with skills 9 and 10)
  - future skill additions (fan-out and loop patterns established)

tech-stack:
  added: []
  patterns:
    - "Fan-Out composition pattern: parallel reads → synthesize → checkpoint → conditional writes"
    - "Loop pattern with per-item checkpoint: enumerate → inspect → propose verdict → await approval → act"
    - "Graceful degradation documented in both SKILL.md and reference file (sqlite-vec)"
    - "Distinction section separating overlapping skills (garden-health vs review-triage)"

key-files:
  created:
    - plugin/skills/garden-health/SKILL.md
    - plugin/skills/garden-health/references/garden-audit.md
    - plugin/skills/review-contradictions/SKILL.md
    - plugin/skills/review-contradictions/references/contradiction-review.md

key-decisions:
  - "garden-health uses Fan-Out pattern (all reads before synthesis) — prevents leaking intermediate state into health report"
  - "review-contradictions uses Loop pattern with per-pair checkpoint — contradictions are permanent graph edges requiring human judgment"
  - "Never-auto-confirm is an Iron Law (not just a note) — contradictions insert bidirectional edges that corrupt future queries if false positive"
  - "sqlite-vec graceful degradation documented in both SKILL.md and contradiction-review.md reference — two discovery surfaces"
  - "Distinction section in garden-health explicitly differentiates from ztl:review-triage to guide routing on ambiguous triggers"

patterns-established:
  - "Fan-Out pattern: all analysis reads complete before synthesis step begins"
  - "Per-pair loop checkpoint: verdict proposed, user confirms, write fires — never pre-approved batch for permanent writes"

requirements-completed:
  - SKIL-09
  - SKIL-10

duration: 3min
completed: 2026-03-22
---

# Phase 30 Plan 02: Differentiator Skills Summary

**ztl:garden-health (Fan-Out health audit) and ztl:review-contradictions (per-pair loop with never-auto-confirm) completing the 5-skill differentiator set**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-22T04:32:37Z
- **Completed:** 2026-03-22T04:35:42Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments

- Created `plugin/skills/garden-health/SKILL.md` (78 lines) with Fan-Out pattern composing 5 analysis tools — vault_review, graph_gaps, graph_bridges, garden/backlog resource, and review/dashboard resource — into a prioritized maintenance report before any remediation
- Created `plugin/skills/review-contradictions/SKILL.md` (70 lines) with Loop per-pair pattern, never-auto-confirm Iron Law, sqlite-vec graceful degradation, and confirm_contradiction gate
- Created `plugin/skills/garden-health/references/garden-audit.md` (63 lines) documenting all tool output fields, gap/bridge scoring interpretation, and three remediation options
- Created `plugin/skills/review-contradictions/references/contradiction-review.md` (63 lines) documenting candidate scoring, genuine vs false positive evaluation criteria, permanent edge semantics, and degradation behavior

## Task Commits

Each task was committed atomically:

1. **Task 1: Create garden-health and review-contradictions SKILL.md files** - `a9a020c` (feat)
2. **Task 2: Create reference files for garden-health and review-contradictions** - `bc1a413` (feat)

**Plan metadata:** _(this summary commit)_ (docs: complete plan)

## Files Created/Modified

- `plugin/skills/garden-health/SKILL.md` — Fan-Out health audit skill with audit-first and never-remediate-without-confirmation Iron Laws
- `plugin/skills/garden-health/references/garden-audit.md` — garden/backlog, review/dashboard, vault_review, graph_gaps, graph_bridges output schemas and remediation options
- `plugin/skills/review-contradictions/SKILL.md` — Loop per-pair contradiction review skill with never-auto-confirm Iron Law and sqlite-vec graceful degradation
- `plugin/skills/review-contradictions/references/contradiction-review.md` — candidate scoring, evaluation criteria (genuine vs false positive), confirm_contradiction edge semantics, degradation behavior

## Decisions Made

- **Fan-Out pattern for garden-health**: all 5 analysis reads complete before any synthesis begins. This prevents leaking intermediate state (e.g., orphan count discovered mid-audit changing the gap priority order) into the health report.
- **Never-auto-confirm as Iron Law (not just guidance)**: the plan required this as an Iron Law because confirm_contradiction inserts permanent bidirectional graph edges. False positives corrupt every future query that traverses those nodes.
- **Sqlite-vec graceful degradation in both files**: documented in SKILL.md (user-facing) and contradiction-review.md (reference), giving two discovery surfaces for agents that encounter the error.
- **Distinction section added to garden-health**: explicitly separates ztl:garden-health (structural vault health) from ztl:review-triage (work queue items) to resolve the common routing ambiguity on triggers like "review my vault" or "what needs attention."

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- All 5 differentiator skills are complete: synthesize, decision-support, orient-session (30-01), garden-health, review-contradictions (30-02)
- Phase 30 is complete — all planned skills authored and committed
- 13 total skills now in plugin/skills/ (5 MVP from Phase 29 + 5 differentiator + 3 others)
- REQUIREMENTS.md: SKIL-09 and SKIL-10 complete

---
*Phase: 30-differentiator-skills*
*Completed: 2026-03-22*
