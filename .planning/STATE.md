---
gsd_state_version: 1.0
milestone: v3.0
milestone_name: Memory and Hardening
status: unknown
stopped_at: Completed 22-02-PLAN.md
last_updated: "2026-03-21T20:35:14.182Z"
progress:
  total_phases: 8
  completed_phases: 8
  total_plans: 20
  completed_plans: 20
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-21)

**Core value:** Agents should only ever have to orchestrate the tool — not build custom functionality that is lacking from the tool.
**Current focus:** Phase 22 — ingestion-pipeline

## Current Position

Phase: 22
Plan: Not started

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
| Phase 17-registry-decomposition-and-plugin-runtime P01 | 15 | 2 tasks | 11 files |
| Phase 18-architecture-cleanup P01 | 12 | 2 tasks | 7 files |
| Phase 18-architecture-cleanup P02 | 4 | 2 tasks | 4 files |
| Phase 19-methodology-guidance-and-polaris P02 | 3 | 2 tasks | 5 files |
| Phase 19-methodology-guidance-and-polaris P01 | 268 | 2 tasks | 8 files |
| Phase 19-methodology-guidance-and-polaris P03 | 8 | 1 tasks | 5 files |
| Phase 20-session-recall P01 | 2 | 2 tasks | 4 files |
| Phase 20 P02 | 5 | 2 tasks | 6 files |
| Phase 21-contradiction-detection P01 | 5 | 2 tasks | 4 files |
| Phase 21-contradiction-detection P02 | 8 | 2 tasks | 8 files |
| Phase 22-ingestion-pipeline P01 | 3 | 2 tasks | 3 files |
| Phase 22-ingestion-pipeline P02 | 4 | 2 tasks | 4 files |

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
- [Phase 17-registry-decomposition-and-plugin-runtime]: _register_core.py decomposed into 9 feature-local modules; each owns one registration function; __init__.py calls all 9 at module load time (ARCH-07)
- [Phase 18-architecture-cleanup]: ServiceError.recovery kept with Field description — confirmed active in controllers/base.py (plugin rejection), controllers/discovery.py (category errors), mcp/response.py (MCP error builder)
- [Phase 18-architecture-cleanup]: Custom note type update/close actions use lifecycle category matching core _lifecycle.py actions
- [Phase 18-architecture-cleanup]: DEFAULT_EMBEDDING_DIM defined in embeddings.py; config/models.py uses literal 384 with comment pointing to canonical source (avoids circular import)
- [Phase 18-architecture-cleanup]: bridges() k-approximation: identical pattern to _node_features() — exact for <=500 nodes, min(500, n) for larger graphs, seed=42 for reproducibility
- [Phase 19]: _GENERIC_TITLE_PATTERNS as module-level frozenset for reuse; title quality at SEVERITY_INFO only (advisory, never blocking); garden_backlog_impl uses lazy CheckService import matching existing pattern
- [Phase 19-methodology-guidance-and-polaris]: polaris scaffolded for all profiles (core + obsidian) — vault-level, not profile-specific
- [Phase 19-methodology-guidance-and-polaris]: AgentContextLayers.polaris field added to Pydantic contract between log_entries and topic_content
- [Phase 19-methodology-guidance-and-polaris]: aligned is always True — check_alignment is purely advisory, never blocks action execution
- [Phase 19-methodology-guidance-and-polaris]: check_alignment uses stopword-filtered keyword-overlap heuristic — no NLP dependency, deterministic
- [Phase 20-01]: recall_temporal uses nodes.created ISO date strings for filtering (SQLite lexicographic comparison is correct for YYYY-MM-DD)
- [Phase 20-01]: recall_topology stubbed on RecallService with empty nodes list — full graph-topology implementation deferred to Plan 02
- [Phase 20-01]: recall_topic uses func.lower() LIKE on session_logs.summary — session_logs not in nodes_fts, LIKE sufficient for use case
- [Phase 20]: recall_topology uses session_logs.references JSON array for shared note detection — nodes.session tracks creation session, references captures cross-session note mentions
- [Phase 20]: sessions_recent_impl delegates to recall_temporal() and slices [:5] — already ordered by created_at desc
- [Phase 21-01]: Patch target for VectorService mocks is ztlctl.services.vector.VectorService (lazy import — patch where class is defined)
- [Phase 21-01]: confirm_contradiction stubbed with NOT_IMPLEMENTED — Plan 02 adds graph edge recording and ActionRegistry wiring
- [Phase 21-contradiction-detection]: CAT_SEMANTIC wired outside vault.engine.connect() block — _check_semantic() opens its own connection internally via ContradictionService
- [Phase 21-contradiction-detection]: confirm_contradiction validates both notes exist before opening transaction (fail-fast before mutation)
- [Phase 21-contradiction-detection]: analysis category now active — check_contradictions and confirm_contradiction bring category count to 17
- [Phase 22-01]: TranscriptionService is stateless utility (not BaseService subclass) — no Vault access needed for file transcription
- [Phase 22-01]: faster-whisper import guarded inside _transcribe_media() — module-level guard would prevent instantiation on import
- [Phase 22-01]: MediaIngestConfig composes into IngestConfig.media — settings.ingest.media.whisper_model/language/compute_type pattern
- [Phase 22]: source_path stored at top level of bundle JSON via extra-field injection post-normalization
- [Phase 22]: SourceBundleData.input_kind Literal extended to include 'media'
- [Phase 22]: ingest_media always targets reference type — enforces two-phase captured to annotated workflow

### Pending Todos

None yet.

### Blockers/Concerns

- Architecture remediation touches many subsystems — Phase 15 fixes correctness, later phases are mechanical; land Phase 15 first
- Plugin compatibility: changing event production order can break plugins that depend on duplicate delivery; keep legacy adapter for one compatibility window
- Latency regression risk: waiting for post-commit work at shutdown may add a few hundred ms; measure and use bounded wait

## Session Continuity

Last session: 2026-03-21T20:31:08.334Z
Stopped at: Completed 22-02-PLAN.md
Resume file: None
