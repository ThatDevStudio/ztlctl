# Phase 32: Validation and Hardening - Context

**Gathered:** 2026-03-22
**Status:** Ready for planning

<domain>
## Phase Boundary

Final validation pass: run PITFALLS.md distribution checklist, verify skill descriptions don't overlap, ensure context budget is under 2%, validate plugin structure, and document any items requiring human verification under installed state.

</domain>

<decisions>
## Implementation Decisions

### Claude's Discretion
All implementation choices are at Claude's discretion — cross-cutting quality pass with no new features. Key constraints:
- PITFALLS.md distribution checklist (20+ items) is the canonical validation reference
- Skill descriptions must be reviewed as a set for overlap (PITFALLS #6)
- Context budget check requires manual verification (human action item)
- Installed-state testing requires manual verification (human action item)
- Automated checks: `claude plugin validate`, directory structure, hook permissions, stdout cleanliness, agent frontmatter, file line counts
- Fix any issues found during validation — this phase is fix-as-you-go, not report-only

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `.planning/research/PITFALLS.md` — distribution checklist (20+ items at bottom of file)
- `tests/plugin/test_plugin_structure.py` — existing 11-test validation suite from Phase 28
- All 10 skills in `plugin/skills/` — descriptions to review as a set
- `.github/workflows/pr-ci.yml` — plugin_validate CI job from Phase 28

### Established Patterns
- Phase 28 created the test suite; Phase 32 extends it for full coverage
- Skill files are all <200 lines — context budget should be well under 2%

### Integration Points
- `tests/plugin/test_plugin_structure.py` — extend with new validation tests
- Plugin directory structure — final state after Phases 28-31

</code_context>

<specifics>
## Specific Ideas

No specific requirements — validation phase

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>
