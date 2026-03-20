# Requirements: ztlctl v2.1

**Defined:** 2026-03-20
**Core Value:** Agents should only ever have to orchestrate the tool — not build custom functionality that is lacking from the tool.

## v1 Requirements

Requirements for this milestone. Each maps to roadmap phases.

### Documentation Infrastructure

- [x] **INFR-01**: Migrate from Jekyll + Just the Docs to MkDocs + mkdocs-shadcn theme with dark mode, modern shadcn/ui aesthetic
- [x] **INFR-02**: Remove internal planning artifacts from public docs site (backlog.md, research-mapping.md, internal roadmap.md)
- [x] **INFR-03**: Exclude docs/plans/ directory from published site via mkdocs.yml config
- [x] **INFR-04**: Set up GitHub Actions workflow for MkDocs gh-deploy to GitHub Pages
- [x] **INFR-05**: Add redirect handling for changed URLs to preserve existing links

### User Guide

- [x] **UGDE-01**: Two-track navigation with User Guide and Developer Guide as top-level sections
- [x] **UGDE-02**: Second-brain vs knowledge garden paradigm walkthroughs with examples and common scenarios
- [x] **UGDE-03**: Built-in plugin guides — Obsidian setup and integration, Git plugin usage, Reweave plugin behavior
- [x] **UGDE-04**: Agentic workflow recipe walkthroughs — research-capture, review-triage, knowledge-synthesis with step-by-step examples
- [x] **UGDE-05**: Session lifecycle guides for both human-driven and agent-driven usage with concrete examples

### Developer Guide

- [ ] **DVGD-01**: Plugin authoring guide — hookspecs, custom note types, config schemas, capability declarations, marketplace metadata
- [ ] **DVGD-02**: Auto-generated API reference from Python docstrings/type hints via griffe/mkdocstrings
- [ ] **DVGD-03**: ActionRegistry and controller architecture documentation for core contributors
- [ ] **DVGD-04**: Update CONTRIBUTING.md with current architecture walkthrough and link to developer guide

### Agent Accessibility

- [x] **AGNT-01**: `llms.txt` at docs root with project summary and section links per llmstxt.org spec
- [x] **AGNT-02**: `llms-full.txt` with concatenated documentation content for single-context-load consumption
- [ ] **AGNT-03**: `ztlctl docs <query>` CLI command for local documentation search with ranked results
- [ ] **AGNT-04**: `ztlctl://docs/search` MCP resource for agent-queryable documentation following existing _impl pattern

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Advanced Documentation

- **ADOC-01**: Versioned documentation (multiple versions served simultaneously)
- **ADOC-02**: Interactive API playground (try commands in-browser)
- **ADOC-03**: Community-contributed plugin showcase/registry page

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Custom docs framework (Docusaurus, Astro) | MkDocs + mkdocs-shadcn provides the aesthetic and features needed without custom JS framework overhead |
| Auto-generated CLI reference replacing hand-authored | Hand-authored command docs have better context and examples; auto-gen loses narrative quality |
| Per-page MCP resources | Creates 1:1 maintenance burden; single parameterized search resource is sufficient |
| Docs hosting migration away from GitHub Pages | GitHub Pages is free, reliable, and fits the project's scale |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| INFR-01 | Phase 8 | Complete |
| INFR-02 | Phase 8 | Complete |
| INFR-03 | Phase 8 | Complete |
| INFR-04 | Phase 8 | Complete |
| INFR-05 | Phase 8 | Complete |
| UGDE-01 | Phase 9 | Complete |
| UGDE-02 | Phase 10 | Complete |
| UGDE-03 | Phase 10 | Complete |
| UGDE-04 | Phase 10 | Complete |
| UGDE-05 | Phase 10 | Complete |
| DVGD-01 | Phase 11 | Pending |
| DVGD-02 | Phase 11 | Pending |
| DVGD-03 | Phase 11 | Pending |
| DVGD-04 | Phase 11 | Pending |
| AGNT-01 | Phase 9 | Complete |
| AGNT-02 | Phase 9 | Complete |
| AGNT-03 | Phase 12 | Pending |
| AGNT-04 | Phase 12 | Pending |

**Coverage:**
- v1 requirements: 18 total
- Mapped to phases: 18
- Unmapped: 0

---
*Requirements defined: 2026-03-20*
*Last updated: 2026-03-20 after roadmap creation*
