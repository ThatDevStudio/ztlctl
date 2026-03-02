---
title: Home
nav_order: 1
---

# ZettelControl Documentation

**ZettelControl** (`ztlctl`) is a local knowledge operating system for human users and AI agents. It separates agent-assisted capture and synthesis from human-led enrichment so research workflows and garden workflows stay distinct.

ztlctl stores durable notes, references, and tasks as markdown files, indexes them in SQLite, and exposes them through a CLI, MCP server, and generated workflow assets. Sessions and other operational state are internal coordination mechanisms rather than part of the file-first durability contract.

For agent-fetched web pages and multimodal captures, ztlctl persists durable source bundles beside ingested references so topic packets, drafts, and dashboard dossiers can keep citing the same evidence later.

## Getting Started

- [Installation](installation.md) — Install via pip, uv, or Homebrew
- [Quick Start](quickstart.md) — Your first vault in 9 commands
- [Tutorial](tutorial.md) — Step-by-step guide to building a knowledge vault

## Understanding ztlctl

- [Core Concepts](concepts.md) — Content types, lifecycle states, vault structure, knowledge graph
- [Knowledge Paradigms](paradigms.md) — Capture/synthesis and enrichment, mapped to Zettelkasten, second-brain, and garden approaches

## Reference

- [Command Reference](commands.md) — All CLI commands, options, and filters
- [Configuration](configuration.md) — `ztlctl.toml` settings and environment variables
- [MCP Server](mcp.md) — Model Context Protocol discovery tools, resources, prompts, and client exports

## For Developers and Agents

- [Agentic Workflows](agentic-workflows.md) — Sessions, context assembly, batch operations, scripting
- [Hybrid Workspace Backlog](backlog.md) — Gap closure roadmap for plugin-driven profiles, Obsidian starter kits, and the hybrid garden model
- [Development](development.md) — Contributing, architecture, and local setup
- [Troubleshooting](troubleshooting.md) — Common issues and solutions
