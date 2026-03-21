# Requirements: ztlctl v3.0 Memory and Hardening

**Defined:** 2026-03-21
**Core Value:** Agents should only ever have to orchestrate the tool — not build custom functionality that is lacking from the tool.

## v3.0 Requirements

Requirements for v3.0 release. Each maps to roadmap phases.

### Architecture Remediation

- [x] **ARCH-01**: Event delivery is reliable — WAL rows drain on CLI shutdown with bounded timeout
- [x] **ARCH-02**: Pending/failed WAL events from prior runs drain on startup before new work begins
- [x] **ARCH-03**: Write-side `post_action` is emitted by services only — controller-side dispatch removed
- [x] **ARCH-04**: Canonical action-event payload model with stable shape (`action_name`, `side_effect`, `payload`, `warnings`)
- [x] **ARCH-05**: Compatibility bridge reversed — stable action events adapt into legacy hook calls (not legacy → stable)
- [x] **ARCH-06**: Generic action executor replaces repeated pre/post hook boilerplate in controllers
- [x] **ARCH-07**: Action registrations decomposed into feature-local modules (`actions/create.py`, `actions/query.py`, etc.)
- [x] **ARCH-08**: Centralized plugin runtime discovery — single coherent owner per scope for plugins, profiles, workflows, init steps
- [x] **ARCH-09**: Command surface convergence — `garden seed` is a first-class action; hybrid patching reduced
- [x] **ARCH-10**: Compatibility residue removed — dead controller helpers, deprecated `workspace_modes.py`, transitional scaffolding

### Tech Debt

- [x] **DEBT-01**: Embedding dimensions configurable (remove hardcoded values)
- [x] **DEBT-02**: EventBus timeout configurable via settings
- [x] **DEBT-03**: Dead-letter event accumulation resolved (cleanup or retry strategy)
- [x] **DEBT-04**: MCP server graceful shutdown implemented
- [x] **DEBT-05**: Phantom `mutation` category in `_DEFAULT_ACTIVE_CATEGORIES` cleaned up
- [x] **DEBT-06**: `ServiceError.recovery` field either used by services or removed
- [x] **DEBT-07**: `load_plugin_commands` creates PluginManager with `inject_configs` support
- [x] **DEBT-08**: `bridges()` betweenness centrality uses k-approximation for large graphs

### Session Recall

- [ ] **RECL-01**: User can retrieve sessions by date range with per-session summaries (temporal recall)
- [ ] **RECL-02**: User can search session history by topic using BM25 or semantic search (topic recall)
- [ ] **RECL-03**: User can discover session connectivity through shared content and recurring topics (topology recall)
- [ ] **RECL-04**: MCP resource `ztlctl://sessions/recent` exposes last N sessions with summaries
- [ ] **RECL-05**: RecallService with `recall_temporal`, `recall_topic`, `recall_topology` actions registered in ActionRegistry

### Polaris Layer

- [x] **POLR-01**: Well-known path `garden/groves/polaris.md` scaffolded during `ztlctl init` with starter template
- [x] **POLR-02**: MCP resource `ztlctl://polaris` exposes polaris document content to agents
- [x] **POLR-03**: ContextAssembler integrates polaris content into Layer 1 (operational state) with token budgeting
- [ ] **POLR-04**: `check_alignment` action accepts a decision description and returns structured polaris context for agent evaluation

### Contradiction Detection

- [ ] **CNTR-01**: Candidate pair discovery identifies notes that may contradict (topic-scoped, high-similarity, decision conflicts)
- [ ] **CNTR-02**: Heuristic evaluation scores candidate pairs using negation patterns and key_points comparison
- [ ] **CNTR-03**: `CAT_SEMANTIC` check category in CheckService reports contradiction candidates
- [ ] **CNTR-04**: Confirmed contradictions recorded as `contradicts` edges in the graph
- [ ] **CNTR-05**: MCP resource `ztlctl://review/contradictions` surfaces contradiction pairs in review dashboard
- [ ] **CNTR-06**: `check_contradictions` action registered in ActionRegistry (category: analysis)

### Ingestion Pipeline

- [ ] **INGP-01**: Source provider plugin accepts media files (mp4, mp3, m4a, wav) and transcript files (txt, vtt, srt)
- [ ] **INGP-02**: Local transcription via whisper/faster-whisper (no data leaves the machine)
- [ ] **INGP-03**: Two-phase workflow: plugin produces `captured` reference, agent annotates to `annotated` with structured key_points
- [ ] **INGP-04**: `ingest_media` action registered in ActionRegistry with MCP tool auto-generated
- [ ] **INGP-05**: Config section `[ingest.media]` for whisper model selection, language hints, output preferences
- [ ] **INGP-06**: Source bundle populated with transcription output (normalized_text, capture_agent, modalities)

### Methodology Guidance

- [x] **METH-01**: Prose-as-title convention documented in `methodology.md.j2` template (research-partner tone)
- [x] **METH-02**: Title quality check in CheckService under `CAT_STRUCTURAL` flags short/generic titles (info severity)
- [x] **METH-03**: Garden backlog resource includes title improvement candidates alongside stale seeds and orphans

## v4.0 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Advanced Memory

- **AMEM-01**: Session graph visualization (interactive session-to-file topology browser)
- **AMEM-02**: Claude Code JSONL conversation parsing into indexed markdown
- **AMEM-03**: Kanban board generation from unstructured task text

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| GUI/web interface | ztlctl is CLI/MCP-first; Obsidian serves as the visual layer |
| Multi-user/collaboration | Local single-user tool; collaboration through shared repos |
| Cloud sync | Filesystem is the storage layer; sync is the user's responsibility |
| Mobile app | CLI tool; mobile access through Obsidian mobile or MCP clients |
| LLM provider coupling in core | Ingestion plugin uses whisper for transcription; LLM extraction is agent-side, not tool-side |
| Enforced title conventions | Title quality is advisory (info severity), not validation-blocking |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| ARCH-01 | Phase 15 | Complete |
| ARCH-02 | Phase 15 | Complete |
| ARCH-03 | Phase 15 | Complete |
| ARCH-04 | Phase 15 | Complete |
| ARCH-05 | Phase 16 | Complete |
| ARCH-06 | Phase 16 | Complete |
| ARCH-07 | Phase 17 | Complete |
| ARCH-08 | Phase 17 | Complete |
| ARCH-09 | Phase 16 | Complete |
| ARCH-10 | Phase 18 | Complete |
| DEBT-01 | Phase 18 | Complete |
| DEBT-02 | Phase 15 | Complete |
| DEBT-03 | Phase 15 | Complete |
| DEBT-04 | Phase 16 | Complete |
| DEBT-05 | Phase 18 | Complete |
| DEBT-06 | Phase 18 | Complete |
| DEBT-07 | Phase 17 | Complete |
| DEBT-08 | Phase 18 | Complete |
| RECL-01 | Phase 20 | Pending |
| RECL-02 | Phase 20 | Pending |
| RECL-03 | Phase 20 | Pending |
| RECL-04 | Phase 20 | Pending |
| RECL-05 | Phase 20 | Pending |
| POLR-01 | Phase 19 | Complete |
| POLR-02 | Phase 19 | Complete |
| POLR-03 | Phase 19 | Complete |
| POLR-04 | Phase 19 | Pending |
| CNTR-01 | Phase 21 | Pending |
| CNTR-02 | Phase 21 | Pending |
| CNTR-03 | Phase 21 | Pending |
| CNTR-04 | Phase 21 | Pending |
| CNTR-05 | Phase 21 | Pending |
| CNTR-06 | Phase 21 | Pending |
| INGP-01 | Phase 22 | Pending |
| INGP-02 | Phase 22 | Pending |
| INGP-03 | Phase 22 | Pending |
| INGP-04 | Phase 22 | Pending |
| INGP-05 | Phase 22 | Pending |
| INGP-06 | Phase 22 | Pending |
| METH-01 | Phase 19 | Complete |
| METH-02 | Phase 19 | Complete |
| METH-03 | Phase 19 | Complete |

**Coverage:**
- v3.0 requirements: 42 total
- Mapped to phases: 42
- Unmapped: 0 ✓

---
*Requirements defined: 2026-03-21*
*Last updated: 2026-03-21 after roadmap creation*
