# Technology Stack: v4.0 Agentic Skills — Claude Code Plugin

**Project:** ztlctl Claude Code Plugin
**Researched:** 2026-03-22
**Confidence:** HIGH — all findings verified from live installed plugin source code

> This document covers the Claude Code plugin ecosystem exclusively. All existing ztlctl stack
> (Python 3.13, uv, Click, Pydantic, FastMCP, pluggy) is unchanged and not re-researched.
> The plugin itself is a filesystem artifact — no new Python packages are required for the
> plugin directory structure. The .mcp.json integration uses the already-running `ztlctl serve`.

---

## Existing Capabilities Not Re-Researched

| Capability | Status |
|------------|--------|
| `ztlctl serve` (stdio + streamable-http + sse) | Shipping in v3.x; FastMCP via `mcp` package |
| 73+ MCP tools auto-generated from ActionRegistry | In place |
| Python 3.13, uv, Click, Pydantic, SQLAlchemy Core | Established, unchanged |
| pluggy event bus, EntryPoint plugin system | Established, unchanged |

---

## Plugin Filesystem Structure

**Verified from:** `plugins/example-plugin/`, `plugins/hookify/`, `plugins/plugin-dev/`,
`external_plugins/greptile/`, and the Vercel plugin (cached at version `3fe23669ec5a`).

```
ztlctl/
├── .claude-plugin/
│   └── plugin.json          # Plugin manifest (REQUIRED — must be at this exact path)
├── .mcp.json                 # MCP server config connecting Claude to ztlctl serve
├── commands/                 # Slash commands (user-invoked via /command-name)
│   └── session-start.md
├── agents/                   # Subagent definitions (Claude-spawned specialized agents)
│   └── vault-curator.md
├── skills/                   # Skill directories (model-invoked contextual guidance)
│   ├── session-lifecycle/
│   │   ├── SKILL.md          # Trigger description + workflow instructions (REQUIRED)
│   │   └── references/       # Optional supplementary docs loaded on demand
│   │       └── session-patterns.md
│   ├── capture-workflow/
│   │   └── SKILL.md
│   └── research-pipeline/
│       └── SKILL.md
├── hooks/
│   └── hooks.json            # Hook event configuration
└── README.md
```

**Key discovery:** The `skills/<name>/SKILL.md` layout is the current preferred format.
The legacy `commands/*.md` flat layout is still supported but not recommended for new plugins.
Both are loaded identically by Claude Code — only directory organization differs.

---

## plugin.json Manifest

**File location:** `.claude-plugin/plugin.json` (REQUIRED — not `.claude/`, not root)

### Field Reference (verified from manifest-reference.md)

```json
{
  "name": "ztlctl",
  "version": "1.0.0",
  "description": "Zettelkasten knowledge management for Claude Code — skills for session lifecycle, capture workflows, research pipelines, review cycles, and decision support wrapping ztlctl's 73+ MCP tools.",
  "author": {
    "name": "ThatDevStudio",
    "email": "support@thatdev.studio",
    "url": "https://github.com/ThatDevStudio/ztlctl"
  },
  "homepage": "https://ztlctl.thatdev.studio/docs",
  "repository": "https://github.com/ThatDevStudio/ztlctl",
  "license": "MIT",
  "keywords": [
    "zettelkasten",
    "knowledge-management",
    "second-brain",
    "notes",
    "mcp",
    "agentic",
    "session",
    "research"
  ]
}
```

**Required fields:** `name` only. Everything else is optional but recommended for marketplace.

**Name rules:**
- kebab-case, lowercase letters/numbers/hyphens only
- Must match: `/^[a-z][a-z0-9]*(-[a-z0-9]+)*$/`
- Unique across installed plugins

**Component path fields** (all optional — Claude Code uses conventional defaults):

| Field | Default | Override |
|-------|---------|---------|
| `commands` | `./commands/` | String or array of paths |
| `agents` | `./agents/` | String or array of paths |
| `skills` | `./skills/` | String (Vercel uses `"skills": "skills"`) |
| `hooks` | `./hooks/hooks.json` | Path string or inline object |
| `mcpServers` | `./.mcp.json` | Path string or inline object |

**Note on `skills` field:** Observed in Vercel plugin's `.cursor-plugin/plugin.json` as
`"skills": "skills"`. The Claude Code plugin manifest uses `.claude-plugin/plugin.json`
but the `skills` path field follows the same convention.

---

## SKILL.md Format

**Verified from:** example-plugin skills, skill-creator SKILL.md, hookify writing-rules SKILL.md,
Vercel observability SKILL.md (most comprehensive real-world example).

### Minimal SKILL.md (model-invoked)

```markdown
---
name: session-lifecycle
description: This skill should be used when the user wants to "start a session", "begin work", "open a session", "end my session", "close session", discusses session management in ztlctl, or needs to orchestrate a multi-step zettelkasten workflow. Encodes the full session start → capture → close pipeline using ztlctl MCP tools.
version: 1.0.0
---

# Session Lifecycle Skill

[Skill body — instructions for Claude on how to execute this workflow]
```

### Full SKILL.md with All Supported Frontmatter

```markdown
---
name: session-lifecycle
description: [TRIGGER DESCRIPTION — the most important field]
version: 1.0.0
license: MIT
# For user-invoked command layout only (skills/<name>/SKILL.md used as a command):
argument-hint: <vault-path> [--topic <topic>]
allowed-tools: [mcp__plugin_ztlctl_ztlctl__session_start, mcp__plugin_ztlctl_ztlctl__context_assemble]
model: inherit
---
```

### Frontmatter Fields (verified)

| Field | Required | Type | Notes |
|-------|----------|------|-------|
| `name` | YES | string | Skill identifier; matches directory name by convention |
| `description` | YES | string | PRIMARY TRIGGER MECHANISM — describes when Claude should invoke |
| `version` | no | string | Semantic version (e.g., `1.0.0`) |
| `license` | no | string | License identifier |
| `argument-hint` | no | string | Shown in `/help`; only for user-invoked command layout |
| `allowed-tools` | no | array | Pre-approved tools — reduces permission prompts |
| `model` | no | string | Override model (`"haiku"`, `"sonnet"`, `"opus"`, `"inherit"`) |

**Advanced Vercel-style metadata** (observed in Vercel observability skill — HIGH confidence
these fields are real as they're in deployed plugin code, but undocumented in Anthropic's
official example plugins):

```yaml
metadata:
  priority: 6                    # Ordering hint for skill selection
  docs:
    - "https://example.com/docs" # Official docs Claude should consult
  pathPatterns:                  # File path patterns that trigger skill injection
    - 'instrumentation.ts'
  bashPatterns:                  # Bash command patterns that trigger injection
    - '\bvercel\s+logs?\b'
  promptSignals:                 # Prompt text patterns for triggering
    phrases:
      - "add logging"
    allOf:
      - [add, logging]
    anyOf:
      - "monitoring"
    minScore: 6
validate:                        # Validation rules checked against open files
  - pattern: "export.*function"
    message: "Wrap in try/catch for production debugging"
    severity: warn
    skipIfFileContains: "console\\.error"
retrieval:
  aliases:
    - monitoring
  intents:
    - add monitoring
  entities:
    - Web Analytics
chainTo:                         # Skill chaining — load another skill when pattern matches
  - pattern: 'console\.log\s*\('
    targetSkill: another-skill
    message: "Console.log detected — loading guidance."
```

**Confidence on advanced fields:** MEDIUM — present in live Vercel plugin source, injected
into hook context at runtime, clearly functional. Not documented in official example-plugin
or plugin-dev reference. Use the `description` field as the primary trigger; treat advanced
fields as progressive enhancement.

### Three-Level Progressive Disclosure (verified from skill-creator)

```
Level 1: SKILL.md frontmatter (name + description)
         Always loaded into context (~100 words)
         Purpose: trigger detection

Level 2: SKILL.md body
         Loaded when skill activates (<500 lines recommended)
         Purpose: workflow instructions for Claude

Level 3: Bundled resources in subdirectories
         Loaded on demand by skill body instructions
         Purpose: reference docs, scripts, examples
```

**Directory structure for complex skills:**
```
skills/session-lifecycle/
├── SKILL.md                    # Primary — always loaded
├── references/
│   ├── workflow-patterns.md    # Read when user asks about session patterns
│   └── mcp-tools-reference.md  # Read when composing tool sequences
├── examples/
│   └── research-session.md     # Example session transcript
└── scripts/
    └── validate-vault.sh       # Helper script (executes without loading into context)
```

### Description Field Best Practices (verified from skill-creator)

The description is the trigger mechanism. Claude tends to "undertrigger" — err on the side
of pushy descriptions:

```yaml
# WEAK — undertriggered
description: Session management for ztlctl vaults.

# STRONG — verified pattern from skill-creator guidance
description: This skill should be used when the user wants to "start a session", "begin work",
  mentions "zettelkasten", "vault", "capture notes", "research session", or discusses any
  ztlctl workflow involving MCP tools. Make sure to use this skill whenever session lifecycle
  or vault operations are mentioned, even if the user doesn't say "session" explicitly.
```

Include:
- Exact trigger phrases in quotes
- Keywords indicating relevance
- Topic areas covered
- Anti-narrowing language ("even if...")

---

## Commands (Slash Commands)

**Verified from:** example-plugin, hookify commands, plugin-dev examples.

### Format

```markdown
---
description: Start a ztlctl knowledge session for the current project
argument-hint: [--topic <topic>] [--vault <path>]
allowed-tools: [mcp__plugin_ztlctl_ztlctl__session_start, mcp__plugin_ztlctl_ztlctl__context_assemble, mcp__plugin_ztlctl_ztlctl__polaris_check_alignment]
model: sonnet
---

# Start Knowledge Session

Invoked as: /ztlctl-session-start

## Instructions

1. Check if vault is initialized (use ztlctl_vault_status MCP tool)
2. Start a session (ztlctl_session_start)
3. Assemble context for the current project (ztlctl_context_assemble)
4. Check alignment with Polaris priorities (ztlctl_polaris_check_alignment)
5. Report session state and recommended next actions

Arguments: $ARGUMENTS
```

### Command Frontmatter

| Field | Required | Notes |
|-------|----------|-------|
| `description` | YES | Shown in `/help` |
| `argument-hint` | no | Usage hint displayed to user |
| `allowed-tools` | no | Pre-approved tools list |
| `model` | no | Model override |

**Commands vs skills:** Commands are user-invoked via `/command-name`. Skills are
model-invoked based on context. For ztlctl, the primary interface is skills (automatic
activation). Commands provide explicit invocation for power users.

---

## Agents

**Verified from:** hookify agents/, Vercel agents/, plugin-dev agent-development SKILL.md.

### Format

```markdown
---
name: vault-curator
description: Use this agent when analyzing vault health, running integrity checks, finding
  orphaned notes, or curating the knowledge graph. Examples: <example>Context: User wants
  to clean up vault\nuser: "analyze my vault health"\nassistant: "I'll spawn the vault
  curator agent to analyze structure and health metrics"</example>
model: inherit
color: blue
tools: ["mcp__plugin_ztlctl_ztlctl__check_integrity", "mcp__plugin_ztlctl_ztlctl__graph_gaps", "mcp__plugin_ztlctl_ztlctl__list_items"]
---

You are a zettelkasten vault curator specializing in knowledge graph health and maintenance.

[System prompt defining agent behavior, responsibilities, analysis process, output format]
```

### Agent Frontmatter

| Field | Required | Notes |
|-------|----------|-------|
| `name` | YES | Agent identifier |
| `description` | YES | When to spawn, with examples |
| `model` | no | `"inherit"`, `"haiku"`, `"sonnet"`, `"opus"` |
| `color` | no | `"blue"`, `"yellow"`, `"green"`, `"red"` — visual distinction |
| `tools` | no | Array of allowed tool names |

**Description format for agents** (verified from hookify conversation-analyzer.md):

```yaml
description: Use this agent when [condition]. Examples: <example>Context: [context]\nuser: "[user message]"\nassistant: "[how Claude responds]"\n<commentary>[why agent is used]</commentary></example>
```

Agents are spawned by Claude (not by users). They receive an isolated context and operate
on a focused task. The `description` field determines when the parent Claude spawns the agent.

---

## Hooks System

**Verified from:** hookify hooks.json + Python implementations, plugin-dev hook-development SKILL.md.

### hooks.json Structure (plugin format)

The plugin hook file uses a **wrapper format** — hooks events are nested under a `"hooks"` key:

```json
{
  "description": "ztlctl vault awareness hooks",
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 ${CLAUDE_PLUGIN_ROOT}/hooks/session_start.py",
            "timeout": 10
          }
        ]
      }
    ],
    "PreToolUse": [
      {
        "matcher": "mcp__plugin_ztlctl_ztlctl__*",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ${CLAUDE_PLUGIN_ROOT}/hooks/pretooluse.py",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

**CRITICAL:** Plugin `hooks.json` uses `{"hooks": {...}}` wrapper. User `.claude/settings.json`
hooks use the event names directly at top level. These are different formats — do NOT confuse them.

### Hook Events (all verified)

| Event | When | Primary Use for ztlctl |
|-------|------|----------------------|
| `PreToolUse` | Before any tool executes | Validate MCP tool calls; add vault context |
| `PostToolUse` | After tool executes | React to tool results; update session state |
| `UserPromptSubmit` | When user submits prompt | Detect ztlctl intent; inject vault context |
| `Stop` | When main agent wants to stop | Ensure session closed; check work queue |
| `SubagentStop` | When subagent wants to stop | Validate subagent task completion |
| `SessionStart` | Session begins | Load vault status; inject project context |
| `SessionEnd` | Session ends | Cleanup; auto-close ztlctl session |
| `PreCompact` | Before context compaction | Preserve critical vault state |
| `Notification` | Claude sends notification | Log activity |

### Hook Types

**Command hooks** — deterministic, bash/Python scripts:
```json
{
  "type": "command",
  "command": "python3 ${CLAUDE_PLUGIN_ROOT}/hooks/pretooluse.py",
  "timeout": 10
}
```

**Prompt hooks** — LLM-driven, for context-aware decisions:
```json
{
  "type": "prompt",
  "prompt": "Check if vault is initialized before MCP tool use. Return systemMessage if vault not found.",
  "timeout": 30
}
```

### Hook I/O Protocol (verified from hookify Python implementations)

**Input:** JSON on stdin
```json
{
  "session_id": "abc123",
  "transcript_path": "/path/to/transcript.txt",
  "cwd": "/current/working/dir",
  "permission_mode": "ask|allow",
  "hook_event_name": "PreToolUse",
  "tool_name": "mcp__plugin_ztlctl_ztlctl__session_start",
  "tool_input": {},
  "tool_result": {}
}
```

**Output:** JSON on stdout
```json
{
  "systemMessage": "Message injected into Claude's context",
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "allow"
  }
}
```

**PreToolUse permission decisions:**
- `"allow"` — proceed
- `"deny"` — block the tool call
- `"ask"` — prompt user for confirmation

**Stop event decisions:**
```json
{
  "decision": "block",
  "reason": "Open session detected — run ztlctl session close before stopping.",
  "systemMessage": "Reminder: close your ztlctl session"
}
```

**Exit codes:**
- `0` — success, stdout shown in transcript
- `2` — blocking error, stderr fed back to Claude
- Other — non-blocking error, logged

### Environment Variables in Hooks

```bash
$CLAUDE_PLUGIN_ROOT    # Plugin installation directory (ALWAYS use for portable paths)
$CLAUDE_PROJECT_DIR    # Current project root
$CLAUDE_ENV_FILE       # SessionStart only: write "export VAR=val" to persist env vars
$CLAUDE_CODE_REMOTE    # Set if running in remote context
```

### Matchers

```json
"matcher": "Bash"                         # Exact tool name
"matcher": "Write|Edit|MultiEdit"         # Pipe-separated OR
"matcher": "*"                            # All tools
"matcher": "mcp__plugin_ztlctl_ztlctl__*" # Regex — all ztlctl MCP tools
```

Matchers are case-sensitive. Use regex patterns to match MCP tool names by prefix.

---

## MCP Server Integration (.mcp.json)

**Verified from:** example-plugin .mcp.json (HTTP), greptile .mcp.json (HTTP with auth headers),
Vercel .mcp.json (HTTP), plugin-dev mcp-integration SKILL.md.

### .mcp.json Format

```json
{
  "ztlctl": {
    "type": "stdio",
    "command": "ztlctl",
    "args": ["serve"],
    "env": {
      "ZTLCTL_VAULT": "${ZTLCTL_VAULT_PATH}"
    }
  }
}
```

### Transport Type Selection for ztlctl

| Transport | Config | Use When |
|-----------|--------|---------|
| `stdio` | `"command": "ztlctl", "args": ["serve"]` | ztlctl installed in user's PATH (recommended default) |
| `http` | `"type": "http", "url": "http://localhost:8000"` | User already running `ztlctl serve --transport streamable-http` |
| `sse` | `"type": "sse", "url": "http://localhost:8000"` | SSE transport variant |

**Recommended: stdio** — Claude Code spawns and manages the `ztlctl serve` process. No
pre-running server needed. Zero user configuration. Vault path passed via env var.

**stdio example with uv for isolation:**
```json
{
  "ztlctl": {
    "type": "stdio",
    "command": "uvx",
    "args": ["--from", "ztlctl[mcp]", "ztlctl", "serve"],
    "env": {
      "ZTLCTL_VAULT_PATH": "${ZTLCTL_VAULT_PATH}"
    }
  }
}
```

### MCP Tool Naming Convention (verified from plugin-dev mcp-integration SKILL.md)

When the plugin is named `ztlctl` and the MCP server is named `ztlctl`:

```
mcp__plugin_<plugin-name>_<server-name>__<tool-name>

Example:
  Plugin: ztlctl
  Server: ztlctl
  Tool: session_start
  Full name: mcp__plugin_ztlctl_ztlctl__session_start
```

**Use in allowed-tools:**
```yaml
allowed-tools:
  - "mcp__plugin_ztlctl_ztlctl__session_start"
  - "mcp__plugin_ztlctl_ztlctl__context_assemble"
```

**Wildcard (use sparingly):**
```yaml
allowed-tools:
  - "mcp__plugin_ztlctl_ztlctl__*"
```

---

## Marketplace Distribution

**Verified from:** README.md of `anthropics/claude-plugins-official`, known_marketplaces.json,
installed_plugins.json, external_plugins directory, plugin-dev marketplace-considerations.md.

### How the Marketplace Works

The official marketplace is a **GitHub repository** at `anthropics/claude-plugins-official`:

```
anthropics/claude-plugins-official/
├── plugins/          # Internal Anthropic plugins
│   └── example-plugin/
│       └── .claude-plugin/plugin.json
│       └── skills/
│       └── ...
├── external_plugins/ # Third-party partner plugins
│   └── greptile/
│       └── .claude-plugin/plugin.json
│       └── .mcp.json
│       └── README.md
└── README.md         # Submission instructions
```

**Plugin install command:**
```bash
/plugin install ztlctl@claude-plugins-official
```

Or browse via `/plugin > Discover` in Claude Code.

### Submission Process

**External plugin submission:**
1. Create plugin in own GitHub repository (e.g., `ThatDevStudio/ztlctl` — already exists)
2. The plugin files live at the repo root (`.claude-plugin/plugin.json`, `skills/`, etc.)
3. Submit via [plugin directory submission form](https://clau.de/plugin-directory-submission)
4. Anthropic reviews for quality and security
5. Plugin listed in `external_plugins/<plugin-name>/` with a pointer to the source repo

**What external plugins look like in the marketplace:**

The greptile external plugin is a minimal stub:
```
external_plugins/greptile/
├── .claude-plugin/plugin.json    # Metadata stub
├── .mcp.json                     # MCP server config
└── README.md
```

This suggests external plugins can be either full plugin directories OR minimal stubs
pointing to an MCP server. For ztlctl, a full plugin with skills is the right approach.

### Versioning Strategy

**Observed patterns:**
- `anthropics/claude-plugins-official` plugins use git commit SHA as version:
  `"version": "61c0597779bd"` — auto-updated on marketplace sync
- `figma@claude-plugins-official` uses semver: `"version": "1.2.0"`
- `superpowers@claude-plugins-official` uses semver: `"version": "5.0.5"`
- `greptile` has no version field in plugin.json (uses default)

**Recommendation for ztlctl plugin:** Use semver (`"version": "1.0.0"`) in `.claude-plugin/plugin.json`.
Version the plugin directory independently from the Python package version if needed,
or keep them in sync.

### Distribution Options

| Option | How | Pros | Cons |
|--------|-----|------|------|
| Official marketplace | Submit to `anthropics/claude-plugins-official` | Discoverability, `/plugin install name@claude-plugins-official` | Requires Anthropic approval, review process |
| Own marketplace | Host GitHub repo, user adds via `/plugin add-marketplace github:ThatDevStudio/ztlctl-plugins` | Full control, no approval | Less discoverable, users must know repo |
| Bundled in ztlctl repo | Plugin directory lives in `ztlctl` repo root | Single repo, single release | User must install manually or via custom marketplace |
| PyPI + auto-install | Ship plugin files in Python package, `ztlctl install-plugin` command creates `.claude-plugin/` | Seamless for existing users | Non-standard, requires manual integration step |

**Recommended approach:** Bundle plugin directory in the `ztlctl` repo itself (option 3),
then submit to official marketplace as an external plugin (option 1). The marketplace entry
points to the `ztlctl` repo. This gives both discoverability and a single source of truth.

### Local Installation (Development)

Claude Code discovers plugins by scanning:
1. User scope: `~/.claude/plugins/` (user-installed)
2. Project scope: `.claude-plugin/` in current working directory

**For development:** Place `.claude-plugin/plugin.json` + plugin files in `ztlctl/`
(repo root). Claude Code auto-loads them when working in the ztlctl project directory.

For user-scope install during development:
```bash
/plugin install --local /path/to/ztlctl
```

---

## GSD Plugin Reference Structure

**Verified from:** `/Users/shparki/.claude/get-shit-done/` directory inspection.

The GSD (get-shit-done) plugin is delivered differently from the marketplace pattern.
It installs hooks into `.claude/settings.json` directly and delivers commands as `.md`
files in `~/.claude/commands/` (global user scope). Its hooks:

```
SessionStart → gsd-check-update.js (update check)
PostToolUse  → gsd-context-monitor.js (context budget tracking)
PreToolUse   → gsd-prompt-guard.js (guard against over-writing)
statusLine   → gsd-statusline.js (status display)
```

**Key insight for ztlctl:** GSD uses hooks for session-level concerns (context monitoring,
update checks). ztlctl's plugin should use hooks similarly for vault-level concerns:
- `SessionStart`: Detect vault path, inject vault status as system context
- `Stop`: Check for unclosed ztlctl sessions
- `UserPromptSubmit`: Detect ztlctl-relevant intent early

---

## Vercel Plugin Reference Structure

**Verified from:** cached plugin at `/Users/shparki/.claude/plugins/cache/claude-plugins-official/vercel/3fe23669ec5a/`

The Vercel plugin is the most sophisticated reference implementation. Key patterns:

**Scale:** 60+ skills, 3 agents, 6 commands, 1 MCP server (HTTP OAuth)

**Skill organization:** Each skill is a domain (`nextjs/`, `observability/`, `workflow/`).
Skills use the advanced metadata frontmatter (`pathPatterns`, `bashPatterns`, `promptSignals`,
`chainTo`) for precision triggering via the Vercel PreToolUse hook.

**Hook system:** Vercel's `hooks/src/` contains the skill injection engine. When a file
path or bash command matches a skill's `pathPatterns` or `bashPatterns`, the skill is
injected into Claude's context via the PreToolUse hook. This is the **skill injection
pattern** — hooks read SKILL.md frontmatter and inject skill content contextually.

**Agent pattern:** Vercel's agents (`deployment-expert.md`, `performance-optimizer.md`,
`ai-architect.md`) are diagnostic specialists — each encodes a decision tree for their domain.

**Takeaway for ztlctl:** The Vercel plugin's architecture is the production template.
ztlctl should replicate:
- Domain-organized skills (one per major workflow)
- A `SessionStart` hook that loads vault status and injects it as system context
- Agents as specialized diagnostic tools (vault-curator, research-analyst)
- skills use `description` field for semantic triggering (simpler is fine for v1)

---

## No New Dependencies Required

The ztlctl Claude Code plugin is a **pure filesystem artifact**. No new Python packages
are needed. All plugin components are:

- Markdown files (`.md`) — skills, commands, agents
- JSON files (`.json`) — plugin.json manifest, hooks.json, .mcp.json
- Optional: Python/bash scripts for hooks (use existing Python 3.13 from PATH)

The only runtime dependency is `ztlctl` itself (already installed) for the MCP server.

---

## Sources

**All sources are first-party — directly read from installed plugin files on this machine.**

| Source | Confidence | Notes |
|--------|------------|-------|
| `plugins/example-plugin/` (marketplace) | HIGH | Reference implementation by Anthropic |
| `plugins/hookify/` (marketplace) | HIGH | Hook system reference; full Python implementation |
| `plugins/plugin-dev/` (marketplace) | HIGH | Plugin authoring guide with full reference docs |
| `plugins/skill-creator/` (marketplace) | HIGH | Skill authoring process and schema reference |
| `external_plugins/greptile/` | HIGH | Minimal external plugin pattern |
| `vercel` plugin (cached `3fe23669ec5a`) | HIGH | Production-scale reference with advanced skill patterns |
| `known_marketplaces.json` | HIGH | Marketplace GitHub repo location |
| `installed_plugins.json` | HIGH | Version and install patterns for 21 plugins |
| `claude-plugins-official/README.md` | HIGH | Marketplace structure, submission process |
| `plugin-dev` skill reference docs | HIGH | manifest-reference.md, hook-development SKILL.md, mcp-integration SKILL.md |
| `~/.claude/settings.json` | HIGH | Live GSD hook registration pattern |
| `ztlctl/src/ztlctl/commands/serve.py` | HIGH | Confirmed transport options (stdio, streamable-http, sse) |

---

*Stack research for: ztlctl v4.0 — Claude Code Plugin with Agentic Skills*
*Researched: 2026-03-22*
