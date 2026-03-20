---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: unknown
stopped_at: Completed 05-plugin-formalization plan 01 (05-01-PLAN.md)
last_updated: "2026-03-20T02:43:22.064Z"
progress:
  total_phases: 6
  completed_phases: 4
  total_plans: 16
  completed_plans: 14
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-19)

**Core value:** Agents should only ever have to orchestrate the tool — not build custom functionality that is lacking from the tool.
**Current focus:** Phase 05 — plugin-formalization

## Current Position

Phase: 05 (plugin-formalization) — EXECUTING
Plan: 1 of 3

## Performance Metrics

**Velocity:**

- Total plans completed: 5
- Average duration: 4 min
- Total execution time: 0.33 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01-core-hardening | 5/5 | 20 min | 4 min |

**Recent Trend:**

- Last 5 plans: 3 min, ?, 5 min
- Trend: -

*Updated after each plan completion*
| Phase 01-core-hardening P02 | 10 | 2 tasks | 6 files |
| Phase 01-core-hardening P04 | 95 | 2 tasks | 8 files |
| Phase 02-action-registry P01 | 3 | 2 tasks | 6 files |
| Phase 02-action-registry P02 | 3 | 2 tasks | 12 files |
| Phase 02-action-registry P03 | 4 | 2 tasks | 11 files |
| Phase 02-action-registry P04 | 10 | 3 tasks | 5 files |
| Phase 03-mcp-surface-generation P01 | 15 | 2 tasks | 16 files |
| Phase 03-mcp-surface-generation P02 | 4 | 2 tasks | 3 files |
| Phase 04-cli-surface-generation P01 | 9 | 2 tasks | 5 files |
| Phase 04-cli-surface-generation P02 | 90 | 2 tasks | 16 files |
| Phase 05-plugin-formalization PP01 | 470 | 2 tasks | 11 files |

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- Core hardening before plugin formalization — tool must be standalone-capable before extending
- CLI/MCP as auto-generated presentation layers — define-once, use-everywhere via ActionRegistry
- NoteTypeDefinition lives in domain/ (no infrastructure imports) per 6-layer architecture rules
- log type uses base ContentModel since no LogModel class exists (sessions are DB-only)
- Transition validation enforces all target states must be map keys (no orphaned states)
- ThreadPoolExecutor reads only (writes remain sequential) for SQLite concurrency safety in rebuild()
- betweenness centrality: k=None for <=500 nodes (exact), k=500+seed=42 for larger graphs
- _fts5_escape() wraps terms in double-quotes and escapes internal double-quotes per FTS5 spec
- [Phase 01-core-hardening]: Warned on sse and streamable-http transports in serve.py — both are HTTP-based and unauthenticated
- [Phase 01-core-hardening]: Copier uses unsafe= not trust= parameter; current default unsafe=False is already safe — documented rather than changed
- [Phase 01-05]: Pre-Alembic vaults (None revision, tables exist) treated as current — UpgradeService.apply() handles stamping, _check_schema_current() should not block on this case
- [Phase 01-05]: Schema version check runs outside engine.connect() block in CheckService to avoid nested connection issues
- [Phase 01-core-hardening]: Coverage omit list reduced to only __main__.py — all service/plugin/MCP modules now measured at 87.66% overall
- [Phase 01-core-hardening]: DummyServer pattern: call registered handlers immediately to cover inner closure bodies without mcp package
- [Phase 02-action-registry]: ActionParam.handler typed as Callable[..., Any] to avoid circular import with ServiceResult
- [Phase 02-action-registry]: No built-in action registrations in plan 02-01 — controllers register their own definitions in plan 02-02
- [Phase 02-action-registry]: ReweaveController uses actual service signature (content_id, dry_run, min_score_override) — plan example had incorrect params
- [Phase 02-action-registry]: Controllers construct services per-call (not instance variables) — avoids stale service state across calls
- [Phase 02-action-registry]: WorkflowController and InitController extend BaseController for consistency even though their services use static methods
- [Phase 02-action-registry]: InitController named init_ctrl.py to avoid shadowing __init__.py
- [Phase 02-action-registry]: Factory lambda handlers: lambda vault, **kw: Controller(vault).method(**kw) for stateless per-call controller construction
- [Phase 02-action-registry]: 59 ActionDefinitions registered (plan required >=45) — all 13 categories covered at module load time
- [Phase 03-mcp-surface-generation]: McpResponse.warnings is list[str] | None (not list[str]) so model_dump(exclude_none=True) omits empty warnings — matching old _to_mcp_response() behavior
- [Phase 03-mcp-surface-generation]: tool_catalog()/common_error_recovery() compatibility shims added to generator.py for callers previously importing from mcp/tools
- [Phase 03-mcp-surface-generation]: manifest.json tool names updated to ActionRegistry names (session_status->status, create_log->start, graph_themes->themes, etc.)
- [Phase 03-mcp-surface-generation]: PREVIOUSLY_MISSING test set uses actual registry names (apply, check_pending, stamp_current, check) not plan-doc names — corrected at test time
- [Phase 03-mcp-surface-generation]: Budget-aware MCP tools: BUDGET_AWARE_ACTIONS frozenset gates injection; _apply_token_budget() truncates first list-valued field iteratively from tail
- [Phase 04-cli-surface-generation]: update action marked custom_presentation=True — keeps hand-written update.py which decomposes changes dict into individual flags
- [Phase 04-cli-surface-generation]: reweave/prune/undo grouped under cli_group="reweave" subgroup; archive/supersede stay top-level (cli_group=None)
- [Phase 04-cli-surface-generation]: @click.pass_obj callback uses positional-only app param (def callback(app, /, **kwargs)) to satisfy mypy strict arg-type check
- [Phase 04-cli-surface-generation P02]: ActionParam.cli_name field cleanly separates CLI flag name from Python kwarg name — generator uses param_decls=[option_name, p.name] to map --type -> content_type kwarg
- [Phase 04-cli-surface-generation P02]: choices removed from export_dashboard viewer param — service layer normalizes 'vanilla' alias; CLI choices restriction was too strict
- [Phase 04-cli-surface-generation P02]: _render_export content-key detection prints raw DOT/JSON to stdout enabling shell piping for export graph
- [Phase 04-cli-surface-generation P02]: Harvest-and-reattach pattern for init group — collect generated subcommands before overwrite, re-attach to wizard group
- [Phase 05-plugin-formalization]: plugins/_version.py private module breaks circular import between __init__.py and manager.py for API versioning helpers
- [Phase 05-plugin-formalization]: PluginsConfig extra=allow stores arbitrary [plugins.<name>] TOML sections for PLUG-03 config injection; legacy test updated to reflect new intent

### Pending Todos

None yet.

### Blockers/Concerns

None yet.

## Session Continuity

Last session: 2026-03-20T02:43:22.061Z
Stopped at: Completed 05-plugin-formalization plan 01 (05-01-PLAN.md)
Resume file: None
