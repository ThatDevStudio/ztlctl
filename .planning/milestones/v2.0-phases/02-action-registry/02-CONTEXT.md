# Phase 2: Action Registry - Context

**Gathered:** 2026-03-19
**Status:** Ready for planning

<domain>
## Phase Boundary

Build the ActionDefinition/ActionRegistry infrastructure AND refactor the existing codebase into a clean 4-layer architecture: Data layer (repository) → Service layer (pure domain logic) → Controller layer (orchestration) → Registry layer (schema + auto-generation). Every public operation must go through the controller+registry path. No escape hatches — complex operations like batch, init wizard, and serve get thin registry definitions with `custom_presentation=True` for optional hand-written CLI/MCP surfaces while remaining discoverable and hookable.

This phase does NOT generate CLI or MCP surfaces from the registry — that's Phases 3-4. This phase establishes the registry infrastructure and refactors existing code into the new layers.

</domain>

<decisions>
## Implementation Decisions

### Architecture — 4-Layer Refactoring

- **Data layer**: Repository pattern encapsulating DB + filesystem. The current `Vault`, `VaultTransaction`, `DatabaseEngine`, `FilesystemOps` largely fill this role. ACID guarantees managed here via SQLAlchemy transactions + compensation-based file rollback. Services should NOT directly manage files or databases.
- **Service layer**: Pure domain logic — side-effect-free functions that take inputs and return results. Current services mix orchestration with domain logic; this needs separation. Services should be composable, testable in isolation, and free of Vault/transaction management.
- **Controller layer** (NEW): Orchestrates service calls + data layer operations. Manages transactions, dispatches events, coordinates multi-step workflows. The controller is the single interface for the registry layer. This replaces the current pattern where services do both domain logic and orchestration.
- **Registry layer** (NEW): Wraps controller methods with required schema (type hints, docstrings, parameter metadata). Provides auto-mapping to CLI and MCP. The registry is the only way to connect controller functionality to events and to generate presentation layer interfaces.

### Registration — All Public Methods

- **ALL public controller methods** get ActionDefinitions — no exceptions. This ensures no functionality is left out of the registry and any mapping changes apply unilaterally.
- **No escape hatches**: Complex commands (batch, init wizard, serve) still go through the registry with thin definitions. They can be marked for custom presentation (the registry skips auto-generation but the action is still registered, discoverable, and hookable).
- **Controller is the only way to expose functionality**: No direct service-to-CLI/MCP paths. Everything flows through controllers → registry → presentation.

### Scope — Full Refactor in Phase 2

- This is NOT registry-only — Phase 2 includes refactoring existing services into the controller+service+data split.
- The goal is that by end of Phase 2, the new architecture is in place and all existing operations are registered as ActionDefinitions through their controllers.
- CLI and MCP continue to work via the current hand-written code during Phase 2 — auto-generation replaces them in Phases 3-4.

### Claude's Discretion

- **ActionDefinition dataclass shape**: What fields it carries, how metadata is structured, complexity budget per definition. Research recommended 50-line budget.
- **Param type system**: How ActionParam maps to both Click types and MCP JSON schema. Single type system that generates both.
- **Controller granularity**: How to split current services. Whether each current service becomes one controller or whether controllers are organized differently (by domain area, by command group, etc.).
- **Migration strategy**: How to incrementally refactor without breaking existing CLI/MCP. Whether to do service-by-service or all-at-once.
- **Event dispatch location**: Whether events fire from controllers (new location) or stay in services (current location via BaseService._dispatch_event).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Current Architecture
- `src/ztlctl/domain/registry.py` — NoteTypeDefinition pattern (frozen dataclass, registry singleton) — follow this same pattern for ActionDefinition/ActionRegistry
- `.planning/codebase/ARCHITECTURE.md` — Current 6-layer architecture, data flow, key abstractions
- `.planning/codebase/CONVENTIONS.md` — Service layer patterns, error handling, import organization

### Current Service Methods (what becomes controller methods)
- `src/ztlctl/services/` — 12 service files with 45+ public methods that need refactoring
- `src/ztlctl/commands/` — 20+ CLI command files showing current parameter shapes
- `src/ztlctl/mcp/tools.py` — 29 `_impl` functions showing MCP parameter shapes

### Research
- `.planning/research/ARCHITECTURE.md` — ActionDefinition/ActionRegistry design, NoteTypeDefinition integration, build order
- `.planning/research/PITFALLS.md` — Action model god object risk (Pitfall 4), premature API freeze (Pitfall 1)
- `.planning/research/SUMMARY.md` — Phase ordering rationale, CLI/MCP impedance mismatch

### Requirements
- `.planning/REQUIREMENTS.md` — ACTN-01, ACTN-02

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `domain/registry.py`: NoteTypeDefinition frozen dataclass + NoteTypeRegistry — direct template for ActionDefinition + ActionRegistry pattern
- `services/result.py`: ServiceResult frozen Pydantic model — all controller methods should return ServiceResult (continuity)
- `services/contracts.py`: `dump_validated()` for typed payload validation — reusable for action parameter validation
- `services/base.py`: BaseService with `_vault` and `_dispatch_event()` — controllers may follow a similar BaseController pattern

### Established Patterns
- **Frozen dataclass for definitions**: NoteTypeDefinition uses `@dataclass(frozen=True)` — ActionDefinition should match
- **Module-level singleton registry**: `_REGISTRY` in registry.py — ActionRegistry should follow the same `get_action_registry()` accessor pattern
- **ServiceResult as universal return**: All services return ServiceResult — controllers must maintain this contract
- **Lazy local imports**: Cross-service imports use local imports inside methods — controller imports should follow same pattern

### Integration Points
- `services/base.py`: BaseService._dispatch_event() — event dispatch may move to controllers
- `commands/_context.py`: AppContext lazy Vault init + emit() — CLI commands currently get Vault through AppContext; controllers will need Vault injection
- `mcp/tools.py`: `_impl` functions — these are effectively proto-controllers already (they receive Vault and call services)
- `plugins/hookspecs.py`: 16 hookspecs — pre-action hooks (Phase 5) will target controllers, not services

</code_context>

<specifics>
## Specific Ideas

- The `_impl` functions in `mcp/tools.py` are effectively proto-controllers — they receive a Vault, orchestrate service calls, and return results. The controller refactoring can use these as the migration starting point.
- "The controller layer is the only way to expose functionality, the registry layer is the only way to connect that functionality to events" — this is the key architectural invariant to enforce.
- User explicitly rejected escape hatches: "Everything goes through the registry, no escape hatch. In lieu of an escape hatch, we can simply wrap a thin definition."

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 02-action-registry*
*Context gathered: 2026-03-19*
