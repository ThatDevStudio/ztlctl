---
title: Agentic Workflows
nav_order: 8
---

# Agentic Workflows

ztlctl is designed to be operated by AI agents as a first-class use case. Every command supports `--json` output for structured parsing, and the session/context system provides token-budgeted context windows.

## Session-Based Agent Workflow

Sessions are the primary organizational container for agentic work:

```bash
# Agent starts a focused research session
ztlctl agent session start "API design patterns" --json

# Agent creates notes as it discovers knowledge
ztlctl create note "REST vs GraphQL trade-offs" \
  --tags "architecture/api" --session LOG-0001 --json

# Agent logs its reasoning and costs
ztlctl agent session log "Analyzed 5 API frameworks" --cost 1200 --json
ztlctl agent session log "Key insight: GraphQL better for nested data" --pin --json

# Agent checks token budget
ztlctl agent session cost --report 50000 --json

# Agent requests context for continued work
ztlctl agent context --topic "api" --budget 4000 --json

# Agent closes session, triggering enrichment pipeline
ztlctl agent session close --summary "Mapped API paradigms" --json
```

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

ztlctl includes a Model Context Protocol (MCP) server for direct integration with AI clients like Claude Desktop:

```bash
ztlctl serve --transport stdio
```

See the [MCP Server](mcp.md) page for full details on available tools, resources, and prompts.

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
