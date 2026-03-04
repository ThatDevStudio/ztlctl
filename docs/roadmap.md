---
title: Product Roadmap
nav_order: 11
---

# Product Roadmap

This roadmap starts from the current post-backlog baseline:

- dynamic workspace profiles are in place
- the first-party Obsidian starter kit is shipped
- `garden/` is scaffolded but human-owned
- export is positioned as an external review workbench
- the old `research` parity backlog is closed

The next roadmap should optimize for product value from here, not for further parity with the old PoC workspace.

## Roadmap Principles

- Keep the file-first core fast, durable, and predictable.
- Improve capture, synthesis, and review loops before adding more surface area.
- Treat Obsidian as a strong companion workspace, not as a configuration lifecycle owned by ztlctl.
- Extend through plugins and source providers where that keeps the core clean.
- Avoid reopening non-goals such as full `research` migration parity, garden indexing, or durable conversation markdown.

## Near-Term Priorities

### 1. Capture and Source Fidelity

Strengthen the path from raw input to durable evidence:

- richer source-bundle normalization for agent captures
- better provenance handling for multimodal ingestion
- stronger source-provider ergonomics and diagnostics
- clearer durable boundaries between captured source artifacts and synthesized notes

### 2. Review and Synthesis Ergonomics

Make the machine-layer review loop more useful without turning it into a second workspace:

- better review packets and topic dossiers
- stronger prioritization and explanations in work/review queues
- improved draft and decision-support flows
- tighter guidance for turning machine-layer signals into human garden work

### 3. Obsidian Quality of Life

Improve the starter kit without reclaiming ownership of `.obsidian/` after init:

- better templates and examples for common garden workflows
- curated starter-kit refinements where defaults are clearly useful
- optional plugin/profile extensions that add value without increasing core complexity
- clearer documentation for operating the hybrid vault day to day

### 4. Plugin and Extension Maturity

Build on the profile/plugin system now that the architecture exists:

- more robust plugin discovery and diagnostics
- stronger contracts for profile and source-provider contributions
- safer extension failure isolation
- better developer ergonomics for plugin authors

### 5. Trust, Performance, and Product Polish

Keep the core credible as usage scales:

- drift-resistant docs and generated guidance
- performance work on indexing, retrieval, and graph operations
- clearer CLI/MCP affordances for common tasks
- continued test coverage around compatibility boundaries and exported workflow assets

## Explicit Non-Goals

These are intentionally not the current roadmap:

- automatic migration/import from the old `research` workspace
- a lifecycle engine that validates or rewrites user-edited `.obsidian/` files
- indexing `garden/` as part of the core machine layer
- bringing back durable conversation markdown as a first-class content type
- expanding export into a live vault-integrated workspace surface

## How to Read This with the Backlog

- [Hybrid Workspace Closure Record](backlog.md) explains what was closed and why.
- [Research to ztlctl Mapping](research-mapping.md) explains how the old workspace concepts map to the current product.
- This page is the forward-looking product direction from the new baseline.
