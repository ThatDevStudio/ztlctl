# Roadmap: ztlctl

## Milestones

- ✅ **v2.0 Platform** — Phases 1-7 (shipped 2026-03-20)
- ✅ **v2.1 Documentation** — Phases 8-14 (shipped 2026-03-21)
- 🚧 **v3.0 Memory and Hardening** — Phases 15-22 (in progress)

## Phases

<details>
<summary>✅ v2.0 Platform (Phases 1-7) — SHIPPED 2026-03-20</summary>

- [x] Phase 1: Core Hardening (5/5 plans) — completed 2026-03-19
- [x] Phase 2: Action Registry (4/4 plans) — completed 2026-03-19
- [x] Phase 3: MCP Surface Generation (2/2 plans) — completed 2026-03-19
- [x] Phase 4: CLI Surface Generation (2/2 plans) — completed 2026-03-20
- [x] Phase 5: Plugin Formalization (3/3 plans) — completed 2026-03-20
- [x] Phase 6: Agentic Integration & Security (3/3 plans) — completed 2026-03-20
- [x] Phase 7: Plugin & Agentic Wiring Fixes (3/3 plans) — completed 2026-03-20

Full details: `.planning/milestones/v2.0-ROADMAP.md`

</details>

<details>
<summary>✅ v2.1 Documentation (Phases 8-14) — SHIPPED 2026-03-21</summary>

- [x] Phase 8: MkDocs Infrastructure (3/3 plans) — completed 2026-03-20
- [x] Phase 9: Navigation Structure (2/2 plans) — completed 2026-03-20
- [x] Phase 10: User Guide Content (3/3 plans) — completed 2026-03-20
- [x] Phase 11: Developer Guide + API Reference (4/4 plans) — completed 2026-03-20
- [x] Phase 12: Doc Search Integration (3/3 plans) — completed 2026-03-20
- [x] Phase 13: Actions Artifact Deploy (1/1 plan) — completed 2026-03-20
- [x] Phase 14: Documentation Quality Pass (5/5 plans) — completed 2026-03-20

Full details: `.planning/milestones/v2.1-ROADMAP.md`

</details>

### 🚧 v3.0 Memory and Hardening (In Progress)

**Milestone Goal:** Harden the core architecture (event model, action execution, plugin discovery) and add memory-layer features (session recall, polaris priorities, contradiction detection, ingestion pipeline, methodology guidance) that make ztlctl a persistent memory system for agents and humans.

- [x] **Phase 15: Event Model Hardening** - Reliable event delivery, canonical payload shape, service-only post_action emission (gap closure in progress) (completed 2026-03-21)
- [x] **Phase 16: Plugin Bridge and Action Executor** - Bridge reversal, generic action executor, MCP graceful shutdown (completed 2026-03-21)
- [x] **Phase 17: Registry Decomposition and Plugin Runtime** - Feature-local action registrations, centralized plugin discovery (completed 2026-03-21)
- [x] **Phase 18: Architecture Cleanup** - Residue removal, phantom category fix, embedding config, graph performance (completed 2026-03-21)
- [ ] **Phase 19: Methodology Guidance and Polaris** - Title quality checks, prose-as-title template, polaris priorities layer
- [ ] **Phase 20: Session Recall** - Temporal, topic, and topology querying across session history
- [ ] **Phase 21: Contradiction Detection** - Semantic integrity analysis, contradiction edges, review dashboard
- [ ] **Phase 22: Ingestion Pipeline** - Media and transcript ingestion via source provider plugin

## Phase Details

### Phase 15: Event Model Hardening
**Goal**: Event delivery is reliable — one canonical post-commit payload shape, service-only emission, and graceful shutdown/startup drain
**Depends on**: Phase 14 (v2.1 complete)
**Requirements**: ARCH-01, ARCH-02, ARCH-03, ARCH-04, DEBT-02, DEBT-03
**Success Criteria** (what must be TRUE):
  1. After a normal CLI command with a slow local plugin, no `pending` WAL rows remain when the process exits
  2. On startup after an interrupted run, pending WAL events from the prior session drain before new work begins
  3. Every mutating action has exactly one `post_action` producer — the service layer — with no controller-side write dispatch
  4. All `post_action` events carry a stable `action_name / side_effect / payload / warnings` shape that plugins can depend on
  5. EventBus drain timeout and dead-letter handling strategy are configurable in settings rather than hardcoded or silently accumulating
**Plans**: 4 plans

Plans:
- [x] 15-01-PLAN.md — EventBusConfig + ActionEvent models + EventBus constructor refactor
- [x] 15-02-PLAN.md — Service-only post_action emission, shutdown/startup drain, controller cleanup
- [x] 15-03-PLAN.md — Dead-letter reporting, auto-purge, event_purge action
- [x] 15-04-PLAN.md — Gap closure: wire _dispatch_post_action_event into service write methods + REQUIREMENTS.md update

### Phase 16: Plugin Bridge and Action Executor
**Goal**: The compatibility bridge is reversed so stable events drive legacy hooks, a generic action executor eliminates controller boilerplate, and MCP server shuts down cleanly
**Depends on**: Phase 15
**Requirements**: ARCH-05, ARCH-06, ARCH-09, DEBT-04
**Success Criteria** (what must be TRUE):
  1. Legacy per-event plugin hooks receive calls through an adapter that reads from stable action events — not the reverse bridge
  2. Controllers no longer contain repeated pre/post hook dispatch boilerplate — a shared action executor handles that path once
  3. `garden seed` exercises the same pre-action and post-commit machinery as all other create flows
  4. `ztlctl serve` exits cleanly without dangling asyncio tasks or open file handles when the MCP client disconnects
**Plans**: 2 plans

Plans:
- [x] 16-01-PLAN.md — Bridge reversal (ARCH-05) + generic _run_action executor on BaseController (ARCH-06)
- [x] 16-02-PLAN.md — MCP graceful shutdown with ServerContext and vault cleanup (DEBT-04)
- [x] 16-03-PLAN.md — Controller migration to _run_action (ARCH-06) + garden_seed ActionDefinition (ARCH-09)

### Phase 17: Registry Decomposition and Plugin Runtime
**Goal**: Action registrations live in feature-local modules, plugin/profile/workflow discovery is handled by a single coherent runtime owner, and load_plugin_commands participates in config injection
**Depends on**: Phase 16
**Requirements**: ARCH-07, ARCH-08, DEBT-07
**Success Criteria** (what must be TRUE):
  1. `_register_core.py` is decomposed — each feature area owns its ActionDefinitions in a local `actions/` module colocated with the relevant service/controller code
  2. Plugin runtime discovery happens once per process scope — `PluginManager` is not reconstructed independently for init steps, workspace profiles, workflow export, and live vault runtime
  3. `load_plugin_commands` uses the same discovery path and config injection as the vault runtime plugin manager
**Plans**: 2 plans

Plans:
- [x] 17-01-PLAN.md — Feature-local action registration modules (ARCH-07)
- [x] 17-02-PLAN.md — Centralized plugin runtime and load_plugin_commands fix (ARCH-08, DEBT-07)

### Phase 18: Architecture Cleanup
**Goal**: Compatibility residue is removed, phantom categories corrected, unused fields resolved, embedding dimensions made configurable, and graph commands performant on large vaults
**Depends on**: Phase 17
**Requirements**: ARCH-10, DEBT-01, DEBT-05, DEBT-06, DEBT-08
**Success Criteria** (what must be TRUE):
  1. Dead controller helpers, deprecated `workspace_modes.py`, and transitional scaffolding wrappers are removed — no dangling compatibility modules remain
  2. `_DEFAULT_ACTIVE_CATEGORIES` no longer contains a phantom `mutation` entry — the active category list accurately reflects available categories
  3. `ServiceError.recovery` field is either populated by services or removed — no unused structural debt in the error model
  4. Embedding dimensions are configurable in settings — no hardcoded vector dimension values remain in source
  5. `bridges()` uses k-approximation for betweenness centrality above a vault size threshold — the command stays responsive for vaults up to 5,000 notes
**Plans**: 2 plans

Plans:
- [x] 18-01-PLAN.md — Residue removal (workspace_modes.py, mutation category), ServiceError.recovery resolution, REQUIREMENTS update
- [x] 18-02-PLAN.md — Embedding dimension constant, bridges k-approximation, REQUIREMENTS update

### Phase 19: Methodology Guidance and Polaris
**Goal**: Prose-as-title conventions are documented and checked by the integrity scanner, and a persistent polaris priorities layer is accessible to agents and users
**Depends on**: Phase 15 (stable event model for context assembler integration)
**Requirements**: METH-01, METH-02, METH-03, POLR-01, POLR-02, POLR-03, POLR-04
**Success Criteria** (what must be TRUE):
  1. A new vault created with `ztlctl init` contains a scaffolded `garden/groves/polaris.md` with a starter priorities template
  2. An MCP agent reading `ztlctl://polaris` receives the polaris document content in Layer 1 of context assembly (operational state, token-budgeted)
  3. The `check_alignment` action accepts a decision description and returns structured polaris context the agent can reason against
  4. `ztlctl check` under `CAT_STRUCTURAL` flags notes with short or generic titles at info severity — the garden backlog resource includes title improvement candidates alongside stale seeds and orphans
  5. The prose-as-title convention and concrete examples are present in the `methodology.md.j2` init template
**Plans**: 2 plans

Plans:
- [ ] 19-01: Polaris init scaffold, MCP resource, and context assembler integration
- [ ] 19-02: `check_alignment` action and polaris-aware decision support
- [ ] 19-03: Methodology template and title quality check in CheckService

### Phase 20: Session Recall
**Goal**: Users and agents can query session history temporally, by topic, and through session-to-session connectivity
**Depends on**: Phase 15 (reliable event model ensures session history is complete before recall is exposed)
**Requirements**: RECL-01, RECL-02, RECL-03, RECL-04, RECL-05
**Success Criteria** (what must be TRUE):
  1. User can retrieve sessions filtered by date range and see a per-session summary of topics covered
  2. User can search across all session history with a text query and see which sessions match and why
  3. User can discover which sessions share content or recurring topics — the topology view shows session connectivity
  4. An MCP agent reading `ztlctl://sessions/recent` receives the last N sessions with summaries without invoking a command
  5. `recall_temporal`, `recall_topic`, and `recall_topology` are registered actions in ActionRegistry with RecallService backing them
**Plans**: 2 plans

Plans:
- [ ] 20-01: RecallService with temporal and topic recall
- [ ] 20-02: Topology recall, MCP resource, and ActionRegistry registration

### Phase 21: Contradiction Detection
**Goal**: The vault can surface notes that likely contradict each other, record confirmed contradictions as graph edges, and expose them in an agent review resource
**Depends on**: Phase 20 (vector index populated by session recall infrastructure); Phase 17 (decomposed registry for clean action addition)
**Requirements**: CNTR-01, CNTR-02, CNTR-03, CNTR-04, CNTR-05, CNTR-06
**Success Criteria** (what must be TRUE):
  1. Running `ztlctl check` with the semantic category returns candidate note pairs that may contradict — scoped to shared topic, high vector similarity, and decision note type
  2. Candidate pairs are scored by heuristic evaluation (negation patterns, key_points comparison) so the most likely contradictions surface first
  3. User can confirm a contradiction and a `contradicts` edge is recorded in the graph between the two notes
  4. An MCP agent reading `ztlctl://review/contradictions` receives current contradiction candidate pairs without invoking a command
  5. `check_contradictions` is a registered action in ActionRegistry under the analysis category
**Plans**: 2 plans

Plans:
- [ ] 21-01: Candidate pair discovery and heuristic scoring
- [ ] 21-02: CheckService CAT_SEMANTIC integration, graph edge recording, MCP resource, and ActionRegistry registration

### Phase 22: Ingestion Pipeline
**Goal**: Media files and transcripts can be ingested into the vault as structured captured references, ready for agent annotation
**Depends on**: Phase 21 (completes the memory layer); Phase 17 (decomposed registry for clean action addition)
**Requirements**: INGP-01, INGP-02, INGP-03, INGP-04, INGP-05, INGP-06
**Success Criteria** (what must be TRUE):
  1. User can pass a media file (mp4, mp3, m4a, wav) or transcript file (txt, vtt, srt) to `ztlctl ingest` and receive a `captured` reference note created in the vault
  2. Local transcription runs via whisper/faster-whisper with no audio data leaving the machine
  3. The `ingest_media` MCP tool is auto-generated from ActionRegistry and accepts the same parameters as the CLI command
  4. Whisper model selection, language hints, and output preferences are configurable in a `[ingest.media]` config section
  5. The captured reference source bundle contains `normalized_text`, `capture_agent`, and `modalities` from the transcription output — ready for an agent to annotate to `annotated` status
**Plans**: 2 plans

Plans:
- [ ] 22-01: Source provider plugin scaffolding and whisper transcription integration
- [ ] 22-02: Two-phase workflow, `ingest_media` action registration, config section

## Progress

**Execution Order:**
Phases execute in numeric order: 15 → 16 → 17 → 18 → 19 → 20 → 21 → 22

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Core Hardening | v2.0 | 5/5 | Complete | 2026-03-19 |
| 2. Action Registry | v2.0 | 4/4 | Complete | 2026-03-19 |
| 3. MCP Surface Generation | v2.0 | 2/2 | Complete | 2026-03-19 |
| 4. CLI Surface Generation | v2.0 | 2/2 | Complete | 2026-03-20 |
| 5. Plugin Formalization | v2.0 | 3/3 | Complete | 2026-03-20 |
| 6. Agentic Integration & Security | v2.0 | 3/3 | Complete | 2026-03-20 |
| 7. Plugin & Agentic Wiring Fixes | v2.0 | 3/3 | Complete | 2026-03-20 |
| 8. MkDocs Infrastructure | v2.1 | 3/3 | Complete | 2026-03-20 |
| 9. Navigation Structure | v2.1 | 2/2 | Complete | 2026-03-20 |
| 10. User Guide Content | v2.1 | 3/3 | Complete | 2026-03-20 |
| 11. Developer Guide + API Ref | v2.1 | 4/4 | Complete | 2026-03-20 |
| 12. Doc Search Integration | v2.1 | 3/3 | Complete | 2026-03-20 |
| 13. Actions Artifact Deploy | v2.1 | 1/1 | Complete | 2026-03-20 |
| 14. Documentation Quality Pass | v2.1 | 5/5 | Complete | 2026-03-20 |
| 15. Event Model Hardening | v3.0 | 4/4 | Complete    | 2026-03-21 |
| 16. Plugin Bridge and Action Executor | v3.0 | 3/3 | Complete    | 2026-03-21 |
| 17. Registry Decomposition and Plugin Runtime | v3.0 | 2/2 | Complete    | 2026-03-21 |
| 18. Architecture Cleanup | v3.0 | 2/2 | Complete    | 2026-03-21 |
| 19. Methodology Guidance and Polaris | v3.0 | 0/3 | Not started | - |
| 20. Session Recall | v3.0 | 0/2 | Not started | - |
| 21. Contradiction Detection | v3.0 | 0/2 | Not started | - |
| 22. Ingestion Pipeline | v3.0 | 0/2 | Not started | - |
