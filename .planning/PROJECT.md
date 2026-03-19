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

**Core Hardening:**
- [ ] Systematic audit and fix of technical debt (dead code, unenforced config, stale indexes)
- [ ] Data model consistency (note lifecycle formalization, edge cases in status transitions)
- [ ] UX polish (CLI rough edges, confusing output, missing flags)
- [ ] Documentation audit (incorrect, missing, or unfriendly docs)
- [ ] Test coverage gaps closed (session, reweave, check, plugins, MCP _impl functions)
- [ ] Performance bottleneck fixes (rebuild I/O, per-candidate FTS5, betweenness centrality)
- [ ] Security hardening (Copier trust, MCP HTTP warnings, git commit message sanitization)

**Plugin System Formalization:**
- [ ] Formalize "note" and "note lifecycle" as extensible core primitives
- [ ] Formalize "action" and "event" as the core operational model
- [ ] Define-once interface: CLI and MCP as auto-generated presentation layers over core actions
- [ ] Plugins can register custom note types with custom lifecycles
- [ ] Plugins can register CLI commands and MCP tools
- [ ] Plugins can extend templates
- [ ] Plugins can hook pre/post on every core action
- [ ] Plugin access to core actions and events

**Agentic Integration:**
- [ ] Complete MCP tool surface (no gaps — agents never need workarounds)
- [ ] Agent orchestration patterns (defined workflows agents can drive end-to-end)
- [ ] Research and evaluate Agent SDK/protocol if warranted
- [ ] Agentic workflow documentation (how agents should use the tool)

### Out of Scope

<!-- Explicit boundaries. Includes reasoning to prevent re-adding. -->

- GUI/web interface — ztlctl is CLI/MCP-first; Obsidian serves as the visual layer
- Multi-user/collaboration — local single-user tool; collaboration through shared repos
- Cloud sync — filesystem is the storage layer; sync is the user's responsibility
- Mobile app — CLI tool; mobile access through Obsidian mobile or MCP clients

## Context

**Existing codebase:** 1256 tests, mypy strict, ruff clean across 12 services, 9 command groups, 3 built-in plugins, MCP adapter, and semantic search. The v1 architecture is a clean 6-layer structure (domain → infrastructure → config → services → output → commands) with a Vault repository pattern.

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
| Formalize note lifecycle as extensible primitive | Plugins need to define custom note types with custom lifecycles | — Pending |
| Research Agent SDK/protocol viability | User's instinct is define-once interfaces; SDK adds value only if research proves it | — Pending |
| Core hardening before plugin formalization | Tool must be standalone-capable before extending; fixes foundation first | — Pending |

---
*Last updated: 2026-03-19 after initialization*
