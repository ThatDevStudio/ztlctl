# Milestones

## v2.0 Platform (Shipped: 2026-03-20)

**Phases completed:** 7 phases, 22 plans, 10 tasks

**Key accomplishments:**

- NoteTypeDefinition registry: formalized all note types as registrable, extensible primitives with lifecycle transitions
- ActionDefinition/ActionRegistry: 59 core operations described declaratively with typed params, CLI/MCP metadata in a single source of truth
- Auto-generated MCP tools: replaced 1,499 lines of hand-written registration with ActionRegistry-driven generation; token-budget truncation for high-volume tools
- Auto-generated CLI commands: eliminated 13 hand-written Click command files; 6 custom_presentation escape hatches preserved
- Stable Plugin API: versioned API (PLUGIN_API_VERSION=1) with pre/post-action hooks, custom note types, config injection, render contributions, marketplace metadata
- Agentic integration: structured error recovery (36 codes), orchestration recipes, progressive tool disclosure, capability-based plugin security

---
