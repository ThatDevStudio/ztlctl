# Phase 21: Contradiction Detection - Context

**Gathered:** 2026-03-21
**Status:** Ready for planning

<domain>
## Phase Boundary

Surface notes that likely contradict each other using vector similarity + heuristic scoring, record confirmed contradictions as `contradicts` graph edges, expose candidates via MCP review resource and CheckService semantic category. Builds on existing vector search and graph infrastructure.

</domain>

<decisions>
## Implementation Decisions

### Contradiction Discovery Strategy
- Candidate pairs scoped by shared tags + high cosine similarity (>0.85) via existing vector search — leverages semantic infrastructure
- Negation heuristic uses keyword-based patterns: "however", "but", "instead", "on the contrary", "disagree", "not", "shouldn't", "won't" — fast, no LLM
- key_points comparison: extract from note frontmatter, find overlapping topics, flag when conclusions differ on same topic — lightweight structural comparison

### Graph Edge and Confirmation
- Edge type string: `"contradicts"` — matches CNTR-04 requirement language
- Separate `confirm_contradiction` action for recording edges — distinct from discovery
- Confirmed contradictions are bidirectional edges (A contradicts B ↔ B contradicts A)

### MCP Resource and CheckService Integration
- `CAT_SEMANTIC` is a new check category alongside existing CAT_STRUCTURAL, CAT_REFERENTIAL, etc.
- `ztlctl://review/contradictions` returns JSON array of `{note_a, note_b, score, signals: [...]}` sorted by score descending
- Contradiction check gracefully skips with info message if no vector index exists — never fails the entire check run

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/ztlctl/services/vector.py` — VectorService with similarity search
- `src/ztlctl/services/query.py` — QueryService with `vector_search` method using cosine similarity
- `src/ztlctl/services/check.py` — CheckService with category-based integrity scanning
- `src/ztlctl/infrastructure/vault.py` — Vault with `add_link(source_id, target_id, edge_type)` and `get_links`
- `src/ztlctl/services/graph.py` — GraphService with edge management

### Established Patterns
- Check categories defined as module constants (CAT_STRUCTURAL, etc.)
- Check issues returned as `CheckIssue(severity=..., category=..., message=...)`
- Graph edges stored in `edges` table with `edge_type` column
- ActionDefinition registration in feature-local modules
- MCP resources in `mcp/resources.py` with `_RESOURCE_CATALOG`

### Integration Points
- `src/ztlctl/services/check.py` — add `CAT_SEMANTIC` category and contradiction check method
- `src/ztlctl/actions/_check.py` — register `check_contradictions` and `confirm_contradiction` actions
- `src/ztlctl/mcp/resources.py` — add `ztlctl://review/contradictions` resource
- `src/ztlctl/controllers/check.py` — add controller methods for contradiction actions

</code_context>

<specifics>
## Specific Ideas

- Cosine similarity threshold of 0.85 should be configurable but start with a sensible default
- The scoring heuristic should weight: cosine similarity (40%), negation keyword density (30%), key_points overlap with different conclusions (30%)
- Candidates should be capped at 20 pairs per check run to keep output manageable

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>
