---
phase: 27-internal-documentation-refresh
plan: "01"
subsystem: docs
tags: [documentation, architecture, readme, claude-md, v3.0]

requires: []
provides:
  - CLAUDE.md architecture section updated with v3.0 service/controller/action inventory
  - README.md features list updated with session recall, polaris, contradiction detection, media ingestion
  - README.md documentation table with 5 new v3.0 feature pages
  - README.md architecture package tree updated with controllers/ and actions/
affects:
  - 27-02 (DESIGN.md update — same internal docs refresh phase)
  - Any future contributor onboarding

tech-stack:
  added: []
  patterns:
    - "Architecture section in CLAUDE.md lists concrete service/controller/action inventories with counts"
    - "Feature-local action registration documented: 9 modules under actions/, aggregated by registry.py"
    - "Centralized PluginManager factory documented: get_plugin_manager() in plugins/runtime.py"

key-files:
  created: []
  modified:
    - CLAUDE.md
    - README.md

key-decisions:
  - "Service count is 16 (not 15 per PROJECT.md) — counted class *Service excluding BaseService; InitService, TranscriptionService, WorkflowService all present"
  - "Action count is 73 — verified by summing ActionDefinition() occurrences across all 9 _*.py modules"
  - "PluginManager factory lives in plugins/runtime.py (not manager.py) — get_plugin_manager() is the single construction point"

patterns-established:
  - "CLAUDE.md Architecture section: concrete inventories with counts and tables, not vague bullet lists"
  - "README.md Features list: each v3.0 feature links to its dedicated doc page"

requirements-completed:
  - IDOC-01
  - IDOC-03

duration: 15min
completed: 2026-03-21
---

# Phase 27 Plan 01: Internal Documentation Refresh Summary

**CLAUDE.md architecture section and README.md features list updated to reflect v3.0 reality: 16 services, 17 controllers, 73 actions, session recall, polaris, contradiction detection, and media ingestion**

## Performance

- **Duration:** ~15 min
- **Started:** 2026-03-21T00:00:00Z
- **Completed:** 2026-03-21T00:15:00Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- CLAUDE.md architecture section rebuilt with concrete v3.0 inventory: 16 services listed, 17 controllers listed, 73 actions tabulated across 9 feature modules
- Feature-local action registration pattern documented with per-module breakdown table
- Centralized PluginManager factory documented (plugins/runtime.py, get_plugin_manager())
- README.md features list expanded with session recall, polaris, contradiction detection, media ingestion, methodology, action registry, and reliable event delivery
- README.md Quick Start updated with recall-topic and check contradictions examples
- README.md documentation table updated with 5 new v3.0 feature pages
- README.md architecture tree updated with controllers/ and actions/ directories

## Task Commits

Each task was committed atomically:

1. **Task 1: Update CLAUDE.md architecture section with v3.0 inventory** - `356bf99` (docs)
2. **Task 2: Update README.md features and commands for v3.0** - `1d2427c` (docs)

## Files Created/Modified

- `CLAUDE.md` - Architecture section replaced with v3.0 service/controller/action inventory plus feature-local registration and centralized PM factory documentation
- `README.md` - Features list, Quick Start, documentation table, and architecture section updated for v3.0

## Decisions Made

- Service count is 16 (not 15 as stated in PROJECT.md context snapshot): counted all `class *Service` excluding `BaseService`, `ServiceResult`, `ServiceError` — InitService, TranscriptionService, and WorkflowService are concrete services not in the PROJECT.md count
- Action count is 73 verified by direct grep count: `_admin.py` (15) + `_session.py` (12) + `_query.py` (10) + `_check.py` (8) + `_graph.py` (8) + `_lifecycle.py` (6) + `_ingest.py` (5) + `_creation.py` (5) + `_export.py` (4)
- PluginManager factory lives in `plugins/runtime.py` not `plugins/manager.py` — runtime.py exports `get_plugin_manager()` with scope-aware caching; manager.py defines the class itself

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- CLAUDE.md and README.md now reflect v3.0 state for all developers and contributors
- Plan 27-02 (DESIGN.md update) can proceed independently

## Self-Check: PASSED

All files present and all commits verified.

---
*Phase: 27-internal-documentation-refresh*
*Completed: 2026-03-21*
