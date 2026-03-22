---
phase: 27-internal-documentation-refresh
plan: "02"
subsystem: docs
tags: [design, architecture, documentation, v3.0]

requires:
  - phase: 27-01
    provides: CLAUDE.md architecture section updated for v3.0

provides:
  - DESIGN.md updated to reflect v3.0 event model, action executor, plugin runtime
  - Section 1 architecture diagram includes controllers/ and actions/ layers
  - Section 10 notes auto-generated CLI from ActionRegistry
  - Section 15 documents reliable event model, ActionEvent, EventBusConfig, bridge reversal
  - Section 16 notes 73+ auto-generated MCP tools and new v3.0 resources
  - Section 19 Decision Log has D-13 through D-21 v3.0 decisions
  - New Section 19 Session Recall with RecallService design
  - New Section 20 Contradiction Detection with ContradictionService design
  - New Section 21 Ingestion Pipeline with IngestService and TranscriptionService
  - New Section 22 Polaris and Methodology design
  - Sections renumbered: Decision Log 19->23, Implementation Backlog 20->24

affects:
  - future-feature-phases
  - developer-onboarding

tech-stack:
  added: []
  patterns:
    - "DESIGN.md section numbering is sequential with no gaps or duplicates"
    - "New service sections follow pattern: overview, key types, invariants, cross-references"

key-files:
  created: []
  modified:
    - DESIGN.md

key-decisions:
  - "New v3.0 service sections inserted before Decision Log (Section 19) and renumbered existing sections to 23 and 24"
  - "Section 19 Session Recall documents that recall queries session metadata, not note content (separation of session state and knowledge artifacts)"
  - "Section 20 Contradiction Detection documents advisory-only model — aligned is always true, candidates surfaced for human confirmation"
  - "Section 21 Ingestion Pipeline documents two-phase capture workflow (captured->annotated) and TranscriptionService as local-only"
  - "Section 22 Polaris documents check_alignment as advisory (aligned always true) and prose-as-title as a title quality convention"

patterns-established:
  - "Architecture layers diagram in DESIGN.md Section 1 must be kept current with actual package structure"

requirements-completed: [IDOC-02]

duration: 20min
completed: "2026-03-21"
---

# Phase 27 Plan 02: Internal Documentation Refresh — DESIGN.md Summary

**DESIGN.md refreshed with v3.0 architectural decisions: event model (WAL drain, service-only post_action, ActionEvent), action executor (_run_action on all 17 controllers), feature-local registration (9 action modules), and four new service design sections (session recall, contradiction detection, ingestion pipeline, polaris/methodology)**

## Performance

- **Duration:** ~20 min
- **Started:** 2026-03-21T23:45:00Z
- **Completed:** 2026-03-21T23:51:10Z
- **Tasks:** 2
- **Files modified:** 1

## Accomplishments

- Updated Section 1 architecture diagram with controllers/ layer, actions/ modules, and accurate service count (15 services, 17 controllers)
- Updated Section 10 to document auto-generated CLI commands via ActionRegistry/generator.py
- Updated Section 15 with complete v3.0 reliable event model: ActionEvent schema, EventBusConfig fields, bridge reversal pattern, centralized PluginManager factory
- Updated Section 16 to note 73+ auto-generated MCP tools and added three new v3.0 resources (sessions/recent, review/contradictions, polaris)
- Added D-13 through D-21 decision log entries for all v3.0 architectural decisions
- Added Section 19 (Session Recall): RecallService three query modes (temporal, topic, topology), MCP resource, design rationale
- Added Section 20 (Contradiction Detection): ContradictionService three-signal heuristic, confirmation flow, graph edge recording, advisory model
- Added Section 21 (Ingestion Pipeline): IngestService normalize-then-create pattern, TranscriptionService 11 formats, two-phase captured→annotated workflow, MediaIngestConfig
- Added Section 22 (Polaris and Methodology): polaris priorities layer, check_alignment advisory semantics, prose-as-title convention, garden backlog candidates
- Renumbered existing sections: Decision Log 19→23, Implementation Backlog 20→24

## Task Commits

1. **Task 1: Update DESIGN.md existing sections for v3.0 accuracy** - `643807c` (docs)
2. **Task 2: Add v3.0 service design sections to DESIGN.md** - `fe2d9c6` (docs)

## Files Created/Modified

- `/Users/shparki/Documents/Workspace/thatdev/ztlctl/DESIGN.md` - v3.0 architectural decisions integrated: updated architecture layers, package structure, CLI command generation, event model, MCP adapter; added 4 new service design sections; 9 new decision log entries; sections renumbered

## Decisions Made

- New v3.0 service sections inserted before Decision Log (not appended after) so that new features appear before the decision log. Decision Log renumbered to 23, Implementation Backlog to 24.
- Section 19 Session Recall documents that recall queries session metadata, not note content — separation of session state from knowledge artifacts is a design invariant.
- Section 20 Contradiction Detection emphasizes advisory-only model: `aligned` is always true, `confirmed` contradictions require explicit human action.
- Section 21 Ingestion Pipeline highlights two-phase captured→annotated workflow and local-only transcription (no audio data leaves machine).
- Section 22 Polaris documents `check_alignment` as always returning `aligned=true` — this is intentional; the tool cannot judge alignment, the agent does.

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- DESIGN.md now fully reflects v3.0 architecture for developer reference
- IDOC-02 requirement satisfied
- Phase 27 complete (both plans done)

---
*Phase: 27-internal-documentation-refresh*
*Completed: 2026-03-21*
