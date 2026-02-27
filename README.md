# ztlctl

[![CI](https://github.com/ThatDevStudio/ztlctl/actions/workflows/ci.yml/badge.svg)](https://github.com/ThatDevStudio/ztlctl/actions/workflows/ci.yml)
[![PyPI version](https://img.shields.io/pypi/v/ztlctl)](https://pypi.org/project/ztlctl/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Zettelkasten Control** — a CLI utility and agentic note-taking ecosystem that combines zettelkasten, second-brain, and knowledge-garden paradigms into a single tool designed for both human users and AI agents.

ztlctl manages your knowledge vault as structured markdown files backed by a SQLite index, connected through a weighted knowledge graph, and accessible via CLI, MCP server, or direct Python API.

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Core Concepts](#core-concepts)
- [Tutorial: Building Your Knowledge Vault](#tutorial-building-your-knowledge-vault)
- [Command Reference](#command-reference)
- [Agentic Workflows](#agentic-workflows)
- [Knowledge Paradigms](#knowledge-paradigms)
- [Configuration](#configuration)
- [MCP Server](#mcp-server)
- [Development](#development)
- [Contributing](#contributing)
- [License](#license)

## Installation

```bash
pip install ztlctl
```

Or with [uv](https://docs.astral.sh/uv/):

```bash
uv tool install ztlctl
```

For MCP server support (optional):

```bash
pip install ztlctl[mcp]
```

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

# 9. Close the session when done
ztlctl agent session close --summary "Mapped async patterns, identified refactoring task"
```

## Core Concepts

### Content Types

ztlctl manages four content types, each with its own lifecycle:

| Type | Purpose | Initial Status | ID Format |
|------|---------|---------------|-----------|
| **Note** | Ideas, knowledge, decisions | `draft` | `ztl_<hash>` |
| **Reference** | External sources (articles, tools, specs) | `captured` | `ref_<hash>` |
| **Task** | Actionable work items | `inbox` | `TSK-NNNN` |
| **Log** | Session journals (JSONL) | `open` | `LOG-NNNN` |

### Content Subtypes

Notes and references can be further classified:

- **Note subtypes**: `knowledge` (long-lived insight), `decision` (architectural/design choice)
- **Reference subtypes**: `article`, `tool`, `spec`
- **Garden maturity**: `seed` (raw capture) → `budding` (developing) → `evergreen` (polished)

### Lifecycle States

Each content type follows a defined state machine:

```
Note:      draft → linked (1+ outgoing link) → connected (3+ outgoing links)
Reference: captured → annotated
Task:      inbox → active → done | blocked | dropped
Decision:  proposed → accepted → superseded
Log:       open ↔ closed (reopenable)
```

Status transitions are enforced — you cannot skip states or make invalid transitions.

### Vault Structure

```
my-vault/
├── ztlctl.toml          # Configuration
├── .ztlctl/
│   └── ztlctl.db        # SQLite index + FTS5 + graph edges
├── self/
│   ├── identity.md      # Agent identity (generated from config)
│   └── methodology.md   # Agent methodology
├── notes/
│   ├── python/          # Topic subdirectories
│   │   └── ztl_a1b2c3d4.md
│   └── architecture/
│       └── ztl_e5f6g7h8.md
└── ops/
    ├── logs/
    │   └── LOG-0001.jsonl
    └── tasks/
        └── TSK-0001.md
```

### Tags

Tags use a `domain/scope` format for structured categorization:

```bash
--tags "lang/python"        # domain=lang, scope=python
--tags "concept/concurrency" # domain=concept, scope=concurrency
--tags "status/wip"         # domain=status, scope=wip
```

Unscoped tags (e.g., `python`) work but generate a warning — the domain/scope format enables powerful filtering.

### Knowledge Graph

Every content item is a node. Edges are created through:

- **Frontmatter links**: Explicit `links:` in YAML frontmatter
- **Wikilinks**: `[[Note Title]]` references in body text
- **Reweave**: Automated link discovery via 4-signal scoring (BM25 lexical similarity, Jaccard tag overlap, graph proximity, topic match)

The graph powers `ztlctl graph` commands for traversal, analysis, and structural insight.

## Tutorial: Building Your Knowledge Vault

### Step 1: Initialize Your Vault

```bash
ztlctl init research-vault --name "Research Notes" --topics "ml,systems,papers"
cd research-vault
```

This creates the directory structure, config file, SQLite database, and agent identity files. The `--topics` flag pre-creates subdirectories under `notes/`.

**Options:**
- `--name TEXT` — Vault display name
- `--client [obsidian|vanilla]` — Client integration (Obsidian adds `.obsidian/` config)
- `--tone [research-partner|assistant|minimal]` — Agent personality for self/ files
- `--topics TEXT` — Comma-separated topic directories
- `--no-workflow` — Skip workflow template setup

### Step 2: Capture Knowledge

**Create a note** — your primary unit of knowledge:

```bash
ztlctl create note "Transformer Architecture" \
  --tags "ml/transformers,concept/architecture" \
  --topic ml
```

**Create a reference** — link to an external source:

```bash
ztlctl create reference "Attention Is All You Need" \
  --url "https://arxiv.org/abs/1706.03762" \
  --subtype article \
  --tags "ml/transformers,papers/seminal"
```

**Quick capture with garden seed** — when you want minimal friction:

```bash
ztlctl garden seed "Idea: attention mechanisms for code review" \
  --tags "ml/attention" --topic ml
```

Seeds start at `seed` maturity and can grow to `budding` → `evergreen` as you develop them.

### Step 3: Work with Tasks

```bash
ztlctl create task "Read BERT paper" --priority high --impact high --effort low
ztlctl create task "Implement attention visualization" --priority medium
```

View your prioritized work queue:

```bash
ztlctl query work-queue
```

Tasks are scored by priority × impact ÷ effort and presented in actionable order.

### Step 4: Connect Knowledge

**Automatic link discovery** — reweave analyzes all content and suggests connections:

```bash
ztlctl reweave --auto-link-related
```

**Dry run** to preview what would change:

```bash
ztlctl reweave --dry-run
```

**Target a specific note:**

```bash
ztlctl reweave --id ztl_a1b2c3d4
```

Reweave uses a 4-signal scoring algorithm:
1. **BM25** (35%) — lexical similarity between content bodies
2. **Tag Jaccard** (25%) — tag overlap between items
3. **Graph Proximity** (25%) — existing network distance
4. **Topic Match** (15%) — shared topic directory

### Step 5: Query and Explore

**Full-text search:**

```bash
ztlctl query search "transformer attention" --rank-by relevance
ztlctl query search "python async" --rank-by recency --type note
ztlctl query search "architecture" --rank-by graph  # PageRank-boosted
```

**List with filters:**

```bash
ztlctl query list --type note --status draft
ztlctl query list --tag "ml/transformers" --sort recency
ztlctl query list --maturity seed --since 2025-01-01
ztlctl query list --include-archived --sort title
```

**Get a specific item:**

```bash
ztlctl query get ztl_a1b2c3d4
```

**Decision support** — aggregate context for a decision:

```bash
ztlctl query decision-support --topic architecture
```

### Step 6: Analyze the Graph

**Find related content** via spreading activation:

```bash
ztlctl graph related ztl_a1b2c3d4 --depth 2 --top 10
```

**Discover topic clusters:**

```bash
ztlctl graph themes
```

**Find the most important nodes** (PageRank):

```bash
ztlctl graph rank --top 20
```

**Find the shortest path** between two ideas:

```bash
ztlctl graph path ztl_a1b2c3d4 ztl_e5f6g7h8
```

**Find structural gaps** — orphan notes with no connections:

```bash
ztlctl graph gaps --top 10
```

**Find bridge nodes** — key connectors between clusters:

```bash
ztlctl graph bridges --top 10
```

### Step 7: Update and Evolve

**Update metadata:**

```bash
ztlctl update ztl_a1b2c3d4 --title "New Title" --tags "new/tag"
ztlctl update ztl_a1b2c3d4 --status linked
ztlctl update ztl_a1b2c3d4 --maturity budding  # Grow a garden note
```

**Archive** — soft-delete that preserves graph edges:

```bash
ztlctl archive ztl_a1b2c3d4
```

**Supersede a decision:**

```bash
ztlctl supersede ztl_old_decision ztl_new_decision
```

### Step 8: Export and Share

**Export markdown** — portable copy of all content:

```bash
ztlctl export markdown --output ./export/
```

**Generate indexes** — type and topic groupings:

```bash
ztlctl export indexes --output ./indexes/
```

**Export the knowledge graph:**

```bash
ztlctl export graph --format dot --output graph.dot  # For Graphviz
ztlctl export graph --format json --output graph.json # For D3.js / vis.js
```

### Step 9: Maintain Integrity

**Check vault health:**

```bash
ztlctl check
```

**Auto-fix detected issues:**

```bash
ztlctl check --fix
ztlctl check --fix --level aggressive  # More thorough repairs
```

**Full rebuild** — re-derive the entire database from files:

```bash
ztlctl check --rebuild
```

**Rollback** to the last backup:

```bash
ztlctl check --rollback
```

## Command Reference

### Global Options

Every command supports these flags:

| Flag | Description |
|------|-------------|
| `--version` | Show version and exit |
| `--json` | Structured JSON output (for scripting and agents) |
| `-q, --quiet` | Minimal output |
| `-v, --verbose` | Detailed output with debug info |
| `--no-interact` | Non-interactive mode (no prompts) |
| `--no-reweave` | Skip automatic reweave on creation |
| `-c, --config TEXT` | Override config file path |
| `--sync` | Force synchronous event dispatch |

Most commands also support `--examples` to show usage examples.

### Commands at a Glance

| Command | Purpose |
|---------|---------|
| `init [PATH]` | Initialize a new vault |
| `create note TITLE` | Create a note |
| `create reference TITLE` | Create a reference |
| `create task TITLE` | Create a task |
| `create batch FILE` | Batch create from JSON |
| `query search QUERY` | Full-text search |
| `query get ID` | Get item by ID |
| `query list` | List with filters |
| `query work-queue` | Prioritized task queue |
| `query decision-support` | Decision context aggregation |
| `graph related ID` | Find related content |
| `graph themes` | Discover topic clusters |
| `graph rank` | PageRank importance |
| `graph path SRC DST` | Shortest path between nodes |
| `graph gaps` | Find structural holes |
| `graph bridges` | Find bridge nodes |
| `graph materialize` | Compute and store graph metrics |
| `agent session start TOPIC` | Start a session |
| `agent session close` | Close with enrichment pipeline |
| `agent session reopen ID` | Reopen a closed session |
| `agent session cost` | Token cost tracking |
| `agent session log MSG` | Append log entry |
| `agent context` | Token-budgeted context payload |
| `agent brief` | Quick orientation summary |
| `agent regenerate` | Re-render self/ files |
| `check` | Integrity check/fix/rebuild |
| `update ID` | Update metadata or body |
| `reweave` | Automated link discovery |
| `archive ID` | Soft-delete content |
| `supersede OLD NEW` | Mark decision as superseded |
| `extract SESSION_ID` | Extract decision from session |
| `export markdown` | Export as portable markdown |
| `export indexes` | Generate type/topic indexes |
| `export graph` | Export graph (DOT or JSON) |
| `garden seed TITLE` | Quick-capture seed note |
| `serve` | Start MCP server |
| `upgrade` | Run database migrations |

### Search Ranking Modes

The `--rank-by` option on `query search` supports three modes:

| Mode | Algorithm | Best For |
|------|-----------|----------|
| `relevance` | BM25 with time decay | General search |
| `recency` | Modified date descending | Finding recent work |
| `graph` | BM25 × PageRank boost | Finding well-connected content |

### Query Filters

The `query list` command supports composable filters:

```bash
# Combine any of these:
--type note|reference|task|log
--status draft|linked|connected|inbox|active|done|...
--tag "domain/scope"
--topic "python"
--subtype knowledge|decision|article|tool|spec
--maturity seed|budding|evergreen
--space notes|ops|self
--since 2025-01-01
--include-archived
--sort recency|title|type|priority
--limit 50
```

## Agentic Workflows

ztlctl is designed to be operated by AI agents as a first-class use case. Every command supports `--json` output for structured parsing, and the session/context system provides token-budgeted context windows.

### Session-Based Agent Workflow

Sessions are the primary organizational container for agentic work:

```bash
# Agent starts a focused research session
ztlctl agent session start "API design patterns" --json

# Agent creates notes as it discovers knowledge
ztlctl create note "REST vs GraphQL trade-offs" \
  --tags "architecture/api" --session LOG-0001 --json

# Agent logs its reasoning and costs
ztlctl agent session log "Analyzed 5 API frameworks" --cost 1200 --json
ztlctl agent session log "Key insight: GraphQL better for nested data" --pin --json

# Agent checks token budget
ztlctl agent session cost --report 50000 --json

# Agent requests context for continued work
ztlctl agent context --topic "api" --budget 4000 --json

# Agent closes session, triggering enrichment pipeline
ztlctl agent session close --summary "Mapped API paradigms" --json
```

### Context Assembly (5-Layer System)

The `agent context` command builds a token-budgeted payload with 5 layers:

| Layer | Content | Budget |
|-------|---------|--------|
| 0 — Identity | `self/identity.md` + `self/methodology.md` | Always included |
| 1 — Operational | Active session, recent decisions, work queue, log entries | Always included |
| 2 — Topic | Notes and references matching the session topic | Budget-dependent |
| 3 — Graph | 1-hop neighbors of Layer 2 content | Budget-dependent |
| 4 — Background | Recent activity, structural gaps | Budget-dependent |

The system tracks token usage per layer and reports pressure status (`normal`, `caution`, `exceeded`).

```bash
# Get full context with default 8000-token budget
ztlctl agent context --json

# Focus on a topic with custom budget
ztlctl agent context --topic "architecture" --budget 4000 --json

# Quick orientation (no session required)
ztlctl agent brief --json
```

### Session Close Enrichment Pipeline

When a session closes, ztlctl automatically runs:

1. **Cross-session reweave** — discovers connections for all notes created in the session
2. **Orphan sweep** — attempts to connect orphan notes (0 outgoing edges)
3. **Integrity check** — validates vault consistency
4. **Graph materialization** — updates PageRank, degree, and betweenness metrics

Each step can be toggled in `ztlctl.toml`:

```toml
[session]
close_reweave = true
close_orphan_sweep = true
close_integrity_check = true
```

### Decision Extraction

Extract decisions from session logs into permanent decision notes:

```bash
# Extracts pinned/decision entries from the session log
ztlctl extract LOG-0001 --title "Decision: Use GraphQL for nested queries"
```

This creates a decision note (`subtype=decision`, status `proposed`) linked to the session via a `derived_from` edge.

### MCP Server Integration

ztlctl includes a Model Context Protocol (MCP) server for direct integration with AI clients like Claude Desktop:

```bash
ztlctl serve --transport stdio
```

**12 MCP tools**: create_note, create_reference, create_task, create_log, update_content, close_content, reweave, search, get_document, get_related, agent_context, session_close

**6 MCP resources**: self/identity, self/methodology, vault overview, work queue, topics, full context

**4 MCP prompts**: research_session, knowledge_capture, vault_orientation, decision_record

Add to Claude Desktop's `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "ztlctl": {
      "command": "ztlctl",
      "args": ["serve"]
    }
  }
}
```

### Batch Operations

For programmatic creation, use batch mode with a JSON file:

```bash
echo '[
  {"type": "note", "title": "Concept A", "tags": ["domain/scope"]},
  {"type": "reference", "title": "Source B", "url": "https://example.com"},
  {"type": "task", "title": "Follow up on C", "priority": "high"}
]' > items.json

ztlctl create batch items.json --json
ztlctl create batch items.json --partial  # Continue on individual failures
```

### Scripting with JSON Output

Every command supports `--json` for structured output:

```bash
# Create and capture the ID
ID=$(ztlctl create note "My Note" --json | jq -r '.data.id')

# Query and process results
ztlctl query search "python" --json | jq '.data.items[].title'

# Check vault health programmatically
ERRORS=$(ztlctl check --json | jq '.data.issues | map(select(.severity == "error")) | length')
```

## Knowledge Paradigms

ztlctl integrates three complementary note-taking paradigms:

### Zettelkasten (Atomic Notes + Links)

The zettelkasten method treats each note as a single, self-contained idea connected to others through links.

**How ztlctl supports it:**

- Each note gets a unique content-hash ID (`ztl_a1b2c3d4`)
- Notes link to each other via `[[wikilinks]]` in body text and explicit frontmatter links
- `ztlctl graph related` implements spreading activation to find connected ideas
- `ztlctl graph path` traces connection chains between any two notes
- Note status evolves automatically: `draft` → `linked` (1+ outgoing) → `connected` (3+ outgoing)

**Workflow:**

```bash
# Capture atomic ideas
ztlctl create note "Immutability reduces bugs" --tags "concept/fp"
ztlctl create note "Pure functions are easier to test" --tags "concept/fp"

# Let reweave connect them
ztlctl reweave --auto-link-related

# Explore the connections
ztlctl graph related ztl_abc123 --depth 2
```

### Second Brain (PARA + Capture Everything)

The second brain approach (inspired by Tiago Forte's PARA) captures everything and organizes by actionability.

**How ztlctl supports it:**

- **Projects** → Tasks with priority/impact/effort scoring and `work-queue`
- **Areas** → Topic directories (`--topic`) for ongoing domains
- **Resources** → References with URL, subtype (article/tool/spec), and tags
- **Archive** → `ztlctl archive` soft-deletes while preserving graph edges
- Sessions provide temporal organization — every piece of content links to its creation session

**Workflow:**

```bash
# Capture everything during a research session
ztlctl agent session start "System design research"

# Resources (articles, tools, specs you encounter)
ztlctl create reference "CAP Theorem Explained" --subtype article --url "..."
ztlctl create reference "Redis Documentation" --subtype tool --url "..."

# Knowledge (your synthesized understanding)
ztlctl create note "Trade-offs in distributed caching" --subtype knowledge

# Tasks (actions that emerge)
ztlctl create task "Evaluate Redis vs Memcached" --priority high --impact high

# Review your work queue
ztlctl query work-queue
```

### Knowledge Garden (Seeds → Evergreen)

The digital garden metaphor treats notes as living things that grow over time through tending.

**How ztlctl supports it:**

- **Maturity levels**: `seed` (raw capture) → `budding` (developing) → `evergreen` (polished)
- `ztlctl garden seed` — quick capture with minimal friction
- `ztlctl update --maturity budding` — promote as you develop ideas
- `ztlctl graph gaps` — find notes that need tending (no outgoing links)
- Garden notes protect body content from accidental overwrites

**Workflow:**

```bash
# Quick-capture seeds throughout the day
ztlctl garden seed "Idea: use event sourcing for audit trail"
ztlctl garden seed "Question: how does CRDT conflict resolution work?"

# Later, tend your garden — find seeds that need attention
ztlctl query list --maturity seed --sort recency

# Develop a seed into a budding note
ztlctl update ztl_abc123 --maturity budding \
  --tags "architecture/event-sourcing,pattern/cqrs"

# Promote to evergreen when fully developed
ztlctl update ztl_abc123 --maturity evergreen
```

### Combining Paradigms

These paradigms work together naturally:

1. **Capture** with garden seeds and references (Second Brain + Garden)
2. **Connect** via reweave and wikilinks (Zettelkasten)
3. **Develop** by promoting seeds through maturity levels (Garden)
4. **Act** on tasks surfaced by the work queue (Second Brain)
5. **Decide** by extracting decisions from sessions (Zettelkasten + Second Brain)
6. **Review** via graph analysis to find gaps and bridges (All three)

## Configuration

ztlctl uses a `ztlctl.toml` file at the vault root. Settings can be overridden via CLI flags or `ZTLCTL_*` environment variables.

### Key Configuration Sections

```toml
[vault]
name = "my-vault"
client = "obsidian"  # or "vanilla"

[agent]
tone = "research-partner"  # or "assistant", "minimal"

[agent.context]
default_budget = 8000      # Token budget for context assembly
layer_2_max_notes = 10     # Max notes in topic layer
layer_3_max_hops = 1       # Graph traversal depth

[reweave]
enabled = true
min_score_threshold = 0.6  # Minimum score to suggest a link
max_links_per_note = 5
lexical_weight = 0.35      # BM25 weight
tag_weight = 0.25          # Tag Jaccard weight
graph_weight = 0.25        # Graph proximity weight
topic_weight = 0.15        # Topic match weight

[garden]
seed_age_warning_days = 7
evergreen_min_key_points = 5
evergreen_min_bidirectional_links = 3

[search]
half_life_days = 30.0      # Time-decay half-life for recency ranking

[session]
close_reweave = true       # Reweave on session close
close_orphan_sweep = true  # Connect orphan notes on close
close_integrity_check = true

[check]
backup_retention_days = 30
backup_max_count = 10

[git]
enabled = true
auto_push = true
commit_style = "conventional"

[mcp]
enabled = true
transport = "stdio"
```

### Environment Variables

Any setting can be overridden with a `ZTLCTL_` prefix:

```bash
ZTLCTL_REWEAVE__MIN_SCORE_THRESHOLD=0.4 ztlctl reweave
ZTLCTL_AGENT__CONTEXT__DEFAULT_BUDGET=16000 ztlctl agent context
```

## MCP Server

The MCP (Model Context Protocol) server exposes ztlctl's full functionality to AI clients.

### Setup

```bash
# Install with MCP support
pip install ztlctl[mcp]

# Start the server
ztlctl serve --transport stdio
```

### Available Tools

| Tool | Description |
|------|-------------|
| `create_note` | Create a note with title, tags, topic |
| `create_reference` | Create a reference with URL |
| `create_task` | Create a task with priority/impact/effort |
| `create_log` | Start a new session |
| `update_content` | Update content metadata |
| `close_content` | Archive or close content |
| `reweave` | Run link discovery |
| `search` | Full-text search with ranking |
| `get_document` | Retrieve content by ID |
| `get_related` | Graph-based related content |
| `agent_context` | Token-budgeted context payload |
| `session_close` | Close session with enrichment |

### Available Resources

| Resource | Description |
|----------|-------------|
| `self/identity` | Agent identity document |
| `self/methodology` | Agent methodology document |
| `vault/overview` | Vault statistics and structure |
| `vault/work-queue` | Prioritized task list |
| `vault/topics` | Available topic directories |
| `vault/context` | Full assembled context |

### Available Prompts

| Prompt | Description |
|--------|-------------|
| `research_session` | Start a structured research session |
| `knowledge_capture` | Guided knowledge capture workflow |
| `vault_orientation` | Orient to the current vault state |
| `decision_record` | Record an architectural decision |

## Development

```bash
uv sync --group dev                              # install all dev dependencies
uv run ztlctl --help                             # run the CLI
uv run pytest --cov --cov-report=term-missing    # run tests with coverage
uv run ruff check .                              # lint
uv run ruff format .                             # format
uv run mypy src/                                 # type check
uv run pre-commit run --all-files                # run all pre-commit hooks
```

### Architecture

ztlctl follows a strict 6-layer package structure:

```
src/ztlctl/
├── domain/          # Types, enums, lifecycle rules, ID patterns
├── infrastructure/  # SQLite/SQLAlchemy, NetworkX graph, filesystem
├── config/          # Pydantic config models, TOML discovery
├── services/        # Business logic (create, query, graph, reweave, ...)
├── output/          # Rich/JSON formatters
├── commands/        # Click CLI commands
├── plugins/         # Pluggy hook specs and built-in plugins
├── mcp/             # MCP server adapter
└── templates/       # Jinja2 templates for content creation
```

Dependencies flow downward: commands → output → services → config/infrastructure → domain.

### Template Overrides

Vault-specific Jinja2 overrides can live under `.ztlctl/templates/`.

- Self-document templates: `.ztlctl/templates/self/identity.md.j2` or `.ztlctl/templates/identity.md.j2`
- Content body templates: `.ztlctl/templates/content/note.md.j2` or `.ztlctl/templates/note.md.j2`

ztlctl checks those override paths first and falls back to the bundled package templates when no user template exists.

## Contributing

This project uses [conventional commits](https://www.conventionalcommits.org/). All commit messages and PR titles must follow the format:

```
<type>(<scope>): <description>
```

Common types: `feat`, `fix`, `docs`, `test`, `refactor`, `ci`, `chore`

### Workflow

1. Branch from `develop`: `git checkout -b feature/<name> develop`
2. Make changes and commit with conventional messages
3. Open a PR targeting `develop`
4. Releases are automated when `develop` is merged to `main`

## License

[MIT](LICENSE)
