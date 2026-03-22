# Phase 30: Differentiator Skills - Context

**Gathered:** 2026-03-22
**Status:** Ready for planning

<domain>
## Phase Boundary

Create 5 advanced Claude Code plugin skills that compose MCP tool calls into multi-step workflows: ztl:synthesize (knowledge synthesis), ztl:decision-support (structured decision analysis), ztl:orient-session (recall-driven session start), ztl:garden-health (garden maintenance), ztl:review-contradictions (contradiction review). Each encodes a workflow that would be error-prone through raw MCP calls.

</domain>

<decisions>
## Implementation Decisions

### Architecture (carried forward from Phase 29)
- SKILL.md files kept lean (<200 lines) with progressive disclosure via `references/` subdirectory
- No `context: fork` — skills are lightweight orchestration guides
- Skills reference MCP tools by abbreviated names (`search`, `create_note`) — Claude resolves prefix automatically

### Activation & Safety
- `disable-model-invocation: true` on ztl:synthesize, ztl:orient-session, ztl:garden-health (all have write side-effects or start sessions)
- ztl:decision-support and ztl:review-contradictions are read-heavy but involve writes (create_note for decisions, confirm_contradiction) — set `disable-model-invocation: true` on both as well (5/5 differentiator skills are write-capable)
- Unique action verbs per skill to prevent overlap with Phase 29 MVP skills: "synthesize/connect" vs "decide/evaluate" vs "recall/resume/continue" vs "garden/maintain/health" vs "contradict/review-conflicts"
- Descriptions must not overlap with ztl:orient, ztl:session, ztl:capture, ztl:review-triage, ztl:align

### Interaction Model
- ztl:synthesize: checkpoint before creating synthesis note — user approves/modifies draft before write
- ztl:decision-support: fully autonomous read pipeline, presents structured briefing with no writes by default; optional decision note creation with confirmation
- ztl:orient-session: checkpoint before opening session — presents prior context summary, user confirms continuation
- ztl:garden-health: fully autonomous analysis, presents maintenance report with confirmation gate before any remediation writes
- ztl:review-contradictions: per-pair confirmation — agent proposes verdict, user confirms before confirm_contradiction fires; never auto-confirm; graceful degradation if sqlite-vec absent (no vector search, falls back to heuristic scoring)

### Claude's Discretion
- Exact SKILL.md wording, reference file structure, and workflow step ordering
- Error handling patterns within skills
- How to handle empty results (no contradictions, no gaps, no prior sessions)

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- 5 MVP skills from Phase 29 in `plugin/skills/`: orient, session, capture, review-triage, align — provide exact patterns
- Research document `.planning/research/FEATURES.md` — contains detailed workflow compositions for all 5 differentiator skills (sections 6-10)

### Established Patterns
- SKILL.md structure: frontmatter → title → Iron Laws → Workflow (numbered steps) → What to report → When NOT to use → reference link
- Reference files: 1-2 per skill with detailed implementation guidance
- Iron Laws pattern: 1-2 critical invariants at top of skill (from session and review-triage)
- All 5 MVP skills are 55-73 lines — differentiator skills should be similar

### Integration Points
- Plugin root `plugin/skills/` — new skill directories created here
- No changes to plugin.json or hooks needed (skills auto-discovered)
- MCP server provides all required tools: search, graph_gaps, topic_packet, draft_from_topic, decision_support, check_alignment, recall_temporal, recall_topic, session_start, vault_review, graph_bridges, check_contradictions, confirm_contradiction

</code_context>

<specifics>
## Specific Ideas

- ztl:synthesize from FEATURES.md: search → graph_gaps → topic_packet → draft_from_topic → user approval → create_note → reweave
- ztl:decision-support from FEATURES.md: search → decision_support → check_alignment → present briefing → optional create_note with subtype=decision
- ztl:orient-session from FEATURES.md: sessions/recent → recall_topic → get_document → present summary → session_start
- ztl:garden-health from FEATURES.md: garden/backlog → review/dashboard → vault_review → graph_gaps → graph_bridges → prioritized action list → confirm → execute
- ztl:review-contradictions from FEATURES.md: review/contradictions → check_contradictions → get_document pairs → per-pair verdict → confirm_contradiction

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>
