# Phase 28: Plugin Foundation - Context

**Gathered:** 2026-03-22
**Status:** Ready for planning

<domain>
## Phase Boundary

Establish the Claude Code plugin directory structure, clean MCP stdio transport, vault gate hook, and CI validation job. Pure infrastructure — no user-facing skills or workflows.

</domain>

<decisions>
## Implementation Decisions

### Claude's Discretion
All implementation choices are at Claude's discretion — pure infrastructure phase. Key constraints from research:
- Plugin directory structure must follow Claude Code conventions (PITFALLS.md #1): components at root, only plugin.json inside .claude-plugin/
- MCP stdio transport must produce zero stdout pollution (PITFALLS.md #2): PYTHONUNBUFFERED=1, all logging to stderr
- PreToolUse vault gate hook must use exit 2 for blocking (PITFALLS.md #9), not exit 1
- Hook scripts must have execute permissions (PITFALLS.md #8)
- Use ${CLAUDE_PLUGIN_ROOT} for all plugin-relative paths (PITFALLS.md #11)
- Plugin name must be kebab-case (PITFALLS.md #17)

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `plugin/` directory already exists with scaffold: .claude-plugin/plugin.json, .mcp.json, hooks/, commands/, agents/, skills/
- Existing plugin.json has name "ztlctl", version "1.0.0", commands/agents/hooks wired
- .mcp.json launches `ztlctl serve` via stdio
- hooks/hooks.json has SessionStart hook calling session-context.sh
- 3 existing skills: vault-methodology, graph-intelligence, session-workflow
- 4 existing commands: capture, seed, session, review
- 2 existing agents: vault-analyst, knowledge-synthesizer

### Established Patterns
- MCP server: `src/ztlctl/mcp/` — FastMCP adapter, auto-generated from ActionRegistry (73+ tools)
- structlog configured to stderr — stdout should already be clean for MCP
- CI: `.github/workflows/pr-ci.yml` — lint, test, typecheck, security audit jobs

### Integration Points
- pr-ci.yml needs new `plugin_validate` job
- .mcp.json may need PYTHONUNBUFFERED=1 in env
- PreToolUse hook needed for vault gate (new hook in hooks.json)

</code_context>

<specifics>
## Specific Ideas

No specific requirements — infrastructure phase

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>
