# Claude Code Plugin Development Pitfalls

**Domain:** Claude Code plugin for an existing Python MCP tool (ztlctl v4.0 — Agentic Skills)
**Researched:** 2026-03-22
**Confidence:** HIGH (official docs verified) / MEDIUM (community issues, bug trackers) / LOW (single-source observations)

---

## Scope

This document covers pitfalls specific to building a Claude Code plugin that wraps an existing Python/MCP tool. The ztlctl MCP server already works. The risks are in the plugin wrapper, skill design, hooks, distribution, and the Python-to-JS boundary where the MCP server is launched by the plugin.

---

## Critical Pitfalls

### Pitfall 1: Directory Structure — Components Inside `.claude-plugin/`

**What goes wrong:**
`commands/`, `agents/`, `skills/`, and `hooks/` directories are placed inside `.claude-plugin/` alongside `plugin.json`. Claude Code looks for these directories at the plugin root, not inside `.claude-plugin/`. The plugin loads, `plugin.json` parses correctly, but every skill and command is silently missing.

**Why it happens:**
The `.claude-plugin/` directory is the first thing you create. It feels like "the plugin config directory" so components naturally land there. The distinction — manifest inside, everything else outside — is not intuitively obvious.

**Consequences:**
Plugin appears installed and valid. No error is shown. All skills, agents, and hooks are simply absent. Debugging is difficult because the plugin "works" from the manifest perspective.

**Prevention:**
```
plugin-root/
├── .claude-plugin/
│   └── plugin.json       <- ONLY this belongs here
├── skills/               <- at root
├── agents/               <- at root
├── hooks/                <- at root
└── .mcp.json             <- at root
```
Run `claude plugin validate` before testing. Check `claude --debug` output for "loading plugin" messages that enumerate discovered components.

**Detection:**
`claude --debug` shows "No commands found" or "No skills found" even though files exist. Plugin installs without error but `/ztlctl:*` slash commands do not appear.

**Phase to address:** Plugin scaffolding phase — enforce structure from the first commit.

---

### Pitfall 2: Python MCP Server Stdout Pollution Breaking stdio Transport

**What goes wrong:**
The ztlctl MCP server is launched by the plugin via `uvx` over stdio. Any `print()` statement, logging to stdout, startup banner, or library that writes to stdout (e.g., dotenv v17+) corrupts the JSON-RPC stream. Claude Code receives malformed JSON, the connection fails, and the server appears disconnected.

**Why it happens:**
Python developers routinely use `print()` for debug output. In a normal CLI context this is harmless. In stdio MCP transport, stdout is a structured protocol channel — any non-JSON byte is fatal.

**Consequences:**
MCP server shows as disconnected in Claude Code. All MCP tool calls fail silently or with a generic timeout error. Symptoms look like a configuration problem, not a logging problem — this is the hardest class of bug to diagnose.

**Prevention:**
- All logging in ztlctl MCP server must go to stderr: `print("...", file=sys.stderr)` or via structlog/logging configured to stderr (ztlctl already uses structlog to stderr — preserve this)
- Set `PYTHONUNBUFFERED=1` in `.mcp.json` environment config to prevent buffering stalls
- Audit all startup paths for `print()` calls before shipping the plugin
- If any dependency (e.g., a logging library, import-time side effects) writes to stdout, silence it at the entry point
- Test server startup in isolation: `echo '{"jsonrpc":"2.0","method":"initialize",...}' | uvx ztlctl serve` and verify the response is clean JSON

**Detection:**
Claude Code shows "MCP server disconnected" or "Request timed out" immediately after connection. Running `uvx ztlctl serve` manually and piping input shows non-JSON output mixed with JSON-RPC responses.

**Phase to address:** MCP integration phase — verify clean stdio before any skill testing.

---

### Pitfall 3: Version Bump Without Plugin Caching Invalidation

**What goes wrong:**
The plugin code is updated and pushed to the marketplace repository, but `version` in `plugin.json` is not incremented. Claude Code uses the cached version and users never see the update. `claude plugin update` reports "already at latest version" because the version string is unchanged, even though the commit is newer.

**Why it happens:**
Semantic versioning discipline that exists for Python packages (`cz bump`) does not automatically apply to the plugin manifest. The plugin is a different artifact with its own versioning lifecycle.

**Consequences:**
Bug fixes and skill improvements are invisible to users. The plugin appears current. Support issues arise from users running stale versions they believe are up to date.

**Prevention:**
- Treat `plugin.json` version as a gate: no merge to main without a version bump when skill content, hooks, or MCP config changes
- Add a CI check that verifies `version` was incremented in any PR that modifies plugin files
- Maintain a `CHANGELOG.md` in the plugin repo to make version history visible
- Use pre-release versions (`2.0.0-beta.1`) for testing before promoting to stable

**Detection:**
`claude plugin update ztlctl-skills@marketplace` reports "already at latest" but `git log` shows new commits. Users report bugs that were fixed in recent commits.

**Phase to address:** Distribution phase — establish as a mandatory PR gate from day one.

---

### Pitfall 4: MCP Server Namespace Collision Under `--plugin-dir` vs Installed

**What goes wrong:**
When loaded via `--plugin-dir` for development, Claude Code adds a `plugin_<plugin-name>_` prefix to MCP tool names. The same plugin installed from a marketplace does not apply this prefix. Skill `allowed-tools` declarations that reference `mcp__ztlctl__*` work when installed but fail silently under `--plugin-dir` because the runtime tool names are `mcp__plugin_ztlctl_skills__ztlctl__*`.

**Why it happens:**
This is a documented Claude Code bug (issue #29360). The plugin-dir loading path applies namespacing that the marketplace installation path does not, and skill frontmatter allowed-tools wildcards are not transformed to match.

**Consequences:**
Skills that restrict tool access via `allowed-tools: mcp__ztlctl__*` appear to work in development (tools show in debug output) but Claude cannot access them without per-use approval. The discrepancy is invisible — development tests pass, production behavior differs.

**Prevention:**
- Test skills using `claude plugin install` to a local marketplace, not just `--plugin-dir`, before declaring them ready
- Do not rely exclusively on `allowed-tools` wildcards for MCP tool access during development — verify under install path
- Monitor issue #29360 for a fix; design skills defensively by not over-restricting `allowed-tools` when the wildcard behavior cannot be verified

**Detection:**
Skills require approval for MCP tool calls when installed but not during `--plugin-dir` testing. `claude --debug` shows different tool name prefixes between the two load paths.

**Phase to address:** Skill integration testing phase — always test installed, not just `--plugin-dir`.

---

### Pitfall 5: Stop Hook Infinite Loop

**What goes wrong:**
A `Stop` hook uses `exit 2` to block Claude's completion (to enforce a review step, for example). Claude tries to stop, the hook blocks it with exit 2, Claude tries to stop again, the hook blocks it again — infinite loop. The session hangs with no way out except killing the process.

**Why it happens:**
`exit 2` from a `Stop` hook signals "block this stop and reprocess." This is the correct signal for blocking tool calls, but in the context of `Stop`, it causes Claude to retry the stop indefinitely.

**Consequences:**
Session hangs. User must force-quit Claude Code. Any unsaved context is lost. If the hook is in a plugin delivered to users, it makes the plugin unusable.

**Prevention:**
All `Stop` hooks must check the `stop_hook_active` field in the hook input JSON. If `stop_hook_active` is `true`, the hook must exit 0 — Claude has already been blocked once and is retrying, so the hook must allow the stop:
```bash
#!/bin/bash
INPUT=$(cat)
STOP_ACTIVE=$(echo "$INPUT" | jq -r '.stop_hook_active // false')
if [ "$STOP_ACTIVE" = "true" ]; then exit 0; fi
# ... hook logic that may exit 2
```

**Detection:**
Session hangs after Claude completes a response. CPU stays high. No progress. Force-quit required.

**Phase to address:** Hooks implementation phase — apply the `stop_hook_active` guard to every `Stop` hook before testing.

---

### Pitfall 6: Skill Description Overlap Causing Activation Failure

**What goes wrong:**
Two skills have descriptions that cover overlapping scenarios. When the user's request could match either, Claude cannot pick one, picks the wrong one, or falls back to base knowledge without activating either skill. Worse, a skill with a vague description ("Use for zettelkasten operations") competes with a more specific skill ("Use when starting a research session") — the vague one suppresses the specific one.

**Why it happens:**
Skills are written in isolation, each optimized for its own purpose. No one reviews all descriptions together to check for overlap. The ztlctl domain is cohesive (everything relates to notes and knowledge), which makes overlap likely.

**Consequences:**
Core workflows silently use base model knowledge instead of the curated skill workflow. The skill exists, is installed, but never fires for the scenarios it was designed for.

**Prevention:**
- Write descriptions that answer exactly "when to activate" using unique action verbs and specific context markers
- Bad: "Use for ztlctl knowledge management operations"
- Good: "Use when the user asks to start, begin, or open a work or research session in their ztlctl vault"
- After writing all skill descriptions, read them together as a list and verify no two descriptions could match the same user request
- Use `disable-model-invocation: true` for skills that should only be invoked manually (e.g., `/ztlctl:capture` for explicit capture, not auto-triggered)
- Test activation rates: for each skill, write 5 prompts that should trigger it and verify it fires

**Detection:**
Manually invoking `/ztlctl:session-start` works, but asking "Let's start a research session" does not activate it. `What skills are available?` shows the skill, but it never fires automatically.

**Phase to address:** Skill design phase — review all descriptions as a set before implementation.

---

### Pitfall 7: SKILL.md Content Persisting in Context Window for the Entire Session

**What goes wrong:**
When Claude invokes a skill, the full SKILL.md content is injected into conversation history as a hidden message. It persists and is sent with every subsequent API call for the rest of the session. A 500-line "session lifecycle" skill invoked at the start of a session occupies tokens for every subsequent exchange — even simple follow-ups that have nothing to do with session management.

**Why it happens:**
Skills are designed to be authoritative — their full content is always available. The trade-off (context window consumption for the rest of the session) is not visible during development because individual sessions are short.

**Consequences:**
In long sessions, multiple invoked skills accumulate in context, crowding out conversation history. Context compaction occurs earlier. Response quality degrades. A 200K context window may have ~70K usable tokens after tool definitions and loaded skills.

**Prevention:**
- Keep SKILL.md under 500 lines. The official guidance: keep `SKILL.md` under 500 lines; move detailed reference to supporting files (reference.md, examples.md) that Claude loads only when needed
- Use progressive disclosure: SKILL.md describes the workflow at high level; detailed step references are in separate files linked from SKILL.md
- Prefer `context: fork` for heavy skills — forked subagent skills run in isolation and don't accumulate in the parent session context
- Do not encode reference content (MCP tool signatures, full parameter lists) directly in SKILL.md — Claude already has MCP tool descriptions; link to them or abbreviate
- For ztlctl: the session lifecycle skill is the most at-risk (multi-step, many MCP calls) — design it with `context: fork` and a lean SKILL.md

**Detection:**
Slow response times after several skill invocations. `/context` shows high context usage. Context compaction triggers mid-session during complex workflows.

**Phase to address:** Skill content design phase — apply 500-line limit before writing any skill.

---

### Pitfall 8: Hook Script Not Executable on First Install

**What goes wrong:**
Hook scripts are committed to the repository without execute permissions (`chmod +x`). On install, the hook fires, tries to run the script, gets a permission denied error, and either silently passes (exit 0) or blocks incorrectly (exit 2, depending on error handling). On macOS the failure may be silent; on Linux, the error is visible but only in `claude --debug`.

**Why it happens:**
Git does not preserve execute permissions by default on some systems. Developers test on their own machine (where the script was already executable) and do not verify the installed permission state.

**Consequences:**
Hooks appear to install correctly but never execute. The plugin's safety or automation features (lint on save, telemetry on session start) are silently inactive.

**Prevention:**
- Always verify hook script permissions after `git clone` of the plugin repo: `ls -la hooks/scripts/`
- Explicitly set permissions in the plugin's SessionStart hook or README installation steps: `chmod +x ${CLAUDE_PLUGIN_ROOT}/scripts/*.sh`
- Add a setup validation to the plugin's CI: verify all files in `scripts/` have execute bit set
- Use the `${CLAUDE_PLUGIN_ROOT}` variable in hook commands so paths are absolute after install

**Detection:**
Hooks do not fire after installation. `claude --debug` shows "Permission denied" for hook commands. Manual execution of the script from a shell fails with "Permission denied."

**Phase to address:** Hooks implementation phase — add a CI permission check before distribution.

---

## Moderate Pitfalls

### Pitfall 9: Using `exit 1` Instead of `exit 2` in Security Gate Hooks

**What goes wrong:**
A PreToolUse hook is intended as a gate that blocks dangerous operations. The hook exits with code 1 when it wants to block. Exit 1 means "error" — Claude Code logs it and continues the tool call. The "security gate" is a suggestion that is always ignored.

**Prevention:**
- `exit 0` — pass, proceed with tool call
- `exit 1` — non-blocking error, logged only, tool call proceeds
- `exit 2` — blocking error, tool call is cancelled, stderr is shown to Claude

Use `exit 2` for any hook that is meant to prevent a tool from executing.

**Phase to address:** Hooks implementation phase.

---

### Pitfall 10: Slow Hooks Degrading Autonomy Speed

**What goes wrong:**
A PostToolUse hook that runs a linter, calls the MCP server, or performs file analysis takes 3-5 seconds per invocation. On a session with 50 file edits, this adds 2.5+ minutes of dead time. Autonomous sessions that were supposed to run hands-free are now interactive because the bottleneck makes them slow enough that users intervene.

**Prevention:**
- Keep hooks under 500ms for synchronous operations
- Use matchers to narrow execution scope: `"matcher": "Write|Edit"` only for lint hooks, not all tool events
- Move expensive validation to PostToolUse (non-blocking) rather than PreToolUse (blocking)
- For ztlctl: any hook that calls MCP tools (e.g., indexing after a session) should be async/non-blocking

**Phase to address:** Hooks optimization phase.

---

### Pitfall 11: `$HOME` and Environment Variables Not Expanded in JSON Hook Paths

**What goes wrong:**
Hook command paths in `hooks.json` use `$HOME` or other shell variables that are not expanded in JSON string context. The hook silently fails to load. `${CLAUDE_PLUGIN_ROOT}` is the only variable that Claude Code expands in hook configurations.

**Prevention:**
- Use `${CLAUDE_PLUGIN_ROOT}` for all plugin-relative paths in hooks and MCP configs
- Use `${CLAUDE_PLUGIN_DATA}` for persistent state that survives updates
- Never use `$HOME`, `$USER`, `~/`, or other shell variables in `hooks.json` or `.mcp.json`
- Use absolute paths for user-level system dependencies (e.g., `/usr/local/bin/python3`)

**Phase to address:** Hooks implementation phase.

---

### Pitfall 12: Plugin Files Referencing Paths Outside the Plugin Directory

**What goes wrong:**
A plugin skill references a shared utility at `../../shared/utils.py` or a script at `../scripts/run.sh`. When the plugin is installed from a marketplace, Claude Code copies the plugin to `~/.claude/plugins/cache/`. Files outside the plugin root are not copied. The path traversal fails with a file-not-found error that is invisible until after installation.

**Why it happens:**
During development the paths work because the filesystem contains both the plugin directory and the referenced external files. The caching behavior is only apparent after installation.

**Prevention:**
- All files the plugin needs must be inside the plugin root at the time of installation
- Use symlinks within the plugin directory to reference external files: `ln -s /path/to/shared ./shared` — symlinks are honored during the cache copy
- For Python dependencies, use `${CLAUDE_PLUGIN_DATA}` with a SessionStart hook that installs them on first run

**Phase to address:** Distribution preparation phase.

---

### Pitfall 13: Plugin-MCP Synchronization Mismatch After Install

**What goes wrong:**
A plugin is installed via `claude plugin install`, appears "installed" in the UI, but the plugin's MCP server is not enabled in `.claude.json`. MCP tool calls fail with misleading "Request timed out" errors. The user believes the plugin is working because it shows as installed.

**Why it happens:**
This is a documented Claude Code bug (issue #18762). The plugin installation can succeed at the metadata level while the MCP server activation step fails silently.

**Prevention:**
- After installing the plugin, verify the MCP server is active: run `claude mcp list` and confirm the server appears
- Include a verification step in the plugin README's installation instructions
- Document the manual workaround: add the MCP server config directly to `.claude.json` or `.mcp.json` if the automatic activation fails

**Detection:**
Plugin installed, skills visible in `/help`, but all skill invocations that call MCP tools fail with timeout errors. `claude mcp list` does not show the ztlctl server.

**Phase to address:** Distribution and onboarding phase.

---

### Pitfall 14: Skill Context Budget Overflow When Many Skills Are Installed

**What goes wrong:**
Skill descriptions are loaded into context so Claude knows what is available. The budget scales at 2% of the context window (approximately 16,000 characters as fallback). If the plugin provides many skills, some skill descriptions are dropped to fit the budget. Dropped skills are invisible to Claude — it cannot invoke them, and the user does not know they exist.

**Prevention:**
- Keep skill descriptions under 150 characters where possible — they are selection criteria, not documentation
- Bad description: "Use this skill for the comprehensive multi-step ztlctl research session workflow that includes polaris priorities alignment, vault context assembly, and semantic search preparation"
- Good description: "Use when starting a focused research session in the ztlctl vault"
- Run `/context` to check for skill budget warnings after loading the plugin
- Set `SLASH_COMMAND_TOOL_CHAR_BUDGET` environment variable if budget overflow is a consistent problem

**Phase to address:** Skill design phase.

---

### Pitfall 15: Cross-Platform Windows Compatibility for uvx-Based MCP Server

**What goes wrong:**
The plugin's `.mcp.json` launches ztlctl via `uvx ztlctl serve`. On Windows, `uvx` may not be on PATH in Claude Code's subprocess environment. PowerShell execution policies may block the command. The server fails to start with a cryptic "command not found" error.

**Prevention:**
- Use the full path to `uvx` or `python` when possible, or document that `uv` must be on the system PATH
- For Windows users, provide a fallback launch command using `python -m ztlctl serve` with the virtualenv's Python
- Test the `.mcp.json` command on Windows (via WSL2 or native) before distribution
- Document the Windows installation prerequisite: `uv` installed and on PATH via `winget install astral-sh.uv`
- Consider providing a `.mcp.json` variant or instructions for Windows in the plugin README

**Phase to address:** Distribution phase — Windows validation before marketplace submission.

---

### Pitfall 16: Skills Duplicating MCP Tool Functionality Instead of Orchestrating It

**What goes wrong:**
A skill is written that reimplements logic already in the MCP server — for example, encoding the full 6-stage create pipeline in the SKILL.md instead of calling the `create_note` MCP tool. The skill becomes a parallel implementation that drifts from the server's actual behavior when the server is updated.

**Why it happens:**
Skills feel like the place to describe "how things work." But skills are orchestration guides, not implementations. The MCP tools already encode the domain logic.

**Consequences:**
Skill behavior diverges from server behavior over time. Updates to the MCP server's pipeline (new stages, new validation) are not reflected in the skill. Users get inconsistent results between direct MCP tool calls and skill-guided calls.

**Prevention:**
- Skills should describe **when** to use which tools and **in what sequence**, not **what those tools do internally**
- Never replicate logic from ztlctl's ActionRegistry in SKILL.md — trust the tool descriptions
- Skill content should look like: "Call `ztlctl://create_note` with `{title, type, content}`. If the result contains `needs_reweave: true`, follow with `ztlctl://reweave_note`."
- Not: "The create pipeline validates title length, generates a sequential ID, persists to SQLite, indexes in FTS5, runs reweave scoring..."

**Phase to address:** Skill design phase — establish this as a design principle before writing any skill.

---

## Minor Pitfalls

### Pitfall 17: Plugin Name Using Spaces or Non-Kebab Characters

**What goes wrong:**
`plugin.json` `name` field uses spaces, underscores, or capital letters. This field becomes the skill namespace (e.g., `/ztlctl skills:capture` instead of `/ztlctl-skills:capture`). Commands with spaces in the namespace break slash command autocomplete. Skill names using underscores are inconsistent with Claude Code's kebab-case convention.

**Prevention:**
Use lowercase kebab-case names only: `"name": "ztlctl-skills"`. This produces clean namespaced commands: `/ztlctl-skills:capture`.

**Phase to address:** Plugin scaffolding.

---

### Pitfall 18: Not Restarting Claude Code After Configuration Changes

**What goes wrong:**
MCP server configs in `.mcp.json` are modified during development. Changes do not take effect until Claude Code is restarted. The developer tests the old configuration and wonders why the fix did not work.

**Prevention:**
Use `/reload-plugins` within Claude Code to pick up changes to skills, agents, and hooks without a full restart. For MCP server configuration changes (command, args, env vars), a full restart is required.

**Phase to address:** Development workflow — document in plugin README.

---

### Pitfall 19: Agent Frontmatter Using Unsupported Fields

**What goes wrong:**
Plugin agents are defined with `hooks`, `mcpServers`, or `permissionMode` frontmatter fields. These fields are supported for user-defined agents but are explicitly not supported for plugin-shipped agents (per official docs). The agent loads, but the unsupported fields are silently ignored — or in some Claude Code versions, cause the agent to fail validation.

**Prevention:**
Plugin agents support: `name`, `description`, `model`, `effort`, `maxTurns`, `tools`, `disallowedTools`, `skills`, `memory`, `background`, `isolation` (only valid value: `"worktree"`). Do not include `hooks`, `mcpServers`, or `permissionMode` in plugin agent definitions.

**Phase to address:** Agent design phase.

---

### Pitfall 20: `disable-model-invocation: true` Missing on Side-Effect Skills

**What goes wrong:**
A skill like "capture research" or "close session" does not have `disable-model-invocation: true`. Claude infers from context that it's a good time to capture a finding and automatically invokes the skill — triggering a vault write, a session update, or an MCP tool call that the user did not intend to initiate. The skill fires without explicit user request.

**Prevention:**
Any skill with side effects that should only run on explicit user request must include `disable-model-invocation: true` in frontmatter. Skills that are safe for Claude to invoke proactively (read-only context assembly, reference lookups) can omit it.

For ztlctl: capture, create, update, close, session-start, session-close, export — all must have `disable-model-invocation: true`. Read-only skills (vault-context, graph-explore) may allow automatic invocation.

**Phase to address:** Skill design phase.

---

## Python MCP + Plugin Boundary — Integration Pitfalls

The boundary between Claude Code (JS/TS runtime) and ztlctl (Python process) creates a specific class of failure modes.

| Failure Mode | Root Cause | Prevention |
|---|---|---|
| Server disconnects immediately | Python print() to stdout corrupts JSON-RPC | All output to stderr; PYTHONUNBUFFERED=1 |
| Server connects but tools time out | Python process buffering stdout | Set PYTHONUNBUFFERED=1 in .mcp.json env |
| Server not found on PATH | `uvx` or `uv` not in Claude Code subprocess PATH | Use full path or document PATH requirement |
| Windows: command not found | PowerShell execution policy blocks uvx | Document Windows prerequisite; provide fallback |
| Tool names differ dev vs installed | Plugin-dir namespacing bug (#29360) | Test under install path, not just --plugin-dir |
| Skills can't call MCP tools without approval | allowed-tools wildcard not transformed | Test under installed state; use broader wildcards |
| Server crashes on vault missing | ztlctl requires initialized vault | Add vault existence check in SessionStart hook; surface error clearly |
| Encoding issues on Windows | Python default encoding vs utf-8 | Set PYTHONUTF8=1 in .mcp.json env |

---

## Testing Strategy Recommendations

### Development Loop

```
1. Develop skill content in .claude/skills/ (standalone, short names)
2. Test with /skill-name directly — iterate quickly
3. Move to plugin structure when ready to share
4. Test with --plugin-dir ./ztlctl-skills (namespaced /ztlctl-skills:skill-name)
5. Install to local scope from a test marketplace
6. Test under installed state — this is the canonical test
```

**Do not declare a skill ready until step 6 passes.** Steps 1-4 can hide the namespace collision pitfall (#4) and the plugin-MCP sync pitfall (#13).

### Skill Testing

- For each skill: write 5 prompts that should trigger it (auto-invocation) and verify it fires
- For each skill: write 3 prompts that should NOT trigger it and verify it does not fire (description overlap check)
- For skills with `disable-model-invocation: true`: verify they do not auto-fire under any circumstance

### Hook Testing

- Test each hook individually with a minimal triggering scenario
- Verify exit codes: for blocking hooks, test that exit 2 blocks and exit 0 passes
- Test Stop hooks with and without `stop_hook_active` set to verify the infinite-loop guard
- Measure execution time — anything over 500ms needs optimization or conversion to PostToolUse

### MCP Integration Testing

- Verify server starts: `echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{}}}' | uvx ztlctl serve`
- Verify no stdout pollution: capture stdout during server startup and tool invocation
- Verify all 73+ tools are listed in `claude mcp list` after plugin install
- Test a representative skill end-to-end: invoke skill, confirm it calls the expected MCP tools, confirm result

### Distribution Testing

- Test `claude plugin install <plugin>@<marketplace>` on a clean machine
- Verify `claude mcp list` shows ztlctl server after install
- Test `claude plugin update` after bumping version in plugin.json
- Test on macOS (primary), verify on Linux, document Windows status

---

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|---|---|---|
| Plugin scaffolding | Components inside .claude-plugin/ | Enforce structure in PR template; validate with `claude plugin validate` |
| MCP integration | stdout pollution on server startup | Audit all Python print() calls before plugin testing begins |
| Skill descriptions | Overlap causing activation failure | Review all descriptions as a set; test activation with sample prompts |
| Skill content | Too long, persists in context | 500-line limit; use supporting files; consider `context: fork` for heavy workflows |
| Side-effect skills | Auto-invocation of write operations | `disable-model-invocation: true` on all create/update/delete/session skills |
| Hook implementation | Wrong exit code on security gates | Use exit 2 for blocking; add stop_hook_active guard on Stop hooks |
| Hook performance | Slow hooks degrading autonomy | Keep under 500ms; use matchers; move expensive checks to PostToolUse |
| Distribution | No version bump = stale cache | CI gate on version increment; treat plugin.json version as a mandatory PR field |
| Distribution | Plugin-MCP sync mismatch after install | Verify with `claude mcp list` post-install; document workaround in README |
| Windows support | uvx not on PATH | Document prerequisite; provide fallback command; test on Windows before marketplace submission |

---

## Distribution Checklist

Before submitting to the official Anthropic marketplace (`platform.claude.com/plugins/submit`):

- [ ] `claude plugin validate` passes with zero warnings
- [ ] All hook scripts have execute permissions in the committed repository
- [ ] `plugin.json` has `name`, `version`, `description`, `author`, `repository`, `license`
- [ ] Version is >= `1.0.0` and follows semantic versioning
- [ ] `CHANGELOG.md` exists and documents the current version
- [ ] `README.md` covers: prerequisites (uv, Python 3.13), installation steps, post-install verification (`claude mcp list`), Windows notes
- [ ] MCP server tested for clean stdout (no non-JSON output)
- [ ] All skill descriptions reviewed as a set for overlap
- [ ] All side-effect skills have `disable-model-invocation: true`
- [ ] Plugin tested under installed state (not just `--plugin-dir`)
- [ ] Plugin tested on macOS (primary) and at minimum documented for Linux/Windows
- [ ] Version bump is a mandatory PR gate (CI enforced or policy enforced)
- [ ] No paths outside plugin root (no `../` traversals in hooks or MCP config)
- [ ] `${CLAUDE_PLUGIN_ROOT}` used for all plugin-relative paths
- [ ] `${CLAUDE_PLUGIN_DATA}` used for any state that should persist across updates
- [ ] Hook exit codes verified: `exit 2` for blocking, `exit 0` for pass, `exit 1` for warning-only

---

## Sources

- [Claude Code Plugins Reference — official docs](https://code.claude.com/docs/en/plugins-reference) — manifest schema, directory structure, path rules, version management (HIGH confidence — official)
- [Create Claude Code Plugins — official docs](https://code.claude.com/docs/en/plugins) — skill structure, testing with --plugin-dir, /reload-plugins (HIGH confidence — official)
- [Claude Code Skills — official docs](https://code.claude.com/docs/en/skills) — SKILL.md frontmatter, invocation control, context behavior, 500-line guidance (HIGH confidence — official)
- [Claude Code Hooks Reference — official docs](https://code.claude.com/docs/en/hooks) — hook events, exit codes, stop_hook_active (HIGH confidence — official)
- [Claude Code MCP Docs — official docs](https://code.claude.com/docs/en/mcp) — stdio transport, uvx usage, cross-platform setup (HIGH confidence — official)
- [5 Claude Code Hook Mistakes — dev.to/yurukusa](https://dev.to/yurukusa/5-claude-code-hook-mistakes-that-silently-break-your-safety-net-58l3) — exit code mistakes, $HOME expansion, slow hooks, context monitoring (MEDIUM confidence — community article, verified against official docs)
- [GitHub issue #29360 — anthropics/claude-code](https://github.com/anthropics/claude-code/issues/29360) — plugin-dir namespacing breaks allowed-tools (MEDIUM confidence — bug tracker, open issue)
- [GitHub issue #18762 — anthropics/claude-code](https://github.com/anthropics/claude-code/issues/18762) — plugin-MCP config mismatch causing timeout errors (MEDIUM confidence — bug tracker)
- [GitHub issue #15145 — anthropics/claude-code](https://github.com/anthropics/claude-code/issues/15145) — incorrect plugin namespacing for MCP servers (MEDIUM confidence — bug tracker)
- [Plugin update detection issue #31462 — anthropics/claude-code](https://github.com/anthropics/claude-code/issues/31462) — plugin update mechanism gaps (MEDIUM confidence — bug tracker)
- [Claude plugin update fast-forward bug — issue #29071](https://github.com/anthropics/claude-code/issues/29071) — `claude plugin update` fails to advance branch (MEDIUM confidence — bug tracker)
- [Why Intended Skills Don't Fire — medium.com/@taki4416](https://medium.com/@taki4416/why-intended-skills-dont-fire-an-anti-pattern-in-claude-code-skill-a8c5230a9a5e) — skill description overlap anti-pattern (LOW confidence — 403 on verification, confirmed by independent sources)
- [Context window persistence problem — claudefa.st](https://claudefa.st/blog/guide/mechanics/context-buffer-management) — skill injection persisting through session (MEDIUM confidence — verified against official docs behavior)
- [Invisible Limitations of Skills — medium.com/@cheparsky](https://medium.com/@cheparsky/ai-in-testing-9-the-invisible-limitations-of-claude-code-skills-you-didnt-know-f3adbdcf3680) — context accumulation, skill budget overflow (LOW confidence — 403 on verification)
- [Python MCP stdio stdout pollution — multiple sources](https://gofastmcp.com/integrations/claude-code) — print() to stdout breaks JSON-RPC (HIGH confidence — confirmed by official MCP docs and multiple independent sources)
- [What I Learned Building Three Claude Code Plugins — medium.com/pierce-lamb](https://pierce-lamb.medium.com/what-i-learned-while-building-a-trilogy-of-claude-code-plugins-72121823172b) — directory structure mistakes, context limits (LOW confidence — 403 on verification, key findings confirmed by official docs)

---

*Pitfalls research for: v4.0 Agentic Skills — Claude Code plugin wrapping existing Python/MCP ztlctl tool*
*Researched: 2026-03-22*
