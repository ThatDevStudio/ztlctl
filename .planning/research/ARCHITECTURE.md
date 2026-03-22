# Architecture Research: Claude Code Plugin + MCP Integration

**Domain:** Claude Code plugin wrapping an existing Python MCP server (v4.0 Agentic Skills milestone)
**Researched:** 2026-03-22
**Overall confidence:** HIGH — based on official Claude Code docs (code.claude.com/docs), direct inspection of the existing `plugin/` directory in this repo, and the live MCP server implementation.

---

## Current State Baseline

The ztlctl repo already has a working first-generation plugin at `plugin/`. Before designing v4.0, it is critical to understand what exists:

```
plugin/                                  ← Plugin root (relative to repo root)
├── .claude-plugin/
│   └── plugin.json                      ← Manifest: name=ztlctl, version=1.0.0
├── .mcp.json                            ← MCP server: stdio, command=ztlctl serve
├── commands/                            ← 4 legacy slash commands
│   ├── capture.md
│   ├── review.md
│   ├── seed.md
│   └── session.md
├── skills/                              ← 3 Agent Skills
│   ├── session-workflow/SKILL.md + refs
│   ├── vault-methodology/SKILL.md + refs
│   └── graph-intelligence/SKILL.md + refs
├── agents/                              ← 2 autonomous subagents
│   ├── knowledge-synthesizer.md
│   └── vault-analyst.md
├── hooks/
│   ├── hooks.json                       ← SessionStart hook
│   └── scripts/session-context.sh
└── README.md
```

The `marketplace.json` at the repo root registers this plugin via a relative-path source (`./plugin`). The `plugin.json` does **not** declare `skills/` — only `commands`, `agents`, and `hooks`, so skills are auto-discovered from the default `skills/` location.

The MCP server (`ztlctl serve`) runs as a stdio subprocess. It auto-discovers the vault from `ztlctl.toml` in the working directory or `$ZTLCTL_VAULT`. No explicit vault path is passed in `.mcp.json`.

---

## Integration Architecture

### How Claude Code Loads the Plugin

```
User runs: claude (in vault directory)
                │
                ▼
Claude Code reads .claude/settings.json or ~/.claude/settings.json
  └── enabledPlugins: { "ztlctl@ztlctl-plugins": true }
                │
                ▼
Plugin cache at ~/.claude/plugins/cache/ztlctl-plugins/ztlctl/1.0.0/
  ├── plugin.json          → registers name, commands, agents, hooks
  ├── .mcp.json            → starts MCP subprocess
  ├── skills/              → auto-discovered Agent Skills
  └── hooks/hooks.json     → registers SessionStart hook
                │
                ▼
MCP server subprocess: ztlctl serve (stdio)
  └── Vault auto-discovered from CWD (ztlctl.toml)
  └── 73+ tools exposed as mcp__ztlctl__<action_name>
```

### MCP Tool Naming

All ztlctl tools appear in Claude Code as `mcp__ztlctl__<action_name>`. Examples:

```
mcp__ztlctl__create_note
mcp__ztlctl__search
mcp__ztlctl__session_start
mcp__ztlctl__graph_themes
mcp__ztlctl__reweave
mcp__ztlctl__check_alignment      ← Polaris
mcp__ztlctl__context_assembly     ← v3.0 context layer
```

Hook matchers use this full pattern: `"matcher": "mcp__ztlctl__.*"`.

### MCP Server Configuration (.mcp.json)

The existing `.mcp.json` is minimal and correct:

```json
{
  "mcpServers": {
    "ztlctl": {
      "command": "ztlctl",
      "args": ["serve"],
      "env": {}
    }
  }
}
```

**Vault discovery relies entirely on CWD.** When Claude Code starts, the MCP subprocess inherits the working directory where `claude` was invoked. `ztlctl serve` calls `ZtlSettings.from_cli(vault_root=None)`, which walks upward from CWD to find `ztlctl.toml`. This is the correct pattern — no explicit path configuration needed.

**Alternative: explicit vault path via environment variable**

```json
{
  "mcpServers": {
    "ztlctl": {
      "command": "ztlctl",
      "args": ["serve"],
      "env": {
        "ZTLCTL_VAULT": "${CLAUDE_PROJECT_DIR}"
      }
    }
  }
}
```

`CLAUDE_PROJECT_DIR` is injected by Claude Code at plugin startup. Use this only if CWD-based discovery proves unreliable in testing.

### Transport Decision: stdio vs HTTP

**Use stdio (current choice).** Rationale:

| Factor | stdio | HTTP |
|--------|-------|------|
| Latency | Sub-millisecond (local pipe) | Network roundtrip overhead |
| Lifecycle | Managed by Claude Code | User must start/stop server |
| Security | Local process, no port exposure | Requires auth for safety |
| Plugin distribution | Zero setup — ztlctl binary is enough | User must run separate server process |
| Multiple clients | One server per Claude session | Could share across sessions |

The only reason to use HTTP is if multiple MCP clients need simultaneous access to a single ztlctl vault (e.g., Claude Desktop + Claude Code at the same time). For v4.0, stdio is correct.

---

## Directory Layout: Mono-Repo Structure

ztlctl uses a mono-repo model: the Python package and Claude Code plugin live in the same repository. This is the right choice for this project.

**Why mono-repo:**
- The plugin's `.mcp.json` invokes `ztlctl serve` — the plugin and server are tightly coupled
- Version synchronization is automatic (no cross-repo dependency management)
- CI can validate plugin and Python package together
- `git-subdir` source type in marketplace.json supports mono-repo distribution with sparse cloning

**Recommended structure for v4.0:**

```
ztlctl/                                  ← Repo root
├── src/ztlctl/                          ← Python package (unchanged)
│   └── mcp/                            ← FastMCP server (unchanged)
├── plugin/                              ← Claude Code plugin root
│   ├── .claude-plugin/
│   │   └── plugin.json                 ← Manifest (update for v4.0)
│   ├── .mcp.json                       ← MCP server config (minimal change)
│   ├── skills/                         ← Agent Skills (EXPAND in v4.0)
│   │   ├── session-workflow/           ← EXISTS — deepen
│   │   ├── vault-methodology/          ← EXISTS — deepen
│   │   ├── graph-intelligence/         ← EXISTS — deepen
│   │   ├── research-pipeline/          ← NEW: multi-step research workflow
│   │   ├── review-cycle/               ← NEW: vault review + contradiction check
│   │   ├── decision-support/           ← NEW: polaris + decision recording
│   │   ├── capture-workflow/           ← NEW: capture + reweave + link
│   │   └── media-ingestion/            ← NEW: transcription → annotated notes
│   ├── commands/                       ← Slash commands (expand or migrate to skills/)
│   │   ├── session.md                  ← EXISTS — refine
│   │   ├── capture.md                  ← EXISTS — refine
│   │   ├── review.md                   ← EXISTS — refine
│   │   ├── seed.md                     ← EXISTS — keep
│   │   └── research.md                 ← NEW
│   ├── agents/                         ← Autonomous subagents (expand)
│   │   ├── knowledge-synthesizer.md    ← EXISTS — update for v3.0 tools
│   │   ├── vault-analyst.md            ← EXISTS — update for v3.0 tools
│   │   ├── contradiction-resolver.md   ← NEW: uses contradiction detection
│   │   └── session-orchestrator.md     ← NEW: full session lifecycle
│   ├── hooks/
│   │   ├── hooks.json                  ← EXISTS — extend with new hooks
│   │   └── scripts/
│   │       ├── session-context.sh      ← EXISTS — update for v3.0 context
│   │       └── mcp-gate.sh             ← NEW: PreToolUse safety gate
│   └── README.md                       ← EXISTS — update
├── marketplace.json                    ← EXISTS at repo root — update version
└── .claude/
    └── settings.json                   ← Project-level plugin enablement (optional)
```

**Key invariant:** The `.claude-plugin/` directory contains only `plugin.json`. All other directories (`skills/`, `commands/`, `agents/`, `hooks/`) are at the plugin root (`plugin/`). This is a documented Claude Code requirement.

---

## How Skills Invoke MCP Tools

Agent Skills (SKILL.md) are **model-invoked, instruction-based** — they contain natural language guidance, not code. Claude reads the skill context and uses MCP tools directly.

```
Session-workflow SKILL.md:
  "Before starting, check for active sessions..."
  → Claude calls mcp__ztlctl__list_items (checking for open LOG entries)
  → Claude calls mcp__ztlctl__create_log
  → Claude calls mcp__ztlctl__work_queue
```

**Direct tool calls (no wrapper needed).** The tool names are already well-structured: `mcp__ztlctl__<action_name>` maps directly to the ActionRegistry action names. Skills should reference tools by their `mcp__ztlctl__` name explicitly so Claude does not need to guess.

**Pattern for skill tool references:**

```markdown
## Starting a Session

Call `mcp__ztlctl__create_log` with `title` set to the session topic.
After creation, call `mcp__ztlctl__work_queue` to surface pending tasks.
Call `mcp__ztlctl__context_assembly` to inject Polaris priorities as context.
```

**Why not wrapper functions:** Claude Code skills are not JavaScript/Python — they are markdown prompts. There is no layer to add wrapper functions in. The skill IS the wrapper: it encodes the workflow as instructions that Claude follows when invoking raw MCP tools.

---

## Hook Patterns for Tool Enhancement

### PreToolUse: Vault State Gate

Block MCP tool calls that require a vault to be initialized:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "mcp__ztlctl__.*",
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/hooks/scripts/mcp-gate.sh",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

`mcp-gate.sh` reads `tool_name` from stdin JSON and exits 2 with an error message if `ztlctl.toml` is not found in the working directory. This prevents confusing "vault not found" errors from the MCP server.

```bash
#!/usr/bin/env bash
# hooks/scripts/mcp-gate.sh
# Block ztlctl MCP tools if no vault is initialized in CWD

set -euo pipefail

TOOL_NAME=$(echo "${HOOK_INPUT:-{}}" | jq -r '.tool_name // empty' 2>/dev/null || true)

# Skip gate for vault-init level operations
if echo "${TOOL_NAME}" | grep -qE "^mcp__ztlctl__(list_tools|init)$"; then
  exit 0
fi

# Check for vault config file walking up from CWD
DIR="${PWD}"
while [ "${DIR}" != "/" ]; do
  if [ -f "${DIR}/ztlctl.toml" ]; then
    exit 0
  fi
  DIR="$(dirname "${DIR}")"
done

echo "No ztlctl vault found in ${PWD} or any parent directory. Run 'ztlctl init' to initialize a vault." >&2
exit 2
```

### PostToolUse: Session Context Refresh

After session creation, automatically inject updated context:

```json
{
  "PostToolUse": [
    {
      "matcher": "mcp__ztlctl__session_start|mcp__ztlctl__create_log",
      "hooks": [
        {
          "type": "command",
          "command": "${CLAUDE_PLUGIN_ROOT}/hooks/scripts/session-context.sh",
          "timeout": 10
        }
      ]
    }
  ]
}
```

### SessionStart: Vault Orientation (existing, enhance)

The existing `session-context.sh` calls `ztlctl --json agent brief` and `ztlctl --json query work-queue`. For v4.0, this should also pull from the MCP resource `ztlctl://polaris/priorities` to surface active goals.

Enhanced pattern:

```bash
# After existing brief + work-queue output:
POLARIS="$(ztlctl --json polaris list 2>/dev/null || true)"
if [ -n "${POLARIS}" ]; then
  echo "--- Polaris Priorities ---"
  echo "${POLARIS}"
fi
```

### Hook Input Format for MCP PreToolUse

The hook script receives JSON on stdin (also available via `$HOOK_INPUT`):

```json
{
  "session_id": "abc123",
  "hook_event_name": "PreToolUse",
  "tool_name": "mcp__ztlctl__create_note",
  "tool_input": {
    "title": "Note Title",
    "body": "Content...",
    "tags": ["domain/scope"]
  }
}
```

Use `jq` to extract fields: `jq -r '.tool_name'`, `jq -r '.tool_input.title'`.

### PreToolUse Output for Denying

```bash
jq -n '{
  hookSpecificOutput: {
    hookEventName: "PreToolUse",
    permissionDecision: "deny",
    permissionDecisionReason: "No vault initialized. Run ztlctl init first."
  }
}'
```

Exit 0 with this JSON output to cleanly deny with a user-visible reason.

---

## MCP Server Discovery Pattern

The MCP server discovers the vault via CWD. There is no auto-detection magic — the contract is:

1. User `cd` into their vault directory (contains `ztlctl.toml`)
2. User runs `claude` from that directory
3. Claude Code starts `ztlctl serve` subprocess, inheriting CWD
4. `ztlctl serve` → `create_server(vault_root=None)` → `ZtlSettings.from_cli(vault_root=None)` → walks up from CWD to find `ztlctl.toml`

**What to document for users:** Always run `claude` from your vault directory (where `ztlctl.toml` lives), not from a parent directory.

**Environment variable override:** `ZTLCTL_VAULT=/path/to/vault` can be set in the shell before launching Claude Code. This is the escape hatch for cases where CWD-based discovery is inconvenient.

**Verifying discovery works:** The `SessionStart` hook script already tests this by calling `ztlctl --json agent brief` — if it returns empty, the vault was not found. This serves as a natural health check.

### Multiple Vault Scenario

A user with multiple vaults launches a separate `claude` session per vault (each from the respective vault directory). Each session gets its own `ztlctl serve` subprocess with the correct vault. No multiplexing is needed.

---

## plugin.json: Required Updates for v4.0

The current `plugin.json` does not declare `skills/` (relies on auto-discovery) and does not explicitly list MCP servers (relies on `.mcp.json`). For v4.0, both should be explicit:

```json
{
  "name": "ztlctl",
  "version": "4.0.0",
  "description": "Deep skills and agentic workflows for ztlctl knowledge vaults",
  "author": {
    "name": "ThatDev Studio",
    "url": "https://github.com/ThatDevStudio/ztlctl"
  },
  "repository": "https://github.com/ThatDevStudio/ztlctl",
  "homepage": "https://thatdevstudio.github.io/ztlctl/",
  "license": "MIT",
  "keywords": ["zettelkasten", "knowledge-management", "research", "second-brain", "agentic"],
  "commands": "./commands",
  "agents": "./agents",
  "hooks": "./hooks/hooks.json",
  "mcpServers": "./.mcp.json"
}
```

Notes:
- `skills/` is omitted because it is auto-discovered from the default location
- `mcpServers: "./.mcp.json"` makes the MCP config explicit rather than relying on file presence
- Version must be bumped to trigger cache invalidation for existing installations

---

## marketplace.json: Source Type for Mono-Repo

The current `marketplace.json` uses a relative path source:

```json
{ "source": "./plugin" }
```

This works for local testing (`/plugin marketplace add ./ztlctl`) but does NOT work when users add the marketplace via a remote URL. For reliable distribution, use `git-subdir`:

```json
{
  "$schema": "https://anthropic.com/claude-code/marketplace.schema.json",
  "name": "ztlctl-plugins",
  "description": "Agentic skills and workflows for ztlctl knowledge vaults",
  "owner": {
    "name": "ThatDev Studio",
    "email": "hello@thatdevstudio.com"
  },
  "plugins": [
    {
      "name": "ztlctl",
      "description": "Deep skills and agentic workflows for ztlctl knowledge vaults",
      "version": "4.0.0",
      "category": "productivity",
      "source": {
        "source": "git-subdir",
        "url": "ThatDevStudio/ztlctl",
        "path": "plugin",
        "ref": "develop"
      },
      "homepage": "https://thatdevstudio.github.io/ztlctl/",
      "repository": "https://github.com/ThatDevStudio/ztlctl",
      "license": "MIT",
      "tags": ["zettelkasten", "notes", "knowledge-graph", "research", "mcp"]
    }
  ]
}
```

`git-subdir` performs a sparse clone of only the `plugin/` subdirectory — minimal bandwidth for users even as the Python package grows.

**Installation command for users:**

```bash
/plugin marketplace add ThatDevStudio/ztlctl
/plugin install ztlctl@ztlctl-plugins
```

---

## Build and Distribution: Python + Plugin Boundary

There is no JavaScript or TypeScript in this plugin. The architecture is:

```
Python package (ztlctl)           Claude Code plugin (plugin/)
─────────────────────────         ──────────────────────────────
PyPI distribution                 git-subdir from GitHub
ztlctl binary in PATH             Skills / commands / hooks (markdown + shell)
ztlctl serve = MCP server         .mcp.json invokes ztlctl serve
```

**The plugin has zero build step.** It is pure markdown files, JSON config, and bash scripts. No npm, no bundling, no compilation.

**The dependency chain:**
1. User installs ztlctl: `pipx install ztlctl[mcp]` or `uv tool install ztlctl[mcp]`
2. User installs plugin: `/plugin install ztlctl@ztlctl-plugins`
3. Plugin's `.mcp.json` runs `ztlctl serve` — the binary from step 1
4. Plugin's hook scripts run `ztlctl --json ...` — same binary

**The `[mcp]` extra is mandatory.** Without it, `ztlctl serve` exits with an error. The `README.md` must state this prerequisite clearly.

**Hook script dependencies:** The existing `session-context.sh` uses `jq`. This is a system dependency. Add a check: if `jq` is not available, fall back to raw JSON output rather than failing silently.

---

## Server Lifecycle in the Plugin

Claude Code manages the MCP server process lifecycle entirely:

1. **Startup:** When a session begins, Claude Code reads `.mcp.json`, spawns `ztlctl serve` as a subprocess, and performs MCP capability negotiation
2. **Running:** The subprocess stays alive for the entire Claude Code session, communicating via stdin/stdout JSON-RPC
3. **Shutdown:** When the Claude Code session ends, Claude Code terminates the subprocess; `ztlctl serve` runs `vault.close(wait_for_events=True)` in its `finally` block, draining the WAL before exit

**ztlctl's WAL drain is already correct** for this lifecycle: the `finally: ctx.vault.close(wait_for_events=True)` in `serve.py` ensures no events are dropped on subprocess termination.

**No health check or restart needed at the plugin level.** If the MCP server crashes mid-session, Claude Code will report tool failures. The user would need to `/reload-plugins` or restart the session.

**Plugin data directory is not needed.** The ztlctl vault (SQLite + markdown files) lives in the user's vault directory, not in `${CLAUDE_PLUGIN_DATA}`. The plugin itself has no persistent state to store.

---

## Component Interaction Diagram

```
User vault directory (CWD)
  └── ztlctl.toml
  └── notes/
  └── vault.db

                                    Claude Code session
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  SessionStart hook                                              │
│    └── session-context.sh → ztlctl --json agent brief          │
│    └── Injects vault orientation into conversation context      │
│                                                                 │
│  Agent Skills (model-invoked)                                   │
│    └── session-workflow   → guides session lifecycle            │
│    └── vault-methodology  → guides content type choices         │
│    └── graph-intelligence → guides graph analysis               │
│    └── research-pipeline  → NEW: multi-step research            │
│    └── review-cycle       → NEW: contradiction + gaps           │
│    └── decision-support   → NEW: polaris + decision recording   │
│                                                                 │
│  Slash Commands (user-invoked)                                  │
│    └── /ztlctl:session   → starts structured session           │
│    └── /ztlctl:capture   → guided knowledge capture            │
│    └── /ztlctl:review    → vault health review                 │
│    └── /ztlctl:seed      → quick idea capture                  │
│    └── /ztlctl:research  → NEW: full research pipeline         │
│                                                                 │
│  Autonomous Agents (Claude-invoked or user-triggered)           │
│    └── knowledge-synthesizer → cross-note synthesis            │
│    └── vault-analyst         → structural analysis             │
│    └── contradiction-resolver → NEW: resolve conflicts         │
│    └── session-orchestrator  → NEW: full session autonomous    │
│                                                                 │
│  PreToolUse hook                                                │
│    └── mcp-gate.sh → verifies vault exists before MCP calls    │
│                                                                 │
│  MCP Server subprocess (stdio)                                  │
│    └── ztlctl serve                                            │
│    └── 73+ tools as mcp__ztlctl__<action_name>                 │
│    └── Resources: ztlctl://context, ztlctl://polaris/...       │
│    └── Vault auto-discovered from CWD                          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Patterns to Follow

### Pattern 1: Skill Workflow Encoding

Each skill encodes a multi-step workflow with explicit MCP tool names, decision points, and failure modes.

```markdown
---
name: research-pipeline
description: >
  Use when starting a deep research session. Encodes: orient → session start →
  polaris alignment → capture pipeline → synthesis → close.
version: 4.0.0
---

## Research Pipeline Workflow

### 1. Orient (before starting)
Call `mcp__ztlctl__context_assembly` to get vault state snapshot.
Call `mcp__ztlctl__check_alignment` to surface polaris priorities.

### 2. Start Session
Call `mcp__ztlctl__create_log` with title = research topic.
[continue with explicit steps...]
```

### Pattern 2: Commands as Entry Points

Commands (`/ztlctl:session`) are thin entry points that invoke the appropriate skill workflow and surface key information. They do not duplicate skill content — they orient the user and activate skill context.

### Pattern 3: Agents for Autonomous Loops

Agents declare their allowed MCP tools explicitly in frontmatter. Only the tools the agent needs. This constrains the autonomous loop and prevents unintended side effects.

```markdown
---
name: session-orchestrator
tools: ["mcp__ztlctl__create_log", "mcp__ztlctl__context_assembly",
        "mcp__ztlctl__check_alignment", "mcp__ztlctl__work_queue",
        "mcp__ztlctl__session_close"]
maxTurns: 10
---
```

### Pattern 4: Hook Scripts via CLAUDE_PLUGIN_ROOT

All hook script references must use `${CLAUDE_PLUGIN_ROOT}` — absolute paths and relative paths both fail after plugin installation because the plugin is copied to a cache location.

```json
{ "command": "${CLAUDE_PLUGIN_ROOT}/hooks/scripts/session-context.sh" }
```

---

## Anti-Patterns to Avoid

### Anti-Pattern 1: Skills That Shell Out to ztlctl CLI

```markdown
<!-- BAD: Using the CLI instead of MCP tools -->
Run `ztlctl query search "machine learning"` to find notes.
```

```markdown
<!-- GOOD: Using MCP tools exclusively -->
Call `mcp__ztlctl__search` with query "machine learning".
```

CLI invocations break when `ztlctl` is not in PATH, bypass MCP's structured error recovery, and produce Rich-formatted output that is harder to parse. MCP tools return structured JSON and include error recovery hints.

### Anti-Pattern 2: HTTP Transport for Single-User Plugin Distribution

HTTP transport requires the user to start `ztlctl serve --transport streamable-http` separately before launching Claude Code, adds latency, exposes a local port, and provides no authentication. Stdio is always better for this use case.

### Anti-Pattern 3: Hardcoded Vault Paths in .mcp.json

```json
// BAD: hardcoded path breaks for other users
{ "command": "ztlctl", "args": ["serve", "--vault", "/home/alice/notes"] }
```

```json
// GOOD: CWD-based discovery works for any vault
{ "command": "ztlctl", "args": ["serve"] }
```

### Anti-Pattern 4: Putting Commands/Skills Inside .claude-plugin/

All plugin components (`commands/`, `skills/`, `agents/`, `hooks/`) must be at the **plugin root**, not inside `.claude-plugin/`. Only `plugin.json` belongs in `.claude-plugin/`. A common mistake is nesting everything inside the metadata directory.

### Anti-Pattern 5: Separate Repo for Plugin

A separate repo for the plugin creates version drift: when the Python package adds new actions, the plugin skills referring to old action names silently break. The mono-repo keeps them synchronized. Use `git-subdir` source type to distribute just the `plugin/` directory without requiring users to clone the entire Python package.

---

## Scalability Considerations

| Concern | Current (v4.0) | Future |
|---------|---------------|--------|
| Number of MCP tools | 73+ auto-generated | ActionRegistry scales linearly — no plugin changes needed as new actions are added |
| Skill breadth | 8 skills covering key workflows | Skills are additive — add new `skills/<name>/SKILL.md` without modifying existing skills |
| Agent autonomy | Constrained by explicit `tools` list | Expand tools list or add new agents as trust increases |
| Hook complexity | 2 hooks (SessionStart, PreToolUse) | Add PostToolUse hooks for audit/telemetry without breaking existing hooks |
| Multi-vault users | One Claude session per vault (CWD-based) | Could add vault switcher command if demand emerges |

---

## Sources

- [Claude Code Plugins reference](https://code.claude.com/docs/en/plugins-reference) — plugin manifest schema, directory structure, CLAUDE_PLUGIN_ROOT, CLAUDE_PLUGIN_DATA (HIGH confidence — official docs)
- [Claude Code Plugins creation guide](https://code.claude.com/docs/en/plugins) — plugin structure, .claude-plugin/ layout, .mcp.json location (HIGH confidence — official docs)
- [Claude Code Plugin marketplaces](https://code.claude.com/docs/en/plugin-marketplaces) — marketplace.json schema, git-subdir source type, strict mode (HIGH confidence — official docs)
- [Claude Code Hooks reference](https://code.claude.com/docs/en/hooks) — PreToolUse/PostToolUse patterns, MCP tool matching (mcp__server__tool naming), hook output format, exit code behavior (HIGH confidence — official docs, fetched directly)
- [Claude Code MCP](https://code.claude.com/docs/en/mcp) — .mcp.json format, stdio vs HTTP transports (HIGH confidence — official docs)
- Existing plugin/ directory in this repo — `find plugin -type f` inspection (HIGH confidence — ground truth)
- `src/ztlctl/mcp/server.py` — vault discovery via CWD, `create_server()` signature (HIGH confidence — source code)
- `src/ztlctl/commands/serve.py` — stdio/HTTP transport options, `vault.close()` lifecycle (HIGH confidence — source code)
