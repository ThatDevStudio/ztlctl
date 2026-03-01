# ztlctl — Claude Code Reference Bundle

Reference assets for Claude Code integration with [ztlctl](https://github.com/ThatDevStudio/ztlctl) knowledge vaults.

The supported path is to generate project-local assets from the packaged workflow source:

```bash
ztlctl workflow export --client claude
```

This directory remains as a checked-in reference bundle, but the package source of truth now lives under `src/ztlctl/templates/agent_workflow`.

## What This Plugin Provides

| Component | Purpose |
|---|---|
| **3 Skills** | Zettelkasten methodology, session workflows, graph intelligence |
| **4 Commands** | `/ztlctl:session`, `/ztlctl:capture`, `/ztlctl:review`, `/ztlctl:seed` |
| **2 Agents** | Knowledge synthesizer, vault analyst |
| **1 Hook** | SessionStart context injection |
| **MCP Server** | 25 tools via `ztlctl serve` |

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

3. **Export the Claude bundle** with `ztlctl workflow export --client claude`.

## How It Works

The Claude bundle connects two layers:

- **MCP Server** (`ztlctl serve`) — provides 25 tools for vault operations and workflow state
- **Project Assets** — skills teach Claude *how* to think about knowledge management; commands provide structured entry points; agents handle complex autonomous tasks; hooks inject context automatically

The MCP server auto-discovers the vault from `ztlctl.toml` in the working directory or `$ZTLCTL_VAULT` environment variable.

## Quick Start

After installation, start a Claude Code session in your vault directory:

```bash
cd my-vault
claude
```

The SessionStart hook automatically injects compact vault context. Then:

- `/ztlctl:session "Topic"` — start a structured research session
- `/ztlctl:capture` — guided knowledge capture with duplicate checking
- `/ztlctl:review` — review vault state, connections, and gaps
- `/ztlctl:seed "Quick idea"` — capture a seed note instantly

Ask Claude to "analyze knowledge gaps" or "synthesize connections about X" to trigger the autonomous agents.

## Bundle Structure

```
.claude/
├── settings.json                 # Claude hooks config
├── commands/                     # Slash commands
├── skills/                       # Domain knowledge
└── agents/                       # Autonomous subagents
.mcp.json                         # MCP server config
```
