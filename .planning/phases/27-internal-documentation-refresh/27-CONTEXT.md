# Phase 27: Internal Documentation Refresh - Context

**Gathered:** 2026-03-21
**Status:** Ready for planning

<domain>
## Phase Boundary

Update CLAUDE.md architecture section, DESIGN.md, and README.md to accurately describe the v3.0 system. Developers and contributors work from current information. Does NOT modify external docs pages (Phases 25-26 complete).

</domain>

<decisions>
## Implementation Decisions

### All Decisions from Requirements
- **IDOC-01**: CLAUDE.md architecture section lists all 15 services, 17 controllers, 73+ actions; describes feature-local action registration and centralized PluginManager factory
- **IDOC-02**: DESIGN.md captures v3.0 architectural decisions: reliable event model (WAL drain, service-only post_action), generic action executor, feature-local registration, recall/contradiction/ingestion design choices
- **IDOC-03**: README.md feature list and command examples include session recall, polaris priorities, contradiction detection, and media ingestion

### Claude's Discretion
- All implementation choices — pure infrastructure phase. Content is dictated by current source code state.
- Whether to restructure sections or just update content
- How much architectural detail to include in DESIGN.md

</decisions>

<code_context>
## Existing Code Insights

### Integration Points
- `CLAUDE.md` — Architecture section needs v3.0 service/controller/action counts
- `DESIGN.md` — Needs v3.0 architectural decisions added
- `README.md` — Feature list and command examples need v3.0 additions

</code_context>

<specifics>
## Specific Ideas

No specific requirements — infrastructure phase.

</specifics>

<deferred>
## Deferred Ideas

None — this is the last phase of v3.1.

</deferred>
