---
title: Agentic Workflows
nav_order: 8
---

# Agentic Workflows

ztlctl is designed for agent-assisted capture and synthesis. Every command supports `--json`, sessions provide operational coordination, and topic packets provide read-oriented retrieval even when no session is active.

## Capture and Synthesis Workflow

Sessions are operational coordination state, not durable authored knowledge. Use them to structure research work, then turn findings into notes, references, and tasks:

```bash
# Agent starts a focused research session
ztlctl agent session start "API design patterns" --json

# Agent captures sources and synthesis
ztlctl ingest text "API source notes" --stdin --as reference --json
ztlctl create note "REST vs GraphQL trade-offs" \
  --tags "architecture/api" --session LOG-0001 --json

# Agent logs its reasoning and costs
ztlctl agent session log "Analyzed 5 API frameworks" --cost 1200 --json
ztlctl agent session log "Key insight: GraphQL better for nested data" --pin --json

# Agent checks token budget
ztlctl agent session cost --report 50000 --json

# Agent requests context for continued work
ztlctl agent context --topic "api" --budget 4000 --json

# Agent closes session, triggering capture/synthesis cleanup
ztlctl agent session close --summary "Mapped API paradigms" --json
```

## Ingestion

Core ingestion is text-first:

- raw text via `ztlctl ingest text`
- markdown and plain text files via `ztlctl ingest file`
- URLs via `ztlctl ingest url`, but only when a source-provider plugin is installed

```bash
ztlctl ingest text "OAuth notes" --stdin --as reference --json
ztlctl ingest file ./source.md --as note --json
ztlctl ingest providers --json
```

URL ingestion is provider-backed by design. The core tool does not ship a built-in remote fetcher in the base install.

For agent-fetched web and multimodal workflows, use a bundle-first handoff:

1. Fetch or extract the source outside ztlctl.
2. Normalize the capture into plain text plus a nested `source_bundle`.
3. Call MCP `ingest_source` with `content=<normalized text>` and `source_bundle=<bundle>`.
4. Let ztlctl persist the bundle beside the ingested reference under `sources/<reference-id>/`.

Read `ztlctl://capture/spec` for the exact bundle contract. The flat evidence-envelope fields (`source_kind`, `modalities`, `capture_agent`, `capture_method`, `citations`, `excerpts`, and `artifacts`) still work, but ztlctl now normalizes them into the durable source bundle format internally.

## Context Assembly (5-Layer System)

The `agent context` command builds a token-budgeted payload with 5 layers:

| Layer | Content | Budget |
|-------|---------|--------|
| 0 — Identity | `self/identity.md` + `self/methodology.md` | Always included |
| 1 — Operational | Active session, recent decisions, work queue, log entries | Always included |
| 2 — Topic | Notes and references matching the session topic | Budget-dependent |
| 3 — Graph | 1-hop neighbors of Layer 2 content | Budget-dependent |
| 4 — Background | Recent activity, structural gaps | Budget-dependent |

The system tracks token usage per layer and reports pressure status (`normal`, `caution`, `exceeded`).

```bash
# Get full context with default 8000-token budget
ztlctl agent context --json

# Focus on a topic with custom budget
ztlctl agent context --topic "architecture" --budget 4000 --json

# Quick orientation (no session required)
ztlctl agent brief --json
```

## Topic Packets

Use topic packets when you want conversational retrieval without depending on an active session:

```bash
ztlctl query packet --topic architecture --mode learn --json
ztlctl query packet --topic architecture --mode review --json
ztlctl query packet --topic architecture --mode decision --json
```

Packets combine topic-matched notes, references, decisions, tasks, graph-adjacent material, evidence excerpts, supporting/conflicting links, stale items, bridge candidates, suggested actions, ranking explanations, and provenance maps so an agent can continue reasoning from captured knowledge rather than only from recent session state.

Packets now merge topic-scoped items with search-ranked items, so a reference tagged to a topic is still available for review and learning even when its title/body is a weak lexical match for the topic string itself.

When a packet should become durable work, draft from it directly:

```bash
ztlctl query draft --topic architecture --target note --json
ztlctl query draft --topic architecture --mode review --target task --json
ztlctl query draft --topic architecture --mode decision --target decision --json
```

## Session Close Enrichment Pipeline

When a session closes, ztlctl automatically runs:

1. **Cross-session reweave** — discovers connections for all notes created in the session
2. **Orphan sweep** — attempts to connect orphan notes (0 outgoing edges)
3. **Integrity check** — validates vault consistency
4. **Graph materialization** — updates PageRank, degree, and betweenness metrics

Each step can be toggled in `ztlctl.toml`:

```toml
[session]
close_reweave = true
close_orphan_sweep = true
close_integrity_check = true
```

## Decision Extraction

Extract decisions from session logs into permanent decision notes:

```bash
# Extracts pinned/decision entries from the session log
ztlctl extract LOG-0001 --title "Decision: Use GraphQL for nested queries"
```

This creates a decision note (`subtype=decision`, status `proposed`) linked to the session via a `derived_from` edge.

## MCP Server Integration

ztlctl includes a Model Context Protocol (MCP) server for direct integration with AI clients like Claude Desktop and Codex-compatible environments:

```bash
ztlctl serve --transport stdio
```

Use the discovery flow in MCP clients:

1. `discover_tools`
2. `describe_tool`
3. `ztlctl://agent-reference`

For enrichment-focused agents, the most useful read models are:

- `ztlctl://review/dashboard`
- `ztlctl://garden/backlog`
- `ztlctl://decision-queue`
- `ztlctl://capture/spec`

The MCP prompt layer now also includes `topic_learn`, `topic_review`, `topic_decision`, `capture_web_source`, and `capture_multimodal_source`.

See the [MCP Server](mcp.md) page for tool categories, resources, prompts, and exported client assets.

## Batch Operations

For programmatic creation, use batch mode with a JSON file:

```bash
echo '[
  {"type": "note", "title": "Concept A", "tags": ["domain/scope"]},
  {"type": "reference", "title": "Source B", "url": "https://example.com"},
  {"type": "task", "title": "Follow up on C", "priority": "high"}
]' > items.json

ztlctl create batch items.json --json
ztlctl create batch items.json --partial  # Continue on individual failures
```

## Scripting with JSON Output

Every command supports `--json` for structured output:

```bash
# Create and capture the ID
ID=$(ztlctl create note "My Note" --json | jq -r '.data.id')

# Query and process results
ztlctl query search "python" --json | jq '.data.items[].title'

# Check vault health programmatically
ERRORS=$(ztlctl check --json | jq '.data.issues | map(select(.severity == "error")) | length')
```
