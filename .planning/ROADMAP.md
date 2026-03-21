# Roadmap: ztlctl

## Milestones

- ✅ **v2.0 Platform** — Phases 1-7 (shipped 2026-03-20)
- ✅ **v2.1 Documentation** — Phases 8-14 (shipped 2026-03-21)
- ✅ **v3.0 Memory and Hardening** — Phases 15-22 (shipped 2026-03-21)
- **v3.1 Documentation & Hardening** — Phases 23-27 (active)

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

<details>
<summary>✅ v3.0 Memory and Hardening (Phases 15-22) — SHIPPED 2026-03-21</summary>

- [x] Phase 15: Event Model Hardening (4/4 plans) — completed 2026-03-21
- [x] Phase 16: Plugin Bridge and Action Executor (3/3 plans) — completed 2026-03-21
- [x] Phase 17: Registry Decomposition and Plugin Runtime (2/2 plans) — completed 2026-03-21
- [x] Phase 18: Architecture Cleanup (2/2 plans) — completed 2026-03-21
- [x] Phase 19: Methodology Guidance and Polaris (3/3 plans) — completed 2026-03-21
- [x] Phase 20: Session Recall (2/2 plans) — completed 2026-03-21
- [x] Phase 21: Contradiction Detection (2/2 plans) — completed 2026-03-21
- [x] Phase 22: Ingestion Pipeline (2/2 plans) — completed 2026-03-21

Full details: `.planning/milestones/v3.0-ROADMAP.md`

</details>

### v3.1 Documentation & Hardening (Phases 23-27)

- [ ] **Phase 23: Docs-as-Code Infrastructure** — CI gate, prose linting, CLAUDE.md enforcement rule, git-sourced dates, and IngestService/docstring debt
- [ ] **Phase 24: Navigation and Information Architecture** — Diataxis audit, nav reordering for beginner-to-advanced progression, consistent quality conventions
- [ ] **Phase 25: New v3.0 Feature Pages** — Five standalone pages for session recall, polaris, contradiction detection, media ingestion, and methodology guidance
- [ ] **Phase 26: Existing Pages and Quality Pass** — Update concepts, commands, agentic-workflows, agents, mcp with v3.0 content; refresh llms.txt and llms-full.txt
- [ ] **Phase 27: Internal Documentation Refresh** — CLAUDE.md architecture section, DESIGN.md, README.md updated for v3.0 reality

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
**Plans**: 3 plans

Plans:
- [x] 19-01-PLAN.md — Polaris template, init scaffold, MCP resource, and context assembler integration (POLR-01, POLR-02, POLR-03)
- [x] 19-02-PLAN.md — Methodology template prose-as-title section, title quality check, and garden backlog integration (METH-01, METH-02, METH-03)
- [x] 19-03-PLAN.md — check_alignment action with structured polaris context for agent evaluation (POLR-04)

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
- [x] 20-01: RecallService with temporal and topic recall
- [x] 20-02: Topology recall, MCP resource, and ActionRegistry registration

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
- [x] 21-01: Candidate pair discovery and heuristic scoring
- [x] 21-02: CheckService CAT_SEMANTIC integration, graph edge recording, MCP resource, and ActionRegistry registration

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
- [x] 22-01-PLAN.md — TranscriptionService with whisper integration, transcript parsing, and MediaIngestConfig
- [x] 22-02-PLAN.md — IngestService.ingest_media method, controller wiring, ActionRegistry registration

### Phase 23: Docs-as-Code Infrastructure
**Goal**: Broken or incomplete documentation cannot merge — CI gates enforce docs quality, CLAUDE.md mandates docs updates with every feature change, and known code-level debt is cleared
**Depends on**: Phase 22 (v3.0 complete)
**Requirements**: DINF-01, DINF-02, DINF-03, DINF-04, DEBT-09, DEBT-10
**Success Criteria** (what must be TRUE):
  1. A PR with a broken MkDocs build or prose lint failures is blocked from merging — `doc_lint` job runs in parallel with `validate_pr` in `pr-ci.yml`
  2. CLAUDE.md contains a Documentation Rule section with a per-change checklist — every developer (and Claude) knows the docs update obligation before touching a feature
  3. Every GSD feature phase plan template includes a mandatory Documentation Tasks block — docs updates are structural, not optional
  4. Every docs page shows a "last updated" date sourced from git history — currency is visible without author discipline
  5. IngestService post_action events fire for all `ingest_*` actions — the missing dispatch call is present and covered by `test_post_action_dispatch.py`
  6. Stale docstrings in ContradictionController and stale comments in `commands/generator.py` are replaced with accurate descriptions
**Plans**: TBD

### Phase 24: Navigation and Information Architecture
**Goal**: The docs site navigation reflects a beginner-to-advanced learning path, every page is classified by Diataxis content type, and quality conventions are consistently applied across all pages
**Depends on**: Phase 23 (doc lint CI gate is live before structural audit begins)
**Requirements**: QUAL-01, QUAL-04
**Success Criteria** (what must be TRUE):
  1. Every existing docs page has a recorded Diataxis classification (tutorial / how-to / reference / explanation) — mixed-purpose pages are identified and flagged for remediation
  2. The User Guide `nav:` order in `mkdocs.yml` reflects install → daily capture → search/graph → sessions → strategic alignment → ingestion → extensibility — not feature ship order
  3. Confirmed placement slots exist for all five v3.0 feature pages in the navigation order before those pages are written
  4. CLI syntax conventions (Google style: `[optional]`, `{required}`, `$` prompts), admonition taxonomy (Warning/Note/Tip), and "What's next" links are documented as standards in CLAUDE.md or a contributing guide
**Plans**: TBD

### Phase 25: New v3.0 Feature Pages
**Goal**: All five v3.0 features shipped without documentation now have standalone pages that are navigable, agent-discoverable, and cross-referenced from existing pages
**Depends on**: Phase 24 (navigation placement confirmed before pages are written)
**Requirements**: NDOC-01, NDOC-02, NDOC-03, NDOC-04, NDOC-05
**Success Criteria** (what must be TRUE):
  1. User can find and read a `session-recall.md` page that covers temporal, topic, and topology recall with CLI usage, MCP tool reference, and an agent workflow example
  2. User can find and read a `polaris.md` page that covers the init scaffold, `ztlctl://polaris` MCP resource, `check_alignment` action, and an agent alignment workflow — framed as the strategic layer of the vault
  3. User can find and read a `contradiction-detection.md` page that covers heuristic scoring, the `CAT_SEMANTIC` check, `confirm_contradiction`, graph edges, and the MCP review resource
  4. User can find and read a `media-ingestion.md` page with a prominent optional-dependency callout for faster-whisper, format coverage, `ingest_media` CLI/MCP usage, and the two-phase captured-to-annotated workflow
  5. User can find and read a `methodology.md` page that covers the prose-as-title convention, title quality check severity, and garden backlog candidates
  6. Each new page has a `mkdocs.yml nav:` entry, an `llms.txt` entry, and an `llms-full.txt` append — agent discovery indexes are current after every page addition
**Plans**: TBD

### Phase 26: Existing Pages and Quality Pass
**Goal**: Existing docs pages reflect v3.0 reality and agent discovery indexes are fully current
**Depends on**: Phase 25 (new pages must exist before cross-references and index updates are complete)
**Requirements**: QUAL-02, QUAL-03
**Success Criteria** (what must be TRUE):
  1. `concepts.md` covers v3.0 content types — sessions, contradictions, media — and links to the new feature pages
  2. `agentic-workflows.md` includes v3.0 recipes: polaris-aligned session startup, recall-driven context loading, and contradiction review workflow
  3. `agents.md` tool inventory includes all 73+ registered actions and documents v3.0 failure modes for agent error recovery
  4. `mcp.md` reflects the current tool count (73+) and documents all new MCP resources (`ztlctl://polaris`, `ztlctl://sessions/recent`, `ztlctl://review/contradictions`)
  5. `llms.txt` and `llms-full.txt` contain entries for all new pages and accurate v3.0 feature descriptions — an agent using llms.txt discovers session recall, polaris, contradiction detection, and media ingestion
**Plans**: TBD

### Phase 27: Internal Documentation Refresh
**Goal**: CLAUDE.md, DESIGN.md, and README.md accurately describe the v3.0 system — developers and contributors work from current information
**Depends on**: Phase 26 (external docs complete — internal docs can reference final external doc structure)
**Requirements**: IDOC-01, IDOC-02, IDOC-03
**Success Criteria** (what must be TRUE):
  1. CLAUDE.md architecture section lists all 15 services, 17 controllers, and 73+ actions; describes feature-local action registration and the centralized PluginManager factory
  2. DESIGN.md captures the v3.0 architectural decisions: reliable event model (WAL drain, service-only post_action), generic action executor, feature-local registration, recall/contradiction/ingestion design choices
  3. README.md feature list and command examples include session recall, polaris priorities, contradiction detection, and media ingestion — a new contributor reading README.md gets an accurate picture of the current tool
**Plans**: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 23 → 24 → 25 → 26 → 27

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
| 15. Event Model Hardening | v3.0 | 4/4 | Complete | 2026-03-21 |
| 16. Plugin Bridge and Action Executor | v3.0 | 3/3 | Complete | 2026-03-21 |
| 17. Registry Decomposition and Plugin Runtime | v3.0 | 2/2 | Complete | 2026-03-21 |
| 18. Architecture Cleanup | v3.0 | 2/2 | Complete | 2026-03-21 |
| 19. Methodology Guidance and Polaris | v3.0 | 3/3 | Complete | 2026-03-21 |
| 20. Session Recall | v3.0 | 2/2 | Complete | 2026-03-21 |
| 21. Contradiction Detection | v3.0 | 2/2 | Complete | 2026-03-21 |
| 22. Ingestion Pipeline | v3.0 | 2/2 | Complete | 2026-03-21 |
| 23. Docs-as-Code Infrastructure | v3.1 | 0/? | Not started | - |
| 24. Navigation and Information Architecture | v3.1 | 0/? | Not started | - |
| 25. New v3.0 Feature Pages | v3.1 | 0/? | Not started | - |
| 26. Existing Pages and Quality Pass | v3.1 | 0/? | Not started | - |
| 27. Internal Documentation Refresh | v3.1 | 0/? | Not started | - |
