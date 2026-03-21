---
title: Command Reference
---

# Command Reference

Every command example on this page is verified against the Click command source in `src/ztlctl/commands/` and the ActionDefinition registry in `src/ztlctl/actions/_register_core.py`. See [Configuration](configuration.md) for config-based defaults.

## Global Options

Every command supports these flags:

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--version` | flag | — | Show version and exit |
| `--json` | flag | false | Structured JSON output (for scripting and agents) |
| `-q, --quiet` | flag | false | Minimal output |
| `-v, --verbose` | flag | false | Detailed output with span tree and debug info |
| `--log-json` | flag | false | Structured JSON log output to stderr (structlog) |
| `--no-interact` | flag | false | Non-interactive mode (no prompts) |
| `--no-reweave` | flag | false | Skip automatic reweave on creation |
| `-c, --config TEXT` | text | — | Override config file path |
| `--sync` | flag | false | Force synchronous event dispatch |

Most commands also support `--examples` to show usage examples.

## Commands at a Glance

| Command | Purpose |
|---------|---------|
| `init [OPTIONS]` | Initialize a new vault (interactive wizard) |
| `init regenerate` | Re-render self/ agent context files |
| `init staleness` | Check whether self/ files need regeneration |
| `create note TITLE` | Create a note |
| `create reference TITLE` | Create a reference |
| `create task TITLE` | Create a task |
| `create batch FILE` | Batch create from JSON |
| `query search QUERY` | Full-text search |
| `query get ID` | Get item by ID |
| `query list` | List with filters |
| `query count` | Total indexed item count |
| `query tags` | List active tags with usage counts |
| `query work-queue` | Prioritized task queue |
| `query decision-support` | Decision context aggregation |
| `query packet TOPIC` | Topic-scoped learning/review packet |
| `query draft TOPIC` | Draft a note, task, or decision from a topic packet |
| `query review` | Vault health and structure snapshot |
| `graph related ID` | Find related content |
| `graph themes` | Discover topic clusters |
| `graph rank` | PageRank importance |
| `graph path SRC DST` | Shortest path between nodes |
| `graph gaps` | Find structural holes |
| `graph bridges` | Find bridge nodes |
| `graph unlink SRC DST` | Remove link between two nodes |
| `graph materialize` | Compute and store graph metrics |
| `session start TOPIC` | Start a session |
| `session close` | Close with enrichment pipeline |
| `session reopen ID` | Reopen a closed session |
| `session status` | Show active session summary |
| `session cost` | Token cost tracking |
| `session log MSG` | Append log entry |
| `session context` | Token-budgeted context payload |
| `session brief` | Quick orientation summary |
| `session extract SESSION_ID` | Extract decision from session |
| `check check` | Report integrity issues |
| `check fix` | Auto-repair integrity issues |
| `check rebuild` | Full DB rebuild from filesystem |
| `check rollback` | Restore DB from latest backup |
| `update ID` | Update metadata or body |
| `reweave run` | Run link discovery on vault or a specific item |
| `reweave prune` | Remove stale links below threshold |
| `reweave undo` | Reverse a reweave operation |
| `archive ID` | Soft-delete content |
| `supersede OLD NEW` | Mark decision as superseded |
| `export markdown OUTPUT_DIR` | Export as portable markdown |
| `export indexes OUTPUT_DIR` | Generate type/topic indexes |
| `export graph` | Export graph (DOT or JSON) |
| `export dashboard OUTPUT_DIR` | Export an external review workbench |
| `garden seed TITLE` | Quick-capture seed note |
| `ingest text TITLE` | Ingest raw text into a note or reference |
| `ingest file PATH` | Ingest a markdown or text file |
| `ingest url URL` | Ingest a URL through an installed source provider |
| `ingest providers` | List installed source providers |
| `docs search QUERY` | Search ztlctl documentation corpus |
| `serve` | Start MCP server |
| `upgrade check` | List pending migrations |
| `upgrade apply` | Apply pending migrations |
| `upgrade stamp` | Stamp DB as current head |
| `vector status` | Check semantic search availability |
| `vector reindex` | Rebuild the vector index |
| `workflow init VAULT_ROOT` | Initialize workflow scaffolding |
| `workflow update VAULT_ROOT` | Update workflow scaffolding |
| `workflow export VAULT_ROOT` | Export agent workflow assets |

## Command Details

### init

```bash
ztlctl init [--path PATH] [--name NAME] [--profile PROFILE] [--tone TONE] [--topics TEXT] [--no-workflow]
```

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--path TEXT` | text | `.` | Vault directory |
| `--name TEXT` | text | — | Vault display name (prompted if omitted in interactive mode) |
| `--profile TEXT` | text | `core` | Workspace profile (`core`, `obsidian`, or plugin-defined) |
| `--tone TEXT` | choice | `research-partner` | Agent tone: `research-partner`, `assistant`, or `minimal` |
| `--topics TEXT` | text | — | Comma-separated topic directories |
| `--no-workflow` | flag | false | Skip workflow template setup |

### create note

```bash
ztlctl create note TITLE [--subtype TEXT] [--tags TEXT]... [--topic TEXT] [--body TEXT] [--key-points TEXT]... [--links JSON] [--aliases TEXT]...
```

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--subtype TEXT` | text | — | Optional subtype (e.g. `knowledge`, `decision`, or plugin-defined) |
| `--tags TEXT` | multiple | — | Tags (repeatable: `--tags ml/ai --tags research/papers`) |
| `--topic TEXT` | text | — | Topic directory under notes/ |
| `--body TEXT` | text | — | Markdown body |
| `--key-points TEXT` | multiple | — | Bullet-style summary items (repeatable) |
| `--links JSON` | json | — | Explicit edge map keyed by relation type |
| `--aliases TEXT` | multiple | — | Alternate names for search and linking (repeatable) |

### create reference

```bash
ztlctl create reference TITLE [--url TEXT] [--subtype TEXT] [--tags TEXT]... [--topic TEXT] [--body TEXT] [--summary TEXT]
```

### create task

```bash
ztlctl create task TITLE [--priority CHOICE] [--impact CHOICE] [--effort CHOICE] [--tags TEXT]...
```

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--priority` | choice | `medium` | `low`, `medium`, or `high` |
| `--impact` | choice | `medium` | `low`, `medium`, or `high` |
| `--effort` | choice | `medium` | `low`, `medium`, or `high` |
| `--tags TEXT` | multiple | — | Tags (repeatable) |

### create batch

```bash
ztlctl create batch FILE [--partial]
```

FILE must be a JSON array of objects, each with `type` and at minimum `title` keys.

### query search

```bash
ztlctl query search QUERY [--type CHOICE] [--tag TEXT] [--space CHOICE] [--rank-by CHOICE] [--limit INT]
```

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--type` | choice | — | `note`, `reference`, `task`, or `log` |
| `--tag TEXT` | text | — | Tag filter |
| `--space` | choice | — | `notes`, `ops`, or `self` |
| `--rank-by` | choice | `relevance` | See [Search Ranking Modes](#search-ranking-modes) |
| `--limit INT` | int | `20` | Maximum results |

### query list

```bash
ztlctl query list [--type CHOICE] [--status TEXT] [--tag TEXT] [--topic TEXT] [--subtype TEXT] [--maturity CHOICE] [--space CHOICE] [--since TEXT] [--include-archived] [--sort CHOICE] [--limit INT]
```

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--type` | choice | — | `note`, `reference`, `task`, or `log` |
| `--status TEXT` | text | — | Status filter |
| `--tag TEXT` | text | — | Tag filter |
| `--topic TEXT` | text | — | Topic filter |
| `--subtype TEXT` | text | — | Subtype filter |
| `--maturity` | choice | — | `seed`, `sprout`, or `evergreen` |
| `--space` | choice | — | `notes`, `ops`, or `self` |
| `--since TEXT` | text | — | Lower bound date (e.g. `2025-01-01`) |
| `--include-archived` | flag | false | Include archived items |
| `--sort` | choice | `recency` | `recency`, `title`, `type`, or `priority` |
| `--limit INT` | int | `20` | Maximum items |

### update

```bash
ztlctl update CONTENT_ID [--title TEXT] [--status TEXT] [--tags TEXT]... [--topic TEXT] [--body TEXT] [--maturity CHOICE]
```

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--title TEXT` | text | — | New title |
| `--status TEXT` | text | — | New status (must be a valid lifecycle transition) |
| `--tags TEXT` | multiple | — | Replace tags (repeatable) |
| `--topic TEXT` | text | — | New topic subdirectory |
| `--body TEXT` | text | — | New body text |
| `--maturity` | choice | — | `seed`, `budding`, or `evergreen` |

### reweave

```bash
ztlctl reweave run [--content-id TEXT] [--dry-run] [--min-score-override FLOAT]
ztlctl reweave prune [--content-id TEXT] [--dry-run]
ztlctl reweave undo [--reweave-id INT]
```

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--content-id TEXT` | text | — | Target item ID (omit to run across the vault) |
| `--dry-run` | flag | false | Preview without writing changes |
| `--min-score-override FLOAT` | float | — | Override minimum relevance threshold |

### check

```bash
ztlctl check check [--min-severity CHOICE]
ztlctl check fix [--level CHOICE]
ztlctl check rebuild
ztlctl check rollback
```

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--min-severity` | choice | `warning` | `info`, `warning`, or `error` |
| `--level` | choice | `safe` | `safe` or `aggressive` |

### session

```bash
ztlctl session start TOPIC
ztlctl session close [--summary TEXT]
ztlctl session reopen SESSION_ID
ztlctl session status
ztlctl session log MESSAGE [--pin] [--cost INT] [--detail TEXT]
ztlctl session cost [--report INT]
ztlctl session context [--topic TEXT] [--budget INT] [--ignore-checkpoints]
ztlctl session brief
ztlctl session extract SESSION_ID [--title TEXT]
```

### graph

```bash
ztlctl graph related CONTENT_ID [--depth INT] [--top INT]
ztlctl graph themes
ztlctl graph rank [--top INT]
ztlctl graph path SOURCE_ID TARGET_ID
ztlctl graph gaps [--top INT]
ztlctl graph bridges [--top INT]
ztlctl graph unlink SOURCE_ID TARGET_ID [--both]
ztlctl graph materialize
```

### export

```bash
ztlctl export markdown OUTPUT_DIR [--type CHOICE]
ztlctl export indexes OUTPUT_DIR [--type CHOICE]
ztlctl export graph [--format CHOICE] [--output FILE] [--type CHOICE]
ztlctl export dashboard OUTPUT_DIR [--viewer TEXT]
```

### docs

```bash
ztlctl docs search QUERY [--limit INT] [--json]
```

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--limit INT` | int | `5` | Maximum number of results |
| `--json` | flag | false | Output results as JSON |

The `docs search` command searches the bundled ztlctl documentation corpus using TF-IDF and returns page titles, scores, and excerpts. This is also available as the `docs_search` MCP tool for agent-driven documentation lookup.

### ingest

```bash
ztlctl ingest text TITLE [--target-type CHOICE] [--topic TEXT] [--tags TEXT]... [--summary TEXT] [--dry-run]
ztlctl ingest file PATH [--title TEXT] [--target-type CHOICE] [--topic TEXT] [--tags TEXT]... [--summary TEXT] [--dry-run]
ztlctl ingest url URL [--provider TEXT] [--title TEXT] [--target-type CHOICE] [--topic TEXT] [--tags TEXT]... [--summary TEXT] [--dry-run]
ztlctl ingest providers
```

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--target-type` | choice | — | `reference` or `note` |
| `--tags TEXT` | multiple | — | Tags (repeatable) |
| `--dry-run` | flag | false | Preview without writing |

## Search Ranking Modes

The `--rank-by` option on `query search` supports seven modes:

| Mode | Algorithm | Best For |
|------|-----------|----------|
| `relevance` | BM25 | General lexical search |
| `recency` | BM25 with time decay | Recent-but-relevant work |
| `graph` | BM25 x PageRank boost | Finding well-connected content |
| `semantic` | Vector similarity | Meaning-based retrieval |
| `hybrid` | BM25 + vector merge | Mixed lexical and semantic discovery |
| `review` | Enrichment rerank over search results | Stale, weakly connected, review-worthy items |
| `garden` | Enrichment rerank with provenance/maturity signals | Human-led enrichment and garden work |

Search results in `--json` mode include a `ranking` block with reasons and signal scores so agents can explain why an item surfaced.

## Query Filters

The `query list` command supports composable filters:

```bash
# Combine any of these:
ztlctl query list --type note|reference|task|log
ztlctl query list --status draft|linked|connected|inbox|active|done
ztlctl query list --tag "domain/scope"
ztlctl query list --topic "python"
ztlctl query list --subtype knowledge|decision|article|tool|spec
ztlctl query list --maturity seed|sprout|evergreen
ztlctl query list --space notes|ops|self
ztlctl query list --since 2025-01-01
ztlctl query list --include-archived
ztlctl query list --sort recency|title|type|priority
ztlctl query list --limit 50
```

## Ingestion

Use ingestion when the source material should be normalized into a durable artifact:

```bash
ztlctl ingest text "OAuth Notes" --target-type reference
ztlctl ingest file ./source.md --target-type note
ztlctl ingest providers
ztlctl ingest url https://example.com/spec --provider my-provider --target-type reference
```

URL ingestion is provider-backed. If no source provider is installed, `ingest url` returns `NO_PROVIDER` and suggests `ztlctl ingest providers`.

For richer agent-driven capture, the MCP `ingest_source` tool accepts a nested `source_bundle` object. ztlctl persists that bundle beside the created reference under `sources/<reference-id>/bundle.json` plus `sources/<reference-id>/normalized.md`.

Read `ztlctl://capture/spec` for the exact bundle contract.

## Topic Packets and Drafts

Use packets when you want a conversational bundle rather than a flat result list:

```bash
ztlctl query packet architecture --mode learn
ztlctl query packet architecture --mode review
ztlctl query packet architecture --mode decision
```

Packets include evidence excerpts, supporting/conflicting links, stale items, bridge candidates, suggested actions, and ranking explanations.

Use drafts when you want the next durable artifact sketched from the packet:

```bash
ztlctl query draft architecture --target note
ztlctl query draft architecture --mode review --target task
ztlctl query draft architecture --mode decision --target decision
```
