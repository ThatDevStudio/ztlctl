# Project Research Summary

**Project:** ztlctl v2 — Plugin Formalization, Define-Once Actions, Agentic Integration
**Domain:** Extensible plugin-based CLI/MCP tool for Zettelkasten knowledge management
**Researched:** 2026-03-19
**Confidence:** HIGH

## Executive Summary

ztlctl v2 is a post-v1-complete evolution of a mature CLI tool (1256 tests, mypy strict, ruff clean) into a formally extensible, agent-ready platform. The core challenge is not building a new product — it is formalizing and unifying what already exists without breaking it. Three interrelated goals drive the work: (1) eliminating ~3000 lines of duplicated CLI/MCP surface code through a "define-once" action registry, (2) formalizing the plugin system so third-party authors have a stable, versioned contract to build against, and (3) completing the MCP tool surface so AI agents can orchestrate ztlctl without gaps or workarounds.

The recommended approach is a layered, dependency-ordered build: start by stabilizing the data model and lifecycle formalization (core hardening), then introduce the ActionDefinition/ActionRegistry infrastructure as an internal abstraction, then auto-generate the MCP surface (lower risk, fewer edge cases), then auto-generate the CLI surface (higher complexity due to interactive prompts and output formatting), then expose the formalized plugin API with versioning. The existing service layer, vault pattern, and 6-layer architecture are not changed — the action registry is a thin declarative mapping layer inserted above services and below the presentation layers.

The primary risks are (a) premature plugin API freeze before the action model is validated — which destroys third-party trust if hooks change after publication — and (b) parity regression during the CLI/MCP unification where capabilities silently disappear as hand-crafted surfaces are replaced with generated ones. Both are mitigated by the same practice: build parity tests before starting, migrate incrementally, keep the existing surfaces running in parallel during transition, and only promote the plugin API to stable after the built-in plugins (GitPlugin, ReweavePlugin) have been successfully ported to the new API.

## Key Findings

### Recommended Stack

The v1 stack (Python 3.13, Click, Pydantic, SQLAlchemy Core, NetworkX, Rich, structlog, pluggy, Jinja2, Copier, sqlite-vec) is unchanged. Two targeted updates are recommended. First, bump the `mcp` optional dependency from `>=1.0` to `>=1.26.0` to pick up Streamable HTTP transport (which supersedes SSE for production deployments) and improved tool schemas. Second, bump the `pluggy` pin from `>=1.4` to `>=1.6.0` for a bugfix release with no API changes. No new runtime dependencies are introduced — the define-once action registry is a ~500 LOC custom implementation because no existing library (pydanclick, clidantic, pydantic-cli) handles the Click-groups-plus-MCP-schema use case adequately.

**Core technologies:**
- Custom `ActionRegistry` (~500 LOC): define-once source of truth — no library is mature enough for this use case
- `mcp>=1.26.0`: Streamable HTTP transport for production MCP deployments
- `pluggy>=1.6.0`: pin bump for bugfixes, existing hookspec/hookimpl pattern is the correct abstraction
- Agent frameworks (OpenAI Agents SDK, PydanticAI): explicitly rejected — ztlctl is a tool agents use, not an agent itself; MCP is the correct integration layer

### Expected Features

See `.planning/research/FEATURES.md` for full feature landscape.

**Must have (table stakes):**
- Pre-action hooks with modification/cancellation — v1 has post_ hooks only; pre_ hooks with abort semantics complete the contract
- Plugin API versioning with deprecation helpers — silent breakage destroys third-party trust faster than anything else
- Plugin configuration via `ztlctl.toml` (`[plugins.<name>]` sections) — plugins without config are limited to hardcoded behavior
- Complete MCP tool parity with CLI — agents cannot work around missing tools; archive, extract, supersede, upgrade, check, init, workflow currently have no MCP equivalents
- Define-once action registry — eliminates ~1500 lines of MCP wrapper duplication and ensures parity by construction

**Should have (competitive):**
- Custom note types with plugin-registered lifecycles — no other Zettelkasten tool offers this; high value, high complexity
- Token-budget-aware MCP responses — extend existing `topic_packet` budget param to list, search, vault_review
- Plugin-contributed content type rendering — custom note types need custom Rich/MCP output
- Agent orchestration recipes as MCP resources — makes agent behavior predictable and debuggable
- Plugin marketplace metadata convention (`pyproject.toml` section) — enables future discoverability

**Defer:**
- Plugin sandboxing with capability declarations — important at scale; overkill before third-party plugins exist
- Bidirectional MCP (sampling) — adds LLM dependency to core tool; contradicts "works fully without agentic systems"
- AI-powered plugin generation — produces unmaintainable code with subtle bugs
- Runtime plugin hot-reload — enormous complexity for short-lived CLI invocations

### Architecture Approach

The v2 architecture inserts a single new layer — the ActionRegistry — between the existing service layer and the existing presentation layers (CLI commands, MCP tools). Services are unchanged. CLI and MCP become thin, auto-generated adapters over ActionDefinitions. Plugins can register ActionDefinitions and NoteTypeDefinitions into the same registries, gaining auto-generated CLI commands and MCP tools without writing Click or FastMCP boilerplate. The existing hookspecs for `register_cli_commands()` and `register_mcp_tools()` are retained as escape hatches for the ~10% of cases (batch, init, serve) that cannot be expressed through the abstraction.

**Major components:**
1. **ActionDefinition + ActionRegistry** — declarative dataclass describing one operation (name, params, service method binding, CLI/MCP metadata); registry collects definitions from core and plugins; single source of truth
2. **NoteTypeDefinition + NoteTypeRegistry** — bundles ContentModel subclass + lifecycle transition map + Jinja2 template into one registrable unit; `generate_actions()` auto-produces ActionDefinitions so a new note type automatically gets both CLI and MCP surfaces
3. **CLI Generator** — reads ActionRegistry, produces Click commands; handles CLI-specific concerns (interactive prompts, AppContext.emit(), exit codes, `--verbose`/`--json` flags)
4. **MCP Generator** — reads ActionRegistry, produces FastMCP tool registrations with catalog metadata; simpler than CLI generator (no interactive mode, no output formatting)
5. **PluginManager (extended)** — new hookspecs: `register_actions()`, `register_note_types()`; existing hookspecs preserved for compatibility

### Critical Pitfalls

1. **Premature plugin API freeze** — formalizing the API before the action model is validated guarantees churn that breaks third-party plugins. Keep the API marked `experimental` until all three built-in plugins (GitPlugin, ReweavePlugin, plus a test plugin) are successfully ported to the new hookspecs.

2. **CLI/MCP parity regression during unification** — the ~3000 lines of hand-crafted CLI and MCP surfaces contain presentation logic that is hard to auto-generate (Click types like `click.Choice`, progressive disclosure, exit codes). Build a parity test suite asserting CLI/MCP equivalence before starting, then migrate incrementally (read-only tools first).

3. **Breaking existing vaults during lifecycle formalization** — moving lifecycle maps from compile-time constants to runtime-registered definitions can invalidate existing vault frontmatter. The formalized system must treat current four lifecycle maps as built-in defaults; notes with no `lifecycle_version` are implicitly v1.

4. **Action model becomes a god object** — the temptation to capture CLI metadata, MCP metadata, event hooks, telemetry spans, and permissions in one `ActionDefinition` produces a 200-field monster. Use layered annotations: core action (name + params + service method), with separate optional CLI and MCP annotation layers. Complexity budget: 50 lines per action definition.

5. **EventBus misused for synchronous pre-hooks** — the WAL-backed async EventBus is correct for fire-and-forget post-event notifications but wrong for pre-hooks that must abort before an action proceeds. Pre-hooks must be synchronous via pluggy's `firstresult` pattern; post-hooks remain async via EventBus.

## Implications for Roadmap

Based on research, the natural phase structure follows the dependency chain: data model stability unlocks lifecycle formalization, which unlocks the action registry, which unlocks CLI/MCP auto-generation, which unlocks plugin API publication. Each phase proves the foundation for the next.

### Phase 1: Core Hardening
**Rationale:** The lifecycle formalization (extensible note types) and vault migration path must be stable before any other v2 work. If the data model shifts after the action registry is built, everything above it needs revision. This phase has no new external dependencies — it is refactoring and validation of existing code.
**Delivers:** Stable `NoteTypeDefinition` as an extensible primitive; vault schema versioning; `upgrade` command for v1 -> v2 migration; validated migration path for existing vaults.
**Addresses:** Complete MCP parity (archive, extract, supersede, upgrade gaps); lifecycle transition safety
**Avoids:** Breaking existing vaults (Pitfall 3); `check --rebuild` regressions

### Phase 2: Action Registry Infrastructure
**Rationale:** The ActionDefinition and ActionRegistry are pure infrastructure with no external consumers yet. This phase builds and validates the core abstraction against real operations without changing any user-facing surface. The registry must be proven correct before CLI or MCP generation is layered on top.
**Delivers:** `actions/` package with `ActionDefinition`, `ActionParam`, `ActionRegistry`; all existing core operations registered as ActionDefinitions; full test coverage of registry behavior
**Addresses:** Define-once action registry (internal phase)
**Avoids:** Action model god object (Pitfall 4) — design validated internally before external consumers

### Phase 3: MCP Surface Generation
**Rationale:** MCP tools are simpler to auto-generate than CLI commands (no interactive prompts, no output formatting, no exit codes). Proving the generation pattern against the MCP surface first validates the ActionDefinition design with the lower-risk surface before tackling CLI complexity.
**Delivers:** `ActionRegistry.generate_mcp_tools()` replacing hand-written `register_tools()`; MCP tool parity for all CLI commands (archive, extract, supersede, upgrade, check, init, workflow); stale_indexes field in write responses; token-budget-aware responses extended
**Addresses:** Complete MCP tool parity with CLI; agent state staleness (Pitfall 8); token budget accuracy (Pitfall 12)
**Avoids:** MCP tool explosion (Pitfall 6) — implement tool category filtering before plugins can add tools

### Phase 4: CLI Surface Generation
**Rationale:** CLI generation is more complex than MCP generation (interactive prompts, TTY detection, output formatting, exit codes). It comes after MCP generation validates the pattern. The parity test suite built in Phase 3 serves as the regression gate.
**Delivers:** `ActionRegistry.generate_click_commands()` replacing hand-crafted command files; escape hatch preservation for batch/init/serve; full CLI/MCP parity by construction
**Addresses:** ~1500 lines of wrapper duplication eliminated; CLI/MCP parity maintained structurally
**Avoids:** Parity regression (Pitfall 2) — parity tests run as regression gate

### Phase 5: Plugin System Formalization
**Rationale:** The plugin API can only be published once the action model is stable — publishing it before Phase 2-4 prove the design risks the premature freeze pitfall. This phase ports all built-in plugins to the new API, validates it, then marks it stable.
**Delivers:** `register_actions()` and `register_note_types()` hookspecs; plugin API versioning with deprecation helpers; plugin configuration via `[plugins.<name>]` TOML; pre-action hooks (synchronous, via pluggy firstresult); GitPlugin and ReweavePlugin ported to new API; plugin marketplace metadata convention
**Addresses:** Plugin API versioning; pre/post hooks; plugin TOML configuration; plugin-contributed note types
**Avoids:** Premature API freeze (Pitfall 1); EventBus misuse for pre-hooks (Pitfall 7); plugin discovery race condition (Pitfall 5)

### Phase 6: Agentic Integration Polish
**Rationale:** With a complete, parity-guaranteed CLI/MCP surface and a formalized plugin API, this phase focuses on the agent-facing experience: orchestration recipes, progressive tool disclosure, and agent state transparency.
**Delivers:** Agent orchestration recipe resources (research-capture, review-triage, knowledge-synthesis); progressive tool disclosure (category-based activation); `stale_indexes` in all write responses; compact tool description mode; plugin tool namespacing
**Addresses:** Agent orchestration recipes; MCP tool explosion mitigation; token budget accuracy
**Avoids:** Tool explosion (Pitfall 6); agent state assumptions (Pitfall 8)

### Phase 7: Security Hardening
**Rationale:** Plugin sandboxing and Copier trust restrictions are deferred until plugin-contributed workflows are actually possible (Phase 5). Addressing security before the feature exists wastes effort.
**Delivers:** Copier `--trust=false` enforcement for plugin-contributed templates; plugin capability declarations; audit logging for plugin-initiated executions
**Addresses:** Plugin security escalation (Pitfall 9)
**Avoids:** Trust escalation via plugin-contributed Copier templates

### Phase Ordering Rationale

- Phase 1 before Phase 2: lifecycle formalization changes domain types that ActionDefinitions reference; must be stable first
- Phase 2 before Phases 3 and 4: ActionRegistry is the shared foundation; both generators depend on it
- Phase 3 before Phase 4: MCP has simpler semantics; validates the generation pattern before CLI complexity
- Phase 4 before Phase 5: plugin API cannot be frozen until it is proven against generated CLI/MCP surfaces
- Phase 5 before Phase 6: agent orchestration recipes reference plugin-contributed tools; plugin system must be stable
- Phase 5 before Phase 7: security hardening for plugin workflows is only relevant after plugins can contribute workflows

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 4 (CLI Generation):** Click dynamic command generation has subtle edge cases (command groups, custom types, `invoke_without_command`, `result_callback`). The impedance mismatch between ActionParam types and Click types (Choice, Path, IntRange) needs careful mapping research before implementation.
- **Phase 5 (Plugin Formalization):** Pre-hook design (synchronous abort semantics, hook ordering with `tryfirst`/`trylast`, interaction with the async EventBus) needs explicit design research. The pluggy `firstresult` pattern is the right mechanism but the integration with `BaseService._dispatch_event()` needs a clear protocol.

Phases with standard patterns (skip research-phase):
- **Phase 1 (Core Hardening):** All work is refactoring existing code with well-understood patterns (Pydantic model migration, vault schema versioning). No new external dependencies.
- **Phase 2 (Action Registry):** Declarative dataclass registry is a well-understood pattern. The design is fully specified in ARCHITECTURE.md.
- **Phase 3 (MCP Generation):** FastMCP tool registration is well-documented. The existing 29 `_impl` functions provide the reference implementation.
- **Phase 7 (Security):** Copier trust flags and audit logging are straightforward; no novel patterns required.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | No new dependencies; two minor version bumps verified on PyPI. Custom action registry is an architectural decision, not a library gap. |
| Features | HIGH | Grounded in both existing v1 codebase analysis (concrete gaps) and established plugin ecosystem patterns (Obsidian, pytest, webpack). Anti-features clearly justified. |
| Architecture | HIGH | ActionDefinition/ActionRegistry pattern is validated against the existing `_impl` function structure. Build order has concrete phase dependencies. Migration strategy is incremental. |
| Pitfalls | HIGH | Most pitfalls are grounded in existing codebase analysis (specific files, line counts, concrete failure modes) rather than generic warnings. Phase mapping is precise. |

**Overall confidence:** HIGH

### Gaps to Address

- **Click type mapping table:** The exact mapping from `ActionParam.type` to Click option types (Choice, Path, IntRange, multiple=True) is not fully specified. Needs a concrete mapping table before Phase 4 implementation begins.
- **Pre-hook abort protocol:** The exact contract for pre-hooks (what they return, what exception they raise to abort, how this interacts with `ServiceResult`) is described conceptually but not specified concretely. Needs a precise protocol spec before Phase 5.
- **Plugin API version scheme:** Whether the plugin API version is pinned to the project SemVer or managed independently (e.g., `PLUGIN_API_VERSION = "2.0"`) is not decided. Needs a decision before Phase 5 publishes the stable API.
- **Test plugin for validation:** The "validate the plugin API with a test plugin before marking stable" recommendation requires a concrete test plugin. This plugin needs to be specified during Phase 5 planning.

## Sources

### Primary (HIGH confidence)
- MCP Python SDK — PyPI (v1.26.0 verified 2026-03-19)
- pluggy — PyPI (v1.6.0 verified 2026-03-19)
- Model Context Protocol specification — modelcontextprotocol.io
- ztlctl v1 codebase — `src/ztlctl/plugins/hookspecs.py`, `contracts.py`, `mcp/tools.py`, `plugins/event_bus.py`, `services/base.py`, `.planning/codebase/CONCERNS.md`

### Secondary (MEDIUM confidence)
- Obsidian plugin ecosystem — plugin API patterns, 1500+ community plugins as reference
- pluggy documentation — hookspec patterns, firstresult, trylast/tryfirst
- FastMCP tools documentation — tool registration patterns
- AI agents CLI + MCP design patterns — RudderStack, Unified.to articles

### Tertiary (LOW confidence)
- Agentic workflow patterns 2025-2026 — Vellum AI blog (emerging patterns, not yet established)
- Plugin sandbox bypass CVE-2026-33139 — specific advisory informing security hardening approach

---
*Research completed: 2026-03-19*
*Ready for roadmap: yes*
