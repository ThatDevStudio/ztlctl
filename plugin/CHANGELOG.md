# Changelog

## 1.0.0

Initial release of the ztlctl Claude Code plugin.

### Added

- 13 skills covering vault orientation, session management, knowledge capture,
  review workflows, synthesis, decision support, graph intelligence, and
  methodology guidance: `align`, `capture`, `decision-support`, `garden-health`,
  `graph-intelligence`, `orient`, `orient-session`, `review-contradictions`,
  `review-triage`, `session`, `session-workflow`, `synthesize`, `vault-methodology`
- 5 slash commands: `/ztlctl:session`, `/ztlctl:capture`, `/ztlctl:review`,
  `/ztlctl:seed`, `/ztlctl:align`
- 2 autonomous agents: `research` (read-only vault exploration) and `maintenance`
  (health diagnostics with confirmation gates)
- Vault gate hook: blocks MCP tool calls when no vault is initialized
- MCP stdio transport configuration with `PYTHONUNBUFFERED=1` for clean JSON-RPC
