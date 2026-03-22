---
title: Agent System Manual
---

# Agent System Manual

> This page is for LLM systems consuming ztlctl via MCP or CLI. For human-readable workflow guides, see [Agentic Workflows](agentic-workflows.md).

All schemas, states, and constraints on this page are verified against source code. Use structured access patterns; do not infer behavior from names alone.

---

## System Capabilities

| Category | Capability | CLI | MCP Tool |
|----------|-----------|-----|----------|
| Discovery | List available tools by category | `ztlctl --help` | `discover_tools` |
| Discovery | Describe a specific tool contract | `ztlctl <cmd> --help` | `describe_tool` |
| Discovery | List all registered tags | `ztlctl query list --type tag` | `list_tags` |
| Discovery | List installed source providers | — | `list_source_providers` |
| Creation | Create note | `ztlctl create note` | `create_note` |
| Creation | Create reference | `ztlctl create reference` | `create_reference` |
| Creation | Create task | `ztlctl create task` | `create_task` |
| Creation | Create garden seed | `ztlctl garden seed` | `garden_seed` |
| Creation | Ingest text/file/URL source | `ztlctl ingest text\|file\|url` | `ingest_source` |
| Lifecycle | Update metadata | `ztlctl update <id>` | `update_content` |
| Lifecycle | Close/archive content | `ztlctl archive <id>` | `close_content` |
| Lifecycle | Discover and apply links | `ztlctl reweave` | `reweave` |
| Query | Full-text search | `ztlctl query search` | `search` |
| Query | Get single document | `ztlctl query get <id>` | `get_document` |
| Query | List with filters | `ztlctl query list` | `list_items` |
| Query | Prioritized work queue | `ztlctl query work-queue` | `work_queue` |
| Query | Topic learning/review/decision packet | `ztlctl query packet` | `topic_packet` |
| Query | Draft from topic packet | `ztlctl query draft` | `draft_from_topic` |
| Query | Agent context assembly | `ztlctl agent context` | `agent_context` |
| Analysis | Decision support aggregate | `ztlctl query decision-support` | `decision_support` |
| Analysis | Vault review snapshot | — | `vault_review` |
| Graph | Find related content | `ztlctl graph related <id>` | `get_related` |
| Graph | Discover topic clusters | `ztlctl graph themes` | `graph_themes` |
| Graph | PageRank-ordered nodes | `ztlctl graph rank` | `graph_rank` |
| Graph | Shortest path between nodes | `ztlctl graph path <a> <b>` | `graph_path` |
| Graph | Orphan/gap detection | `ztlctl graph gaps` | `graph_gaps` |
| Graph | Bridge node detection | `ztlctl graph bridges` | `graph_bridges` |
| Session | Start session | `ztlctl agent session start` | `session_start` |
| Session | Close session + enrichment | `ztlctl agent session close` | `session_close` |
| Session | Query session status | `ztlctl agent session status` | `session_status` |
| Session | Log reasoning entry | `ztlctl agent session log` | — |
| Recall | Query session history by date range | `ztlctl session recall-temporal [--from-date DATE] [--to-date DATE]` | `recall_temporal` |
| Recall | Find sessions by log content | `ztlctl session recall-topic QUERY` | `recall_topic` |
| Recall | Discover sessions connected by shared content | `ztlctl session recall-topology [--limit N]` | `recall_topology` |
| Analysis | Find candidate contradicting note pairs | `ztlctl check contradictions` | `check_contradictions` |
| Analysis | Confirm a contradiction as a graph edge | `ztlctl check confirm-contradiction NOTE_A NOTE_B` | `confirm_contradiction` |
| Check | Check decision against polaris alignment | `ztlctl check alignment --decision TEXT` | `check_alignment` |
| Ingest | Ingest audio, video, or transcript file | `ztlctl ingest media PATH` | `ingest_media` |
| Export | Markdown export | `ztlctl export markdown` | — |
| Export | Graph export (dot/json) | `ztlctl export graph` | — |
| Export | Review dashboard | `ztlctl export dashboard` | — |
| Check | Vault integrity scan | `ztlctl check` | — |
| Check | Auto-fix issues | `ztlctl check --fix` | — |
| Check | Full rebuild from files | `ztlctl check --rebuild` | — |

---

## Entity Schemas

### Note

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `title` | `str` | Yes | 3–200 chars | Unique display title |
| `content_type` | `str` | Yes | `"note"` | Fixed; cannot change post-creation |
| `subtype` | `str` | No | `knowledge` \| `decision` \| `None` | Subtype affects lifecycle rules |
| `tags` | `list[str]` | No | `domain/scope` format recommended | Bare tags work but emit warning |
| `topic` | `str` | No | Must match a vault topic directory | Routing prefix for context assembly |
| `maturity` | `str` | No | `seed` \| `budding` \| `evergreen` | Garden lifecycle; human-advisory |
| `body` | `str` | No | Markdown | Content body |
| `key_points` | `list[str]` | No | — | Structured summary bullets |
| `links` | `dict[str, list[str]]` | No | Wikilink titles `[[Title]]` | Explicit outgoing link map |
| `aliases` | `list[str]` | No | — | Alternative lookup names |
| `session` | `str` | No | Must be a `LOG-NNNN` of an open session | Associates note with session |

**Computed fields (read-only):**

| Field | Type | Description |
|-------|------|-------------|
| `id` | `str` | `ztl_<8-char hash>` |
| `status` | `str` | `draft` \| `linked` \| `connected` — computed from outgoing link count |
| `created_at` | `str` | ISO 8601 timestamp |
| `modified_at` | `str` | ISO 8601 timestamp |

### Reference

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `title` | `str` | Yes | 3–200 chars | Unique display title |
| `content_type` | `str` | Yes | `"reference"` | Fixed; cannot change post-creation |
| `subtype` | `str` | No | `article` \| `tool` \| `spec` | Classification (no lifecycle enforcement) |
| `url` | `str` | No | Valid URL | Source location |
| `tags` | `list[str]` | No | `domain/scope` format recommended | — |
| `topic` | `str` | No | Must match a vault topic directory | — |
| `body` | `str` | No | Markdown | Annotation or excerpt |
| `session` | `str` | No | Must be a `LOG-NNNN` of an open session | — |

**Computed fields:**

| Field | Type | Description |
|-------|------|-------------|
| `id` | `str` | `ref_<8-char hash>` |
| `status` | `str` | `captured` \| `annotated` — computed from annotation presence |

### Task

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `title` | `str` | Yes | 3–200 chars | Unique display title |
| `content_type` | `str` | Yes | `"task"` | Fixed |
| `priority` | `str` | No | `low` \| `medium` \| `high` | Work queue scoring signal |
| `impact` | `str` | No | `low` \| `medium` \| `high` | Work queue scoring signal |
| `effort` | `str` | No | `low` \| `medium` \| `high` | Work queue scoring signal |
| `tags` | `list[str]` | No | `domain/scope` format | — |

**Computed fields:**

| Field | Type | Description |
|-------|------|-------------|
| `id` | `str` | `TASK-NNNN` (sequential) |
| `status` | `str` | `inbox` \| `active` \| `blocked` \| `done` \| `dropped` |
| `score` | `float` | `priority × impact / effort` — work queue ordering |

### Session Log

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `topic` | `str` | Yes | Free text | Session focus topic |
| `summary` | `str` | No (at close) | Free text | Close summary |

**Computed fields:**

| Field | Type | Description |
|-------|------|-------------|
| `id` | `str` | `LOG-NNNN` (sequential) |
| `status` | `str` | `open` \| `closed` |
| `created_at` | `str` | Session start timestamp |

---

## Lifecycle State Machines

All status transitions are enforced. Invalid transitions return `ServiceResult(success=False)`.

### Note Status

Status is computed from outgoing link count — not settable directly via update.

```
             (0 outgoing links)
                    |
                  DRAFT
                    |
           (>= 1 outgoing link)
                    |
                 LINKED
                    |
           (>= 3 outgoing links)
                    |
               CONNECTED
```

**Thresholds (from `domain/lifecycle.py`):**
- `draft` → `linked`: requires 1+ outgoing links
- `linked` → `connected`: requires 3+ outgoing links

### Note Decision Subtype Status

```
PROPOSED ──> ACCEPTED ──> SUPERSEDED
```

Trigger `proposed → accepted` via `ztlctl update <id> --status accepted`.
Trigger `accepted → superseded` via `ztlctl supersede <old_id> <new_id>`.

### Reference Status

```
CAPTURED ──> ANNOTATED
```

Status advances when the reference body field is populated.

### Task Status

```
        INBOX
       /     \
    ACTIVE  DROPPED
   /      \
BLOCKED   DONE
   \
  ACTIVE (return from blocked)
   \
  DROPPED
```

Valid transitions:
- `inbox → active`, `inbox → dropped`
- `active → blocked`, `active → done`, `active → dropped`
- `blocked → active`, `blocked → dropped`
- `done →` (terminal)
- `dropped →` (terminal)

### Session Log Status

```
OPEN <──> CLOSED
```

Sessions are reopenable. Only one session may be `open` at a time (enforced server-side).

### Garden Maturity

Advisory only — not enforced by the engine. Human-driven via `ztlctl update --maturity`.

```
SEED ──> BUDDING ──> EVERGREEN
```

---

## Constraint Rules

These are hard constraints enforced by service layer and domain rules:

1. **Content type is immutable.** `content_type` cannot be changed after creation.
2. **One open session at a time.** `session_start` returns an error if a session with `status=open` already exists.
3. **Session must exist before session-close.** `session_close` requires a `LOG-NNNN` with `status=open`.
4. **Note status is computed, not settable.** `update --status linked` is rejected for notes — status derives from outgoing link count.
5. **Decision note subtype status uses a separate machine.** Decision notes (`subtype=decision`) use `proposed/accepted/superseded`, not the note link-count machine.
6. **Decision notes are excluded from auto-reweave.** The Reweave plugin skips `subtype=decision` to protect decision integrity. Call `ztlctl reweave --id <id>` manually to link a decision note.
7. **Tags should use `domain/scope` format.** Bare tags (e.g., `python`) are accepted but emit a warning and cannot be filtered with domain-prefix queries.
8. **Task scoring signals are optional but influence queue ordering.** Omitting `priority`, `impact`, or `effort` reduces work queue signal quality.
9. **Batch mode requires session close to commit.** With `[plugins.git] batch_commits = true`, file changes are staged but not committed until `session_close`.
10. **`check --rebuild` reconstructs durable content only.** Session rows, event WAL, and generated `self/` files are not part of the file-first guarantee and are not rebuilt.
11. **Semantic search requires sqlite-vec extension.** `ztlctl vector search` and `[search] semantic_enabled = true` require the sqlite-vec Python package.
12. **Garden maturity `evergreen` requires 5+ key points and 3+ bidirectional links** (configurable via `[garden]` section).

---

## Deterministic Interaction Flows

### Research Capture Flow

Purpose: Capture external sources and synthesize findings into linked notes.

```
Step 1: Start session
  CLI: ztlctl agent session start "Research: {topic}" --json
  MCP: session_start(topic="{topic}")
  → Returns: {"id": "LOG-NNNN", "status": "open"}

Step 2: Orient to existing knowledge
  CLI: ztlctl agent context --topic "{topic}" --budget 4000 --json
  MCP: agent_context(topic="{topic}", budget=4000)
  → Returns: 5-layer context payload

Step 3: Ingest source material
  CLI: ztlctl ingest text "{title}" --stdin --as reference --tags "{tag}" --json
  MCP: ingest_source(title="{title}", content="{text}", as_type="reference", tags=["{tag}"])
  → Returns: {"id": "ref_XXXXXXXX", "status": "captured"}

Step 4: Create synthesis note
  CLI: ztlctl create note "{title}" --tags "{tag}" --session LOG-NNNN --json
  MCP: create_note(title="{title}", tags=["{tag}"], session="LOG-NNNN")
  → Returns: {"id": "ztl_XXXXXXXX", "status": "draft", "reweave_suggestions": [...]}
  Note: Reweave plugin fires automatically for notes/references

Step 5: Log key insights
  CLI: ztlctl agent session log "{insight}" --pin --json
  MCP: (no direct MCP equivalent — use CLI or session log entry via create_log)

Step 6: Close session
  CLI: ztlctl agent session close --summary "{summary}" --json
  MCP: session_close(summary="{summary}")
  → Returns: {"reweave_count": N, "orphan_count": N, "integrity_issues": N}
```

### Knowledge Retrieval Flow

Purpose: Retrieve structured context for a topic before reasoning or creating.

```
Step 1: Search existing content
  CLI: ztlctl query search "{query}" --rank-by relevance --json
  MCP: search(query="{query}", rank_by="relevance", limit=10)
  → Returns: list of matching items with scores

Step 2 (optional): Get topic packet for richer context
  CLI: ztlctl query packet --topic "{topic}" --mode learn --json
  MCP: topic_packet(topic="{topic}", mode="learn")
  → Returns: notes, references, decisions, graph neighbors, bridge candidates

Step 3 (optional): Get graph neighbors
  CLI: ztlctl graph related {id} --depth 2 --top 10 --json
  MCP: get_related(content_id="{id}", depth=2, top=10)
  → Returns: spread-activated related items with distance scores

Step 4 (optional): Draft from topic packet
  CLI: ztlctl query draft --topic "{topic}" --target note --json
  MCP: draft_from_topic(topic="{topic}", target="note")
  → Returns: draft payload (does NOT write to vault — caller decides to create)
```

### Session Management Flow

Purpose: Start, track, and close a bounded work session.

```
Step 1: Check session status before starting
  CLI: ztlctl agent session status --json
  MCP: session_status()
  → Returns: {"active": false} or {"active": true, "session_id": "LOG-NNNN"}

Step 2: Start session (only if no active session)
  CLI: ztlctl agent session start "{topic}" --json
  MCP: session_start(topic="{topic}")
  Constraint: Fails if a session is already open

Step 3: Do work (create notes/references, log reasoning)

Step 4: Check token budget
  CLI: ztlctl agent session cost --report {token_budget} --json
  → Returns: token usage per layer, pressure status

Step 5: Close session
  CLI: ztlctl agent session close --summary "{summary}" --json
  MCP: session_close(summary="{summary}")
  → Triggers: reweave → orphan sweep → integrity check → graph materialization
```

### Recall Flow

Purpose: Load context from past sessions before starting new work on a recurring topic.

```
Step 1: Read recent sessions resource
  MCP resource: ztlctl://sessions/recent
  → Returns: last 5 sessions with topics, timestamps, and note_ids

Step 2: Temporal recall for a broader date window
  CLI: ztlctl session recall-temporal --from-date {date} --json
  MCP: recall_temporal(from_date="{date}")
  → Returns: sessions in range with log_entry_count and note_ids

Step 3: Topic recall to find sessions by content
  CLI: ztlctl session recall-topic "{query}" --json
  MCP: recall_topic(query="{query}")
  → Returns: sessions with matching log entries and matched_entries

Step 4: Fetch notes from recalled sessions
  CLI: ztlctl query get {note_id} --json  (repeat per note_id from session results)
  MCP: get_document(content_id="{note_id}")
  → Returns: full note content for context loading

Step 5 (optional): Topology recall to discover related work streams
  CLI: ztlctl session recall-topology --limit 10 --json
  MCP: recall_topology(limit=10)
  → Returns: session pairs with shared_notes and shared_tags
```

---

## Input/Output Schemas

### Create Note — Request

```json
{
  "title": "string (required, 3-200 chars)",
  "content_type": "note",
  "subtype": "knowledge | decision | null",
  "tags": ["domain/scope"],
  "topic": "string (vault topic directory name)",
  "maturity": "seed | budding | evergreen",
  "body": "string (markdown)",
  "key_points": ["string"],
  "links": {"outgoing": ["[[Target Title]]"]},
  "aliases": ["string"],
  "session": "LOG-NNNN"
}
```

### Create Note — Response

```json
{
  "success": true,
  "data": {
    "id": "ztl_a1b2c3d4",
    "title": "string",
    "content_type": "note",
    "status": "draft",
    "created_at": "2026-01-01T00:00:00Z"
  },
  "meta": {
    "reweave_suggestions": [
      {"id": "ztl_e5f6g7h8", "title": "string", "score": 0.74}
    ]
  }
}
```

### Search — Request

```json
{
  "query": "string (required)",
  "rank_by": "relevance | recency | graph | review | garden",
  "content_type": "note | reference | task | log | null",
  "limit": 10,
  "tags": ["domain/scope"]
}
```

### Search — Response

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "ztl_a1b2c3d4",
        "title": "string",
        "content_type": "note",
        "status": "linked",
        "score": 0.87,
        "tags": ["lang/python"]
      }
    ],
    "total": 42
  }
}
```

### Session Close — Response

```json
{
  "success": true,
  "data": {
    "session_id": "LOG-NNNN",
    "status": "closed",
    "reweave_count": 7,
    "orphan_count": 2,
    "integrity_issues": 0
  }
}
```

### ServiceResult Envelope (all operations)

```json
{
  "success": true | false,
  "data": {},
  "error": {
    "message": "string",
    "code": "string",
    "recovery": "string — corrective action hint"
  },
  "meta": {}
}
```

`error` is present only when `success` is `false`. `meta` contains operation-specific context (e.g., reweave suggestions, telemetry spans). Always check `success` before consuming `data`.

---

## Error Handling

| Error Condition | CLI Exit Code | `error.message` Pattern | `error.recovery` Hint |
|----------------|--------------|------------------------|----------------------|
| Vault not initialized | 1 | `"Vault not initialized"` | `"Run ztlctl init"` |
| Note/reference not found | 1 | `"Content {id} not found"` | `"Verify ID format: ztl_/ref_/TASK-/LOG-"` |
| Session already open | 1 | `"Session already open"` | `"Close existing session first"` |
| No active session | 1 | `"No open session"` | `"Run ztlctl agent session start"` |
| Invalid content type | 1 | `"Invalid content type"` | `"Use: note, reference, task"` |
| Invalid status transition | 1 | `"Invalid transition"` | `"Check allowed transitions for content type"` |
| Title too short | 1 | `"Title must be 3+ chars"` | `"Provide a longer title"` |
| Duplicate title | 1 | `"Title already exists"` | `"Use a unique title or update existing"` |
| Semantic search unavailable | 1 | `"sqlite-vec not installed"` | `"pip install sqlite-vec"` |
| Config not found | 1 | `"ztlctl.toml not found"` | `"Run ztlctl init or cd to vault root"` |
| No contradiction candidates | 1 | `"No contradiction candidates"` | `"Add more notes or enable semantic search"` |
| Media file not found | 1 | `"File not found"` | `"Check file path"` |
| Transcription unavailable | 1 | `"faster-whisper not installed"` | `"uv add --group media faster-whisper"` |
| Polaris not found | 1 | `"Polaris document not found"` | `"Run ztlctl init or create garden/groves/polaris.md"` |
| No session history | 1 | `"No sessions found"` | `"Start a session first"` |

**Retry guidance:**

- Exit code 0: Success — proceed.
- Exit code 1, `recovery` present: Apply recovery hint, then retry once.
- Exit code 1, no `recovery`: Structural problem — do not retry without human input.
- Exit code 2: CLI usage error (bad flag/argument) — fix the call, do not retry as-is.

---

## MCP Discovery Protocol

The recommended onboarding sequence for any MCP client:

```
1. discover_tools(category="all")
   → Returns categorized tool list with one-line descriptions

2. describe_tool(name="{tool_name}")
   → Returns full parameter schema, examples, and return contract

3. ztlctl://agent-reference   (read resource)
   → Returns onboarding payload: tool guidance, workflow examples, vault orientation
```

For ongoing operation, use read resources to avoid tool calls for static context:

| Resource URI | Content |
|-------------|---------|
| `ztlctl://self/identity` | Vault identity and agent personality |
| `ztlctl://self/methodology` | Vault methodology and workflow guidance |
| `ztlctl://overview` | Vault statistics and content counts |
| `ztlctl://work-queue` | Prioritized task list |
| `ztlctl://decision-queue` | Recent decisions + active work queue |
| `ztlctl://garden/backlog` | Stale seeds and orphan notes |
| `ztlctl://capture/spec` | Source bundle contract for ingest handoff |
| `ztlctl://agent-reference` | Full agent onboarding payload |
| `ztlctl://polaris` | Vault strategic priorities document |
| `ztlctl://sessions/recent` | Recent session summaries for recall |
| `ztlctl://review/contradictions` | Contradiction candidate pairs for review |

See [MCP Server](mcp.md) for the complete tool catalog, resource list, and prompt library.
