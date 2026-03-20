---
phase: 10-user-guide-content
plan: "01"
subsystem: documentation
tags: [mkdocs, paradigms, second-brain, knowledge-garden, user-guide]

# Dependency graph
requires:
  - phase: 09-navigation-structure
    provides: MkDocs nav structure with all 8 User Guide pages
provides:
  - Comprehensive paradigms.md comparison guide (192 lines, 3 scenarios, comparison table)
  - docs/plugins.md committed (previously untracked from plan 02)
  - mkdocs.yml nav entry for Built-in Plugins page
affects: [phase 11, any phase reading docs/paradigms.md]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Scenario-based comparison guide pattern: intro → table → choose-your-path → 3 scenarios → map → next steps"
    - "MkDocs admonitions: !!! note for behavioral caveats, !!! tip for best-practice shortcuts"

key-files:
  created: []
  modified:
    - docs/paradigms.md
    - docs/plugins.md
    - mkdocs.yml

key-decisions:
  - "Expanded paradigms.md from 72 to 192 lines while preserving original paradigms map, disclaimers, and intended flow sections verbatim"
  - "Committed docs/plugins.md (untracked from plan 02) alongside paradigms.md to fix pre-existing broken link that blocked mkdocs build --strict"

patterns-established:
  - "Comparison guide pattern: At a Glance table → Choose Your Path → Scenario walkthroughs → How They Map → Next Steps"

requirements-completed: [UGDE-02]

# Metrics
duration: 3min
completed: 2026-03-20
---

# Phase 10 Plan 01: Knowledge Paradigms Comparison Guide Summary

**Rewrote docs/paradigms.md into a 192-line decision guide with a 7-dimension second-brain vs knowledge-garden comparison table, three full command-sequence scenarios, and scenario-based "choose your path" routing**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-20T18:21:11Z
- **Completed:** 2026-03-20T18:23:50Z
- **Tasks:** 1
- **Files modified:** 3

## Accomplishments

- docs/paradigms.md expanded from 72 lines to 192 lines with all required content
- Added 7-dimension comparison table (second-brain vs knowledge garden)
- Added "Choose Your Path" section with 3 scenario-based routing options
- Added 3 full command-sequence scenarios: research capture, tending existing knowledge, hybrid agent+human
- Preserved original paradigms map, disclaimers, and intended flow sections verbatim
- Added Next Steps section linking tutorial.md, concepts.md, agentic-workflows.md
- Fixed pre-existing `obsidian.md` broken link to `plugins.md` by committing the untracked `plugins.md` file

## Task Commits

Each task was committed atomically:

1. **Task 1: Expand paradigms.md into a comprehensive comparison guide** - `b6d7036` (docs)

**Plan metadata:** (to be added in final commit)

## Files Created/Modified

- `docs/paradigms.md` - Expanded from 72 to 192 lines; comprehensive second-brain vs knowledge-garden comparison guide with comparison table, choose-your-path routing, 3 full scenarios, admonitions, and next steps
- `docs/plugins.md` - Committed previously untracked file (created by plan 02) to resolve broken link blocking mkdocs build
- `mkdocs.yml` - Committed nav entry for Built-in Plugins (added by plan 02 but never committed)

## Decisions Made

- Preserved the original paradigms map table, "What ztlctl Does Not Claim" bullets, and "Intended Flow" numbered list verbatim as instructed in the plan — they were accurate and complete
- Committed `docs/plugins.md` and the `mkdocs.yml` nav entry together with `paradigms.md` because they were untracked/unstaged artifacts from plan 02 that blocked `mkdocs build --strict`

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Fixed pre-existing broken obsidian.md → plugins.md link**
- **Found during:** Task 1 (post-write mkdocs build verification)
- **Issue:** `docs/plugins.md` was untracked and never committed; `mkdocs build --strict` aborted with a broken-link warning in obsidian.md. The file and mkdocs.yml nav entry were created by plan 02 but left uncommitted.
- **Fix:** Staged and committed `docs/plugins.md` and the `mkdocs.yml` nav entry alongside the paradigms.md change
- **Files modified:** docs/plugins.md (committed), mkdocs.yml (committed)
- **Verification:** `mkdocs build --strict` exits 0 with no warnings
- **Committed in:** b6d7036 (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Fix was necessary to satisfy the `mkdocs build --strict` acceptance criterion. No scope creep — the files were already authored and staged.

## Issues Encountered

None beyond the blocking deviation documented above.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- docs/paradigms.md is complete and passes mkdocs build --strict
- Phase 10 Plan 02 (obsidian.md) was already executed in a prior session (commit e2d234b)
- Phase 10 Plan 03 is the next unit to execute

---
*Phase: 10-user-guide-content*
*Completed: 2026-03-20*
