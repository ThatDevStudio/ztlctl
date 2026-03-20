# Roadmap: ztlctl

## Milestones

- ✅ **v2.0 Platform** — Phases 1-7 (shipped 2026-03-20)
- 🚧 **v2.1 Documentation** — Phases 8-12 (in progress)

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

### 🚧 v2.1 Documentation (In Progress)

**Milestone Goal:** A production docs site that serves knowledge workers, plugin authors, and AI agents — each finding exactly what they need without wading through the others' content.

- [ ] **Phase 8: MkDocs Infrastructure** - Migrate from Jekyll to MkDocs + mkdocs-shadcn, clean up internal artifacts, wire GitHub Actions deploy
- [x] **Phase 9: Navigation Structure** - Build two-track nav (User Guide / Developer Guide), publish llms.txt and llms-full.txt (completed 2026-03-20)
- [x] **Phase 10: User Guide Content** - Paradigm walkthroughs, built-in plugin guides, agentic workflow recipes, session lifecycle guides (completed 2026-03-20)
- [ ] **Phase 11: Developer Guide + API Reference** - Plugin authoring guide, auto-generated API reference, architecture docs, CONTRIBUTING update
- [ ] **Phase 12: Doc Search Integration** - `ztlctl docs <query>` CLI command, `ztlctl://docs/search` MCP resource

## Phase Details

### Phase 8: MkDocs Infrastructure
**Goal**: The docs site builds and deploys from MkDocs + mkdocs-shadcn with no internal planning artifacts visible to the public
**Depends on**: Nothing (first phase of this milestone)
**Requirements**: INFR-01, INFR-02, INFR-03, INFR-04, INFR-05
**Success Criteria** (what must be TRUE):
  1. `mkdocs build` completes without errors using the shadcn theme with dark mode
  2. GitHub Actions workflow deploys to GitHub Pages on push to develop
  3. docs/plans/ directory content is excluded from the built site
  4. No internal artifacts (backlog.md, research-mapping.md, internal roadmap.md) appear in the published site
  5. Redirect stubs preserve any existing public URLs that changed during migration
**Plans:** 2/3 plans executed

Plans:
- [ ] 08-01-PLAN.md — Delete internal docs artifacts (backlog.md, research-mapping.md, roadmap.md) and repair index.md links
- [ ] 08-02-PLAN.md — Create mkdocs.yml, install dev dependencies, delete _config.yml, strip nav_order front matter from all 13 docs
- [ ] 08-03-PLAN.md — Create GitHub Actions docs.yml deploy workflow and verify live site after Pages source update

### Phase 9: Navigation Structure
**Goal**: Users land on the docs site and immediately see two clear paths — User Guide and Developer Guide — and agents can discover the full documentation corpus via llms.txt
**Depends on**: Phase 8
**Requirements**: UGDE-01, AGNT-01, AGNT-02
**Success Criteria** (what must be TRUE):
  1. Top-level navigation shows User Guide and Developer Guide as distinct sections with no content overlap
  2. `llms.txt` is served at the docs root per llmstxt.org spec with project summary and section links
  3. `llms-full.txt` is served at the docs root with concatenated documentation content for single-context-load consumption
  4. All existing docs pages are reachable under the new two-track structure with no broken internal links
**Plans:** 2/2 plans complete

Plans:
- [ ] 09-01-PLAN.md — Restructure mkdocs.yml nav into two tracks and create docs/guide/index.md + docs/dev/index.md
- [ ] 09-02-PLAN.md — Author docs/llms.txt per llmstxt.org spec, write scripts/gen_llms_full_txt.py, generate docs/llms-full.txt

### Phase 10: User Guide Content
**Goal**: Knowledge workers have concrete, example-driven guides for every core workflow — from understanding the paradigm to running agentic sessions
**Depends on**: Phase 9
**Requirements**: UGDE-02, UGDE-03, UGDE-04, UGDE-05
**Success Criteria** (what must be TRUE):
  1. A reader can follow the second-brain vs knowledge garden guide and understand which paradigm applies to their workflow
  2. A reader can set up and use each built-in plugin (Obsidian, Git, Reweave) by following the guide alone
  3. A reader can run a complete research-capture, review-triage, or knowledge-synthesis workflow end-to-end using the recipe walkthroughs
  4. A reader can understand the session lifecycle for both human-driven and agent-driven usage with concrete command examples
**Plans:** 3/3 plans complete

Plans:
- [ ] 10-01-PLAN.md — Expand docs/paradigms.md into comprehensive second-brain vs knowledge-garden comparison guide with scenarios
- [ ] 10-02-PLAN.md — Enhance docs/obsidian.md, create docs/plugins.md (Git + Reweave guides), update mkdocs.yml nav and llms infra
- [ ] 10-03-PLAN.md — Expand docs/agentic-workflows.md with 3 recipe walkthroughs and session lifecycle guides, regenerate llms-full.txt

### Phase 11: Developer Guide + API Reference
**Goal**: Plugin authors have a complete, accurate reference for every hookspec, custom note type, and config contract — and contributors have an architecture walkthrough that matches the current codebase
**Depends on**: Phase 9
**Requirements**: DVGD-01, DVGD-02, DVGD-03, DVGD-04
**Success Criteria** (what must be TRUE):
  1. A plugin author can implement a working plugin with a custom note type and capability declaration by following the authoring guide alone
  2. Auto-generated API reference reflects current Python docstrings/type hints for all public plugin contracts, hook signatures, event types, and ActionRegistry
  3. A core contributor can understand the ActionRegistry and controller architecture by reading the architecture documentation
  4. CONTRIBUTING.md links to the developer guide and describes the current architecture accurately
**Plans**: TBD

### Phase 12: Doc Search Integration
**Goal**: Agents and users can query the documentation corpus directly from the CLI or through MCP without leaving their tool
**Depends on**: Phase 10, Phase 11
**Requirements**: AGNT-03, AGNT-04
**Success Criteria** (what must be TRUE):
  1. `ztlctl docs <query>` returns ranked results from the docs corpus with relevant excerpts
  2. An MCP client can query `ztlctl://docs/search` with a query string and receive relevant documentation passages
  3. Both CLI and MCP search use the same underlying `_impl` function following the established pattern
**Plans**: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 8 → 9 → 10 → 11 → 12
Note: Phase 10 and Phase 11 depend on Phase 9 but not on each other — they can be parallelized.

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Core Hardening | v2.0 | 5/5 | Complete | 2026-03-19 |
| 2. Action Registry | v2.0 | 4/4 | Complete | 2026-03-19 |
| 3. MCP Surface Generation | v2.0 | 2/2 | Complete | 2026-03-19 |
| 4. CLI Surface Generation | v2.0 | 2/2 | Complete | 2026-03-20 |
| 5. Plugin Formalization | v2.0 | 3/3 | Complete | 2026-03-20 |
| 6. Agentic Integration & Security | v2.0 | 3/3 | Complete | 2026-03-20 |
| 7. Plugin & Agentic Wiring Fixes | v2.0 | 3/3 | Complete | 2026-03-20 |
| 8. MkDocs Infrastructure | v2.1 | 2/3 | In Progress | - |
| 9. Navigation Structure | 2/2 | Complete   | 2026-03-20 | - |
| 10. User Guide Content | 3/3 | Complete   | 2026-03-20 | - |
| 11. Developer Guide + API Reference | v2.1 | 0/? | Not started | - |
| 12. Doc Search Integration | v2.1 | 0/? | Not started | - |
