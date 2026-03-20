# Phase 10: User Guide Content - Context

**Gathered:** 2026-03-20
**Status:** Ready for planning

<domain>
## Phase Boundary

Write and enhance User Guide content for knowledge workers. Covers paradigm walkthroughs (second-brain vs knowledge garden), built-in plugin guides (Obsidian, Git, Reweave), agentic workflow recipe walkthroughs, and session lifecycle guides. All content lives in existing docs under the User Guide nav section. No new features or code changes — documentation only.

</domain>

<decisions>
## Implementation Decisions

### Writing depth and tone
- Expand existing terse docs with examples, scenarios, and expected CLI output
- Keep existing content as foundation — enhance, don't rewrite from scratch
- Show expected terminal output for key commands so readers can verify progress
- Explanatory tone: guide the reader through "why" not just "what"
- Each guide should be self-contained — a reader can follow it without reading other guides first

### Paradigm guide (docs/paradigms.md) — UGDE-02
- Restructure from current 72-line overview into a comprehensive comparison guide
- Comparison table: second-brain vs knowledge garden approaches (capture style, organization, enrichment, tools)
- "Choose your path" guidance: scenario-based recommendations (e.g., "If you're researching a new technology → second-brain capture-first approach", "If you're tending long-term knowledge → garden enrichment-first approach")
- 2-3 concrete scenarios per paradigm with full command sequences
- Explain how ztlctl supports both paradigms simultaneously (they're not exclusive)

### Built-in plugin guides — UGDE-03
- **Obsidian (docs/obsidian.md):** Enhance existing 71-line doc — add setup walkthrough with screenshots/output, vault structure explanation, garden/ directory usage, community plugin recommendations
- **Git plugin:** New section or page — setup, what it auto-commits, when it fires (post_action), how to configure, ztlctl.toml `[plugins.git]` example
- **Reweave plugin:** New section or page — what it does (auto-reweave after create), when it fires, scoring signals, how to tune via config, practical examples of reweave improving connections
- Each plugin guide includes: what it does, how to enable/configure, ztlctl.toml config example, common scenarios

### Agentic workflow recipes — UGDE-04
- Full terminal session walkthroughs for all 3 MCP recipe resources:
  1. **Research-capture:** Agent-driven research session → ingest → note creation → reweave
  2. **Review-triage:** Agent reviews work queue → prioritizes → processes actionable items
  3. **Knowledge-synthesis:** Agent analyzes graph → identifies themes → generates synthesis notes
- Each recipe: introduction (what it accomplishes), prerequisites, step-by-step commands with expected output, what to expect after completion
- Include both human-driven and agent-driven variants where applicable

### Session lifecycle guides — UGDE-05
- Expand session content (currently in agentic-workflows.md at 192 lines)
- Human-driven session: start → work → log entries → close with enrichment pipeline
- Agent-driven session: MCP tool calls → structured context → automated enrichment
- Include concrete examples: "A 30-minute research session", "An agent-driven literature review"
- Show the enrichment pipeline (reweave + orphan sweep + integrity check) that runs on session close

### Claude's Discretion
- Exact page structure and heading hierarchy within each guide
- Whether Git and Reweave plugin content is new pages or sections within existing pages
- Markdown formatting choices (admonitions, code tabs, etc. within mkdocs-shadcn capabilities)
- Order of scenarios within each guide

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Existing docs to enhance
- `docs/paradigms.md` — Current 72-line paradigm overview (foundation for UGDE-02)
- `docs/obsidian.md` — Current 71-line Obsidian starter kit doc (foundation for UGDE-03)
- `docs/agentic-workflows.md` — Current 192-line agentic workflows doc (foundation for UGDE-04, UGDE-05)
- `docs/tutorial.md` — Current 264-line tutorial (reference for tone and depth)
- `docs/concepts.md` — Current 91-line concepts doc (reference for terminology)

### Source code for accurate documentation
- `src/ztlctl/plugins/builtins/git.py` — Git plugin implementation (what actions it hooks, behavior)
- `src/ztlctl/plugins/builtins/reweave_plugin.py` — Reweave plugin implementation
- `src/ztlctl/services/session.py` — Session lifecycle (start, close, reopen, enrichment pipeline)
- `src/ztlctl/mcp/resources.py` — MCP recipe resource implementations (research-capture, review-triage, knowledge-synthesis)
- `src/ztlctl/config/models.py` — Plugin config models (for ztlctl.toml examples)

### Prior phase context
- `.planning/phases/09-navigation-structure/09-CONTEXT.md` — Nav structure decisions (User Guide section with 8 pages)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- 8 existing User Guide docs with varying depth (72-264 lines) — enhance, don't replace
- MCP recipe _impl functions in `resources.py` — source of truth for recipe steps
- Git plugin `post_action` handler — documents exactly which actions trigger git commits
- Reweave plugin `post_action` handler — documents auto-reweave trigger conditions
- Session enrichment pipeline in `session.py` — reweave + orphan sweep + integrity check sequence

### Established Patterns
- Existing tutorial.md has the best tone/depth example — 264 lines with command examples
- mkdocs-shadcn supports admonitions, code blocks, tables — use for structured content
- MkDocs nav already has User Guide section with all 8 pages listed

### Integration Points
- `mkdocs.yml` nav may need updates if new pages are added (Git plugin guide, Reweave plugin guide)
- `docs/llms.txt` and `docs/llms-full.txt` need regeneration if new pages are added
- `scripts/gen_llms_full_txt.py` NAV_ORDER constant needs updating for any new pages

</code_context>

<specifics>
## Specific Ideas

- User explicitly said: "end users may be using agents — detailed walkthroughs of what that workflow looks like and all the different recipes available"
- User wants "explanatory, with examples and common scenarios" — not terse reference docs
- "Discuss the second-brain vs knowledge garden patterns" — this is the conceptual foundation users need
- "Walk through built-in plugins like Obsidian" — practical setup and usage, not just listing what exists

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 10-user-guide-content*
*Context gathered: 2026-03-20*
