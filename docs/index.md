---
title: Home
---

# ZettelControl Documentation

**ZettelControl** (`ztlctl`) is a local knowledge operating system for human users and AI agents. It separates agent-assisted capture and synthesis from human-led enrichment so research workflows and knowledge-garden workflows stay distinct — and coexist without interference.

ztlctl stores durable notes, references, and tasks as markdown files, indexes them in SQLite, and exposes them through a CLI, an MCP server, and generated workflow assets.

## What Makes ztlctl Different

- **Local-first SQLite** — your vault is a directory of markdown files backed by a single `.ztlctl/ztlctl.db`; no cloud account required
- **Graph-native** — every note, reference, and task is a node; links and reweave scores are edges; graph traversal and structural analysis are first-class commands
- **Agent-native MCP** — 59 MCP tools, 6 resources, and 4 prompts let AI agents query, create, and navigate your vault without custom glue code
- **Plugin ecosystem** — pluggy-based hook system with a stable versioned API; extend via local plugins or published packages

## For Knowledge Workers

Build and tend a knowledge vault using the CLI and Obsidian.

- [Quick Start](quickstart.md) — your first vault in 5 minutes
- [Tutorial](tutorial.md) — step-by-step guide to building a knowledge vault
- [Core Concepts](concepts.md) — content types, lifecycle states, vault structure, knowledge graph
- [Knowledge Paradigms](paradigms.md) — capture/synthesis and enrichment, mapped to Zettelkasten, second-brain, and garden approaches
- [Best Practices](best-practices.md) — workflow patterns and anti-patterns

## For Developers and Plugin Authors

Extend ztlctl or integrate it into your tooling.

- [Development](development.md) — architecture, ActionRegistry, and local setup
- [Plugin Authoring](plugin-guide.md) — hookspecs, plugin lifecycle, publishing
- [API Reference](api-reference.md) — auto-generated from source
- [MCP Server](mcp.md) — 59 tools, resources, prompts, and client export

## For AI Agents

Consume and operate a ztlctl vault from an agentic context.

- [agents.md](agents.md) — machine-readable system manual: tool inventory, ID formats, state machines, error codes
- [llms.txt](llms.txt) — full documentation corpus for agent ingestion
- [Agentic Workflows](agentic-workflows.md) — sessions, context assembly, batch operations, scripting

## Quick Links

| Page | Purpose |
|------|---------|
| [Installation](installation.md) | pip, uv, Homebrew, and dev install |
| [Quick Start](quickstart.md) | First vault in 5 minutes |
| [Command Reference](commands.md) | All CLI commands, options, and filters |
| [Configuration](configuration.md) | `ztlctl.toml` settings and environment variables |
| [Troubleshooting](troubleshooting.md) | Common issues and solutions |
