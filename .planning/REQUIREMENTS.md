# Requirements: ztlctl v2

**Defined:** 2026-03-19
**Core Value:** Agents should only ever have to orchestrate the tool — not build custom functionality that is lacking from the tool.

## v1 Requirements

Requirements for this milestone. Each maps to roadmap phases.

### Core Hardening

- [x] **HARD-01**: Systematic tech debt cleanup — dead code removal, unenforced config enforcement (backup_retention_days, graph auto-materialize), stale index fixes (FTS5/vec divergence after rollback)
- [x] **HARD-02**: Data model consistency — lifecycle formalization, status transition edge case fixes, garden note protection validation
- [x] **HARD-03**: UX polish — CLI rough edges, missing flags, confusing output improvements, progressive disclosure consistency
- [x] **HARD-04**: Documentation audit — incorrect, missing, or unfriendly docs identified and fixed across README, help text, and inline docs
- [x] **HARD-05**: Test coverage gaps closed — session, reweave, check services lifted from coverage exclusion; plugin code (EventBus state machine, GitPlugin modes); MCP _impl functions tested
- [x] **HARD-06**: Performance bottleneck fixes — rebuild I/O parallelization via ThreadPoolExecutor, FTS5 batch BM25 scoring (single query vs per-candidate), betweenness centrality approximation (k parameter)
- [x] **HARD-07**: Security fixes — Copier trust flag enforcement, MCP HTTP transport binding warning, git commit message newline sanitization
- [x] **HARD-08**: Vault schema versioning with v1→v2 migration path via upgrade command; forward-compatible schema markers
- [x] **HARD-09**: NoteTypeDefinition as extensible primitive — formalizes note type + lifecycle transition map + Jinja2 template as one registrable unit; existing 4 content types (note, reference, task, garden) become built-in NoteTypeDefinitions

### Action Registry

- [x] **ACTN-01**: ActionDefinition dataclass — name, typed params (ActionParam), service method binding, CLI metadata (group, help, interactive params), MCP metadata (catalog entries, when_to_use, avoid_when)
- [x] **ACTN-02**: ActionRegistry — collects ActionDefinitions from core modules and plugins; validates uniqueness; provides lookup by name; single source of truth for all operations
- [x] **ACTN-03**: Auto-generated MCP tools from ActionDefinitions — replaces hand-written register_tools() (~280 lines); produces FastMCP tool registrations with JSON schema, catalog metadata, and side-effect annotations
- [x] **ACTN-04**: Auto-generated CLI commands from ActionDefinitions — replaces hand-crafted Click command files; handles interactive prompts, AppContext.emit(), exit codes, --verbose/--json flags, progressive disclosure
- [x] **ACTN-05**: Escape hatch preservation — batch operations, init wizard, serve command, and other complex commands retain hand-written implementations where the ActionDefinition abstraction doesn't fit

### Plugin System

- [x] **PLUG-01**: Plugin API versioning with deprecation helpers — explicit PLUGIN_API_VERSION constant; @deprecated decorator that warns for N versions before removal; compatibility checks at plugin load time
- [x] **PLUG-02**: Pre-action hooks with modification and cancellation — synchronous dispatch via pluggy firstresult pattern; plugins can modify action inputs or return a rejection to abort the action before execution
- [x] **PLUG-03**: Plugin configuration via `[plugins.<name>]` sections in ztlctl.toml — passed to plugins during initialization; validated against plugin-declared config schema
- [x] **PLUG-04**: Complete MCP tool parity with CLI — archive, extract, supersede, upgrade, check, init, workflow commands all have MCP tool equivalents (achieved by construction via ActionRegistry)
- [x] **PLUG-05**: Custom note types with custom lifecycles registered by plugins — plugins register NoteTypeDefinitions that automatically gain CLI commands (create, update, close) and MCP tools
- [x] **PLUG-06**: Plugin-contributed content type rendering — custom note types control their Rich CLI output and MCP response format via render contribution contracts
- [x] **PLUG-07**: Plugin marketplace metadata convention — structured metadata (name, version, author, capabilities, compatibility) in pyproject.toml `[tool.ztlctl-plugin]` section for future discoverability

### Agentic Integration

- [x] **AGNT-01**: Structured error responses with machine-readable recovery guidance — extend COMMON_ERROR_RECOVERY to cover all failure modes; every ServiceResult error includes actionable "what to do next" for agents
- [x] **AGNT-02**: Token-budget-aware MCP responses — extend existing topic_packet budget parameter pattern to list_items, search, vault_review, and other high-volume MCP tools
- [ ] **AGNT-03**: Agent orchestration recipe resources — defined multi-step workflows (research-capture, review-triage, knowledge-synthesis) exposed as MCP resources that agents can follow step-by-step
- [ ] **AGNT-04**: Progressive tool disclosure — category-based tool activation so plugins don't overwhelm the MCP tool surface; agents can discover and activate tool categories on demand

### Security

- [x] **SECU-01**: Copier `--trust=false` enforcement for plugin-contributed workflow templates — restrict template hook execution; require explicit --force-trust flag for plugin templates
- [x] **SECU-02**: Plugin capability declarations — plugins declare what they need (filesystem, network, database, git) and the host validates access; audit logging for plugin-initiated operations

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Advanced Plugin Features

- **ADVP-01**: Plugin sandboxing with process isolation — restrict plugin execution environment
- **ADVP-02**: Bidirectional MCP (sampling support) — MCP server requests LLM completions through client for auto-summarization
- **ADVP-03**: Plugin dependency graph — plugins can declare dependencies on other plugins with version constraints

### Advanced Agentic Features

- **ADVA-01**: Agent SDK/protocol integration — evaluate and implement if research proves value
- **ADVA-02**: MCP sampling for AI-powered enrichment — auto-summarization, smart reweave suggestions via server-initiated LLM calls

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| GUI/web interface | ztlctl is CLI/MCP-first; Obsidian serves as visual layer |
| Multi-user/collaboration | Local single-user tool; collaboration through shared repos |
| Cloud sync | Filesystem is storage layer; sync is user's responsibility |
| Mobile app | CLI tool; mobile access through Obsidian mobile or MCP clients |
| Runtime plugin hot-reload | Enormous complexity for short-lived CLI invocations; plugins load once at vault init |
| Plugin-to-plugin direct dependencies | Creates dependency graph nightmare; communicate via events and hooks only |
| AI-powered plugin generation | Produces unmaintainable code; provide docs and templates instead |
| Multi-transport MCP (WebSocket, gRPC) | stdio + HTTP cover all current MCP clients; revisit only if spec mandates |
| Agent framework bindings (LangChain, CrewAI) | MCP is the universal integration layer; framework-specific bindings couple to churning ecosystems |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| HARD-01 | Phase 1 | Complete |
| HARD-02 | Phase 1 | Complete |
| HARD-03 | Phase 1 | Complete |
| HARD-04 | Phase 1 | Complete |
| HARD-05 | Phase 1 | Complete |
| HARD-06 | Phase 1 | Complete |
| HARD-07 | Phase 1 | Complete |
| HARD-08 | Phase 1 | Complete |
| HARD-09 | Phase 1 | Complete |
| ACTN-01 | Phase 2 | Complete |
| ACTN-02 | Phase 2 | Complete |
| ACTN-03 | Phase 3 | Complete |
| ACTN-04 | Phase 4 | Complete |
| ACTN-05 | Phase 4 | Complete |
| PLUG-01 | Phase 5 | Complete |
| PLUG-02 | Phase 5 | Complete |
| PLUG-03 | Phase 5 | Complete |
| PLUG-04 | Phase 3 | Complete |
| PLUG-05 | Phase 5 | Complete |
| PLUG-06 | Phase 5 | Complete |
| PLUG-07 | Phase 5 | Complete |
| AGNT-01 | Phase 6 | Complete |
| AGNT-02 | Phase 3 | Complete |
| AGNT-03 | Phase 6 | Pending |
| AGNT-04 | Phase 6 | Pending |
| SECU-01 | Phase 6 | Complete |
| SECU-02 | Phase 6 | Complete |

**Coverage:**
- v1 requirements: 27 total
- Mapped to phases: 27
- Unmapped: 0

---
*Requirements defined: 2026-03-19*
*Last updated: 2026-03-19 after roadmap creation*
