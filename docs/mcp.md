---
title: MCP Server
nav_order: 10
---

# MCP Server

The MCP (Model Context Protocol) server exposes ztlctl's full functionality to AI clients.

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

## Available Tools

ztlctl currently exposes **25 MCP tools**:

| Category | Tools |
|----------|-------|
| Discovery | `discover_tools`, `list_tags` |
| Creation | `create_note`, `create_reference`, `create_task`, `create_log`, `garden_seed` |
| Lifecycle | `update_content`, `close_content`, `reweave` |
| Query | `search`, `get_document`, `get_related`, `agent_context`, `list_items`, `work_queue` |
| Analysis | `decision_support`, `vault_review` |
| Graph | `graph_themes`, `graph_rank`, `graph_path`, `graph_gaps`, `graph_bridges` |
| Session | `session_close`, `session_status` |

Notable workflow-specific additions:

- `create_note` accepts authored `body`, `key_points`, `aliases`, and `links`
- `create_reference` accepts `subtype` for `article`, `tool`, or `spec`
- `vault_review` returns a review-ready aggregate snapshot
- `session_status` lets clients reason about active-session state without inferring from errors

## Generated Client Assets

For project-local Claude and Codex setup, export generated workflow assets from the packaged templates:

```bash
ztlctl workflow export --client both
```

This writes a `.claude/` project bundle, a root `AGENTS.md`, and supporting files derived from the same portable workflow source.

## Available Resources

| Resource | Description |
|----------|-------------|
| `self/identity` | Agent identity document |
| `self/methodology` | Agent methodology document |
| `vault/overview` | Vault statistics and structure |
| `vault/work-queue` | Prioritized task list |
| `vault/topics` | Available topic directories |
| `vault/context` | Full assembled context |

## Available Prompts

| Prompt | Description |
|--------|-------------|
| `research_session` | Start a structured research session |
| `knowledge_capture` | Guided knowledge capture workflow |
| `vault_orientation` | Orient to the current vault state |
| `decision_record` | Record an architectural decision |
