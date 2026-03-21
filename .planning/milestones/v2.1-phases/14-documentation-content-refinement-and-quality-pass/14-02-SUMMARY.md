---
phase: 14-documentation-content-refinement-and-quality-pass
plan: "02"
subsystem: docs
tags: [mkdocs, documentation, best-practices, agents, llm, machine-readable]

requires: []
provides:
  - docs/best-practices.md — 270-line opinionated anti-pattern reference for User Guide audience
  - docs/agents.md — 493-line machine-readable system manual for LLM consumers
affects:
  - 14-05 (mkdocs.yml nav integration plan)

tech-stack:
  added: []
  patterns:
    - "best-practices.md: anti-pattern/correct-pattern entries with warning admonitions and summary table"
    - "agents.md: source-verified schemas, ASCII state machines, structured tables over prose"

key-files:
  created:
    - docs/best-practices.md
    - docs/agents.md
  modified: []

key-decisions:
  - "best-practices.md uses mentor/teacher tone for human User Guide audience — not tutorial walkthrough"
  - "agents.md uses structured data over prose — tables, JSON schemas, ASCII diagrams for machine readers"
  - "agents.md content verified against domain/lifecycle.py, config/models.py, and service source before writing"
  - "Reweave threshold documented as 0.6 (not 0.3 as plan spec suggested) — source-verified from ReweaveConfig default"
  - "auto_push default is true in GitConfig source — plan spec said false; documented actual default with recommendation to set false"

patterns-established:
  - "Machine-readable docs: structured tables + JSON schema blocks + ASCII state diagrams, minimal prose"
  - "Human-facing docs: mentor tone, warning admonitions (3-4 max), summary table at end, cross-links"

requirements-completed: []

duration: 12min
completed: "2026-03-20"
---

# Phase 14 Plan 02: New Documentation Pages Summary

**Two audience-targeted doc pages: 270-line anti-pattern/best-practices reference and 493-line machine-readable agent system manual with source-verified schemas, state machines, and I/O contracts**

## Performance

- **Duration:** 12 min
- **Started:** 2026-03-20T21:58:00Z
- **Completed:** 2026-03-20T22:10:37Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- Created docs/best-practices.md (270 lines) — opinionated mentor-tone reference with 7 H2 sections covering vault, notes, tags, reweave, sessions, plugins, and agents; 4 warning admonitions; summary table; cross-links
- Created docs/agents.md (493 lines) — machine-readable system manual with entity schemas for all 4 content types, lifecycle state machines verified from domain/lifecycle.py, 12 hard constraint rules, 3 deterministic interaction flows, 6 JSON schema blocks, error handling table, MCP discovery protocol

## Task Commits

Each task was committed atomically:

1. **Task 1: Create best-practices.md** - `4a5cad4` (docs)
2. **Task 2: Create agents.md** - `06d1e48` (docs)

## Files Created/Modified

- `docs/best-practices.md` — Opinionated anti-pattern/correct-pattern reference for human User Guide audience
- `docs/agents.md` — Machine-readable system manual for LLM consumers of ztlctl via MCP or CLI

## Decisions Made

- **Reweave threshold**: Plan spec said 0.3 but source (`config/models.py` `ReweaveConfig.min_score_threshold`) defaults to 0.6 — documented the actual default
- **auto_push default**: `GitConfig.auto_push` defaults to `true` in source; plan said false — documented actual default with recommendation to set false for new users
- **agents.md format**: Chose structured tables + ASCII diagrams + JSON blocks over any prose paragraphs to match machine-reader access patterns
- **best-practices.md scope**: Kept to 270 lines (within 200-350 target) by keeping each entry to 3-5 lines with cross-links to authoritative pages for detail

## Deviations from Plan

None — plan executed exactly as written. Source-read findings adjusted a few specific threshold values to match actual defaults but did not change structure or scope.

## Issues Encountered

None.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- Both pages are complete and ready for mkdocs.yml nav integration in Plan 05
- Pages serve their distinct audiences without content duplication
- All content is source-verified against domain/lifecycle.py, config/models.py, and service layer

---
*Phase: 14-documentation-content-refinement-and-quality-pass*
*Completed: 2026-03-20*
