# Requirements: ztlctl v3.1 Documentation & Hardening

**Defined:** 2026-03-21
**Core Value:** Agents should only ever have to orchestrate the tool — not build custom functionality that is lacking from the tool.

## v3.1 Requirements

Requirements for v3.1 release. Each maps to roadmap phases.

### Documentation Infrastructure

- [x] **DINF-01**: Doc lint CI gate in pr-ci.yml: `mkdocs build --strict` + Vale prose lint + pymarkdownlnt structure lint — broken docs cannot merge
- [x] **DINF-02**: CLAUDE.md contains enforceable rule: when adding/modifying actions or features, update relevant docs pages and llms.txt in the same PR
- [x] **DINF-03**: GSD workflow templates include documentation tasks in every feature phase plan — structural enforcement, not optional
- [x] **DINF-04**: mkdocs-git-revision-date-localized shows "last updated" dates from git history on every docs page

### New Feature Documentation

- [ ] **NDOC-01**: Standalone `session-recall.md` page covering temporal/topic/topology recall: CLI usage, MCP tools, agent workflow examples, configuration
- [ ] **NDOC-02**: Standalone `polaris.md` page covering priorities layer: init scaffold, MCP resource `ztlctl://polaris`, context assembly, `check_alignment` action, agent decision workflows
- [ ] **NDOC-03**: Standalone `contradiction-detection.md` page covering semantic integrity: `check_contradictions`, heuristic scoring, `confirm_contradiction`, graph edges, MCP review resource
- [ ] **NDOC-04**: Standalone `media-ingestion.md` page covering ingestion pipeline: supported formats, faster-whisper transcription, `ingest_media` CLI/MCP, two-phase captured→annotated workflow, `[ingest.media]` config
- [ ] **NDOC-05**: Standalone `methodology.md` page covering prose-as-title convention, title quality checks, garden backlog title candidates

### Documentation Quality

- [ ] **QUAL-01**: Diataxis audit of all existing docs pages — classify each by content type (tutorial/how-to/reference/explanation), identify and fix mixed-purpose pages
- [ ] **QUAL-02**: Existing pages updated with v3.0 feature coverage: concepts.md, agentic-workflows.md, agents.md, mcp.md reflect all new services, actions, and MCP resources
- [ ] **QUAL-03**: llms.txt and llms-full.txt refreshed with all new pages and v3.0 feature descriptions — agent discovery indexes are current
- [ ] **QUAL-04**: Consistent CLI syntax conventions, admonition taxonomy, and cross-referencing across all docs pages — Stripe/Docker-quality presentation

### Internal Documentation

- [ ] **IDOC-01**: CLAUDE.md architecture section updated with v3.0 services (15 services, 17 controllers, 73+ actions, feature-local registration, centralized PM)
- [ ] **IDOC-02**: DESIGN.md refreshed with v3.0 architectural decisions (event model, action executor, plugin runtime, recall, contradiction, ingestion)
- [ ] **IDOC-03**: README.md feature list and command examples updated for v3.0 (session recall, polaris, contradiction, ingestion commands)

### Tech Debt

- [x] **DEBT-09**: IngestService._ingest_normalized calls `_dispatch_post_action_event` — post_action plugin hooks fire for ingest_* actions; `test_post_action_dispatch.py` includes `ingest.py`
- [x] **DEBT-10**: Stale docstrings/comments fixed: ContradictionController.confirm_contradiction stub docstring, commands/generator.py stale `_register_core_actions` comment

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
| Auto-generated llms.txt script | Current page count (~25) doesn't justify build automation; hand-maintenance is still manageable |
| External link checking in CI | Adds latency and network flakiness to CI; lychee can be added later if broken external links become a problem |
| MkDocs theme change | mkdocs-shadcn is working well; no reason to switch |
| Video tutorials | Text docs are the priority; video can come later for broader adoption |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| DINF-01 | Phase 23 | Complete |
| DINF-02 | Phase 23 | Complete |
| DINF-03 | Phase 23 | Complete |
| DINF-04 | Phase 23 | Complete |
| DEBT-09 | Phase 23 | Complete |
| DEBT-10 | Phase 23 | Complete |
| QUAL-01 | Phase 24 | Pending |
| QUAL-04 | Phase 24 | Pending |
| NDOC-01 | Phase 25 | Pending |
| NDOC-02 | Phase 25 | Pending |
| NDOC-03 | Phase 25 | Pending |
| NDOC-04 | Phase 25 | Pending |
| NDOC-05 | Phase 25 | Pending |
| QUAL-02 | Phase 26 | Pending |
| QUAL-03 | Phase 26 | Pending |
| IDOC-01 | Phase 27 | Pending |
| IDOC-02 | Phase 27 | Pending |
| IDOC-03 | Phase 27 | Pending |

**Coverage:**
- v3.1 requirements: 18 total
- Mapped to phases: 18
- Unmapped: 0

---
*Requirements defined: 2026-03-21*
*Last updated: 2026-03-21 after roadmap creation (traceability complete)*
