# Phase 12: Doc Search Integration - Context

**Gathered:** 2026-03-20
**Status:** Ready for planning

<domain>
## Phase Boundary

Add `ztlctl docs <query>` CLI command and `ztlctl://docs/search` MCP resource so users and agents can search the documentation corpus from within the tool. Both use a shared `_impl` function. No external dependencies — stdlib only for search logic.

</domain>

<decisions>
## Implementation Decisions

### Search behavior
- Search returns ranked list of matching pages with: title, relevance score, and excerpt (first matching paragraph)
- Default top 5 results, configurable with `--limit N`
- Search scope: title + headings + body text; title matches weighted 3x, heading matches 2x, body 1x
- Case-insensitive matching
- Multi-word queries: all terms must appear in the page (AND logic)

### Docs path resolution
- Primary: look for `docs/` directory relative to the ztlctl package install location (e.g., `Path(__file__).parent.parent.parent / "docs"`)
- Override: `ZTLCTL_DOCS_PATH` environment variable points to an alternate docs directory
- Fallback: if docs not found, return clear error with instructions to set `ZTLCTL_DOCS_PATH`
- At runtime, walk `docs/*.md` and `docs/guide/*.md` and `docs/dev/*.md` — the ~18 page corpus

### CLI command design
- `ztlctl docs <query>` — positional query argument (required)
- `--limit N` — max results (default 5)
- `--json` — structured JSON output
- Default output: Rich table with columns (Title, Score, Excerpt)
- Progressive disclosure: table shows top results; `--json` gives full structured data
- Register as a Click command group `docs` with `search` as default subcommand
- Follow existing ActionDefinition pattern: register in ActionRegistry, auto-generate CLI command

### MCP resource design
- `ztlctl://docs/search` — parameterized resource accepting `query` string, returns ranked results
- `ztlctl://docs/index` — static resource returning navigation map (mirrors llms.txt structure)
- Both follow existing `_impl` pattern in `resources.py`
- Results format: list of dicts with `{title, path, score, excerpt}` fields

### Shared _impl function
- `_docs_search_impl(query: str, limit: int = 5, docs_path: Path | None = None) -> list[dict]`
- Lives in a new module: `src/ztlctl/services/docs.py` (or `src/ztlctl/docs/search.py`)
- Pure function: takes query + path, returns results — testable without MCP or CLI
- CLI command calls `_docs_search_impl()` and renders with Rich
- MCP resource calls `_docs_search_impl()` and wraps in resource response

### Output format
- CLI default: Rich table
  ```
  ┌──────────────────────┬───────┬────────────────────────────────┐
  │ Title                │ Score │ Excerpt                        │
  ├──────────────────────┼───────┼────────────────────────────────┤
  │ Command Reference    │  0.85 │ ...matching paragraph...       │
  │ Configuration        │  0.72 │ ...matching paragraph...       │
  └──────────────────────┴───────┴────────────────────────────────┘
  ```
- CLI `--json`: `{"results": [{"title": "...", "path": "...", "score": 0.85, "excerpt": "..."}]}`
- MCP: same JSON structure as `--json` output

### Claude's Discretion
- Exact scoring algorithm (simple weighted term frequency is fine)
- Whether to strip markdown formatting from excerpts
- Module placement (`services/docs.py` vs `docs/search.py`)
- Whether `docs` is a command group or standalone command

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Existing patterns to follow
- `src/ztlctl/mcp/resources.py` — 15 existing `_impl` functions, `_RESOURCE_CATALOG`, resource registration pattern
- `src/ztlctl/actions/definitions.py` — ActionDefinition for registering CLI/MCP actions
- `src/ztlctl/actions/_register_core.py` — How to register new ActionDefinitions
- `src/ztlctl/controllers/base.py` — BaseController pattern for the new DocsController
- `src/ztlctl/commands/__init__.py` — How CLI command groups are registered

### Docs corpus
- `docs/*.md` + `docs/guide/*.md` + `docs/dev/*.md` — 18 pages, ~2988 lines total
- `docs/llms.txt` — navigation structure (could serve as `docs/index` resource content)

### Prior research
- `.planning/research/STACK.md` — Recommended stdlib-only search with pathlib + re
- `.planning/research/FEATURES.md` — MCP doc resource pattern (ztlctl://docs/search + index)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `resources.py` has 15 `_impl` functions — exact pattern to follow for `_docs_search_impl` and `_docs_index_impl`
- ActionRegistry + Controller pattern — new `docs` action can be registered like all other actions
- `docs/llms.txt` — already a structured index of all pages, can serve as `ztlctl://docs/index` content
- Rich output patterns in `output/` module — table rendering for CLI results

### Established Patterns
- `_impl` functions are pure: take args, return data — no MCP or CLI coupling
- Controllers wrap services, get registered as ActionDefinitions
- MCP resources use `_RESOURCE_CATALOG` for metadata + `_impl` for logic
- CLI commands auto-generated from ActionRegistry

### Integration Points
- `src/ztlctl/actions/_register_core.py` — register `docs_search` ActionDefinition
- `src/ztlctl/controllers/` — new `docs.py` controller (or add to existing)
- `src/ztlctl/mcp/resources.py` — add `ztlctl://docs/search` and `ztlctl://docs/index`
- `src/ztlctl/commands/__init__.py` — may need manual wiring if `docs` command group is custom
- `tests/` — new test files for search logic, controller, and MCP resource

</code_context>

<specifics>
## Specific Ideas

- User explicitly said: "using mechanisms which are typical for agents (like an llms.txt)" and "let's go for it" on in-tool search
- The `_impl` pattern is the established ztlctl way to share logic between CLI and MCP
- 18 pages at ~3000 lines is small enough for simple scoring — no need for FTS5 or external indexing
- `ztlctl://docs/index` can literally serve the content of `docs/llms.txt`

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 12-doc-search-integration*
*Context gathered: 2026-03-20*
