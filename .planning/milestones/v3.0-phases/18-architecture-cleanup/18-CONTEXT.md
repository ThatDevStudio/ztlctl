# Phase 18: Architecture Cleanup - Context

**Gathered:** 2026-03-21
**Status:** Ready for planning

<domain>
## Phase Boundary

Remove compatibility residue (dead controller helpers, deprecated `workspace_modes.py`, transitional scaffolding), fix phantom `mutation` category in `_DEFAULT_ACTIVE_CATEGORIES`, resolve unused `ServiceError.recovery` field, make embedding dimensions configurable, and add k-approximation for `bridges()` betweenness centrality on large vaults. Pure internal cleanup — no user-facing command changes.

</domain>

<decisions>
## Implementation Decisions

### Claude's Discretion
All implementation choices are at Claude's discretion — pure infrastructure/cleanup phase. Key targets from requirements:
- ARCH-10: Dead controller helpers, deprecated `workspace_modes.py` (currently only imported by `services/export.py`), transitional scaffolding wrappers
- DEBT-01: Hardcoded 384 in `infrastructure/embeddings.py`, `services/vector.py`, `config/models.py` — make configurable via settings
- DEBT-05: `_DEFAULT_ACTIVE_CATEGORIES` in `mcp/generator.py` contains phantom `mutation` — remove it (no ActionDefinitions use `mutation` category)
- DEBT-06: `ServiceError.recovery` field is used in tests but no service ever populates it — either remove or populate
- DEBT-08: `betweenness_centrality` in `services/graph.py` — use `k` parameter approximation above a threshold

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/ztlctl/mcp/generator.py:86` — `_DEFAULT_ACTIVE_CATEGORIES` frozenset with phantom `mutation`
- `src/ztlctl/services/result.py` — `ServiceError` model with `recovery: str | None`
- `src/ztlctl/infrastructure/embeddings.py` — hardcoded 384 dimension
- `src/ztlctl/services/graph.py` — `betweenness_centrality` call without k-approximation
- `src/ztlctl/services/export.py` — only file importing from `workspace_modes.py`

### Established Patterns
- Config via Pydantic `ZtlSettings` in `config/models.py`
- MCP category management via `_DEFAULT_ACTIVE_CATEGORIES`, `activate_category`, `deactivate_category`
- ServiceError is a Pydantic model in `services/result.py`

### Integration Points
- `tests/mcp/test_generator.py` — tests asserting `mutation` in `_DEFAULT_ACTIVE_CATEGORIES`
- `tests/services/test_result.py`, `tests/mcp/test_response.py` — tests using `ServiceError.recovery`
- `tests/infrastructure/test_embeddings.py`, `tests/integration/test_semantic_extra.py` — embedding dimension tests

</code_context>

<specifics>
## Specific Ideas

No specific requirements — infrastructure phase

</specifics>

<deferred>
## Deferred Ideas

None

</deferred>
