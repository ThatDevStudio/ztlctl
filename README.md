# ZettelControl (ztlctl)

[![CI](https://github.com/ThatDevStudio/ztlctl/actions/workflows/ci.yml/badge.svg)](https://github.com/ThatDevStudio/ztlctl/actions/workflows/ci.yml)
[![PyPI version](https://img.shields.io/pypi/v/ztlctl)](https://pypi.org/project/ztlctl/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Docs](https://img.shields.io/badge/docs-GitHub%20Pages-blue)](https://thatdevstudio.github.io/ztlctl/)

**ZettelControl** (`ztlctl`) is a local knowledge operating system for human users and AI agents. It separates agent-assisted **capture and synthesis** from human-led **enrichment**, so research capture, durable notes, and garden work can coexist without sharing the same workflow.

ztlctl manages durable knowledge artifacts as structured markdown files backed by a SQLite index and a weighted knowledge graph. Operational state such as sessions, logs, generated `self/` documents, and event dispatch is internal and rebuildable rather than part of the file-first durability contract.

## Installation

```bash
pip install ztlctl
```

Or with [uv](https://docs.astral.sh/uv/):

```bash
uv tool install ztlctl
```

Or with Homebrew:

```bash
brew tap ThatDev/ztlctl
brew install ThatDev/ztlctl/ztlctl
```

Optional extras: `pip install ztlctl[mcp]` (MCP server), `pip install ztlctl[semantic]` (vector search), `pip install ztlctl[community]` (advanced graph algorithms).

Homebrew installs the base CLI. For optional extras such as MCP or semantic search, use `pip` or `uv`.

See the [Installation Guide](docs/installation.md) for details.

## Quick Start

```bash
# 1. Initialize a new vault
ztlctl init my-vault --topics "python,architecture,devops"

# 2. Enter the vault directory
cd my-vault

# 3. Start a research session
ztlctl agent session start "Learning Python async patterns"

# 4. Create notes as you learn
ztlctl create note "Asyncio Event Loop" --tags "lang/python,concept/concurrency"
ztlctl create note "Async vs Threading" --tags "lang/python,concept/concurrency"

# 5. Create references to external sources
ztlctl create reference "Python asyncio docs" --url "https://docs.python.org/3/library/asyncio.html"

# 6. Track tasks that emerge
ztlctl create task "Refactor API to use async" --priority high --impact high

# 7. Let the graph grow — reweave discovers connections
ztlctl reweave --auto-link-related

# 8. Search your knowledge
ztlctl query search "async patterns" --rank-by relevance

# 9. Build a topic packet and draft from it
ztlctl query packet --topic architecture --mode review
ztlctl query draft --topic architecture --target note

# 10. Close the session when done
ztlctl agent session close --summary "Mapped async patterns, identified refactoring task"

# Recall past sessions by topic (v3.0)
ztlctl agent session recall-topic "async patterns"

# Check for contradictions across the vault (v3.0)
ztlctl check contradictions
```

## Features

- **Two explicit working layers**: capture/synthesis for agent-assisted research and enrichment for garden work ([Knowledge Paradigms](docs/paradigms.md))
- **File-first durable artifacts** for notes, references, and tasks, with rebuildable indexes and operational state ([Core Concepts](docs/concepts.md))
- **Knowledge graph** with 4-signal reweave scoring (BM25, tag overlap, graph proximity, topic match) for automated link discovery ([Tutorial](docs/tutorial.md))
- **Session-based agentic workflows** with token-budgeted 5-layer context assembly ([Agentic Workflows](docs/agentic-workflows.md))
- **Session recall** — temporal, topic, and topology queries across session history; `ztlctl://sessions/recent` MCP resource ([Session Recall](docs/session-recall.md))
- **Digital garden maturity** tracking — seed, budding, and evergreen stages ([Knowledge Paradigms](docs/paradigms.md))
- **Polaris priorities** — persistent strategic alignment layer with MCP resource, context assembly, and `check alignment` action ([Polaris](docs/polaris.md))
- **Contradiction detection** — heuristic semantic integrity checking, bidirectional graph edges, and MCP review resource ([Contradiction Detection](docs/contradiction-detection.md))
- **Media ingestion** — faster-whisper transcription, 11 audio/video format support, captured-to-annotated two-phase workflow ([Media Ingestion](docs/media-ingestion.md))
- **Text-first ingestion** for raw text, markdown files, and provider-backed URL capture; extends to media via `ztlctl[community]` ([Command Reference](docs/commands.md))
- **Durable source bundles** for agent-fetched web and multimodal captures, persisted beside ingested references for later packet/export reuse ([Agentic Workflows](docs/agentic-workflows.md))
- **Full-text + semantic search** with BM25/vector hybrid ranking, explainable review/garden modes, and topic packets ([Command Reference](docs/commands.md))
- **Methodology guidance** — prose-as-title convention, title quality checks at info severity, garden backlog candidates ([Methodology](docs/methodology.md))
- **Conversational enrichment workflows** with packet-to-draft note/task/decision generation ([Agentic Workflows](docs/agentic-workflows.md))
- **Dashboard and dossier export** for review queues, garden backlog, and topic workbenches ([Tutorial](docs/tutorial.md#step-8-export-and-share))
- **Action registry** — 73+ ActionDefinitions in 9 feature-local modules; CLI and MCP surfaces auto-generated from a single source of truth
- **MCP server** with 73+ auto-generated tools, 20 resources, and 9 prompts for AI integration ([MCP Server](docs/mcp.md))
- **Reliable event delivery** — WAL-backed async dispatch with bounded shutdown drain and service-only `post_action` hooks
- **Generated Claude and Codex workflow assets** via `ztlctl workflow export` for portable agent setup
- **Export** to markdown, indexes, graph formats, and dashboard artifacts ([Tutorial](docs/tutorial.md#step-8-export-and-share))
- **Plugin system** via pluggy event bus with built-in git integration ([Development](docs/development.md))
- **Structured JSON output** on every command for scripting and agent consumption (`--json` flag)
- **Vault integrity** checking, auto-fix, full rebuild, and rollback ([Troubleshooting](docs/troubleshooting.md))

## CLI Command Reference

All commands support `--json` for structured output and `--help` for full option details.
Use `--log-json` on the root command to emit structured JSON logs to stderr (e.g. for agent pipelines).

| Command | Description |
|---------|-------------|
| `ztlctl init` | Initialize a new vault |
| `ztlctl create` | Create notes, references, and tasks |
| `ztlctl update` | Update content metadata or body |
| `ztlctl query` | Search, list, and query vault content |
| `ztlctl graph` | Traverse and analyze the knowledge graph |
| `ztlctl reweave` | Reweave links to densify the knowledge graph |
| `ztlctl agent` | Manage sessions, context, and agent workflows |
| `ztlctl garden` | Cultivate knowledge with the garden persona |
| `ztlctl ingest` | Ingest text and source material into the vault |
| `ztlctl check` | Check vault integrity; optionally fix, rebuild, or rollback |
| `ztlctl upgrade` | Run pending database schema migrations |
| `ztlctl export` | Export vault content (markdown, indexes, graph formats) |
| `ztlctl vector` | Manage the semantic search vector index |
| `ztlctl workflow` | Manage workflow templates and configuration |
| `ztlctl serve` | Start the MCP server (`ztlctl[mcp]` extra required) |
| `ztlctl archive` | Archive a content item (sets archived flag) |
| `ztlctl extract` | Extract a decision note from a session log |
| `ztlctl supersede` | Mark a decision as superseded by a newer decision |

## Documentation

| Guide | Description |
|-------|-------------|
| [Installation](docs/installation.md) | Install via pip, uv, or Homebrew |
| [Quick Start](docs/quickstart.md) | Your first vault in 9 commands |
| [Tutorial](docs/tutorial.md) | Step-by-step vault building guide |
| [Core Concepts](docs/concepts.md) | Content types, lifecycle, vault structure, graph |
| [Command Reference](docs/commands.md) | All CLI commands, options, and filters |
| [Configuration](docs/configuration.md) | `ztlctl.toml` settings and environment variables |
| [Agentic Workflows](docs/agentic-workflows.md) | Sessions, context assembly, batch, scripting |
| [Session Recall](docs/session-recall.md) | Temporal, topic, and topology queries across session history |
| [Polaris](docs/polaris.md) | Persistent strategic priorities layer and alignment checking |
| [Contradiction Detection](docs/contradiction-detection.md) | Heuristic semantic integrity checking across vault notes |
| [Media Ingestion](docs/media-ingestion.md) | Audio/video transcription and captured-to-annotated workflow |
| [Methodology](docs/methodology.md) | Prose-as-title convention and title quality guidance |
| [Knowledge Paradigms](docs/paradigms.md) | Capture/synthesis and enrichment, mapped to note-taking paradigms |
| [MCP Server](docs/mcp.md) | Model Context Protocol integration |
| [Development](docs/development.md) | Contributing, architecture, local setup |
| [Troubleshooting](docs/troubleshooting.md) | Common issues and solutions |

Full documentation is also available at [thatdevstudio.github.io/ztlctl](https://thatdevstudio.github.io/ztlctl/).

## Architecture

ztlctl follows a strict 6-layer package structure where dependencies flow downward:

```
src/ztlctl/
├── domain/          # Types, enums, lifecycle rules, ID patterns
├── infrastructure/  # SQLite/SQLAlchemy, NetworkX graph, filesystem
├── config/          # Pydantic config models, TOML discovery
├── services/        # Business logic — 16 services (create, query, graph, reweave, ...)
├── output/          # Rich/JSON formatters
├── controllers/     # Delegation layer between ActionRegistry and services (v3.0)
├── actions/         # 73 ActionDefinitions in 9 feature-local modules (v3.0)
├── commands/        # Click CLI — auto-generated from ActionRegistry
├── plugins/         # Pluggy hook specs, built-in plugins, centralized PM factory
├── mcp/             # MCP server adapter — auto-generated from ActionRegistry
└── templates/       # Jinja2 templates for content creation
```

CLI and MCP surfaces are both auto-generated from the `ActionRegistry` — define an action once in `actions/`, and both surfaces get it automatically.

See [Development](docs/development.md) for details and [DESIGN.md](DESIGN.md) for the complete internal design specification.

## Contributing

This project uses [conventional commits](https://www.conventionalcommits.org/). See [CONTRIBUTING.md](CONTRIBUTING.md) for the full guide.

1. Branch from `develop`: `git checkout -b feature/<name> develop`
2. Make changes and commit with conventional messages
3. Open a PR targeting `develop`
4. Releases are automated when version-bumping commits (`feat:`, `fix:`) merge to `develop`

## Community

- [Code of Conduct](CODE_OF_CONDUCT.md)
- [Security Policy](SECURITY.md)
- [Support](SUPPORT.md)

## License

[MIT](LICENSE)
