# Roadmap: ztlctl

## Milestones

- ✅ **v2.0 Platform** — Phases 1-7 (shipped 2026-03-20)
- ✅ **v2.1 Documentation** — Phases 8-14 (shipped 2026-03-21)
- ✅ **v3.0 Memory and Hardening** — Phases 15-22 (shipped 2026-03-21)
- ✅ **v3.1 Documentation & Hardening** — Phases 23-27 (shipped 2026-03-22)
- 🚧 **v4.0 Agentic Skills** — Phases 28-32 (in progress)

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

<details>
<summary>✅ v3.1 Documentation & Hardening (Phases 23-27) — SHIPPED 2026-03-22</summary>

- [x] Phase 23: Docs-as-Code Infrastructure (2/2 plans) — completed 2026-03-21
- [x] Phase 24: Navigation and Information Architecture (1/1 plan) — completed 2026-03-21
- [x] Phase 25: New v3.0 Feature Pages (3/3 plans) — completed 2026-03-21
- [x] Phase 26: Existing Pages and Quality Pass (2/2 plans) — completed 2026-03-21
- [x] Phase 27: Internal Documentation Refresh (2/2 plans) — completed 2026-03-21

Full details: `.planning/milestones/v3.1-ROADMAP.md`

</details>

### 🚧 v4.0 Agentic Skills (In Progress)

**Milestone Goal:** Create a production-grade Claude Code plugin for ztlctl that wraps the MCP server with deep skills encoding core vault workflows, enabling agents to orchestrate zettelkasten operations through guided skill invocations rather than raw tool calls. Distribute via Claude Code plugin marketplace.

- [ ] **Phase 28: Plugin Foundation** - Scaffold correct plugin directory layout, validate MCP stdio transport, wire vault gate hook, and establish CI gate for plugin validation
- [ ] **Phase 29: MVP Skills** - Implement five table-stakes skills (orient, session, capture, review-triage, align) that cover the core vault workflows agents use most
- [ ] **Phase 30: Differentiator Skills** - Implement five advanced skills (synthesize, decision-support, orient-session, garden-health, review-contradictions) that encode ztlctl's unique capabilities
- [ ] **Phase 31: Commands, Agents, and Distribution** - Wire slash commands as skill entry points, implement autonomous agents, and validate end-to-end marketplace installation
- [ ] **Phase 32: Validation and Hardening** - Run the full distribution checklist, validate skill activation under installed state, and lock in CI gates before marketplace submission

## Phase Details

### Phase 28: Plugin Foundation
**Goal**: The plugin directory is correctly structured, the MCP stdio transport is clean, the vault gate blocks unauthenticated access, and CI catches plugin regressions before merge
**Depends on**: Nothing (first v4.0 phase; builds on shipped v3.1 MCP server)
**Requirements**: PLGN-01, PLGN-02, PLGN-03, PLGN-04
**Success Criteria** (what must be TRUE):
  1. Running `claude plugin validate` on the plugin directory exits with zero warnings or errors
  2. Sending a raw JSON-RPC request to `ztlctl serve` via stdin produces a well-formed JSON response with no non-JSON bytes on stdout
  3. Invoking any `mcp__ztlctl__*` tool without an initialized vault causes Claude Code to display a user-friendly error message directing the user to run `ztlctl init`
  4. Opening a pull request that introduces a manifest error or missing hook file causes the `plugin_validate` CI job to fail and block the merge
**Plans**: TBD

### Phase 29: MVP Skills
**Goal**: Five table-stakes skills are installed, correctly activated by natural language, and guide agents through the most common vault workflows without requiring knowledge of raw MCP tool names
**Depends on**: Phase 28
**Requirements**: SKIL-01, SKIL-02, SKIL-03, SKIL-04, SKIL-05
**Success Criteria** (what must be TRUE):
  1. Asking "what is the state of my vault?" or similar orientation prompts causes `ztl:orient` to activate and return a structured summary of recent activity, open sessions, polaris priorities, and work queue without any manual tool invocation
  2. Asking to start a work session causes `ztl:session` to run the full lifecycle (polaris alignment check, session start, capture during session, session close with enrichment report) with a user confirmation gate before each write operation
  3. Asking to capture a note, reference, or task causes `ztl:capture` to search the vault for existing related content, create the item with appropriate metadata and links, and trigger reweave — without the user specifying MCP tool names
  4. Asking to review the work queue or vault health causes `ztl:review-triage` to surface integrity issues, work queue priorities, and garden backlog, then present a proposed action set for user approval before executing any writes
  5. Asking whether a decision aligns with priorities causes `ztl:align` to read the polaris document, run `check_alignment`, and present a structured alignment analysis with a clear recommendation
**Plans**: TBD

### Phase 30: Differentiator Skills
**Goal**: Five advanced skills are installed and correctly activated, covering knowledge synthesis, decision analysis, recall-driven sessions, garden maintenance, and contradiction review — each encoding multi-step workflows that would be error-prone to perform through raw MCP calls
**Depends on**: Phase 29
**Requirements**: SKIL-06, SKIL-07, SKIL-08, SKIL-09, SKIL-10
**Success Criteria** (what must be TRUE):
  1. Asking to synthesize knowledge on a topic causes `ztl:synthesize` to search the vault, identify graph gaps, assemble a topic packet, generate a draft, and wait for user approval before creating any note
  2. Asking for decision support causes `ztl:decision-support` to autonomously gather relevant notes, run `decision_support`, and evaluate results against polaris — presenting a structured briefing with no writes
  3. Asking to start a session on a topic previously worked on causes `ztl:orient-session` to surface what was worked on via temporal and topic recall before starting the session grounded in prior context
  4. Asking to run garden maintenance causes `ztl:garden-health` to audit orphans, structural gaps, and bridge nodes autonomously, then present a maintenance report with a confirmation gate before executing any writes
  5. Asking to review contradictions causes `ztl:review-contradictions` to surface candidate pairs, present each for human evaluation, and only call `confirm_contradiction` after explicit per-pair user approval — never auto-confirming; gracefully degrades if sqlite-vec is absent
**Plans**: TBD

### Phase 31: Commands, Agents, and Distribution
**Goal**: Slash commands provide quick entry points to skills, autonomous agents operate safely within constrained tool allowlists, and the plugin installs correctly from the marketplace with synchronized versioning and clear prerequisite documentation
**Depends on**: Phase 29 (skills must exist before commands reference them)
**Requirements**: CMDA-01, CMDA-02, CMDA-03, DIST-01, DIST-02, DIST-03
**Success Criteria** (what must be TRUE):
  1. Typing `/ztlctl:session`, `/ztlctl:capture`, or `/ztlctl:review` in Claude Code activates the corresponding skill with any provided arguments passed through correctly
  2. Invoking the research agent causes it to search the vault, follow graph connections, and assemble findings autonomously — stopping when it hits the configured depth limit or token budget without requiring user intervention
  3. Running the maintenance agent executes integrity check, contradiction scan, and garden cleanup in read-heavy mode — presenting a summary and requesting confirmation before any mutation
  4. Running `claude plugin install ztlctl` on a machine where ztlctl is installed and a vault is initialized successfully installs the plugin and makes all skills and commands available in Claude Code
  5. After a release merges to develop, `plugin.json` version is automatically bumped alongside `pyproject.toml` so that `claude plugin update` delivers the latest skills to users
**Plans**: TBD

### Phase 32: Validation and Hardening
**Goal**: Every plugin component has been verified under installed state (not just `--plugin-dir`), all 20+ distribution checklist items pass, skill activation is reliable across all 10 skills, and the plugin is ready for marketplace submission
**Depends on**: Phases 28, 29, 30, 31 (all prior phases must be complete)
**Requirements**: (cross-cutting quality pass — no new requirements; validates PLGN-01 through DIST-03)
**Success Criteria** (what must be TRUE):
  1. Every skill activates correctly on at least 5 distinct trigger prompts and does not activate on at least 3 non-trigger prompts, tested under installed state (not `--plugin-dir`)
  2. Loading all 10 skills simultaneously in a Claude Code session leaves sufficient context window for a normal conversation (verified via `/context` check showing skills consuming less than 2% of context budget)
  3. The full PITFALLS.md distribution checklist passes with zero open items — covering directory structure, stdout cleanliness, version bump gate, hook exit codes, agent frontmatter, and MCP tool name consistency
  4. `claude plugin validate` reports zero warnings on the final plugin directory structure
**Plans**: TBD

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1-7. v2.0 Platform | v2.0 | 22/22 | Complete | 2026-03-20 |
| 8-14. v2.1 Documentation | v2.1 | 21/21 | Complete | 2026-03-21 |
| 15-22. v3.0 Memory and Hardening | v3.0 | 22/22 | Complete | 2026-03-21 |
| 23-27. v3.1 Documentation & Hardening | v3.1 | 10/10 | Complete | 2026-03-22 |
| 28. Plugin Foundation | v4.0 | 0/? | Not started | - |
| 29. MVP Skills | v4.0 | 0/? | Not started | - |
| 30. Differentiator Skills | v4.0 | 0/? | Not started | - |
| 31. Commands, Agents, and Distribution | v4.0 | 0/? | Not started | - |
| 32. Validation and Hardening | v4.0 | 0/? | Not started | - |
