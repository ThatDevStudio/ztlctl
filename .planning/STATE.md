---
gsd_state_version: 1.0
milestone: v3.0
milestone_name: Memory and Hardening
status: unknown
stopped_at: Completed 17-02-PLAN.md
last_updated: "2026-03-21T18:21:48.086Z"
progress:
  total_phases: 8
  completed_phases: 2
  total_plans: 9
  completed_plans: 8
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-21)

**Core value:** Agents should only ever have to orchestrate the tool — not build custom functionality that is lacking from the tool.
**Current focus:** Phase 17 — registry-decomposition-and-plugin-runtime

## Current Position

Phase: 17 (registry-decomposition-and-plugin-runtime) — EXECUTING
Plan: 2 of 2

## Performance Metrics

**Velocity:**

- Total plans completed: 43 (22 v2.0 + 21 v2.1)
- Average duration: ~53 min (v2.0), varies widely by phase (v2.1)
- Total execution time: estimated ~30+ hours across all milestones

**By Phase (v2.1 — most recent):**

| Phase | Plans | Avg/Plan |
|-------|-------|----------|
| 08 MkDocs Infra | 3 | ~47 min |
| 09 Navigation | 2 | ~2 min |
| 10 User Guide | 3 | ~3 min |
| 11 Developer Guide | 4 | ~2 min |
| 12 Doc Search | 3 | ~175175 min (outlier) |
| 13 Pages Deploy | 1 | ~48 min |
| 14 Quality Pass | 5 | ~15 min |

**Recent Trend:**

- v3.0: Not started
- Trend: Stable (architecture phases expected to be heavier than docs)

*Updated after each plan completion*
| Phase 15-event-model-hardening P01 | 18 | 2 tasks | 8 files |
| Phase 15-event-model-hardening P02 | 60 | 2 tasks | 22 files |
| Phase 15 P03 | 20 | 2 tasks | 10 files |
| Phase 15-event-model-hardening P04 | 371 | 2 tasks | 7 files |
| Phase 16-plugin-bridge-and-action-executor P01 | 249 | 2 tasks | 4 files |
| Phase 16-plugin-bridge-and-action-executor P03 | 45 | 2 tasks | 19 files |
| Phase 17-registry-decomposition-and-plugin-runtime P02 | 6 | 2 tasks | 7 files |

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- Architecture remediation design doc committed: 5-phase internal plan (event hardening → bridge cleanup → executor → registry → residue)
- DEBT-02 (EventBus timeout) and DEBT-03 (dead-letter) co-phased with ARCH-01/ARCH-02 in Phase 15
- DEBT-04 (MCP graceful shutdown) co-phased with ARCH-06/ARCH-09 in Phase 16 (same execution context)
- DEBT-07 (load_plugin_commands) co-phased with ARCH-08 in Phase 17 (same discovery path)
- METH-* co-phased with POLR-* in Phase 19 (both zero-code, high value, no blocking arch dependency beyond Phase 15)
- Phase 20 (Recall) placed before Phase 21 (Contradiction) because recall infrastructure populates vector index needed by CNTR-01
- Phase 22 (Ingestion) placed last — largest scope, external dependency (whisper), no other features depend on it
- [Phase 15-event-model-hardening]: EventBus config parameter is optional (config: EventBusConfig | None = None) to preserve backward compat with tests using max_retries kwarg
- [Phase 15-event-model-hardening]: ActionEvent.result: Any = None carries full ServiceResult without coupling domain to services layer
- [Phase 15-event-model-hardening]: Single-step cutover: all 64 controller _dispatch_post_action calls removed atomically
- [Phase 15-event-model-hardening]: Bounded shutdown drain uses EventBusConfig.shutdown_timeout_seconds with pending rows preserved on timeout
- [Phase 15-event-model-hardening]: Startup drain is best-effort: failure logs warning and continues
- [Phase 15]: SEVERITY_INFO rank=0 so dead-letter issues only appear at min_severity='info', not default 'warning'
- [Phase 15]: event_purge placed in 'maintenance' category (not 'check') — operational housekeeping vs. integrity scanning
- [Phase 15-event-model-hardening]: _dispatch_post_action_event placed after _dispatch_event and before return in all write methods
- [Phase 15-event-model-hardening]: graph.py unlink uses unlink_result variable name to avoid CursorResult type collision
- [Phase 16]: _HOOK_TO_ACTION dict removed — dead code once services own post_action via _dispatch_post_action_event (Phase 15)
- [Phase 16]: _run_action uses local imports for ServiceError/ServiceResult to match existing controller pattern and avoid circular imports
- [Phase 16]: All 63 controller methods now delegate to _run_action; _dispatch_pre_action called only in base.py (ARCH-06 complete)
- [Phase 16]: garden_seed handler uses single-call lambda (vault, **kw) matching all other ActionDefinitions — two-level lambda incompatible with CLI/MCP generator calling convention
- [Phase 16]: garden_seed registered in creation category; commands/garden.py deleted; generator auto-creates garden CLI group (ARCH-09 complete)
- [Phase 17]: vault.py uses cache=False in get_plugin_manager() because it mutates the PM with instance-specific built-ins (git-builtin, reweave-builtin) — caching would cause re-registration errors on second Vault construction
- [Phase 17]: load_plugin_commands passes settings=settings to get_plugin_manager() fixing DEBT-07 (inject_configs gap)

### Pending Todos

None yet.

### Blockers/Concerns

- Architecture remediation touches many subsystems — Phase 15 fixes correctness, later phases are mechanical; land Phase 15 first
- Plugin compatibility: changing event production order can break plugins that depend on duplicate delivery; keep legacy adapter for one compatibility window
- Latency regression risk: waiting for post-commit work at shutdown may add a few hundred ms; measure and use bounded wait

## Session Continuity

Last session: 2026-03-21T18:21:48.084Z
Stopped at: Completed 17-02-PLAN.md
Resume file: None
