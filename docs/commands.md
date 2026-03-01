---
title: Command Reference
nav_order: 6
---

# Command Reference

## Global Options

Every command supports these flags:

| Flag | Description |
|------|-------------|
| `--version` | Show version and exit |
| `--json` | Structured JSON output (for scripting and agents) |
| `-q, --quiet` | Minimal output |
| `-v, --verbose` | Detailed output with debug info |
| `--log-json` | Structured JSON log output to stderr |
| `--no-interact` | Non-interactive mode (no prompts) |
| `--no-reweave` | Skip automatic reweave on creation |
| `-c, --config TEXT` | Override config file path |
| `--sync` | Force synchronous event dispatch |

Most commands also support `--examples` to show usage examples.

## Commands at a Glance

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
| `query packet` | Topic-scoped learning/review packet |
| `query draft` | Draft a note, task, or decision from a topic packet |
| `graph related ID` | Find related content |
| `graph themes` | Discover topic clusters |
| `graph rank` | PageRank importance |
| `graph path SRC DST` | Shortest path between nodes |
| `graph gaps` | Find structural holes |
| `graph bridges` | Find bridge nodes |
| `graph unlink SRC DST` | Remove link between two nodes |
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
| `export dashboard` | Export dashboard note, review queues, and topic dossier artifacts |
| `garden seed TITLE` | Quick-capture seed note |
| `ingest text TITLE` | Ingest raw text into a note or reference |
| `ingest file PATH` | Ingest a markdown or text file |
| `ingest url URL` | Ingest a URL through an installed source provider |
| `ingest providers` | List installed source providers |
| `serve` | Start MCP server |
| `upgrade` | Run database migrations |
| `vector status` | Check semantic search availability |
| `vector reindex` | Rebuild the vector index |
| `workflow init` | Initialize workflow scaffolding |
| `workflow update` | Update workflow scaffolding |
| `workflow export` | Export agent workflow assets (Claude/Codex) |
| `workflow validate` | Validate exported workflow assets |

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

Search results in JSON mode now include a `ranking` block with reasons and signal scores so agents can explain why an item surfaced.

## Query Filters

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

## Ingestion

Use ingestion when the source material should be normalized into a durable artifact:

```bash
ztlctl ingest text "OAuth Notes" --stdin --as reference
ztlctl ingest file ./source.md --as note
ztlctl ingest providers
ztlctl ingest url https://example.com/spec --provider my-provider --as reference
```

URL ingestion is provider-backed. If no source provider is installed, `ingest url` returns `NO_PROVIDER` and suggests `ztlctl ingest providers`.

For richer agent-driven capture, the MCP `ingest_source` tool accepts a nested `source_bundle` object. ztlctl persists that bundle beside the created reference under `sources/<reference-id>/bundle.json` plus `sources/<reference-id>/normalized.md`.

Read `ztlctl://capture/spec` for the exact bundle contract. The older flat evidence-envelope fields (`source_kind`, `modalities`, `capture_agent`, `capture_method`, `citations`, `excerpts`, and `artifacts`) still work, but ztlctl now lifts them into the durable source bundle format internally.

## Topic Packets and Drafts

Use packets when you want a conversational bundle rather than a flat result list:

```bash
ztlctl query packet --topic architecture --mode learn
ztlctl query packet --topic architecture --mode review
ztlctl query packet --topic architecture --mode decision
```

Packets now include evidence excerpts, supporting/conflicting links, stale items, bridge candidates, suggested actions, and ranking explanations.

Packets also merge topic-scoped items with search-ranked items, so topic-tagged references and notes still surface even when the topic string is not a strong lexical match.

Use drafts when you want the next durable artifact sketched from the packet:

```bash
ztlctl query draft --topic architecture --target note
ztlctl query draft --topic architecture --mode review --target task
ztlctl query draft --topic architecture --mode decision --target decision
```
