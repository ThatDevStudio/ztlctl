---
gsd_state_version: 1.0
milestone: v4.0
milestone_name: Agentic Skills
status: unknown
stopped_at: Completed 29-mvp-skills/29-02-PLAN.md
last_updated: "2026-03-22T04:17:14.849Z"
progress:
  total_phases: 5
  completed_phases: 2
  total_plans: 4
  completed_plans: 4
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-22)

**Core value:** Agents should only ever have to orchestrate the tool — not build custom functionality that is lacking from the tool.
**Current focus:** Phase 29 — mvp-skills

## Current Position

Phase: 29 (mvp-skills) — EXECUTING
Plan: 2 of 2

## Performance Metrics

**Velocity:**

- Total plans completed: 75 (v2.0: 22, v2.1: 21, v3.0: 22, v3.1: 10)
- Prior milestones: 4 shipped

*Updated after each plan completion*

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.

Key constraints for v4.0:

- Plugin is a pure filesystem artifact — no new Python packages, no build step
- Skills encode multi-step workflow sequences, never single-tool wrappers
- All write-operation skills must have `disable-model-invocation: true`
- Test every skill under installed state, not just `--plugin-dir`
- `plugin.json` version must bump on every plugin-modifying PR (CI-enforced from Phase 28)
- [Phase 28-plugin-foundation]: vault-gate.sh walks CWD upward for ztlctl.toml — matches ztlctl's own config discovery behavior
- [Phase 28-plugin-foundation]: test_stdio_no_stdout_pollution skips gracefully when mcp extra absent — consistent with existing mcp test pattern
- [Phase 28]: plugin_validate runs in parallel (no needs:) — plugin CI is independent of Python linting and doc linting
- [Phase 29-mvp-skills]: orient and align are read-only skills (no disable-model-invocation); capture has disable-model-invocation: true for write side-effects
- [Phase 29-mvp-skills]: align is standalone: other skills mention polaris but do NOT invoke align (prevents skill-chaining cascades)
- [Phase 29-mvp-skills]: Single ztl:session skill with path detection instead of separate start/close skills — single activation point is cleaner
- [Phase 29-mvp-skills]: Batch confirmation gate in review-triage — present full proposed action set before any writes

### Pending Todos

None — fresh milestone, roadmap just defined.

### Blockers/Concerns

None identified.

## Session Continuity

Last session: 2026-03-22T04:17:14.846Z
Stopped at: Completed 29-mvp-skills/29-02-PLAN.md
Resume file: None
Next action: `/gsd:plan-phase 28`
