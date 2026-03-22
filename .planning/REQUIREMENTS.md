# Requirements: ztlctl v4.0 Agentic Skills

**Defined:** 2026-03-22
**Core Value:** Agents should only ever have to orchestrate the tool — not build custom functionality that is lacking from the tool.

## v4.0 Requirements

Requirements for v4.0 release. Each maps to roadmap phases.

### Plugin Foundation

- [x] **PLGN-01**: Plugin directory layout follows Claude Code conventions — plugin.json manifest, .mcp.json, skills/, hooks/, commands/, agents/ all in correct locations; `claude plugin validate` passes
- [x] **PLGN-02**: MCP stdio transport is clean — ztlctl serve produces zero stdout pollution; JSON-RPC stream verified with protocol-level test
- [x] **PLGN-03**: PreToolUse vault gate hook blocks all mcp__ztlctl__* calls when no vault is initialized, returning a user-friendly error with `ztlctl init` guidance
- [x] **PLGN-04**: Plugin validation runs in CI — pr-ci.yml includes a `plugin_validate` job that catches manifest errors, missing files, and broken hooks before merge

### Table Stakes Skills

- [x] **SKIL-01**: `ztl:orient` skill provides vault status overview — recent activity, open sessions, polaris priorities, work queue summary — via composing discover_tools, session_status, and agent_context MCP calls
- [x] **SKIL-02**: `ztl:session` skill manages full session lifecycle — start (with polaris alignment), capture during session, close (with enrichment pipeline) — via session_start, create_note/reference/task, session_close MCP calls
- [x] **SKIL-03**: `ztl:capture` skill guides structured content creation — notes, references, tasks with appropriate metadata, tags, and links — via create_note, create_reference, create_task MCP calls with reweave follow-up
- [x] **SKIL-04**: `ztl:review-triage` skill runs vault health check and surfaces actionable items — integrity issues, work queue priorities, garden backlog — via check_integrity, work_queue, vault_review MCP calls
- [x] **SKIL-05**: `ztl:align` skill evaluates decisions against polaris priorities — reads polaris document, runs check_alignment, presents structured alignment analysis for agent decision-making

### Differentiator Skills

- [ ] **SKIL-06**: `ztl:synthesize` skill drives topic-driven research pipeline — search vault, assemble topic packet, analyze gaps, generate draft — via search, topic_packet, graph_gaps, draft_from_topic MCP calls
- [ ] **SKIL-07**: `ztl:decision-support` skill provides structured decision analysis — gathers relevant notes, runs decision_support, evaluates against polaris — via search, decision_support, check_alignment MCP calls
- [ ] **SKIL-08**: `ztl:orient-session` skill starts recall-driven sessions — queries what was worked on recently, identifies continuation points, starts session with context — via recall_temporal, recall_topic, session_start MCP calls
- [ ] **SKIL-09**: `ztl:garden-health` skill runs full garden maintenance cycle — check integrity, identify stale seeds, review orphans, suggest reweave candidates — via check_integrity, vault_review, work_queue, reweave MCP calls
- [ ] **SKIL-10**: `ztl:review-contradictions` skill manages contradiction review workflow — surface candidates, present for evaluation, record confirmed contradictions — via check_contradictions, confirm_contradiction MCP calls

### Commands and Agents

- [ ] **CMDA-01**: Slash commands provide thin entry points for common skills — `/ztlctl:session`, `/ztlctl:capture`, `/ztlctl:review` map to corresponding skills with argument passthrough
- [ ] **CMDA-02**: Research agent operates autonomously for deep vault exploration — searches, follows graph connections, assembles findings — constrained by configurable depth limit and token budget
- [ ] **CMDA-03**: Maintenance agent runs scheduled vault health operations — integrity check, contradiction scan, garden cleanup — constrained to read-heavy operations with confirmation gates for mutations

### Distribution

- [ ] **DIST-01**: Plugin installs via git-subdir marketplace source — `marketplace.json` uses git-subdir pointing to `plugin/` directory in the ztlctl GitHub repo; `claude plugin install ztlctl` works
- [ ] **DIST-02**: Plugin version is synchronized with release pipeline — plugin.json version bumps alongside pyproject.toml in the release workflow; users get updates via `claude plugin update`
- [ ] **DIST-03**: Installation documentation covers prerequisites — ztlctl must be installed (`pip install ztlctl` or `brew install ztlctl`), vault must be initialized, user must run `claude` from vault directory

## v5.0 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Advanced Memory

- **AMEM-01**: Session graph visualization (interactive session-to-file topology browser)
- **AMEM-02**: Claude Code JSONL conversation parsing into indexed markdown
- **AMEM-03**: Kanban board generation from unstructured task text

### Plugin Ecosystem

- **PECO-01**: Custom skill authoring guide for third-party ztlctl skills
- **PECO-02**: Skill marketplace/registry for community-contributed workflows
- **PECO-03**: Skill composition language (skills that invoke other skills)

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| GUI/web interface | ztlctl is CLI/MCP-first; Obsidian serves as the visual layer |
| Multi-user/collaboration | Local single-user tool; collaboration through shared repos |
| Cloud sync | Filesystem is the storage layer; sync is the user's responsibility |
| Cursor/VS Code plugin | Claude Code first; other editors after marketplace validation |
| Skills that wrap single MCP calls | Anti-pattern per research — skills encode multi-step workflows, not atomic operations |
| LLM-dependent skills | Skills must work without making API calls; ztlctl is LLM-free at runtime |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| PLGN-01 | Phase 28 | Complete |
| PLGN-02 | Phase 28 | Complete |
| PLGN-03 | Phase 28 | Complete |
| PLGN-04 | Phase 28 | Complete |
| SKIL-01 | Phase 29 | Complete |
| SKIL-02 | Phase 29 | Complete |
| SKIL-03 | Phase 29 | Complete |
| SKIL-04 | Phase 29 | Complete |
| SKIL-05 | Phase 29 | Complete |
| SKIL-06 | Phase 30 | Pending |
| SKIL-07 | Phase 30 | Pending |
| SKIL-08 | Phase 30 | Pending |
| SKIL-09 | Phase 30 | Pending |
| SKIL-10 | Phase 30 | Pending |
| CMDA-01 | Phase 31 | Pending |
| CMDA-02 | Phase 31 | Pending |
| CMDA-03 | Phase 31 | Pending |
| DIST-01 | Phase 31 | Pending |
| DIST-02 | Phase 31 | Pending |
| DIST-03 | Phase 31 | Pending |

**Coverage:**
- v4.0 requirements: 19 total
- Mapped to phases: 19
- Unmapped: 0

---
*Requirements defined: 2026-03-22*
*Last updated: 2026-03-22 after roadmap creation*
