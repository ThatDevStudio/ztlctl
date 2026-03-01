# ztlctl — Claude Code Plugin

Agentic research assistant for [ztlctl](https://github.com/ThatDevStudio/ztlctl) knowledge vaults. Gives Claude the methodology, workflows, and guardrails to be a competent research partner.

## What This Plugin Provides

| Component | Purpose |
|---|---|
| **3 Skills** | Zettelkasten methodology, session workflows, graph intelligence |
| **4 Commands** | `/ztlctl:session`, `/ztlctl:capture`, `/ztlctl:review`, `/ztlctl:seed` |
| **2 Agents** | Knowledge synthesizer, vault analyst |
| **1 Hook** | SessionStart context injection |
| **MCP Server** | 21 tools via `ztlctl serve` |

## Prerequisites

1. **Install ztlctl**:
   ```bash
   pipx install ztlctl
   # or
   uv tool install ztlctl
   ```

2. **Initialize a vault**:
   ```bash
   mkdir my-vault && cd my-vault
   ztlctl init
   ```

3. **Enable the plugin** in Claude Code settings or via the plugin browser.

## How It Works

The plugin connects two layers:

- **MCP Server** (`ztlctl serve`) — provides 21 tools for vault operations (create, query, search, graph analysis, session management)
- **Plugin Components** — skills teach Claude *how* to think about knowledge management; commands provide structured entry points; agents handle complex autonomous tasks; hooks inject context automatically

The MCP server auto-discovers the vault from `ztlctl.toml` in the working directory or `$ZTLCTL_VAULT` environment variable.

## Quick Start

After installation, start a Claude Code session in your vault directory:

```bash
cd my-vault
claude
```

The SessionStart hook automatically injects vault context. Then:

- `/ztlctl:session "Topic"` — start a structured research session
- `/ztlctl:capture` — guided knowledge capture with duplicate checking
- `/ztlctl:review` — review vault state, connections, and gaps
- `/ztlctl:seed "Quick idea"` — capture a seed note instantly

Ask Claude to "analyze knowledge gaps" or "synthesize connections about X" to trigger the autonomous agents.

## Plugin Structure

```
plugin/
├── .claude-plugin/plugin.json    # Plugin manifest
├── .mcp.json                     # MCP server config
├── commands/                     # Slash commands
├── skills/                       # Domain knowledge
│   ├── vault-methodology/        # Content types, lifecycle, linking
│   ├── session-workflow/         # Research session patterns
│   └── graph-intelligence/       # Graph analysis guidance
├── agents/                       # Autonomous subagents
└── hooks/                        # Event-driven automation
```
