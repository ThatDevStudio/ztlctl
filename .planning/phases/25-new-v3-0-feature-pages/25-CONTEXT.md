# Phase 25: New v3.0 Feature Pages - Context

**Gathered:** 2026-03-21
**Status:** Ready for planning

<domain>
## Phase Boundary

Write 5 standalone docs pages for v3.0 features. Each page follows the Documentation Conventions from CLAUDE.md (Phase 24) and slots into the confirmed nav positions in mkdocs.yml (Phase 24 placeholders). Also update llms.txt and llms-full.txt with entries for each new page. Does NOT update existing pages — that is Phase 26.

</domain>

<decisions>
## Implementation Decisions

### Page Structure and Conventions
- All 5 pages go in `docs/` root (consistent with all v2.1 pages)
- Each page follows Documentation Conventions from CLAUDE.md: Google CLI syntax, sentence-case headings, 3-type admonition taxonomy (warning/note/tip), "What's next" section
- Each page classified by Diataxis type (from Phase 24 audit): feature pages are primarily How-to guides
- Replace Phase 24 placeholder comments in mkdocs.yml with actual nav entries
- Append entries to llms.txt and llms-full.txt for each new page
- Every CLI example and flag name MUST be verified against `uv run ztlctl <command> --help` and ActionRegistry source — never from memory (per STATE.md blocker note)

### Five Pages (from NDOC requirements)
1. **session-recall.md** (NDOC-01): temporal/topic/topology recall, CLI usage, MCP tools, agent workflow
2. **polaris.md** (NDOC-02): init scaffold, MCP resource, context assembly, check_alignment, agent decisions
3. **contradiction-detection.md** (NDOC-03): heuristic scoring, CAT_SEMANTIC, confirm_contradiction, graph edges, MCP review
4. **media-ingestion.md** (NDOC-04): formats, faster-whisper (with optional-dep callout), ingest_media CLI/MCP, captured→annotated workflow, config
5. **methodology.md** (NDOC-05): prose-as-title, title quality check severity, garden backlog candidates

### Claude's Discretion
- Exact page length and depth (aim for comprehensive but not exhaustive)
- Whether to include diagrams or just text
- How much agent workflow detail per page
- Ordering of sections within each page

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `mkdocs.yml` — has placeholder comment markers for all 5 pages (Phase 24)
- `CLAUDE.md` — Documentation Conventions section with style guide
- `.planning/phases/24-*/24-DIATAXIS-AUDIT.md` — page classification reference
- Existing docs pages (tutorial.md, commands.md, etc.) — follow established style patterns
- `llms.txt` and `llms-full.txt` — existing agent discovery indexes to append to

### Established Patterns
- Feature pages typically have: overview, usage (CLI + MCP), configuration, agent workflow examples, "What's next"
- CLI examples use `$ ztlctl` prefix with Google style
- MCP tool references include tool name, parameters, return format
- Admonitions for optional dependencies use `!!! warning`

### Integration Points
- `mkdocs.yml` nav — replace 5 placeholder comments with actual entries
- `docs/llms.txt` — append 1-line entries per page
- `docs/llms-full.txt` — append multi-line entries per page
- Source code for verification: `src/ztlctl/services/recall.py`, `src/ztlctl/services/polaris.py`, `src/ztlctl/services/contradiction.py`, `src/ztlctl/services/ingest.py`, `src/ztlctl/services/check.py`

</code_context>

<specifics>
## Specific Ideas

- media-ingestion.md needs a prominent `!!! warning` callout for faster-whisper optional dependency
- polaris.md should frame polaris as the "strategic layer" of the vault
- Each page needs an llms.txt entry and llms-full.txt append — agent discovery indexes must be current after every page
- STATE.md note: "Every Phase 25 feature page must be verified against the ActionRegistry source and `uv run ztlctl <command> --help`"

</specifics>

<deferred>
## Deferred Ideas

- Updating existing pages (concepts.md, agentic-workflows.md, etc.) — Phase 26
- Refreshing llms.txt descriptions for existing pages — Phase 26
- Internal docs (CLAUDE.md architecture, DESIGN.md, README.md) — Phase 27

</deferred>
