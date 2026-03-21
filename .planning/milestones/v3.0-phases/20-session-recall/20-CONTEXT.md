# Phase 20: Session Recall - Context

**Gathered:** 2026-03-21
**Status:** Ready for planning

<domain>
## Phase Boundary

Add session recall capabilities: temporal querying (date-range filtering with per-session summaries), topic searching (BM25 across session logs), and topology discovery (shared notes/tags across sessions). Expose via MCP resource and registered actions.

</domain>

<decisions>
## Implementation Decisions

### Recall Query Design
- Temporal recall summarizes sessions with: topic from session start event, count of log entries, note IDs created — lightweight, no LLM needed
- Topic recall uses BM25 search across `session_logs.summary` field — reuses existing FTS infrastructure, no new dependencies
- Topology recall detects shared content via shared note references across sessions (notes created/modified in multiple sessions) + shared tags — graph-based approach

### MCP Resource and Action Surface
- `ztlctl://sessions/recent` returns last 5 sessions with: session_id, topic, start/end timestamps, note count, log entry count — compact JSON for agent context
- All recall actions are registered ActionDefinitions — auto-generate both CLI and MCP surfaces (define-once architecture)
- Single RecallService with 3 methods (`recall_temporal`, `recall_topic`, `recall_topology`) — matches existing service pattern

### Data Model and Output
- Recall results include summaries only (topic + note count + date range) — token-efficient for agents
- Topology connectivity represented as list of `{session_a, session_b, shared_notes: [...], shared_tags: [...]}` pairs
- ISO strings for input (`--from`, `--to`), both ISO and human-readable in output — consistent with existing CLI patterns

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/ztlctl/services/session.py` — SessionService with start/close/reopen/status/log_entry/context/brief/extract_decision/cost
- `src/ztlctl/infrastructure/database/schema.py` — `nodes` table (has `session` column), `session_logs` table (session_id, timestamp, type, subtype, summary, detail, cost, references)
- `src/ztlctl/services/query.py` — QueryService with BM25 FTS search patterns
- `src/ztlctl/mcp/resources.py` — MCP resource registration patterns
- `src/ztlctl/services/context.py` — ContextAssembler for agent context windows

### Established Patterns
- Services extend `BaseService` with `_vault` access
- ActionDefinition registration in feature-local modules (`src/ztlctl/actions/`)
- FTS5 standalone approach — service layer manages inserts explicitly
- `session_logs` stores type/subtype/summary/detail/references per log entry

### Integration Points
- New `src/ztlctl/services/recall.py` — RecallService
- New `src/ztlctl/controllers/recall.py` — RecallController
- `src/ztlctl/actions/_session.py` — register recall actions alongside session actions
- `src/ztlctl/mcp/resources.py` — add `ztlctl://sessions/recent` resource

</code_context>

<specifics>
## Specific Ideas

- Temporal recall should filter on `nodes.created` for sessions (type='session' in nodes table)
- Topic recall can leverage existing FTS5 on nodes table, plus direct LIKE search on session_logs.summary
- Topology shared-notes detection: query nodes table for notes that have session column matching multiple session IDs

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>
