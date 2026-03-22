# ztlctl Plugin for Claude Code

Agentic research assistant for ztlctl knowledge vaults. Wraps the ztlctl MCP server with 10 deep skills, 5 slash commands, and 2 autonomous agents.

## Prerequisites

1. **Python 3.13+** with uv or pipx:
   ```bash
   # Option A: uv (recommended)
   uv tool install ztlctl
   # Option B: pipx
   pipx install ztlctl
   ```

2. **Initialize a vault:**
   ```bash
   mkdir my-vault && cd my-vault
   ztlctl init
   ```

3. **Verify the MCP server works:**
   ```bash
   echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{}}}' | uvx ztlctl serve
   ```
   You should see a JSON response with no errors.

## Installation

```bash
claude plugin install ztlctl
```

### Post-install verification

```bash
claude mcp list
```

Confirm `ztlctl` appears in the server list. If it does not, see Troubleshooting below.

## What you get

| Component | Count | Purpose |
|-----------|-------|---------|
| Skills | 10 | Multi-step workflow guides (orient, session, capture, etc.) |
| Commands | 5 | `/ztlctl:session`, `/ztlctl:capture`, `/ztlctl:review`, `/ztlctl:seed`, `/ztlctl:align` |
| Agents | 2 | Autonomous research and maintenance |
| Hooks | 1 | Vault gate (blocks tools when no vault found) |

## Quick start

Start Claude Code in your vault directory:

```bash
cd my-vault
claude
```

Then use slash commands:
- `/ztlctl:session "Topic"` -- start a structured research session
- `/ztlctl:capture` -- guided knowledge capture
- `/ztlctl:review` -- vault health review and triage
- `/ztlctl:seed "Quick idea"` -- zero-friction seed capture
- `/ztlctl:align "Should I use X?"` -- check decision against priorities

Or ask naturally: "research what I know about X" or "run vault maintenance" to trigger agents.

## Updating

```bash
claude plugin update ztlctl
```

Plugin versions are synchronized with ztlctl releases. Update both:
```bash
uv tool upgrade ztlctl && claude plugin update ztlctl
```

## Troubleshooting

**MCP server not showing in `claude mcp list`:**
This is a known issue. Restart Claude Code. If still missing, verify ztlctl is on PATH: `which ztlctl` or `uvx ztlctl --version`.

**Tools require approval on every call:**
Run from your vault directory (where `ztlctl.toml` exists). The vault gate hook checks for vault presence.

**Windows users:**
Ensure `uv` is on PATH (`winget install astral-sh.uv`). If `uvx` is not found by Claude Code, use the full path to uvx in your MCP config.

**Plugin loads but skills don't fire:**
Run `/reload-plugins` to refresh. For MCP config changes, restart Claude Code.
