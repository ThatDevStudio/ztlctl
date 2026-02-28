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
| `garden seed TITLE` | Quick-capture seed note |
| `serve` | Start MCP server |
| `upgrade` | Run database migrations |
| `vector status` | Check semantic search availability |
| `vector reindex` | Rebuild the vector index |
| `workflow init` | Initialize workflow scaffolding |
| `workflow update` | Update workflow scaffolding |

## Search Ranking Modes

The `--rank-by` option on `query search` supports three modes:

| Mode | Algorithm | Best For |
|------|-----------|----------|
| `relevance` | BM25 with time decay | General search |
| `recency` | Modified date descending | Finding recent work |
| `graph` | BM25 x PageRank boost | Finding well-connected content |

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
