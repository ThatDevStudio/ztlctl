# Phase 19: Methodology Guidance and Polaris - Context

**Gathered:** 2026-03-21
**Status:** Ready for planning

<domain>
## Phase Boundary

Add a persistent polaris priorities layer (scaffold, MCP resource, context assembly, check_alignment action), title quality checks in the integrity scanner, and methodology template documentation. This phase delivers user-facing features that make ztlctl a priorities-aware memory system.

</domain>

<decisions>
## Implementation Decisions

### Polaris Layer Design
- Polaris document lives at `garden/groves/polaris.md` — dedicated grove for persistent priorities
- Starter template has 3 sections: Mission, Current Priorities (numbered), Decision Principles — research-partner tone
- `check_alignment` returns ServiceResult with structured data: `{aligned: bool, relevant_priorities: [...], reasoning: str}` — agent can reason against it
- Polaris content has 500-token budget in ContextAssembler Layer 1 (operational state)

### Title Quality Check
- Titles ≤3 words OR matching generic patterns ("Untitled", "New Note", "Notes on X", single-word titles) flagged at info severity
- Title improvement candidates appear in garden backlog MCP resource as a new subsection alongside stale seeds and orphans (METH-03)
- Methodology template uses research-partner tone: "Your titles ARE your search index. Write them as complete thoughts."

### Integration Points
- `ztlctl init` automatically scaffolds `garden/groves/polaris.md` with starter content (no prompting)
- `check_alignment` is a registered ActionDefinition — auto-generates both CLI and MCP surfaces
- Polaris content sits in ContextAssembler Layer 1 (operational state), before note content in Layer 2

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/ztlctl/services/check.py` — CheckService with `CAT_STRUCTURAL` category for title checks
- `src/ztlctl/services/context.py` — ContextAssembler with layered token budgeting
- `src/ztlctl/mcp/resources.py` — MCP resource registration including `garden_backlog`
- `src/ztlctl/services/init.py` — vault scaffolding with template-based file generation
- `src/ztlctl/templates/content/` and `src/ztlctl/templates/self/` — existing Jinja2 templates
- `plugin/skills/vault-methodology/SKILL.md` — existing methodology skill with research-partner tone

### Established Patterns
- ActionDefinition registration in feature-local modules (`src/ztlctl/actions/_check.py`, etc.)
- ContextAssembler uses `_budget_content()` for token-limited sections
- CheckService returns issues as `CheckIssue(severity=..., category=..., message=...)`
- MCP resources use `@server.resource()` decorator in `mcp/resources.py`

### Integration Points
- `src/ztlctl/actions/_check.py` — register new `check_alignment` action
- `src/ztlctl/services/init.py` — add polaris scaffolding to init pipeline
- `src/ztlctl/mcp/resources.py` — add `ztlctl://polaris` resource
- `src/ztlctl/services/context.py` — add polaris to Layer 1 assembly

</code_context>

<specifics>
## Specific Ideas

- The methodology template should reference the existing `plugin/skills/vault-methodology/SKILL.md` tone and examples
- Polaris MCP resource should be simple file-read (no service layer needed — it's a static document)
- Title quality check should be advisory only (info severity) — never block note creation

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>
