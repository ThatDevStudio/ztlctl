# ztlctl v2 — Hardening, Plugins & Agentic Integration

## What This Is

The next evolution of ztlctl: a systematic hardening pass across the core tool, a formalized plugin architecture that treats CLI and MCP as presentation layers over a unified action/event system, and deep agentic integration where agents orchestrate — never compensate for missing functionality. This milestone takes ztlctl from a working v1 to a production-grade, extensible platform.

## Core Value

Agents should only ever have to orchestrate the tool — not build custom functionality that is lacking from the tool.

## Requirements

### Validated

<!-- Shipped and confirmed valuable in v1 (Phases 0-9). -->

- ✓ Content creation pipeline (notes, references, tasks) with 6-stage pipeline — v1
- ✓ Query engine (search, get, list, work-queue, decision-support) — v1
- ✓ Graph engine (related, themes, rank, path, gaps, bridges) — v1
- ✓ Reweave engine (4-signal scoring, prune, undo) — v1
- ✓ Update/close pipeline with status transitions — v1
- ✓ Session lifecycle (start, close, reopen, enrichment) — v1
- ✓ Integrity scanner (4-category scan, backup/restore, rebuild) — v1
- ✓ Rich CLI output with progressive disclosure — v1
- ✓ Init/export/agent-regenerate lifecycle — v1
- ✓ Plugin system (pluggy hookspecs, EventBus, entry-point discovery) — v1
- ✓ MCP adapter (12 tools, 6 resources, 4 prompts, stdio + HTTP) — v1
- ✓ Verbose telemetry (structlog, @traced, span trees) — v1
- ✓ Semantic search (sqlite-vec, sentence-transformers, hybrid ranking) — v1
- ✓ Workflow templates (Copier-based scaffold) — v1
- ✓ Obsidian integration (vault generation, client config) — v1

### Active

<!-- Current scope. Building toward these. -->

**Core Hardening:** ✓ Validated in Phase 1
- [x] Systematic audit and fix of technical debt (dead code, unenforced config, stale indexes)
- [x] Data model consistency (NoteTypeDefinition formalization, lifecycle transition maps)
- [x] UX polish (CLI help text, README command reference)
- [x] Documentation audit (README updated, serve warnings added)
- [x] Test coverage gaps closed (1553 tests, 87.66% coverage, omit list cleared)
- [x] Performance bottleneck fixes (parallel rebuild I/O, batch FTS5, betweenness k-approx)
- [x] Security hardening (git sanitization, MCP HTTP warnings, Copier trust documented)

**Action Registry:** ✓ Validated in Phase 2
- [x] ActionDefinition/ActionParam frozen dataclasses with typed parameters, CLI/MCP metadata
- [x] ActionRegistry singleton with register/get/list_actions, name-uniqueness enforcement
- [x] 13-controller layer (BaseController + domain controllers) wrapping all services
- [x] 59 ActionDefinitions registered covering all public controller methods
- [x] custom_presentation=True on complex operations (batch, init, workflow)

**MCP Surface Generation:** ✓ Validated in Phase 3
- [x] Auto-generated MCP tools from ActionRegistry (generator.py replaces 1499-line tools.py)
- [x] McpResponse/McpError Pydantic models for typed MCP responses
- [x] Token-budget-aware truncation on high-volume tools (list_items, search, vault_review, decision_support)
- [x] Parity test suite: 59/59 ActionDefinitions exposed as MCP tools, 13/13 categories covered
- [x] 9 previously missing tools now present (archive, supersede, upgrade, check, init, workflow)

**CLI Surface Generation:** ✓ Validated in Phase 4
- [x] Auto-generated CLI commands from ActionRegistry (generator.py replaces ~2650 lines of hand-written Click commands)
- [x] cli_name field + cli_group assignments on all 59 ActionDefinitions
- [x] 6 custom_presentation actions preserved (batch, update, init wizard, serve, workflow, export)
- [x] CLI parity test suite: every non-custom ActionDefinition has a CLI command
- [x] 13 hand-written command files deleted, replaced by runtime generation

**Plugin System Formalization:** ✓ Validated in Phase 5
- [x] Formalize "note" and "note lifecycle" as extensible core primitives
- [x] Formalize "action" and "event" as the core operational model
- [x] Define-once interface: CLI and MCP as auto-generated presentation layers over core actions
- [x] Plugins can register custom note types with custom lifecycles (auto-gain CLI + MCP)
- [x] Plugins can register CLI commands and MCP tools (via ActionRegistry)
- [x] Plugins can hook pre/post on every core action (pre_action/post_action hookspecs)
- [x] Plugin API versioning (PLUGIN_API_VERSION=1) + deprecated hookspec warnings
- [x] Plugin config from [plugins.<name>] in ztlctl.toml, Pydantic-validated
- [x] Render contributions for custom note types (Rich + MCP formatters)
- [x] Marketplace metadata convention ([tool.ztlctl-plugin] in pyproject.toml)
- [x] GitPlugin + ReweavePlugin ported to post_action + EventBus bridge
- [x] Plugin access to core actions and events (via pre_action/post_action hookspecs)

**Agentic Integration & Security:** ✓ Validated in Phase 6
- [x] Complete MCP tool surface (no gaps — agents never need workarounds)
- [x] Structured error recovery — ServiceError.recovery field + 36 COMMON_ERROR_RECOVERY entries
- [x] Agent orchestration recipes — 3 MCP resources (research-capture, review-triage, knowledge-synthesis)
- [x] Progressive tool disclosure — category-based activation (discover/activate/deactivate categories)
- [x] Copier --trust=false for plugin-contributed templates + --force-trust override
- [x] Plugin capability declarations (filesystem, network, database, git) with audit logging

### Out of Scope

<!-- Explicit boundaries. Includes reasoning to prevent re-adding. -->

- GUI/web interface — ztlctl is CLI/MCP-first; Obsidian serves as the visual layer
- Multi-user/collaboration — local single-user tool; collaboration through shared repos
- Cloud sync — filesystem is the storage layer; sync is the user's responsibility
- Mobile app — CLI tool; mobile access through Obsidian mobile or MCP clients

## Context

**Existing codebase:** 1622 tests, mypy strict, ruff clean across 12 services, 13 controllers, 59 registered actions, 9 command groups, 3 built-in plugins, auto-generated MCP adapter (59 tools from ActionRegistry), and semantic search. The v1 architecture is a clean 6-layer structure (domain → infrastructure → config → services → output → commands) with a Vault repository pattern.

**Key architectural insight from user:** CLI and MCP should be "presentation wrappers around a core construct" — this means the current hand-crafted CLI commands and MCP tools need to evolve into auto-generated surfaces over formalized actions. This is the single biggest architectural shift in v2.

**Known technical debt:** Hardcoded embedding dimensions, unenforced config settings (backup_retention_days), graph materialize not auto-triggered, EventBus timeout not configurable, dead-letter event accumulation, MCP server missing graceful shutdown.

**Known test gaps:** Session, reweave, and check services excluded from coverage; all plugin code excluded; MCP layer has zero coverage; _impl pattern investment is wasted without tests.

**Target audience:** Small group of users, building toward broader adoption. Tool must work fully without agentic systems.

## Constraints

- **Tech stack**: Python 3.13, uv, Click, Pydantic, SQLAlchemy Core, pluggy — no framework changes
- **Backward compatibility**: Existing vaults and configs must continue to work (migration path for schema changes)
- **Plugin API stability**: Once formalized, the plugin API becomes a contract — design carefully before exposing
- **MCP compatibility**: Must remain compatible with Claude Desktop and other MCP clients
- **Performance**: Operations must remain responsive for vaults up to ~5,000 notes

## Key Decisions

<!-- Decisions that constrain future work. Add throughout project lifecycle. -->

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| CLI/MCP as auto-generated presentation layers | Define-once, use-everywhere — reduces duplication, ensures parity | — Pending |
| Formalize note lifecycle as extensible primitive | Plugins need to define custom note types with custom lifecycles | ✓ Good — NoteTypeDefinition + NoteTypeRegistry in domain/registry.py |
| Research Agent SDK/protocol viability | User's instinct is define-once interfaces; SDK adds value only if research proves it | — Pending |
| Core hardening before plugin formalization | Tool must be standalone-capable before extending; fixes foundation first | ✓ Good — Phase 1 complete |
| 4-layer architecture (Data/Service/Controller/Registry) | Controllers wrap services, registry wraps controllers — clean separation of concerns | ✓ Good — 13 controllers + ActionRegistry in Phase 2 |
| All operations through registry, no escape hatches | Complex ops get thin definitions with custom_presentation=True | ✓ Good — 59 definitions, 5 custom_presentation |

---
*Last updated: 2026-03-20 after Phase 6 completion — ALL PHASES COMPLETE*
