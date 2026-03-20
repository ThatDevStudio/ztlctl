---
gsd_state_version: 1.0
milestone: v2.0
milestone_name: milestone
status: unknown
stopped_at: Completed 07-plugin-agentic-wiring-fixes-02-PLAN.md
last_updated: "2026-03-20T05:47:25.849Z"
progress:
  total_phases: 7
  completed_phases: 6
  total_plans: 22
  completed_plans: 21
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-19)

**Core value:** Agents should only ever have to orchestrate the tool — not build custom functionality that is lacking from the tool.
**Current focus:** Phase 07 — plugin-agentic-wiring-fixes

## Current Position

Phase: 07 (plugin-agentic-wiring-fixes) — EXECUTING
Plan: 2 of 3

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
| Phase 05-plugin-formalization P02 | 442 | 2 tasks | 7 files |
| Phase 05-plugin-formalization P03 | 900 | 2 tasks | 6 files |
| Phase 06-agentic-integration-security P01 | 10 | 1 tasks | 4 files |
| Phase 06-agentic-integration-security P03 | 17 | 2 tasks | 10 files |
| Phase 06-agentic-integration-security P02 | 12 | 2 tasks | 8 files |
| Phase 07-plugin-agentic-wiring-fixes P01 | 4 | 2 tasks | 6 files |
| Phase 07-plugin-agentic-wiring-fixes P02 | 5 | 2 tasks | 8 files |

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
- [Phase 05-plugin-formalization P02]: Injectable note_registry/action_registry params on _register_note_types() for test isolation without monkeypatching module-level singletons
- [Phase 05-plugin-formalization P02]: content_type dispatch in create handler routes to create_task/create_reference/create_note based on NoteTypeDefinition.content_type
- [Phase 05-plugin-formalization P02]: close handler maps to UpdateController.archive() — the actual method name in UpdateController
- [Phase 05-plugin-formalization P02]: render_contributions() is lazy (on-demand); _register_note_types() is eager (called in discover_and_load()) for CLI/MCP generators to pick up plugin types at load time
- [Phase 05-plugin-formalization]: GitPlugin post_action uses _handle_* private methods for each action group — keeps routing method short and handlers testable
- [Phase 05-plugin-formalization]: EventBus bridge fires post_action REGARDLESS of per-event hook subscribers; bridge exception isolation prevents WAL status corruption
- [Phase 05-plugin-formalization]: result=None treated as pass-through on EventBus bridge path; result.ok=False guard only skips explicit controller-dispatched failures
- [Phase 06-agentic-integration-security]: ServiceError.recovery is optional (default None) — zero impact on 30+ existing construction sites
- [Phase 06-agentic-integration-security]: from_result() uses result.error.recovery or COMMON_ERROR_RECOVERY.get(code) — explicit override wins over generic fallback
- [Phase 06-agentic-integration-security]: COMMON_ERROR_RECOVERY extended from 9 to 36 entries; test_all_codes_have_recovery provides ongoing regression guard
- [Phase 06-agentic-integration-security]: force_trust applies only to _run_plugin_copy; built-in _run_copy/_run_update always use unsafe=False
- [Phase 06-agentic-integration-security]: Missing capability declarations logged at DEBUG (advisory in API v2); invalid declarations logged at WARNING
- [Phase 06-agentic-integration-security]: Built-in plugins (git, obsidian, reweave) implement declare_capabilities to document access surface and avoid test noise
- [Phase 06-agentic-integration-security]: _DEFAULT_ACTIVE_CATEGORIES frozenset guards deactivate_category -- core categories cannot be deactivated by agents
- [Phase 06-agentic-integration-security]: Category activation state is module-level in generator.py (server-scoped) -- one MCP server process = one session
- [Phase 07-plugin-agentic-wiring-fixes]: PLUG-03 wired via pm.inject_configs(self._settings) immediately after discover_and_load() in vault.init_event_bus()
- [Phase 07-plugin-agentic-wiring-fixes]: ACTION_REJECTED inserted alphabetically in COMMON_ERROR_RECOVERY; detail= forwarded from ServiceError to McpError in from_result()
- [Phase 07-plugin-agentic-wiring-fixes]: AGNT-04 advisory comment placed directly after _active_categories assignment in generator.py; category activation is metadata only (FastMCP does not support dynamic tool deregistration)
- [Phase 07-plugin-agentic-wiring-fixes]: dispatch_post_create excluded from CreateController kwargs — internal CreateService flag not exposed to plugins
- [Phase 07-plugin-agentic-wiring-fixes]: export_graph post-processing stays after service call but before post_action dispatch so post_action sees final result
- [Phase 07-plugin-agentic-wiring-fixes]: Service calls always reference kwargs[key] not original local variables so plugin-modified kwargs take effect

### Pending Todos

None yet.

### Blockers/Concerns

None yet.

## Session Continuity

Last session: 2026-03-20T05:47:25.846Z
Stopped at: Completed 07-plugin-agentic-wiring-fixes-02-PLAN.md
Resume file: None
