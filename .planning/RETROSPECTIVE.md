# Project Retrospective

*A living document updated after each milestone. Lessons feed forward into future planning.*

## Milestone: v2.0 — Platform

**Shipped:** 2026-03-20
**Phases:** 7 | **Plans:** 22 | **Requirements:** 27/27

### What Was Built
- NoteTypeDefinition registry formalizing all note types as extensible primitives with lifecycle transitions
- ActionDefinition/ActionRegistry: 59 core operations as the single source of truth for CLI and MCP surfaces
- Auto-generated MCP tools (replaced 1,499 lines) and CLI commands (replaced 13 hand-written files)
- Stable Plugin API with versioning, pre/post-action hooks, custom note types, config injection
- Agentic integration: structured error recovery (36 codes), orchestration recipes, progressive disclosure
- Full hook wiring across 63 controller methods in 14 controllers

### What Worked
- **Strict dependency chain** — each phase proved the foundation for the next (hardening → registry → MCP gen → CLI gen → plugins → agentic → wiring). No phase needed rework from later phases.
- **ActionRegistry define-once architecture** — once the registry was built (Phase 2), Phases 3-4 generated both MCP and CLI surfaces mechanically. The parity test suite caught issues early.
- **Gap closure phase (Phase 7)** — running an audit before declaring the milestone complete caught 4 integration gaps (hook wiring, config injection, error detail, category semantics) that would have been production issues.
- **Verification-driven development** — each phase had explicit observable truths and VERIFICATION.md. This caught issues at phase boundary, not at milestone end.

### What Was Inefficient
- **SUMMARY frontmatter** — 10 of 27 requirements were never recorded in `requirements_completed` frontmatter fields. The data existed in VERIFICATION.md but the bookkeeping was inconsistent.
- **Phase 1-2 ROADMAP checkboxes** — Phases 1 and 2 plan checkboxes were never updated to `[x]` in ROADMAP.md despite being complete. Cosmetic but signals sloppy state tracking.
- **ServiceError.recovery field** — designed in Phase 6 but never populated by any service. The COMMON_ERROR_RECOVERY fallback works, but the field is unused infrastructure.

### Patterns Established
- **4-layer action model** (Data/Service/Controller/Registry) — services do business logic, controllers wrap for hook dispatch, registry describes for surface generation
- **custom_presentation=True escape hatch** — complex operations opt out of auto-generation while staying in the registry
- **DummyServer test pattern** — MCP tools testable without mcp package by capturing registered handlers
- **Advisory metadata pattern** — when a platform (FastMCP) can't support dynamic behavior, document the intent as advisory metadata rather than building workarounds

### Key Lessons
1. **Run milestone audits early** — Phase 7 gap closure was efficient because the audit identified specific, actionable gaps. Without it, these would have been discovered in production.
2. **Define-once works when the registry is rich enough** — ActionDefinition needed 13 fields to satisfy both CLI and MCP generators. Skimping on metadata would have forced special cases.
3. **Plugin API contracts are hard to get right** — the pre/post-action hook wiring needed to cover 63 methods across 14 controllers. This is maintenance surface that grows with every new action.
4. **EventBus bridge is essential for backward compatibility** — migrating plugins from per-event to post_action required bridging both dispatch paths. Skipping the bridge would have broken existing plugins.

### Cost Observations
- Model mix: primarily sonnet for execution, opus for planning and audits
- Timeline: 2 days (2026-03-19 to 2026-03-20) for 7 phases, 22 plans
- Notable: Phase 5 (Plugin Formalization) was the heaviest phase by execution time (3 complex plans)

---

## Cross-Milestone Trends

### Velocity

| Milestone | Phases | Plans | Days | Plans/Day |
|-----------|--------|-------|------|-----------|
| v2.0 | 7 | 22 | 2 | 11 |

### Quality

| Milestone | Requirements | Satisfied | Verification Score | Integration Issues |
|-----------|-------------|-----------|-------------------|-------------------|
| v2.0 | 27 | 27/27 | 81/81 truths verified | 4 (0 critical, 1 medium, 3 low) |

### Patterns

| Pattern | First Seen | Status |
|---------|-----------|--------|
| 4-layer action model | v2.0 | Established |
| Define-once registry | v2.0 | Established |
| Milestone audit before completion | v2.0 | Established |
| Advisory metadata for unsupported features | v2.0 | Established |
