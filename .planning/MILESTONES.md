# Milestones

## v3.1 Documentation & Hardening (Shipped: 2026-03-22)

**Phases completed:** 2 phases, 3 plans, 4 tasks

**Key accomplishments:**

- 1. [Rule 2 - Auto-fix] Scoped pymarkdown scan to exclude docs/plans/
- Documentation enforcement rule added to CLAUDE.md, IngestService post_action dispatch wired for both note and reference success paths, stale docstrings corrected
- One-liner:

---

## v3.0 Memory and Hardening (Shipped: 2026-03-21)

**Phases completed:** 8 phases, 20 plans, 27 tasks

**Key accomplishments:**

- EventBusConfig frozen model with 4 configurable fields, ActionEvent domain event model, and EventBus refactored to use configurable timeouts from settings instead of hardcoded values
- `BaseService._dispatch_post_action_event()`
- Dead-letter WAL events are now visible in `ztlctl check`, auto-purged at startup, and manually clearable via `event_purge` action registered under maintenance category
- 1. [Rule 1 - Bug] Variable name collision in graph.py
- Task 1 — Remove post_action bridge from EventBus (ARCH-05)
- ServerContext dataclass
- 1. [Rule 1 - Bug] garden_seed handler calling convention
- 9 feature-local registration modules
- One-liner:
- Dead workspace_modes.py wrapper removed, phantom mutation category purged from MCP generator and plugin manager, and ServiceError.recovery self-documented via Pydantic Field
- One-liner:
- Task 1 — Template + Init + MCP resource:
- check_alignment action: polaris-based advisory decision alignment using keyword-overlap heuristic, auto-generating ztlctl check alignment CLI and check_alignment MCP tool
- SQLAlchemy-based session recall via date-range temporal filtering and case-insensitive LIKE search on session_logs.summary, with full controller delegation through _run_action
- recall_topology discovers session pairs sharing log-referenced notes or tags; ztlctl://sessions/recent MCP resource; all 3 recall actions registered in ActionRegistry
- ContradictionService with three-signal heuristic scoring (cosine 40%, negation 30%, key_points 30%) and thin ContradictionController wrapper through _run_action
- One-liner:
- TranscriptionService with guarded faster-whisper import, regex VTT/SRT parsing, and MediaIngestConfig at settings.ingest.media
- One-liner:

---

## v2.1 Documentation (Shipped: 2026-03-21)

**Phases completed:** 7 phases, 21 plans, 11 tasks

**Key accomplishments:**

- (none recorded)

---

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
