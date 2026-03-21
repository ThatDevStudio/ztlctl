# Phase 26: Existing Pages and Quality Pass - Context

**Gathered:** 2026-03-21
**Status:** Ready for planning

<domain>
## Phase Boundary

Update existing docs pages to reflect v3.0 features and ensure agent discovery indexes are fully current. Does NOT write new pages (Phase 25) or update internal docs (Phase 27).

</domain>

<decisions>
## Implementation Decisions

### Pages to Update (QUAL-02)
- **concepts.md** — Add v3.0 content types: sessions, contradictions, media. Link to new feature pages
- **agentic-workflows.md** — Add v3.0 recipes: polaris-aligned session startup, recall-driven context loading, contradiction review workflow
- **agents.md** — Update tool inventory to 73+ registered actions, document v3.0 failure modes for agent error recovery
- **mcp.md** — Reflect current tool count (73+), document new MCP resources (ztlctl://polaris, ztlctl://sessions/recent, ztlctl://review/contradictions)

### Agent Discovery Indexes (QUAL-03)
- **llms.txt** — Verify entries for all new pages and accurate v3.0 feature descriptions
- **llms-full.txt** — Already fixed in Phase 25 gap closure. Verify descriptions are accurate for existing page entries too

### Quality Standards
- Follow Documentation Conventions from CLAUDE.md (Phase 24): Google CLI syntax, sentence-case headings, 3-type admonitions, "What's next" sections
- Every CLI example verified against `uv run ztlctl <command> --help`
- Every MCP tool/resource verified against ActionRegistry source

### Claude's Discretion
- How much detail to add per page (aim for accurate and current, not exhaustive rewrites)
- Whether to restructure existing content or just append v3.0 sections
- Exact wording of agent workflow recipes

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- Phase 25 feature pages — cross-reference targets
- ActionRegistry source files for tool inventory verification
- `src/ztlctl/mcp/resources.py` for MCP resource URIs

### Integration Points
- `docs/concepts.md`, `docs/agentic-workflows.md`, `docs/agents.md`, `docs/mcp.md` — update in place
- `docs/llms.txt`, `docs/llms-full.txt` — verify and update existing entries

</code_context>

<specifics>
## Specific Ideas

- agents.md should list all 73+ actions grouped by category (from ActionRegistry)
- mcp.md should document all MCP resources with their URIs
- agentic-workflows.md recipes should be concrete agent-executable sequences

</specifics>

<deferred>
## Deferred Ideas

- Internal docs (CLAUDE.md architecture, DESIGN.md, README.md) — Phase 27

</deferred>
