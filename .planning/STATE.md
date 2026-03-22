---
gsd_state_version: 1.0
milestone: v4.0
milestone_name: Agentic Skills
status: unknown
stopped_at: Completed 28-plugin-foundation/28-01-PLAN.md
last_updated: "2026-03-22T03:53:42.247Z"
progress:
  total_phases: 5
  completed_phases: 0
  total_plans: 2
  completed_plans: 1
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-22)

**Core value:** Agents should only ever have to orchestrate the tool — not build custom functionality that is lacking from the tool.
**Current focus:** Phase 28 — plugin-foundation

## Current Position

Phase: 28 (plugin-foundation) — EXECUTING
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

### Pending Todos

None — fresh milestone, roadmap just defined.

### Blockers/Concerns

None identified.

## Session Continuity

Last session: 2026-03-22T03:53:42.245Z
Stopped at: Completed 28-plugin-foundation/28-01-PLAN.md
Resume file: None
Next action: `/gsd:plan-phase 28`
