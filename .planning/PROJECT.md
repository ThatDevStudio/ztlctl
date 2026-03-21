# ztlctl — Agentic Zettelkasten Platform

## What This Is

A production-grade CLI and MCP tool for managing a Zettelkasten knowledge system. ztlctl treats CLI and MCP as auto-generated presentation layers over a unified action/event system (ActionRegistry), with a stable plugin API for third-party extensions and deep agentic integration where agents orchestrate — never compensate for missing functionality.

## Core Value

Agents should only ever have to orchestrate the tool — not build custom functionality that is lacking from the tool.

## Requirements

### Validated

<!-- Shipped and confirmed valuable. -->

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
- ✓ Core hardening (tech debt, NoteTypeDefinition, performance, coverage, schema versioning, security) — v2.0
- ✓ ActionRegistry (59 ActionDefinitions, 13 controllers, define-once architecture) — v2.0
- ✓ Auto-generated MCP tools from ActionRegistry (59/59 parity, token budgets) — v2.0
- ✓ Auto-generated CLI commands from ActionRegistry (13 hand-written files replaced) — v2.0
- ✓ Stable Plugin API (versioning, pre/post hooks, config, custom note types, render contributions) — v2.0
- ✓ Agentic integration (structured error recovery, orchestration recipes, progressive disclosure, capability security) — v2.0
- ✓ MkDocs + mkdocs-shadcn docs site with two-track navigation (User Guide + Developer Guide) — v2.1
- ✓ User Guide content: paradigm guides, plugin guides, agentic workflow recipes, session lifecycle — v2.1
- ✓ Developer Guide: plugin authoring (719 lines), auto-generated API reference, architecture docs — v2.1
- ✓ Agent accessibility: llms.txt, llms-full.txt, `ztlctl docs` CLI, MCP doc search — v2.1
- ✓ Documentation quality pass: source-verified CLI examples, anti-patterns, best-practices.md, agents.md — v2.1
- ✓ Actions artifact deploy (gh-pages branch eliminated, trunk-based) — v2.1

### Active

<!-- Current milestone: v3.0 Memory and Hardening -->

## Current Milestone: v3.0 Memory and Hardening

**Goal:** Harden the core architecture (event model, action execution, plugin discovery) and add memory-layer features (session recall, polaris priorities, contradiction detection, ingestion pipeline, methodology guidance) that make ztlctl a persistent memory system for agents and humans.

**Target features:**
- Architecture remediation: reliable event delivery, single post_action producer, canonical payload, generic action executor, feature-local registration, centralized plugin runtime, compatibility cleanup
- Session Recall: temporal/topic/topology querying across session history
- Polaris Layer: persistent goals/priorities with MCP resource and context assembly integration
- Contradiction Detection: semantic integrity analysis using vector similarity
- Ingestion Pipeline: media/transcript → structured notes via source provider plugins
- Methodology Guidance: prose-as-title convention and title quality checks
- Tech debt: hardcoded embedding dims, EventBus timeout, dead-letter accumulation, MCP graceful shutdown, phantom mutation category, unused ServiceError.recovery, load_plugin_commands gap, bridges() k-approximation

### Out of Scope

<!-- Explicit boundaries. Includes reasoning to prevent re-adding. -->

- GUI/web interface — ztlctl is CLI/MCP-first; Obsidian serves as the visual layer
- Multi-user/collaboration — local single-user tool; collaboration through shared repos
- Cloud sync — filesystem is the storage layer; sync is the user's responsibility
- Mobile app — CLI tool; mobile access through Obsidian mobile or MCP clients

## Context

**Current state (v2.1 shipped):** 110 source files (26,439 LOC Python), 123 test files (24,726 LOC), 20 documentation pages (4,889 lines), mypy strict, ruff clean. 12 services, 14 controllers, 59 registered actions, 13 command groups, 3 built-in plugins, auto-generated MCP adapter (59 tools from ActionRegistry), and semantic search. Documentation: MkDocs + mkdocs-shadcn site with two-track navigation, llms.txt agent discovery, `ztlctl docs` CLI/MCP search, best-practices.md, and agents.md system manual. Architecture: 6-layer (domain → infrastructure → config → services → output → commands) with Vault repository pattern and 4-layer action model (Data/Service/Controller/Registry).

**Key architectural insight (realized):** CLI and MCP are auto-generated presentation layers over a unified ActionRegistry — define once, generate both surfaces. This is the foundation all future work builds on.

**Known technical debt (from v2.0 audit):**
- Hardcoded embedding dimensions, EventBus timeout not configurable, dead-letter event accumulation, MCP server missing graceful shutdown
- Phantom `mutation` category in _DEFAULT_ACTIVE_CATEGORIES (self-resolves with plugins)
- ServiceError.recovery field unused by services (COMMON_ERROR_RECOVERY fallback covers all 37 codes)
- load_plugin_commands creates separate PluginManager without inject_configs (edge case)
- bridges() betweenness centrality without k-approximation

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
| CLI/MCP as auto-generated presentation layers | Define-once, use-everywhere — reduces duplication, ensures parity | ✓ Good — 59 ActionDefinitions auto-generate both CLI and MCP surfaces |
| Formalize note lifecycle as extensible primitive | Plugins need to define custom note types with custom lifecycles | ✓ Good — NoteTypeDefinition + NoteTypeRegistry in domain/registry.py |
| Research Agent SDK/protocol viability | User's instinct is define-once interfaces; SDK adds value only if research proves it | — Pending |
| Core hardening before plugin formalization | Tool must be standalone-capable before extending; fixes foundation first | ✓ Good — Phase 1 complete |
| 4-layer architecture (Data/Service/Controller/Registry) | Controllers wrap services, registry wraps controllers — clean separation of concerns | ✓ Good — 13 controllers + ActionRegistry in Phase 2 |
| All operations through registry, no escape hatches | Complex ops get thin definitions with custom_presentation=True | ✓ Good — 59 definitions, 5 custom_presentation |

---
| Pre/post-action hooks wired into all controllers | Plugins can observe/modify/reject any action via hook dispatch | ✓ Good — 63 methods across 14 controllers wired in Phase 7 |
| Category activation is advisory metadata | FastMCP cannot deregister tools dynamically; agents use categories for tool selection heuristics | ✓ Good — documented in Phase 7, AGNT-04 description updated |

| Two-track documentation (user guide + developer guide) | Knowledge workers and plugin authors have fundamentally different needs; flat docs serve neither well | ✓ Good — 10 User Guide pages, 5 Developer Guide pages, distinct tone per track |
| llms.txt + MCP doc search for agent accessibility | Agents are a primary audience; standard machine-readable discovery + in-tool search | ✓ Good — llms.txt (20 pages), docs search CLI + MCP, agents.md system manual |
| MkDocs + mkdocs-shadcn for docs site | Modern shadcn/ui aesthetic, MkDocs ecosystem for Python tools, GitHub Pages deploy | ✓ Good — `mkdocs build --strict` passes, artifact-based deploy |
| Source-verified documentation | Every CLI example, hookspec, and config option must be verified against source code | ✓ Good — 15+ inaccurate commands fixed, configuration.md fully rewritten from models.py |
| Three-audience documentation model | End users (mentor tone), developers (peer tone), agents (structured schemas) | ✓ Good — best-practices.md + agents.md serve distinct reading patterns |

---
*Last updated: 2026-03-21 after v3.0 milestone started*
