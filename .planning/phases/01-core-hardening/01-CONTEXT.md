# Phase 1: Core Hardening - Context

**Gathered:** 2026-03-19
**Status:** Ready for planning

<domain>
## Phase Boundary

Stabilize the existing codebase for production use: fix tech debt, close test coverage gaps, improve performance, harden security, polish UX/docs, add vault schema versioning, and formalize NoteTypeDefinition as an extensible primitive. This phase does NOT change the CLI/MCP surfaces or plugin API — it stabilizes the foundation that Phase 2+ will build on.

</domain>

<decisions>
## Implementation Decisions

### NoteType Formalization

- **Hybrid subtype model**: Subtypes (decision, knowledge, article, tool, spec) CAN have their own lifecycle overrides but inherit from parent by default. DecisionStatus already has its own transition map — formalize that pattern so plugins can do the same.
- **Template references via file paths**: NoteTypeDefinition references templates as file paths (matching current .md.j2 convention). Plugins ship a templates/ directory. No inline template strings.
- Four built-in content types (note, reference, log, task) plus subtypes (decision, knowledge, article, tool, spec) become NoteTypeDefinitions with embedded transition maps.

### Claude's Discretion

- **Lifecycle embedding vs registry**: Whether NoteTypeDefinition embeds its transition map inline or references it via a registry — choose based on downstream Action Registry needs and the 6-layer architecture dependency rules.
- **NoteTypeDefinition layer placement**: Whether it lives in domain/ (pure type, registration in services) or in a new registry package — choose based on dependency direction constraints.
- **Test coverage strategy**: How aggressively to lift pyproject.toml coverage exclusions (session.py, reweave.py, check.py, plugins, MCP). Incremental vs big-bang approach.
- **Schema versioning mechanism**: How to embed version markers in vault databases and detect/upgrade stale vaults via `ztlctl upgrade`.
- **Tech debt / UX / docs audit scope**: Prioritization of the CONCERNS.md items (5 tech debt, 2 bugs, 3 security, 4 performance). Fix all or prioritize by impact.
- **Performance optimization specifics**: ThreadPoolExecutor for rebuild I/O, FTS5 batch scoring approach, betweenness centrality k-approximation parameter.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Domain Model
- `src/ztlctl/domain/lifecycle.py` — Current transition maps, status enums, `is_valid_transition()`, `compute_note_status()`
- `src/ztlctl/domain/content.py` — ContentModel hierarchy, CONTENT_REGISTRY, frontmatter parsing, write_body/read_body
- `src/ztlctl/domain/types.py` — ContentType, NoteSubtype, RefSubtype, Space enums

### Known Issues
- `.planning/codebase/CONCERNS.md` — Complete list of tech debt, bugs, security issues, performance bottlenecks, fragile areas, scaling limits, test coverage gaps

### Architecture
- `.planning/codebase/ARCHITECTURE.md` — 6-layer architecture, data flow, key abstractions (Vault, ServiceResult, BaseService, AppContext)
- `.planning/codebase/CONVENTIONS.md` — Naming patterns, service layer patterns, error handling, import organization

### Requirements
- `.planning/REQUIREMENTS.md` — HARD-01 through HARD-09 requirements with acceptance criteria

### Research
- `.planning/research/ARCHITECTURE.md` — NoteTypeDefinition design recommendations, ActionRegistry component boundaries
- `.planning/research/PITFALLS.md` — Vault backward compatibility risks, premature API freeze warnings

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `lifecycle.py`: 5 transition maps (NOTE, REFERENCE, LOG, TASK, DECISION) + GARDEN_TRANSITIONS — these become the embedded lifecycle data in NoteTypeDefinitions
- `content.py`: `ContentModel` base class with `validate_create()`, `validate_update()`, `required_sections()`, `status_transitions()` — the validation interface NoteTypeDefinition will formalize
- `CONTENT_REGISTRY` dict: maps ContentType → ContentModel subclass — prototype for NoteTypeRegistry
- `build_template_environment()`: Jinja2 env builder in infrastructure/templates.py — already handles template discovery

### Established Patterns
- **Frozen Pydantic models**: All service return types are frozen — NoteTypeDefinition should follow the same pattern
- **StrEnum for status values**: All status types inherit StrEnum — custom lifecycles should too
- **Lazy local imports**: Cross-service imports use lazy/local pattern (6 precedents) — registration code should follow same pattern
- **Coverage exclusion in pyproject.toml**: Currently excludes `__main__.py`, `mcp/*`, `session.py`, `reweave.py`, `check.py` — these are the files to lift

### Integration Points
- `BaseService._dispatch_event()`: Where NoteTypeDefinition lifecycle events would fire
- `CreateService._create_content()`: The 6-stage pipeline that uses ContentModel — will need to resolve NoteTypeDefinition
- `Vault.transaction()`: Atomic context manager that NoteTypeDefinition validation integrates with
- `pyproject.toml [tool.coverage.run] omit`: The coverage exclusion list to reduce

</code_context>

<specifics>
## Specific Ideas

- DecisionStatus (proposed → accepted → superseded) is already the pattern for subtype lifecycle overrides — formalize this so plugins can register similar overrides
- The hybrid model means: a plugin registers a NoteTypeDefinition with `parent_type="note"` and optionally provides its own transition map. If no custom transitions provided, inherits from parent.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 01-core-hardening*
*Context gathered: 2026-03-19*
