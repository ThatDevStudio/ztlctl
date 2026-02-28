# Category 4: Content Updates & Lifecycle — BAT Critique

**Date**: 2026-02-27
**Tester**: Claude (automated BAT runner)
**CLI Version**: ztlctl 0.1.0
**Vault paths**: `/Users/shparki/Documents/Workspace/thatdev/ztlctl/.bat/bat-{40..52}/`

---

## Test Results Summary

| BAT ID | Description | Result | Notes |
|--------|-------------|--------|-------|
| BAT-40 | Update Metadata | **PASS** | Title and tags updated, fields_changed accurate, DB/FS consistent |
| BAT-41 | Update No Changes | **PASS** | Exit 1, error code "no_changes", clear message |
| BAT-42 | Update Not Found | **PASS** | Exit 1, error code "NOT_FOUND" |
| BAT-43 | Note Status Auto-Computation | **FAIL** | Status is one update behind due to PROPAGATE-before-INDEX ordering |
| BAT-44 | Task Status Transitions (Valid) | **PASS** | All 4 transitions succeed: inbox->active->blocked->active->done |
| BAT-45 | Task Status Transitions (Invalid) | **PASS** | inbox->done correctly rejected with INVALID_TRANSITION |
| BAT-46 | Task Terminal States | **PASS** | done->active correctly rejected; done is terminal |
| BAT-47 | Reference Status Transition | **PASS** | captured->annotated succeeds; annotated->captured rejected |
| BAT-48 | Decision Acceptance | **PASS** | proposed->accepted succeeds, status confirmed |
| BAT-49 | Decision Immutability After Acceptance | **PASS** | Title change rejected (VALIDATION_FAILED), tag change allowed |
| BAT-50 | Archive Content | **PASS** | Archive succeeds, excluded from list, still accessible by get |
| BAT-51 | Supersede Decision | **PASS** | Old decision status=superseded, superseded_by set |
| BAT-52 | Garden Maturity -- Body Protection | **PASS** | Body protected with warning, body unchanged, ok=true |
| BAT-53 | Garden Maturity Progression | **PASS** | seed->budding->evergreen all succeed |

**Overall Score: 13/14 passed**

---

## Detailed Evaluation

### BAT-40: Update Metadata -- PASS

The update command cleanly modifies both title and tags in a single call. The `fields_changed` array in the response accurately reflects what changed. Verification via `query get` confirms both the database and filesystem are in sync. The update response includes the content ID and path, making it easy for automation to track changes.

**Usefulness**: High. This is the bread-and-butter operation for content management. The response structure is well-designed for programmatic consumption.

### BAT-41: Update No Changes -- PASS

When no change flags are provided, the CLI correctly returns an error with code "no_changes" at exit 1. The error message helpfully directs the user to `--help`. This is validated at the command layer (before hitting the service), which is efficient.

**Usefulness**: High. Prevents accidental no-op updates and provides clear guidance.

### BAT-42: Update Not Found -- PASS

Attempting to update a nonexistent ID returns a clean NOT_FOUND error. The error message includes the attempted ID, which aids debugging.

**Usefulness**: High. Essential error handling for any CRUD system.

### BAT-43: Note Status Auto-Computation -- FAIL

This is the most significant finding in this category. Note status is computed from outgoing link count in the PROPAGATE stage of the update pipeline, but edges from body wikilinks are re-indexed in the later INDEX stage. This means:

1. After adding wikilinks to the body, status reflects the PREVIOUS edge count, not the current one.
2. A subsequent update (even a trivial one like adding a tag) triggers the correct status computation because PROPAGATE then sees the edges indexed by the previous update's INDEX stage.

**Observed progression**: draft -> draft -> linked -> connected (across 3 updates)
**Expected progression**: draft -> linked -> connected (across 2 updates)

**Root cause**: In `UpdateService.update()` (lines 148-204 of `src/ztlctl/services/update.py`), the PROPAGATE stage (which reads edges from DB to compute status) runs before the INDEX stage (which deletes old edges and re-indexes new ones from wikilinks). The fix would be to either:
- Move the status recomputation after edge re-indexing, or
- Add a second propagation pass after INDEX for notes with body changes.

**Usefulness**: The auto-computation concept is excellent -- freeing users from manually setting note status based on link density is a strong design decision. However, the off-by-one behavior is confusing and could mislead users or agents who expect immediate status reflection.

### BAT-44: Task Status Transitions (Valid) -- PASS

All valid task transitions work flawlessly: inbox -> active -> blocked -> active -> done. Each transition is clean with no warnings. The status field in the response always reflects the new status.

**Usefulness**: Very high. Task management with enforced state machines prevents invalid workflows. The bidirectional blocked <-> active transition is practically useful for real project management.

### BAT-45: Task Status Transitions (Invalid) -- PASS

The attempt to jump from inbox directly to done is correctly rejected. The error message helpfully lists the allowed transitions from the current state (`['active', 'dropped']`), which is excellent for both human users and AI agents.

**Usefulness**: Very high. The allowed-transitions hint in the error message is a standout UX feature.

### BAT-46: Task Terminal States -- PASS

Once a task reaches "done", no further transitions are allowed. The error message shows `Allowed: []`, making it unambiguous that done is terminal.

**Usefulness**: High. Terminal states prevent workflow corruption. However, there's no "reopen" mechanism for tasks -- users who complete a task prematurely have no way to undo it. This is a design trade-off worth noting.

### BAT-47: Reference Status Transition -- PASS

The two-state reference lifecycle (captured -> annotated) works correctly. The forward transition succeeds, and the backward transition is properly rejected.

**Usefulness**: Moderate. The reference lifecycle is simple but effective. The "annotated" terminal state makes sense -- once a reference is fully annotated, its status shouldn't regress.

### BAT-48: Decision Acceptance -- PASS

Decision notes transition cleanly from proposed to accepted. The status is immediately reflected in the response.

**Usefulness**: High. Decision records (ADRs) with enforced lifecycle are valuable for knowledge management. The separate DecisionStatus enum with its own transition map is clean architecture.

### BAT-49: Decision Immutability After Acceptance -- PASS

This is one of the most impressive lifecycle features. After acceptance, the decision is immutable except for a well-defined set of allowed fields (status, superseded_by, modified, tags, aliases, topic). Attempting to change the title produces:

> "Cannot modify accepted decision. Disallowed fields: ['title']. Supersede with a new decision instead."

The error message even suggests the correct workflow (supersede). Meanwhile, tag changes are correctly permitted, allowing categorization metadata to evolve.

**Usefulness**: Very high. This enforces decision record integrity, which is critical for architectural decision records. The allowed-after-acceptance set is well-chosen.

### BAT-50: Archive Content -- PASS

The archive operation is a proper soft delete: it sets the archived flag, excludes the item from list results, but still allows direct access by ID. This is the expected behavior for knowledge management systems where historical access matters.

**Usefulness**: Very high. Soft delete is the correct pattern for a knowledge system. The `--include-archived` flag on `query list` provides a way to see everything when needed.

### BAT-51: Supersede Decision -- PASS

The `supersede` command is a clean abstraction over `update` -- it sets both `status=superseded` and `superseded_by=NEW_ID` atomically. The response includes both fields in `fields_changed`.

**Usefulness**: High. Decision supersession with traceability (the `superseded_by` field) enables decision lineage tracking. The dedicated command (`ztlctl supersede`) provides better ergonomics than a manual update.

### BAT-52: Garden Maturity -- Body Protection -- PASS

Garden notes (those with a maturity level set) have their body protected from modification. The attempt to change the body returns ok=true with a warning rather than a hard error. This is a design choice: the operation partially succeeds (any other changes would apply), and the body rejection is communicated via warnings.

The warning message is clear: "Body change rejected: garden note (maturity=seed)".

**Usefulness**: High. The garden maturity concept (from the Zettelkasten/digital garden paradigm) is well-implemented. Body protection at maturity levels encourages deliberate gardening -- you must consciously manage a note's maturity to modify its content.

### BAT-53: Garden Maturity Progression -- PASS

Both maturity transitions (seed -> budding -> evergreen) succeed. The progression is correctly enforced via GARDEN_TRANSITIONS in the lifecycle module.

**Minor gap**: The `query get` JSON response does not include a "maturity" field, even though maturity is stored in both the database and frontmatter. This means programmatic consumers cannot inspect a note's maturity via the query API -- they must read the file directly or check the DB. This is a schema gap that should be addressed.

**Usefulness**: High. The three-stage maturity model (seed/budding/evergreen) is a well-known digital garden pattern. Having it as a first-class lifecycle concept is a differentiator.

---

## Issues Found

### Critical

1. **BAT-43: Note status auto-computation is off-by-one** -- The PROPAGATE stage runs before INDEX, so status is computed from stale edge data. This affects any workflow that adds wikilinks via body update and expects immediate status reflection. The status catches up on the next update, but this is confusing and incorrect.

### Minor

2. **BAT-53: Maturity not in query get response** -- The `query get` JSON output does not include the `maturity` field. Users and agents cannot inspect maturity programmatically without reading the file directly. All other metadata (status, tags, title, etc.) is included.

---

## Overall Commentary

The content update and lifecycle subsystem is impressively thorough. The state machine enforcement across four content types (notes, tasks, references, decisions) with distinct lifecycle rules demonstrates careful domain modeling. Key strengths:

- **Structured error responses**: Every error includes a code, message, and allowed alternatives. The `INVALID_TRANSITION` errors that list allowed transitions are particularly agent-friendly.
- **Decision immutability**: The accepted-decision protection with a curated set of allowed fields is a real-world-useful feature for architectural decision records.
- **Archive as soft delete**: Proper information preservation with exclusion from default views.
- **Garden maturity body protection**: A thoughtful feature that respects the digital garden paradigm.
- **Supersession traceability**: The `superseded_by` field creates decision lineage.

The one functional bug (BAT-43's PROPAGATE/INDEX ordering) is notable because it affects the core premise that note status is automatically computed from structural properties. It works eventually (status catches up on the next update), but the immediate-feedback contract is broken.

The missing maturity field in `query get` is a polish issue that would be straightforward to fix.

**Verdict**: 13/14 passed. The lifecycle enforcement is production-quality for tasks, references, and decisions. The note status auto-computation needs a pipeline ordering fix but the concept is sound.
