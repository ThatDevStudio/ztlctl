# Roadmap: ztlctl v2

## Overview

ztlctl v2 transforms a mature, tested CLI tool into a production-grade extensible platform. The work follows a strict dependency chain: stabilize the foundation (core hardening), build the define-once action registry, prove it by auto-generating the MCP surface (simpler), then the CLI surface (complex), formalize the plugin API only after the action model is validated, and finish with agentic integration and security hardening. Each phase proves the foundation for the next — no phase can be reordered without breaking what comes after.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Core Hardening** - Stabilize data model, close tech debt, fix performance, formalize note types, add vault schema versioning
- [ ] **Phase 2: Action Registry** - Build the define-once ActionDefinition/ActionRegistry infrastructure as internal abstraction
- [x] **Phase 3: MCP Surface Generation** - Auto-generate MCP tools from ActionRegistry, achieving full CLI/MCP parity (completed 2026-03-19)
- [x] **Phase 4: CLI Surface Generation** - Auto-generate CLI commands from ActionRegistry, eliminating hand-crafted command duplication (completed 2026-03-20)
- [x] **Phase 5: Plugin Formalization** - Publish stable plugin API with versioning, pre-hooks, config, custom note types (completed 2026-03-20)
- [ ] **Phase 6: Agentic Integration & Security** - Agent orchestration recipes, progressive tool disclosure, plugin security hardening

## Phase Details

### Phase 1: Core Hardening
**Goal**: The existing codebase is stable, well-tested, performant, and has a formalized extensible data model ready for the action registry
**Depends on**: Nothing (first phase)
**Requirements**: HARD-01, HARD-02, HARD-03, HARD-04, HARD-05, HARD-06, HARD-07, HARD-08, HARD-09
**Success Criteria** (what must be TRUE):
  1. All previously excluded services (session, reweave, check, plugins, MCP _impl) have test coverage and no longer appear in coverage exclusion config
  2. Existing vaults can be upgraded to v2 schema via `ztlctl upgrade` command without data loss, and the tool detects stale schemas on startup
  3. NoteTypeDefinition exists as a registrable primitive — the four built-in content types (note, reference, task, garden) are defined as NoteTypeDefinitions with lifecycle transition maps
  4. CLI help text, README, and inline docs are accurate and consistent with actual behavior
  5. Performance-critical paths (rebuild, FTS5 scoring, betweenness centrality) are measurably faster than v1 baselines
**Plans**: 5 plans

Plans:
- [ ] 01-01-PLAN.md — NoteTypeDefinition + NoteTypeRegistry (HARD-02, HARD-09)
- [ ] 01-02-PLAN.md — Tech debt cleanup + security fixes (HARD-01, HARD-07)
- [ ] 01-03-PLAN.md — Performance bottleneck fixes (HARD-06)
- [ ] 01-04-PLAN.md — Test coverage gaps closed (HARD-05)
- [ ] 01-05-PLAN.md — Schema versioning + UX/docs audit (HARD-08, HARD-03, HARD-04)

### Phase 2: Action Registry
**Goal**: Every core operation is described as a declarative ActionDefinition in a central registry, ready for presentation layer generation
**Depends on**: Phase 1
**Requirements**: ACTN-01, ACTN-02
**Success Criteria** (what must be TRUE):
  1. ActionDefinition dataclass captures operation name, typed parameters, service method binding, and metadata for both CLI and MCP generation
  2. ActionRegistry collects all core operations, validates uniqueness, and provides lookup by name
  3. All existing service operations that have CLI commands or MCP tools are registered as ActionDefinitions with correct parameter types and metadata
**Plans**: 4 plans

Plans:
- [ ] 02-01-PLAN.md — ActionParam + ActionDefinition + ActionRegistry infrastructure (ACTN-01, ACTN-02)
- [ ] 02-02-PLAN.md — BaseController + read-heavy controllers (Check, Upgrade, Export, Graph, Vector, Reweave) (ACTN-02)
- [ ] 02-03-PLAN.md — Write-heavy + complex controllers (Create, Update, Query, Session, Ingest, Workflow, Init) (ACTN-02)
- [ ] 02-04-PLAN.md — Core registration of all ~50 ActionDefinitions + integration tests (ACTN-01, ACTN-02)

### Phase 3: MCP Surface Generation
**Goal**: MCP tools are auto-generated from the ActionRegistry, replacing hand-written registration and achieving complete parity with CLI capabilities
**Depends on**: Phase 2
**Requirements**: ACTN-03, AGNT-02, PLUG-04
**Success Criteria** (what must be TRUE):
  1. Running `ztlctl serve` exposes MCP tools for all operations that have CLI equivalents — including archive, extract, supersede, upgrade, check, init, and workflow (previously missing)
  2. Hand-written `register_tools()` code (~280 lines) is replaced by ActionRegistry-driven generation
  3. MCP tools that return large result sets (list, search, vault_review) accept a token-budget parameter and truncate responses accordingly
  4. A parity test suite verifies that every CLI command has a corresponding MCP tool with equivalent parameters
**Plans**: 2 plans

Plans:
- [ ] 03-01-PLAN.md — McpResponse model + MCP tool generator + server.py wiring + tools.py deletion (ACTN-03)
- [ ] 03-02-PLAN.md — Token-budget truncation for high-volume tools + parity test suite (AGNT-02, PLUG-04)

### Phase 4: CLI Surface Generation
**Goal**: CLI commands are auto-generated from the ActionRegistry, eliminating hand-crafted Click command duplication while preserving interactive and complex command behaviors
**Depends on**: Phase 3
**Requirements**: ACTN-04, ACTN-05
**Success Criteria** (what must be TRUE):
  1. Standard CRUD-style CLI commands (create, get, list, search, update, close, link, unlink) are generated from ActionDefinitions rather than hand-written
  2. Complex commands (batch, init wizard, serve, interactive create) retain hand-written implementations via documented escape hatch pattern
  3. Generated CLI commands support --verbose, --json, progressive disclosure, and exit codes identically to hand-written predecessors
  4. The parity test suite from Phase 3 continues to pass, confirming CLI/MCP equivalence is maintained by construction
**Plans**: 2 plans

Plans:
- [ ] 04-01-PLAN.md — ActionDefinition CLI metadata + CLI command generator module + unit tests (ACTN-04, ACTN-05)
- [ ] 04-02-PLAN.md — Generator wiring, command file migration, dynamic catalog, CLI parity tests (ACTN-04, ACTN-05)

### Phase 5: Plugin Formalization
**Goal**: Third-party plugin authors have a stable, versioned API to register custom note types, actions, hooks, and configuration
**Depends on**: Phase 4
**Requirements**: PLUG-01, PLUG-02, PLUG-03, PLUG-05, PLUG-06, PLUG-07
**Success Criteria** (what must be TRUE):
  1. Plugins declare a target PLUGIN_API_VERSION and the host validates compatibility at load time, warning on deprecated features with version-specific deprecation messages
  2. Plugins can register pre-action hooks (synchronous, via pluggy firstresult) that can modify inputs or abort actions before execution
  3. Plugin configuration is read from `[plugins.<name>]` sections in ztlctl.toml and validated against plugin-declared schemas
  4. A plugin can register a custom NoteTypeDefinition that automatically gains create/update/close CLI commands and MCP tools, plus custom Rich and MCP rendering
  5. GitPlugin and ReweavePlugin are ported to the new hookspecs, validating the API before it is marked stable
**Plans**: 3 plans

Plans:
- [ ] 05-01-PLAN.md — API versioning + pre/post-action hooks + plugin config infrastructure (PLUG-01, PLUG-02, PLUG-03)
- [ ] 05-02-PLAN.md — Custom note types + render contributions + marketplace metadata (PLUG-05, PLUG-06, PLUG-07)
- [ ] 05-03-PLAN.md — GitPlugin + ReweavePlugin migration to new hookspecs (PLUG-01, PLUG-02)

### Phase 6: Agentic Integration & Security
**Goal**: Agents can orchestrate ztlctl end-to-end without workarounds, with structured error recovery and progressive tool disclosure, and plugin-contributed workflows are security-constrained
**Depends on**: Phase 5
**Requirements**: AGNT-01, AGNT-03, AGNT-04, SECU-01, SECU-02
**Success Criteria** (what must be TRUE):
  1. Every ServiceResult error includes a machine-readable `recovery` field with actionable next steps that agents can follow programmatically
  2. MCP resources expose multi-step orchestration recipes (research-capture, review-triage, knowledge-synthesis) that agents can follow step-by-step
  3. MCP tool surface supports category-based activation — agents can discover tool categories and activate/deactivate them, preventing tool explosion from plugins
  4. Plugin-contributed Copier workflow templates execute with `--trust=false` by default, requiring explicit `--force-trust` to run template hooks
  5. Plugins declare required capabilities (filesystem, network, database, git) and the host validates access at load time with audit logging for plugin-initiated operations
**Plans**: TBD

Plans:
- [ ] 06-01: TBD
- [ ] 06-02: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3 -> 4 -> 5 -> 6

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Core Hardening | 4/5 | In Progress|  |
| 2. Action Registry | 3/4 | In Progress|  |
| 3. MCP Surface Generation | 2/2 | Complete   | 2026-03-19 |
| 4. CLI Surface Generation | 2/2 | Complete   | 2026-03-20 |
| 5. Plugin Formalization | 3/3 | Complete   | 2026-03-20 |
| 6. Agentic Integration & Security | 0/2 | Not started | - |
