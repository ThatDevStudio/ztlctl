---
title: Agentic Workflows
---

# Agentic Workflows

ztlctl is designed for agent-assisted capture and synthesis. Every command supports `--json`, sessions provide operational coordination, and topic packets provide read-oriented retrieval even when no session is active.

## Capture and Synthesis Workflow

Sessions are operational coordination state, not durable authored knowledge. Use them to structure research work, then turn findings into notes, references, and tasks:

```bash
# Agent starts a focused research session
ztlctl session start "API design patterns" --json

# Agent captures sources and synthesis
ztlctl ingest text "API source notes" --target-type reference --json
ztlctl create note "REST vs GraphQL trade-offs" \
  --tags architecture/api --json

# Agent logs its reasoning and costs
ztlctl session log "Analyzed 5 API frameworks" --cost 1200 --json
ztlctl session log "Key insight: GraphQL better for nested data" --pin --json

# Agent checks token budget
ztlctl session cost --report 50000 --json

# Agent requests context for continued work
ztlctl session context --topic "api" --budget 4000 --json

# Agent closes session, triggering capture/synthesis cleanup
ztlctl session close --summary "Mapped API paradigms" --json
```

## Ingestion

Core ingestion is text-first:

- raw text via `ztlctl ingest text`
- markdown and plain text files via `ztlctl ingest file`
- URLs via `ztlctl ingest url`, but only when a source-provider plugin is installed

```bash
ztlctl ingest text "OAuth notes" --target-type reference --json
ztlctl ingest file ./source.md --target-type note --json
ztlctl ingest providers --json
```

URL ingestion is provider-backed by design. The core tool does not ship a built-in remote fetcher in the base install.

## Media ingestion

Audio, video, and transcript files are ingested via `ztlctl ingest media`. ztlctl transcribes audio and video locally using faster-whisper (no data leaves your machine) and parses pre-existing transcript files without any external dependency:

```bash
$ ztlctl ingest media recordings/interview.mp3 \
    --title "Interview: distributed systems patterns" \
    --topic research --tags podcast
$ ztlctl ingest media captions.vtt --title "Conference talk: CRDT internals"
$ ztlctl ingest media lecture.mp4 --dry-run
```

Every ingest call creates a `captured` reference — raw material for human or agent review. Use `ztlctl query work-queue` to surface newly captured media references waiting for annotation.

!!! note
    Audio and video transcription requires the optional `faster-whisper` package (`uv add --group media faster-whisper`). Transcript files (`.txt`, `.vtt`, `.srt`) work without it.

For the full CLI reference, supported formats, and configuration options, see [Media ingestion](media-ingestion.md).

For agent-fetched web and multimodal workflows, use a bundle-first handoff:

1. Fetch or extract the source outside ztlctl.
2. Normalize the capture into plain text plus a nested `source_bundle`.
3. Call MCP `ingest_source` with `content=<normalized text>` and `source_bundle=<bundle>`.
4. Let ztlctl persist the bundle beside the ingested reference under `sources/<reference-id>/`.

Read `ztlctl://capture/spec` for the exact bundle contract. The flat evidence-envelope fields (`source_kind`, `modalities`, `capture_agent`, `capture_method`, `citations`, `excerpts`, and `artifacts`) still work, but ztlctl now normalizes them into the durable source bundle format internally.

## Context Assembly (5-Layer System)

The `session context` command builds a token-budgeted payload with 5 layers:

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
ztlctl session context --json

# Focus on a topic with custom budget
ztlctl session context --topic "architecture" --budget 4000 --json

# Quick orientation (no session required)
ztlctl session brief --json
```

## Topic Packets

Use topic packets when you want conversational retrieval without depending on an active session:

```bash
ztlctl query packet architecture --mode learn --json
ztlctl query packet architecture --mode review --json
ztlctl query packet architecture --mode decision --json
```

Packets combine topic-matched notes, references, decisions, tasks, graph-adjacent material, evidence excerpts, supporting/conflicting links, stale items, bridge candidates, suggested actions, ranking explanations, and provenance maps so an agent can continue reasoning from captured knowledge rather than only from recent session state.

Packets merge topic-scoped items with search-ranked items, so a reference tagged to a topic is still available for review and learning even when its title/body is a weak lexical match for the topic string itself.

When a packet should become durable work, draft from it directly:

```bash
ztlctl query draft architecture --target note --json
ztlctl query draft architecture --mode review --target task --json
ztlctl query draft architecture --mode decision --target decision --json
```

For a portable human review surface outside the vault, use `ztlctl export dashboard ./output/ --viewer obsidian`. That export is an external review workbench for machine-layer queues, stale/orphan signals, and topic dossiers; it complements `garden/` but does not write into the vault or mirror `.obsidian/` state.

## Session Close Enrichment Pipeline

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

## Decision Extraction

Extract decisions from session logs into permanent decision notes:

```bash
# Extracts pinned/decision entries from the session log
ztlctl session extract LOG-0001 --title "Decision: Use GraphQL for nested queries"
```

This creates a decision note (`subtype=decision`, status `proposed`) linked to the session via a `derived_from` edge.

## MCP Server Integration

ztlctl includes a Model Context Protocol (MCP) server for direct integration with AI clients like Claude Desktop and Codex-compatible environments:

```bash
ztlctl serve --transport stdio
```

Use the discovery flow in MCP clients:

1. `discover_categories`
2. `activate_category` (for non-core categories)
3. `ztlctl://agent-reference`

For enrichment-focused agents, the most useful read resources are:

- `ztlctl://review/dashboard`
- `ztlctl://garden/backlog`
- `ztlctl://decision-queue`
- `ztlctl://capture/spec`
- `ztlctl://polaris` — vault strategic priorities (see [Polaris priorities](polaris.md))
- `ztlctl://sessions/recent` — recent session summaries for recall (see [Session recall](session-recall.md))
- `ztlctl://review/contradictions` — contradiction candidate pairs for agent review (see [Contradiction detection](contradiction-detection.md))

The MCP prompt layer includes `topic_learn`, `topic_review`, `topic_decision`, `capture_web_source`, and `capture_multimodal_source`.

See the [MCP Server](mcp.md) page for tool categories, resources, prompts, and exported client assets.

## v3.0 agent recipes

These recipes use v3.0 capabilities — polaris alignment, session recall, and contradiction review. They complement the existing walkthroughs below.

### Polaris-aligned session startup

An agent reads the vault's polaris priorities before opening a session, then checks alignment before creating any significant content. This keeps all creation anchored to the vault's current strategic focus.

```
1. Read ztlctl://polaris
   → Understand the vault's mission, priorities, and decision principles.

2. check_alignment(decision="Open research session on {topic}")
   → Verify the session topic is on-strategy before proceeding.

3. start(topic="{topic}")
   → Open the session, now grounded in polaris context.
```

See [Polaris priorities](polaris.md) for the alignment check workflow and context assembly integration.

### Recall-driven context loading

Before starting a new session on a recurring topic, an agent loads prior session context to avoid re-doing work and to pick up where it left off.

```
1. Read ztlctl://sessions/recent
   → Identify relevant past sessions from the last 5 entries.

2. recall_temporal(from_date="YYYY-MM-DD")
   → Expand the date range to surface older sessions if needed.

3. recall_topic(query="{topic keywords}")
   → Find sessions whose log entries mention the current topic.

4. get_document(content_id="{note_id}")  # repeat per note_id from recalled sessions
   → Fetch the actual notes created during past sessions to rebuild context.

5. start(topic="{topic} — continued")
   → Open the new session with full historical context loaded.
```

See [Session recall](session-recall.md) for the complete recall workflow and MCP tool reference.

### Contradiction review workflow

An agent reviews the vault for conflicting claims and confirms genuine contradictions as permanent graph edges.

```
1. Read ztlctl://review/contradictions
   → Fetch all scored contradiction candidate pairs.

2. get_document(content_id="{note_a}")
   get_document(content_id="{note_b}")
   → Read both notes' full content and key_points for each candidate pair.

3. Evaluate: do the notes genuinely contradict each other?
   → Check the signals field (cosine_similarity, negation_density, key_points_divergence).

4. confirm_contradiction(note_a="{note_a}", note_b="{note_b}")  # only for genuine contradictions
   → Insert bidirectional contradicts edges into the knowledge graph.
```

See [Contradiction detection](contradiction-detection.md) for scoring details and the full MCP tool reference.

## Recipe Walkthroughs

ztlctl exposes three structured workflow recipes via MCP. Each recipe is a sequence of tool calls that accomplishes a common knowledge-work task. Recipes are designed for agent-driven execution but every step has a human CLI equivalent.

Access recipes via MCP resource discovery:

```bash
# Discover available recipes
ztlctl://recipes
```

Or access individual recipe specs directly in your MCP client:

- `ztlctl://recipes/research-capture`
- `ztlctl://recipes/review-triage`
- `ztlctl://recipes/knowledge-synthesis`

### Recipe 1: Research Capture

**What it accomplishes:** Search existing knowledge for a topic, create a synthesis note for new findings, and automatically connect it to related content via reweave.

**When to use:** When an agent (or you) has gathered research on a topic and wants to turn it into a durable knowledge artifact linked to existing context.

**Steps:**

| Step | Action | Condition |
|------|--------|-----------|
| 1 | Search existing content for the topic (limit 10) | Always |
| 2 | Create a seed note with the synthesis title | Skip if step 1 already has a note with the same title |
| 3 | Reweave the new note against existing content | Always |

**Human CLI walkthrough:**

```bash
# Step 1: Check if you already have related content
ztlctl query search "oauth security" --limit 10

# Expected output (if no related notes yet):
# No results for "oauth security"

# Step 2: Create a synthesis note
ztlctl create note "OAuth Security Patterns" --tags auth/oauth --tags security

# Expected output:
# Created note ZTL-0042: OAuth Security Patterns [seed]
# Reweave: 3 links created (auto-triggered by Reweave plugin)

# Step 3: Manual reweave if needed (already ran automatically above)
# ztlctl reweave run --content-id ZTL-0042
```

!!! tip
    The Reweave plugin runs automatically after `create note`, so step 3 is already done for you. Run `ztlctl reweave run --content-id {id}` manually only if you disabled auto-reweave or want to re-run after adding more related content. See [Built-in Plugins](plugins.md) for Reweave configuration.

**Agent MCP tool sequence:**

```
1. search(query="oauth security", limit=10)
2. create_note(title="OAuth Security Patterns", tags=["auth/oauth", "security"])
3. reweave(content_id=<step_2_id>)
```

### Recipe 2: Review Triage

**What it accomplishes:** Surface the current work queue, inspect each actionable item, update stale notes, and archive completed or obsolete ones.

**When to use:** Periodic review — clearing the backlog, promoting mature notes, archiving abandoned tasks.

**Steps:**

| Step | Action | Condition |
|------|--------|-----------|
| 1 | Get the full work queue | Always |
| 2 | Fetch each item's full content | Repeat for each work queue item |
| 3 | Update items that need changes | Skip if item is already current |
| 4 | Archive items that are complete or irrecoverable | Only if item should not continue |

**Human CLI walkthrough:**

```bash
# Step 1: Get the prioritized work queue
ztlctl query work-queue

# Expected output (example):
# TASK-0001  "Follow up on OAuth threat model"   priority: high   maturity: seed   stale: 14 days
# TASK-0002  "Review Attention paper"             priority: medium maturity: seed   stale: 7 days
# ZTL-0035   "Token exchange trade-offs"          maturity: seed   no outgoing edges

# Step 2: Inspect a specific item
ztlctl query get TASK-0001

# Step 3: Update an item (promote maturity, add notes)
ztlctl update TASK-0001 --maturity budding

# Expected output:
# Updated TASK-0001: maturity seed -> budding

# Step 4: Archive a completed item
ztlctl archive TASK-0001

# Expected output:
# Archived TASK-0001: "Follow up on OAuth threat model"
```

**Agent MCP tool sequence:**

```
1. work_queue()
2. get(content_id=<each_item_id>)  <- repeat per item
3. update(content_id=<id>, changes={maturity: "budding"})  <- skip if no changes needed
4. archive(content_id=<id>)  <- only if item is done or stale beyond recovery
```

### Recipe 3: Knowledge Synthesis

**What it accomplishes:** Search a topic broadly, identify structural gaps in the knowledge graph, draft a synthesis note from the topic packet, and reweave it into the graph.

**When to use:** When you want to consolidate scattered knowledge on a topic into a single synthesis artifact that explicitly acknowledges gaps and invites future connection.

**Steps:**

| Step | Action | Condition |
|------|--------|-----------|
| 1 | Search existing content (limit 20) | Always |
| 2 | Find graph gaps — structurally isolated areas | Always |
| 3 | Draft a synthesis note from the topic packet | Skip if step 1 already has a mature (evergreen) synthesis note |
| 4 | Reweave the draft against existing content | Always |

**Human CLI walkthrough:**

```bash
# Step 1: Survey what exists on the topic
ztlctl query search "distributed systems" --limit 20

# Expected output (example):
# ZTL-0010  "CAP theorem trade-offs"        maturity: budding
# ZTL-0018  "Raft consensus algorithm"      maturity: seed
# REF-0003  "Designing Data-Intensive Apps"  maturity: evergreen

# Step 2: Find gaps — where the graph is thin
ztlctl graph gaps --top 10

# Expected output (example):
# Gap 1: "consensus" cluster — 3 notes, 1 bridge connection, no synthesis note
# Gap 2: "replication" cluster — isolated from "consistency" cluster

# Step 3: Draft a synthesis note from the topic
ztlctl query draft "distributed-systems" --target note

# Expected output:
# Drafted ZTL-0055: "Distributed Systems Synthesis" [seed]
#   Sources: 8 notes, 2 references
#   Gaps surfaced: consensus <-> replication bridge missing

# Step 4: Reweave (already ran automatically — manual run if re-running)
ztlctl reweave run --content-id ZTL-0055
```

**Agent MCP tool sequence:**

```
1. search(query="distributed systems", limit=20)
2. gaps(top=10)
3. draft_from_topic(topic="distributed-systems", target="note")  <- skip if step 1 has mature synthesis
4. reweave(content_id=<step_3_id>)
```

!!! tip
    Recipes are starting points, not rigid scripts. An agent can modify steps based on what it finds — for example, skipping the draft step if a recent evergreen note already covers the topic.

## Session Lifecycle

Sessions are operational coordination units — they group a period of work so ztlctl can apply enrichment to everything created during that period when the session closes. Sessions are optional for human users and central to agent-driven workflows.

### Human-Driven Session

A typical 30-minute research session:

```bash
# Start a session with a topic focus
ztlctl session start "oauth security research"

# Expected output:
# Session started: LOG-0001 "oauth security research"
# Session is open. All notes and references created now are linked to LOG-0001.

# Capture sources as you find them
ztlctl ingest text "RFC 6749 key sections" --target-type reference --tags auth/oauth
ztlctl create note "Token exchange threat model" --tags auth/oauth --tags security --topic auth

# Log your reasoning as you go
ztlctl session log "Read RFC 6749 sections 4-6. Key risk: token replay via HTTP."
ztlctl session log "Drafted threat model. Needs peer review." --pin

# Check how much context you have accumulated (useful before asking an agent to continue)
ztlctl session cost --report 50000

# Close the session when done
ztlctl session close --summary "Mapped OAuth 2.0 attack surface"

# Expected output:
# Session closed: LOG-0001
# Cross-session reweave: 7 new links created
# Orphan sweep: 2 orphaned notes connected
# Integrity check: 0 issues
# Graph metrics updated (PageRank, degree, betweenness)
```

!!! note
    Only one session can be open at a time. If you already have an open session, `ztlctl session start` returns an error.

### Agent-Driven Session

Agents use the same session commands via MCP tools. A literature review agent might:

```
# Agent starts session
start(topic="attention mechanisms in transformers")

# Agent fetches topic context to understand what is already captured
context(topic="transformers", budget=8000)

# Agent ingests retrieved sources
ingest_source(title="Attention Is All You Need", content=<paper_text>, input_kind="text", target_type="reference")

# Agent creates synthesis notes as it reads
create_note(title="Multi-head attention intuition", tags=["ml/transformers"])
create_note(title="Self-attention vs cross-attention", tags=["ml/transformers"])

# Agent logs key decisions
log_entry(message="Core insight: Q/K/V projection sizes determine capacity vs. compute tradeoff", pin=True)

# Agent closes session when done
close(summary="Surveyed attention mechanism architecture, 2 synthesis notes created")
```

The agent receives structured JSON at each step, including content IDs it can use in subsequent calls. No special agent-mode configuration is required — the same MCP tools work for both supervised and autonomous agents.

### Session Close Enrichment Pipeline

When you (or an agent) call `session close`, ztlctl runs a 5-step enrichment pipeline automatically:

```
LOG CLOSE -> CROSS-SESSION REWEAVE -> ORPHAN SWEEP -> INTEGRITY CHECK -> GRAPH MATERIALIZATION
```

**Step 1 — Log Close:** The session node is marked `status="closed"` and a `session_close` log entry is inserted. This is atomic — if it fails, no other steps run.

**Step 2 — Cross-Session Reweave** (toggle: `close_reweave`): Runs the reweave algorithm on every note and reference created during this session. New connections are discovered across the full vault — not just within the session. Returns the count of new links created.

**Step 3 — Orphan Sweep** (toggle: `close_orphan_sweep`): Finds every note and reference in the entire vault with zero outgoing edges — not just session notes. Runs reweave with a lower threshold (default: 0.2 instead of 0.6) so orphaned notes have a better chance of getting at least one connection.

**Step 4 — Integrity Check** (toggle: `close_integrity_check`): Runs the vault integrity checker. Counts error-severity issues and appends a warning to the close result. Does **not** auto-fix — only reports.

**Step 5 — Graph Materialization** (always runs): Updates PageRank, degree centrality, and betweenness centrality for all nodes in the graph. This powers rank-ordered search, bridge detection, and gap identification.

**Reading the close result with `--json`:**

```bash
ztlctl session close --summary "Research complete" --json
```

```json
{
  "session_id": "LOG-0001",
  "status": "closed",
  "reweave_count": 7,
  "orphan_count": 2,
  "integrity_issues": 0
}
```

- `reweave_count`: Total new graph edges created across all session notes
- `orphan_count`: Number of previously-isolated notes that received at least one connection via the orphan sweep
- `integrity_issues`: Count of error-severity integrity violations found (0 = healthy)

**Configuring the pipeline** in `ztlctl.toml`:

```toml
[session]
close_reweave = true
close_orphan_sweep = true
close_integrity_check = true
orphan_reweave_threshold = 0.2  # lower = more connections for orphans
```

## Batch Operations

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

## Scripting with JSON Output

Every command supports `--json` for structured output:

```bash
# Create and capture the ID
ID=$(ztlctl create note "My Note" --json | jq -r '.data.id')

# Query and process results
ztlctl query search "python" --json | jq '.data.items[].title'

# Check vault health programmatically
ERRORS=$(ztlctl check check --json | jq '.data.issues | map(select(.severity == "error")) | length')
```

## Anti-Patterns

!!! warning "Anti-Pattern: Agent creating notes without an active session"
    Notes created outside a session are not linked to a coordination unit, so the session-close enrichment pipeline (cross-session reweave, orphan sweep, integrity check) never runs for them. Individual Reweave plugin auto-reweave still fires, but session-level enrichment does not. For agent-driven workflows, always call `start` before creating notes and `close` when done.

!!! warning "Anti-Pattern: Agent ignoring ServiceResult.success"
    Every MCP tool returns a `ServiceResult` with an `ok` boolean. Agents that skip this check and proceed on failure will chain bad state — creating notes with IDs that do not exist, updating records that were never written, or extracting decisions from sessions that failed to close. Always gate the next step on `result.ok == true` and surface the `error.message` field when false.

!!! warning "Anti-Pattern: Agent running reweave run after every single create"
    The Reweave plugin already runs `reweave run` automatically after every `create_note` and `create_reference` call. Calling `reweave` manually after each individual create causes double-reweave on the same item, wasting time and producing duplicate-edge attempts. Use `session close` to trigger a single cross-session reweave on all notes created during a session. Reserve manual `reweave run --content-id {id}` calls for notes with `--no-reweave` or notes created before a new related item was added to the vault.

!!! warning "Anti-Pattern: Agent using raw SQL instead of CLI/MCP tools"
    The SQLite database at `.ztlctl/ztlctl.db` is managed exclusively by ztlctl. Agents that query or mutate it directly bypass frontmatter sync, tag indexing, graph edge maintenance, FTS5 updates, and the event bus. The result is a database that drifts out of sync with the filesystem. All knowledge-work operations must go through the CLI (`ztlctl query search`, `ztlctl create note`) or MCP tools (`search`, `create_note`). Use `ztlctl check rebuild` to recover if the database has already been corrupted by direct SQL access.

---

## Next Steps

- See [Built-in Plugins](plugins.md) for Git and Reweave plugin configuration
- See [Best Practices](best-practices.md) for composing sessions, reweave, and agents safely
- See [Agents Reference](agents.md) for MCP tool schemas, session state machine, and error recovery
- See [Knowledge Paradigms](paradigms.md) for second-brain vs knowledge garden approach guidance
- See [Core Concepts](concepts.md) for the content type and maturity tier reference
- See [MCP Server](mcp.md) for the full MCP tool and resource reference
