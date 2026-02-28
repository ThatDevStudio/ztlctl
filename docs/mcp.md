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

| Tool | Description |
|------|-------------|
| `create_note` | Create a note with title, tags, topic |
| `create_reference` | Create a reference with URL |
| `create_task` | Create a task with priority/impact/effort |
| `create_log` | Start a new session |
| `update_content` | Update content metadata |
| `close_content` | Archive or close content |
| `reweave` | Run link discovery |
| `search` | Full-text search with ranking |
| `get_document` | Retrieve content by ID |
| `get_related` | Graph-based related content |
| `agent_context` | Token-budgeted context payload |
| `session_close` | Close session with enrichment |

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
