---
phase: 21-contradiction-detection
plan: 01
subsystem: services
tags: [contradiction, vector, similarity, heuristic, scoring]

requires:
  - phase: 20-session-recall
    provides: vector index populated by recall infrastructure (VectorService)
  - phase: 18-architecture-cleanup
    provides: BaseService, BaseController patterns

provides:
  - ContradictionService with find_candidates (CNTR-01) and heuristic _score_pair (CNTR-02)
  - ContradictionController wrapping service methods through _run_action
  - confirm_contradiction stub ready for Plan 02 wiring

affects:
  - 21-02-PLAN.md (wires ContradictionController into ActionRegistry, CheckService, MCP)

tech-stack:
  added: []
  patterns:
    - "Lazy VectorService import inside methods (matches cross-service import pattern)"
    - "Cosine distance-to-similarity conversion: similarity = 1 - distance"
    - "Regex-based multi-word negation keyword detection with saturation cap"
    - "Topic-word extraction with stop-word filtering for key_points divergence"

key-files:
  created:
    - src/ztlctl/services/contradiction.py
    - src/ztlctl/controllers/contradiction.py
    - tests/services/test_contradiction.py
    - tests/controllers/test_contradiction.py
  modified: []

key-decisions:
  - "Patch target for VectorService mocks is ztlctl.services.vector.VectorService (lazy import inside method, not module-level)"
  - "_score_pair negation capped at 5 keywords for 1.0 saturation — prevents body length from dominating score"
  - "confirm_contradiction stubbed with NOT_IMPLEMENTED — Plan 02 adds graph edge recording"
  - "Ruff RUF059: unpacked-but-unused signal variables in score tests use _ prefix pattern"

requirements-completed: [CNTR-01, CNTR-02]

duration: 5min
completed: 2026-03-21
---

# Phase 21 Plan 01: Contradiction Detection — Service and Controller Summary

**ContradictionService with three-signal heuristic scoring (cosine 40%, negation 30%, key_points 30%) and thin ContradictionController wrapper through _run_action**

## Performance

- **Duration:** ~5 min
- **Started:** 2026-03-21T19:51:57Z
- **Completed:** 2026-03-21T19:56:31Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments

- ContradictionService.find_candidates filters non-archived notes by cosine similarity >= 0.85 and shared tags, scores pairs with a three-signal heuristic, sorts by score desc, caps at 20 pairs
- _score_pair: cosine (40%), negation density with 8 keyword patterns capped at 5 (30%), key_points topic-word overlap with divergent conclusion detection (30%)
- ContradictionController.check_contradictions and confirm_contradiction both delegate through _run_action (plugin pre-action hook integration)
- confirm_contradiction stubbed with NOT_IMPLEMENTED ServiceError, ready for Plan 02 graph-edge wiring
- 20 tests total: 13 service (TDD RED/GREEN), 7 controller delegation smoke tests

## Task Commits

1. **Task 1: ContradictionService with candidate discovery and heuristic scoring** - `8545d34` (feat)
2. **Task 2: ContradictionController wrapper** - `4f07fc4` (feat)

## Files Created/Modified

- `src/ztlctl/services/contradiction.py` - ContradictionService with find_candidates, _score_pair, _extract_note_content, _extract_topic_words
- `src/ztlctl/controllers/contradiction.py` - ContradictionController with check_contradictions and confirm_contradiction
- `tests/services/test_contradiction.py` - 13 unit tests covering all behavior specs (TDD)
- `tests/controllers/test_contradiction.py` - 7 delegation and plugin rejection tests

## Decisions Made

- VectorService is lazily imported inside find_candidates matching the existing cross-service import pattern; patch target is therefore `ztlctl.services.vector.VectorService` not `ztlctl.services.contradiction.VectorService`
- Negation count saturation at 5 keywords prevents long body text from dominating the negation component of the score
- confirm_contradiction is stubbed — Plan 02 adds the `contradicts` graph edge recording and ActionRegistry wiring

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Corrected mock patch target for VectorService**
- **Found during:** Task 1 (RED phase, first test run)
- **Issue:** Plan suggested patching `ztlctl.services.contradiction.VectorService.is_available` but VectorService is imported lazily inside the method, so the module attribute doesn't exist at patch time
- **Fix:** Changed all patch targets to `ztlctl.services.vector.VectorService.{method}` (patch where the class is defined)
- **Files modified:** tests/services/test_contradiction.py
- **Verification:** All 13 tests pass
- **Committed in:** 8545d34 (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 - bug in test mock target)
**Impact on plan:** Necessary correctness fix for test isolation. No scope creep.

## Issues Encountered

- Pre-commit ruff caught unused variables in tests (`kp_yaml`, `tag_yaml`, `note_a_id`, unused `signals` unpacked variables) — fixed by removing dead code and using `_signals` / `_` naming convention

## Known Stubs

- `ContradictionService.confirm_contradiction` returns `NOT_IMPLEMENTED` error — intentional stub, Plan 02 wires graph edge recording

## Next Phase Readiness

- ContradictionService and ContradictionController ready for Plan 02 wiring
- Plan 02: register actions in ActionRegistry, integrate into CheckService, add `contradicts` graph edge on confirm, expose via MCP

---
*Phase: 21-contradiction-detection*
*Completed: 2026-03-21*
