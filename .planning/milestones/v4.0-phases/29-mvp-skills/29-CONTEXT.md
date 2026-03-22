# Phase 29: MVP Skills - Context

**Gathered:** 2026-03-22
**Status:** Ready for planning

<domain>
## Phase Boundary

Create 5 table-stakes Claude Code plugin skills that compose MCP tool calls into guided vault workflows: ztl:orient, ztl:session, ztl:capture, ztl:review-triage, ztl:align. Each skill encodes a multi-step workflow from the docs, enabling agents to orchestrate vault operations without knowing raw MCP tool names.

</domain>

<decisions>
## Implementation Decisions

### Skill Architecture & Size
- SKILL.md files kept lean (<200 lines) with progressive disclosure — detailed MCP tool signatures, workflow steps, and edge cases in `references/` subdirectory files
- Existing scaffold skills (vault-methodology, graph-intelligence, session-workflow) kept as-is — they are methodology/reference skills with different purpose than the new workflow orchestrator skills
- No `context: fork` — skills are lightweight orchestration guides; fork adds latency without proportional benefit at <200 lines

### Skill Activation & Safety
- `disable-model-invocation: true` on ztl:session, ztl:capture, ztl:review-triage (all have write side-effects); ztl:orient and ztl:align are read-only and safe for auto-invocation
- Skill descriptions use unique action verbs to prevent activation overlap: "orient/status" vs "start/close session" vs "capture/create note" vs "review/triage queue" vs "align/check priority" — descriptions reviewed as a set before implementation
- ztl:align is standalone — other skills mention polaris check in their workflow but do NOT invoke ztl:align (avoids skill-chaining complexity)

### Interaction Model & Confirmation Gates
- ztl:session is a single skill with path detection — "start/begin" runs open path, "close/end" runs close path
- ztl:review-triage uses batch processing — scan queue, present summary table, ask "process all / only high-priority / pick specific", then batch-execute approved set
- ztl:capture does NOT require confirmation for note/reference creation (low-risk, undoable via archive) — only confirms when duplicate detected in search step
- Skills reference MCP tools by abbreviated names (`search`, `create_note`, `session_start`) — Claude resolves `mcp__ztlctl__` prefix automatically from MCP discovery

### Claude's Discretion
- Exact SKILL.md wording, reference file structure, and workflow step ordering
- Which MCP resources vs tools to use in each skill's workflow
- Error handling patterns within skills (how to surface MCP tool failures)
- Skill frontmatter fields beyond name, description, version, and disable-model-invocation

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- 3 existing skills in `plugin/skills/`: vault-methodology, graph-intelligence, session-workflow — provide reference patterns for SKILL.md structure and frontmatter
- Research document `.planning/research/FEATURES.md` — contains detailed workflow compositions for all 5 skills with MCP tool sequences
- Research document `.planning/research/PITFALLS.md` — contains pitfalls #6 (description overlap), #7 (context window), #14 (context budget), #16 (don't duplicate MCP logic), #20 (disable-model-invocation)

### Established Patterns
- SKILL.md frontmatter: `name`, `description`, `version` fields (from existing skills)
- Reference file pattern: `references/<topic>.md` for detailed content (from vault-methodology and session-workflow)
- MCP tools referenced by short name in skill content (e.g., `create_note` not `mcp__ztlctl__create_note`)
- Existing skills are 50-90 lines — new skills should stay under 200 lines

### Integration Points
- Plugin root `plugin/skills/` — new skill directories created here
- `plugin/.claude-plugin/plugin.json` — no changes needed (skills auto-discovered from directory)
- MCP server provides 73+ tools — skills compose these, never duplicate their logic

</code_context>

<specifics>
## Specific Ideas

- ztl:orient workflow from FEATURES.md: identity → polaris → agent_context → report
- ztl:session from FEATURES.md: session_status → polaris → check_alignment → session_start (open path); session_close → enrichment report (close path)
- ztl:capture from FEATURES.md: search → agent_context → ingest_source → create_note → report
- ztl:review-triage from FEATURES.md: work_queue → get_document → evaluate → update/close → report
- ztl:align from FEATURES.md: polaris → check_alignment → present result → optional decision note

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>
