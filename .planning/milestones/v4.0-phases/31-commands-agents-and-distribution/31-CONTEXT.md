# Phase 31: Commands, Agents, and Distribution - Context

**Gathered:** 2026-03-22
**Status:** Ready for planning

<domain>
## Phase Boundary

Create slash commands mapping to key skills, autonomous agents with constrained tool allowlists, marketplace distribution configuration, version synchronization in CI, and comprehensive plugin installation documentation.

</domain>

<decisions>
## Implementation Decisions

### Slash Commands
- 5 slash commands: `/ztlctl:session`, `/ztlctl:capture`, `/ztlctl:review`, `/ztlctl:seed`, `/ztlctl:align`
- Replace existing scaffold commands entirely — scaffold commands reference wrong MCP resources and don't invoke skills
- Commands use `$ARGUMENTS` passthrough with minimal body that delegates to the corresponding skill
- Command files are simple: frontmatter (description, argument-hint) + instructions that invoke the skill

### Autonomous Agents
- Research agent: read-only tool allowlist (`mcp__ztlctl__search`, `mcp__ztlctl__get_document`, `mcp__ztlctl__get_related`, `mcp__ztlctl__graph_*`, `mcp__ztlctl__topic_packet`); maxTurns: 15 for depth limit
- Maintenance agent: all `mcp__ztlctl__*` tools; maxTurns: 20; system prompt includes confirmation-before-mutation instruction
- Replace existing scaffold agents (vault-analyst, knowledge-synthesizer) with research and maintenance agents
- Agent frontmatter follows Claude Code conventions: name, description, model, maxTurns, tools (no unsupported fields per PITFALLS #19)

### Distribution
- Git-subdir marketplace: `marketplace.json` in repo root pointing to `plugin/` directory
- Users install via `claude plugin install ztlctl` from GitHub repo
- Version sync: release-pipeline.yml step copies version from pyproject.toml to plugin.json before tagging — single source of truth
- Plugin README.md covers: prerequisites (uv + Python 3.13 or pipx), install command, post-install verification (`claude mcp list`), troubleshooting (Windows notes, vault init requirement)

### Claude's Discretion
- Exact command file content and argument-hint values
- Agent system prompt wording and example blocks
- marketplace.json schema details
- CI step implementation details for version sync
- README.md formatting and troubleshooting content

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- 4 existing scaffold commands in `plugin/commands/`: capture.md, seed.md, session.md, review.md — will be replaced
- 2 existing scaffold agents in `plugin/agents/`: vault-analyst.md, knowledge-synthesizer.md — will be replaced
- 10 skills in `plugin/skills/` — commands and agents reference these
- CI pipeline in `.github/workflows/release-pipeline.yml` — version sync step added here

### Established Patterns
- Command files: YAML frontmatter (description, argument-hint) + markdown instructions
- Agent files: YAML frontmatter (name, description, model, maxTurns, tools) + examples + system prompt
- plugin.json already has name, version, commands, agents, hooks fields

### Integration Points
- `plugin/commands/` — replace existing, add align.md
- `plugin/agents/` — replace existing with research.md and maintenance.md
- `.github/workflows/release-pipeline.yml` — add version sync step
- Root-level `marketplace.json` — new file for distribution
- `plugin/README.md` — rewrite for installation docs

</code_context>

<specifics>
## Specific Ideas

No specific requirements beyond what's captured in decisions

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>
