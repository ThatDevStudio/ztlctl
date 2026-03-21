---
title: Session recall
---

# Session recall

Session recall lets you query your session history by time window, topic keyword, or structural overlap between sessions. Use it to reload context from past work, find when you last explored a topic, or discover which sessions share a knowledge thread.

All three recall modes are available as CLI commands (`ztlctl session recall-*`) and as MCP tools for agent workflows.

## Temporal recall

Temporal recall returns sessions filtered by a date range. Each session in the result includes its ID, topic, status, start and end timestamps, log entry count, and the IDs of notes created during the session.

```bash
$ ztlctl session recall-temporal --from-date 2026-01-01 --to-date 2026-03-31
```

Both flags are optional. Omit `--from-date` for no lower bound; omit `--to-date` for no upper bound. Omit both to return all sessions ordered by most recent first.

```bash
# All sessions from the past week
$ ztlctl session recall-temporal --from-date 2026-03-14

# All sessions ever (no date filter)
$ ztlctl session recall-temporal
```

**Options:**

| Flag | Type | Description |
|------|------|-------------|
| `--from-date TEXT` | ISO date (YYYY-MM-DD) | Include sessions on or after this date |
| `--to-date TEXT` | ISO date (YYYY-MM-DD) | Include sessions on or before this date |

**Result fields per session:**

| Field | Description |
|-------|-------------|
| `session_id` | Vault ID of the session (e.g. `LOG-0001`) |
| `topic` | Session topic string |
| `status` | `active` or `closed` |
| `started` | ISO timestamp when the session was started |
| `ended` | ISO timestamp when the session was closed (null if still active) |
| `log_entry_count` | Number of log entries recorded in the session |
| `note_ids` | IDs of notes, references, and tasks created during the session |

## Topic recall

Topic recall searches session log entries by text and returns all sessions that contain matching entries. The search is case-insensitive and uses substring matching against the `summary` field of each log entry.

```bash
$ ztlctl session recall-topic "authentication"
```

The query argument is required and must be non-empty.

```bash
# Find sessions where authentication was discussed
$ ztlctl session recall-topic "authentication"

# Find sessions involving graph refactoring work
$ ztlctl session recall-topic "graph refactor"
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `QUERY` | Text to search for in session log entries (required) |

**Result fields per session:**

| Field | Description |
|-------|-------------|
| `session_id` | Vault ID of the matched session |
| `topic` | Session topic |
| `status` | `active` or `closed` |
| `matched_entries` | List of matching log entries: `{summary, timestamp, type}` |

!!! tip
    Use topic recall to quickly find the session where you last worked on something, then fetch the full session to reload its `note_ids` before continuing work.

## Topology recall

Topology recall finds pairs of sessions that share referenced notes or shared tags. It measures structural overlap between sessions rather than date or keyword, making it useful for discovering related work streams across different time periods.

```bash
$ ztlctl session recall-topology
```

By default, the top 10 most-overlapping pairs are returned. Use `--limit` to change this.

```bash
# Top 20 most-connected session pairs
$ ztlctl session recall-topology --limit 20
```

**Options:**

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--limit INTEGER` | int | `10` | Maximum number of session pairs to return |

**Result fields per pair:**

| Field | Description |
|-------|-------------|
| `session_a` | ID of the first session |
| `session_b` | ID of the second session |
| `shared_notes` | Note/reference/task IDs that both sessions referenced |
| `shared_tags` | Tags used by notes created in both sessions |

Pairs are ranked by total shared items (`shared_notes` + `shared_tags`) descending. Pairs with no shared content are excluded.

!!! note
    Topology recall requires at least two sessions to exist in the vault. If fewer than two sessions are present, the result is always an empty pairs list.

## MCP tools

All three recall modes are available as MCP tools. Use these in agent workflows where you need structured session history data.

| Tool | Side effect | When to use |
|------|------------|-------------|
| `recall_temporal` | read | Query session history by date range |
| `recall_topic` | read | Find past sessions by searching log content |
| `recall_topology` | read | Discover connections between sessions by shared content |

**`recall_temporal` parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `from_date` | string | no | ISO date (YYYY-MM-DD). Sessions on or after this date. Example: `2026-01-01` |
| `to_date` | string | no | ISO date (YYYY-MM-DD). Sessions on or before this date. Example: `2026-12-31` |

**`recall_topic` parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query` | string | yes | Text to search for in session log entries. Example: `authentication` |

**`recall_topology` parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `limit` | int | no | Maximum session pairs to return. Default: `10` |

### MCP resource: ztlctl://sessions/recent

The `ztlctl://sessions/recent` resource returns the last 5 sessions in a single read. This is the fastest way to get recent session context at the start of an agent workflow.

```json
{
  "sessions": [
    {
      "session_id": "LOG-0003",
      "topic": "Graph engine refactoring",
      "status": "closed",
      "started": "2026-03-20T14:00:00",
      "ended": "2026-03-20T16:30:00",
      "log_entry_count": 12,
      "note_ids": ["ZTL-0042", "ZTL-0043"]
    }
  ],
  "count": 1
}
```

Read this resource at the start of any session-based workflow before calling `session start` or `session context`.

## Agent workflow example

**Scenario:** An agent is beginning a new work session on a topic it worked on previously. It wants to load relevant context from prior sessions before starting.

**Step 1 — Read recent sessions resource:**

```
resource: ztlctl://sessions/recent
```

The agent inspects the last 5 sessions and identifies a relevant session ID (`LOG-0005`).

**Step 2 — Use temporal recall to retrieve the full week's sessions:**

```
tool: recall_temporal
args: { "from_date": "2026-03-14" }
```

The agent scans the result for sessions with `note_ids` that are worth loading before continuing.

**Step 3 — Use topic recall to find older sessions on the same topic:**

```
tool: recall_topic
args: { "query": "graph engine" }
```

The agent finds two older sessions with matching log entries and extracts the `note_ids` from each. It then fetches those notes using `get_document` to build a comprehensive context before creating new content.

**Step 4 — Start the new session:**

```
tool: start
args: { "topic": "Graph engine refactoring — part 2" }
```

!!! tip
    Combine `recall_topic` with `get_document` to reconstruct the full knowledge context from a past session. The `note_ids` field in each session result gives you the exact IDs to fetch.

## Configuration

Session recall does not have dedicated configuration options. It reads from the session log data written by `session start`, `session log`, and `session close` commands.

To ensure good recall coverage, log work entries during active sessions:

```bash
$ ztlctl session log "Refactored graph proximity scoring for BM25 pipeline"
$ ztlctl session log "Reviewed ZTL-0042 — updating maturity to evergreen"
```

The richer the log, the more precise `recall_topic` results will be.

## What's next

- [Agentic Workflows](agentic-workflows.md) — orchestration patterns that use session recall for context assembly
- [Core Concepts](concepts.md) — how sessions fit into the zettelkasten lifecycle
- [Command Reference](commands.md) — complete CLI reference for all session commands
