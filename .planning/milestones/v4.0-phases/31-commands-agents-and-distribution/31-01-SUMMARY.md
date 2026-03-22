---
phase: 31-commands-agents-and-distribution
plan: "01"
subsystem: plugin
tags: [commands, agents, skills, plugin]
dependency_graph:
  requires:
    - plugin/skills/ (10 skills from phases 29-30)
    - plugin/.claude-plugin/plugin.json
  provides:
    - plugin/commands/session.md
    - plugin/commands/capture.md
    - plugin/commands/review.md
    - plugin/commands/seed.md
    - plugin/commands/align.md
    - plugin/agents/research.md
    - plugin/agents/maintenance.md
  affects:
    - Claude Code plugin slash command surface (/ztlctl:*)
    - Claude Code autonomous agent surface
tech_stack:
  added: []
  patterns:
    - Thin command delegation to skills via $ARGUMENTS passthrough
    - Read-only constrained tool allowlist for research agent
    - Confirmation-before-mutation pattern for maintenance agent
key_files:
  created:
    - plugin/commands/align.md
    - plugin/agents/research.md
    - plugin/agents/maintenance.md
  modified:
    - plugin/commands/session.md
    - plugin/commands/capture.md
    - plugin/commands/review.md
    - plugin/commands/seed.md
  deleted:
    - plugin/agents/vault-analyst.md
    - plugin/agents/knowledge-synthesizer.md
decisions:
  - Commands are thin delegators: each command body is 5-8 lines that invoke the corresponding skill with $ARGUMENTS passthrough — no workflow logic duplicated in commands
  - Research agent is strictly read-only: 9 search/graph tools only, no create/update/session/confirm tools in allowlist
  - Maintenance agent uses mcp__ztlctl__* wildcard for full access but never-auto-confirm is enforced via system prompt iron law
  - Agent frontmatter uses only supported plugin fields (name, description, model, maxTurns, tools) — no hooks, mcpServers, permissionMode
metrics:
  duration: 116s
  completed: "2026-03-22T04:56:36Z"
  tasks_completed: 2
  files_changed: 9
requirements: [CMDA-01, CMDA-02, CMDA-03]
---

# Phase 31 Plan 01: Commands and Agents Summary

5 slash commands wired to 5 skills with $ARGUMENTS passthrough, plus 2 autonomous agents (read-only research, confirmation-gated maintenance) replacing 2 scaffold agents.

## What Was Built

### Task 1: Replace 4 scaffold commands, add align command

Replaced all 4 existing scaffold command files and created 1 new command. Each scaffold command contained 20-30 lines of workflow logic that referenced legacy MCP resources (`ztlctl://context`, `ztlctl://overview`, `create_log`). All were replaced with 5-8 line thin delegators that invoke the corresponding skill.

**Commands created/replaced:**

| Command | Skill | Pattern |
|---------|-------|---------|
| `/ztlctl:session` | `ztl:session` | $ARGUMENTS as topic |
| `/ztlctl:capture` | `ztl:capture` | $ARGUMENTS as capture context |
| `/ztlctl:review` | `ztl:review-triage` | no arguments (skill runs full triage) |
| `/ztlctl:seed` | `ztl:capture` (seed mode) | $ARGUMENTS as seed title + tags |
| `/ztlctl:align` | `ztl:align` | $ARGUMENTS as decision to evaluate |

### Task 2: Replace 2 scaffold agents with research and maintenance agents

Deleted `vault-analyst.md` and `knowledge-synthesizer.md` (both scaffold agents with monolithic system prompts and no skill references). Created 2 new agents with correct Claude Code plugin frontmatter (per PITFALLS #19).

**research.md:**
- Tools: 9 read-only tools — search, get_document, get_related, graph_themes, graph_rank, graph_gaps, graph_path, graph_bridges, topic_packet
- maxTurns: 15 (depth-bounded per CONTEXT.md decision)
- System prompt: autonomous graph traversal workflow → structured research brief with summary, key notes, themes, connections, gaps, source references

**maintenance.md:**
- Tools: `mcp__ztlctl__*` (full access for write operations)
- maxTurns: 20
- System prompt: 4-step diagnostic workflow (integrity, contradictions, garden, work queue) with confirmation-before-mutation iron law and never-auto-confirm rule for contradictions

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None — all 5 commands delegate to implemented skills; both agents have complete system prompts with no placeholder content.

## Self-Check: PASSED

Files verified:
- plugin/commands/session.md: FOUND
- plugin/commands/capture.md: FOUND
- plugin/commands/review.md: FOUND
- plugin/commands/seed.md: FOUND
- plugin/commands/align.md: FOUND
- plugin/agents/research.md: FOUND
- plugin/agents/maintenance.md: FOUND
- plugin/agents/vault-analyst.md: DELETED (confirmed)
- plugin/agents/knowledge-synthesizer.md: DELETED (confirmed)

Commits verified:
- 5bbc400: feat(31-01): replace scaffold commands and add align command
- 53edd65: feat(31-01): replace scaffold agents with research and maintenance agents
