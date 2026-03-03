---
title: MCP Server
nav_order: 10
---

# MCP Server

The MCP (Model Context Protocol) server exposes ztlctl's discovery-first tool surface to AI clients.

## Setup

```bash
# Install with MCP support
pip install ztlctl[mcp]

# Start the server
ztlctl serve --transport stdio
```

## Claude Desktop Integration

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "ztlctl": {
      "command": "ztlctl",
      "args": ["serve"]
    }
  }
}
```

## Discovery Pattern

The intended call sequence is:

1. `discover_tools` to narrow the surface by category
2. `describe_tool` to inspect a specific contract
3. `ztlctl://agent-reference` when the client needs a single onboarding payload

## Tool Categories

| Category | Tools |
|----------|-------|
| Discovery | `discover_tools`, `describe_tool`, `list_tags`, `list_source_providers` |
| Creation | `create_note`, `create_reference`, `create_task`, `create_log`, `garden_seed`, `ingest_source` |
| Lifecycle | `update_content`, `close_content`, `reweave` |
| Query | `search`, `get_document`, `get_related`, `agent_context`, `list_items`, `work_queue`, `topic_packet`, `draft_from_topic` |
| Analysis | `decision_support`, `vault_review` |
| Graph | `graph_themes`, `graph_rank`, `graph_path`, `graph_gaps`, `graph_bridges` |
| Session | `session_close`, `session_status` |

Notable additions for agent workflows:

- `ingest_source` normalizes text, files, and provider-backed URLs into notes or references
- `ingest_source` accepts a nested `source_bundle` contract for agent-fetched web and multimodal captures, while still supporting the older flat evidence fields
- ingested references persist source bundles under `sources/<reference-id>/` so later packets, drafts, and dossier exports can reuse the same evidence
- `list_source_providers` lets clients discover installed URL-ingestion providers
- `topic_packet` assembles topic-scoped learning, review, and decision bundles
- `draft_from_topic` turns a topic packet into a note, task, or decision draft without writing to the vault
- `create_note` accepts authored `body`, `key_points`, `aliases`, and `links`
- `create_reference` accepts `subtype` for `article`, `tool`, or `spec`
- `vault_review` returns a review-ready aggregate snapshot
- `session_status` lets clients reason about active-session state without inferring from errors

## Generated Client Assets

For project-local Claude and Codex setup, export generated workflow assets from the packaged templates:

```bash
ztlctl workflow export --client both
```

This writes a `.claude/` project bundle, a root `AGENTS.md`, and supporting files derived from the same portable workflow source. The exported guidance treats MCP as canonical when available and the CLI as the fallback contract.

## Available Resources

| Resource | Description |
|----------|-------------|
| `ztlctl://self/identity` | Agent identity document |
| `ztlctl://self/methodology` | Agent methodology document |
| `ztlctl://overview` | Vault statistics and structure |
| `ztlctl://work-queue` | Prioritized task list |
| `ztlctl://review/dashboard` | External review workbench snapshot |
| `ztlctl://garden/backlog` | Enrichment backlog signals from stale seeds and orphan notes |
| `ztlctl://decision-queue` | Recent decisions plus active work queue |
| `ztlctl://capture/spec` | Source-bundle contract for agent capture and ingest handoff |
| `ztlctl://topics` | Available topic directories |
| `ztlctl://context` | Full assembled context |
| `ztlctl://agent-reference` | Onboarding payload with tool guidance and workflow examples |

## Available Prompts

| Prompt | Description |
|--------|-------------|
| `research_session` | Start a structured research session |
| `knowledge_capture` | Guided knowledge capture workflow |
| `vault_orientation` | Orient to the current vault state |
| `decision_record` | Record an architectural decision |
| `topic_learn` | Gather and learn from a topic packet |
| `topic_review` | Review a topic for stale and weakly connected knowledge |
| `topic_decision` | Prepare a decision-ready topic packet and draft |
| `capture_web_source` | Turn a fetched web page into a source bundle for ingest |
| `capture_multimodal_source` | Turn extracted multimodal evidence into a source bundle for ingest |
