# ztlctl Improvement Proposals: Research-Driven Enhancements

> **Date**: 2026-03-21
> **Context**: Community research synthesis from 8 X/Twitter posts on Obsidian + AI agent memory systems
> **Scope**: 5 targeted improvements where community patterns reveal genuine gaps in ztlctl's architecture

---

## Table of Contents

1. [Ingestion Pipeline: Media and Transcript Processing](#1-ingestion-pipeline-media-and-transcript-processing)
2. [Session Recall: Cross-Session History Querying](#2-session-recall-cross-session-history-querying)
3. [Polaris Layer: Persistent Goals and Priority Documents](#3-polaris-layer-persistent-goals-and-priority-documents)
4. [Contradiction Detection: Semantic Integrity Analysis](#4-contradiction-detection-semantic-integrity-analysis)
5. [Methodology Guidance: Prose-as-Title and Title Quality](#5-methodology-guidance-prose-as-title-and-title-quality)

---

## 1. Ingestion Pipeline: Media and Transcript Processing

### The Gap

Community practitioners (@nyk_builderz, @arscontexta) describe an ingestion pipeline — `brain-ingest` — that converts raw media (video, audio, meeting recordings, transcripts) into structured Obsidian notes with frontmatter, wikilinks, and extracted claims. From a single 90-minute conference talk, the tool reportedly extracts 12-18 distinct claims, 3-5 frameworks, 5-8 actionable techniques, and 2-4 concrete examples.

ztlctl has a reference capture system and a nascent ingestion service, but neither handles the upstream problem of going from raw media to structured knowledge atoms.

### Current Architecture

ztlctl's ingestion infrastructure is more developed than it might appear at first glance. The foundation exists across three layers:

**IngestService** (`src/ztlctl/services/ingest.py`) provides three entry points:

- `ingest_text(title, body, ...)` — raw text with optional source bundle metadata
- `ingest_file(file_path, ...)` — reads `.md` or `.txt` files from disk
- `ingest_url(url, ...)` — delegates to registered `SourceProviderContribution` plugins

Each entry point normalizes input into a **source bundle** — a structured JSON envelope persisted at `sources/{ref_id}/bundle.json` alongside the normalized text at `sources/{ref_id}/normalized.md`. The bundle schema (`src/ztlctl/services/source_bundles.py`) captures:

```
version, input_kind, title, body_text, normalized_text_path, content_hash,
captured_at, source_kind, modalities, capture_agent, capture_method,
summary_hint, key_points, provenance, citations, excerpts, artifacts
```

This is designed for machine-populated metadata. The `capture_agent` field records which model performed extraction. The `key_points` array holds distilled claims. The `excerpts` array stores located passages with citation linkage. The `artifacts` array tracks derived files (images, diagrams) with MIME types.

**The ReferenceModel** (`src/ztlctl/domain/content.py`) has extensive source metadata fields — `url`, `canonical_url`, `source_provider`, `source_type`, `source_kind`, `modalities`, `capture_agent`, `capture_method`, `citations`, `artifacts`, `source_bundle_path`, `retrieved_at`, `content_hash`, `language`. These exist precisely for the ingestion use case but currently have no upstream pipeline populating them from media.

**The ActionRegistry** exposes `ingest_text`, `ingest_file`, `ingest_url`, and `ingest_providers` as MCP tools. The `ztlctl://capture/spec` resource documents the 4-step agent workflow: fetch → normalize → ingest_source → review/synthesize.

**The event bus** fires `post_action("create_reference", ...)` after ingestion, enabling the ReweavePlugin to automatically link new references to existing notes.

### What's Missing

The gap is between "raw media on disk or at a URL" and "structured source bundle ready for `ingest_text()`." Currently, an external process must:

1. Transcribe audio/video to text
2. Extract structured claims, frameworks, and techniques from the transcript
3. Format the output as a source bundle with populated `key_points`, `citations`, `excerpts`
4. Call `ingest_text()` or `ingest_file()` with the structured data

None of these steps exist inside ztlctl. The community solves this with `brain-ingest`, a separate CLI tool. But ztlctl's plugin architecture — specifically `SourceProviderContribution` and the event bus — is designed to support this pattern natively.

### Proposed Enhancement

**A media ingestion plugin** that registers as a `SourceProviderContribution` and handles the transcription-to-bundle pipeline. The plugin would:

1. **Accept media inputs**: Local files (`.mp4`, `.mp3`, `.m4a`, `.wav`), URLs (YouTube, podcast feeds), and raw transcript files (`.txt`, `.vtt`, `.srt`)

2. **Transcribe locally**: Use `whisper` or `faster-whisper` for local transcription (no data leaves the machine — a key principle from @nyk_builderz). For URLs, download first, then transcribe.

3. **Extract structured knowledge**: Use an LLM (via MCP or direct API call) to process the transcript and produce:
   - `key_points`: Distinct claims worth preserving
   - `citations`: Located passages with timestamp references
   - `excerpts`: Notable quotes with context
   - `artifacts`: Any referenced diagrams, frameworks, or models (as descriptions)

4. **Produce a source bundle**: Populate the existing bundle schema with extracted metadata and normalized text.

5. **Route through existing IngestService**: Call `ingest_text()` with the structured bundle, inheriting all downstream behavior — reference creation, FTS5 indexing, vector embedding, post-create reweave, event bus dispatch.

The critical design decision is **where extraction intelligence lives**. Two options:

**Option A: Plugin performs extraction** — The ingestion plugin includes prompt templates for claim extraction and calls an LLM directly. This makes the plugin self-contained but couples it to a specific LLM provider.

**Option B: Plugin produces raw transcript, agent performs extraction** — The plugin handles transcription only and produces a reference with `status=captured`. The agent then reads the reference, extracts structured knowledge, and updates it to `status=annotated` with populated key_points and links. This leverages the existing reference lifecycle (`captured → annotated`) and lets the agent's judgment drive extraction quality.

Option B is more aligned with ztlctl's philosophy — the tool manages structure and lifecycle; intelligence comes from the agent operating within that structure. The `ztlctl://capture/spec` resource already documents this two-phase workflow.

### Integration Points

- **ActionRegistry**: Register `ingest_media` action in a new `ingest` category
- **SourceProviderContribution**: Register provider for media MIME types and YouTube URL patterns
- **Event bus**: `post_action("ingest_media", ...)` fires after transcription, enabling plugins to trigger annotation workflows
- **MCP resource**: `ztlctl://capture/media-spec` documenting accepted formats, transcription options, and the two-phase capture → annotate workflow
- **Config**: `[ingest.media]` section in `ztlctl.toml` for whisper model selection, language hints, output directory preferences

### Relationship to Community Approaches

Where `brain-ingest` is a standalone CLI tool that produces Obsidian notes, this proposal integrates media ingestion into ztlctl's existing infrastructure. The advantages:

- Source bundles persist the raw transcript alongside structured output (auditable, re-extractable)
- Content hash deduplication prevents re-ingesting the same recording
- The reference lifecycle (`captured → annotated`) formalizes the two-phase workflow that `brain-ingest` does in one opaque step
- Post-create reweave automatically connects new references to existing knowledge
- FTS5 + vector indexing happens automatically — no separate indexing step

---

## 2. Session Recall: Cross-Session History Querying

### The Gap

@ArtemXTech describes a `/recall` skill for Claude Code with three modes:
- **Temporal**: "What did I work on yesterday?" — reconstructed 39 sessions from one day with timeline and activity summaries
- **Topic**: BM25 search across session content
- **Graph**: Interactive visualization of session-to-file relationships

ztlctl has first-class session management but no way to query across session history. Sessions are created, enriched on close, and stored — but there's no dedicated recall interface for "show me what happened last week" or "find sessions where I worked on graph algorithms."

### Current Architecture

**Sessions as content** (`src/ztlctl/services/session.py`): Sessions are stored in the `nodes` table as type `log` with `LOG-NNNN` IDs. They have a topic, timestamps, and status (open/closed). The `session` field in every created item links content to its creation session — meaning the relationship "which items were created during session LOG-0042?" is already tracked.

**Session audit trail** (`session_logs` table): Every session lifecycle event is logged:

```sql
CREATE TABLE session_logs (
    id, session_id, timestamp, type, subtype, summary, detail,
    cost, pinned, references (JSON array), metadata (JSON)
)
```

Entry types include `session_start`, `session_close`, content creation events, and enrichment results. The `metadata` JSON field stores arbitrary structured data (reweave scores, integrity results, orphan counts).

**ContextAssembler** (`src/ztlctl/services/context.py`): Layer 1 of the 5-layer context assembly already retrieves session-scoped data:
- `_recent_decisions()` — decision notes sorted by recency
- `_work_queue()` — scored task items
- `_log_entries()` — session_logs rows since last checkpoint, token-budgeted

The assembler uses these to build operational context for the current session, but it doesn't provide a historical recall interface.

**QueryService** (`src/ztlctl/services/query.py`): The `list_items()` method accepts a `session` parameter to filter items created during a specific session. The `search()` method operates over all indexed content but doesn't specifically target session history.

### What's Missing

Three capabilities that don't exist:

1. **Temporal session listing**: "Show me all sessions from the last 3 days" — filtered by date range, with per-session summaries of what was created and what enrichment occurred.

2. **Session content search**: "Find sessions where I worked on reweave scoring" — BM25 or semantic search scoped to session topics, summaries, and the content created within those sessions.

3. **Session topology**: "How do my recent sessions connect?" — which sessions touched overlapping notes, which sessions built on discoveries from earlier sessions, what topics recur across sessions.

### Proposed Enhancement

**A RecallService** that queries across session history with three modes, exposed as MCP tools and CLI commands.

**Mode 1: Temporal Recall**

Input: date range (relative: "yesterday", "last week"; or absolute: "2026-03-15 to 2026-03-21")

Process:
1. Query `nodes` table for `type='log'` within date range, ordered by `created_at`
2. For each session, join to `session_logs` to get start/close events, summaries
3. For each session, count items created (`nodes.session = LOG-NNNN` grouped by type)
4. For each session, retrieve enrichment metadata from close event (reweave count, orphans found, integrity issues)

Output: Timeline of sessions with topic, duration (start → close timestamps), item counts by type, enrichment summary. Token-budgeted for MCP delivery.

This directly mirrors @ArtemXTech's temporal recall but operates over ztlctl's structured session data rather than parsing JSONL files.

**Mode 2: Topic Recall**

Input: search query string + optional date range

Process:
1. BM25 search over session topics and close summaries (add session summaries to FTS5 index, or query session_logs.summary with LIKE for lightweight approach)
2. For sessions matching by topic, expand to include items created within those sessions
3. Optionally: semantic search if vector index is available — embed the query and find sessions whose created content is semantically similar

Output: Ranked list of sessions relevant to the query, with context about what was created and how it connects to the search topic.

**Mode 3: Topology Recall**

Input: optional session ID or date range

Process:
1. Build a session-to-content bipartite graph: sessions → items they created
2. Find session overlap: sessions that created/modified items linked to items from other sessions
3. Identify recurring topics: sessions sharing the same topic or creating items with overlapping tags
4. Compute session "chains": sequences where session N created items that session N+1 modified or linked to

Output: Session connectivity map — which sessions are related through shared content, which topics thread across multiple sessions, which sessions represent continuation of earlier work.

### Integration Points

- **ActionRegistry**: Register `recall_temporal`, `recall_topic`, `recall_topology` actions in a `recall` category
- **MCP tools**: Auto-generated from ActionRegistry (3 new tools)
- **MCP resource**: `ztlctl://sessions/recent` — last N sessions with summaries (analogous to `ztlctl://garden/backlog`)
- **QueryService extension**: `session_history(since, until, topic)` method returning structured session data
- **ContextAssembler**: Layer 1 could optionally incorporate recall results when the agent starts a session related to recent work
- **CLI**: `ztlctl recall yesterday`, `ztlctl recall topic "graph algorithms"`, `ztlctl recall topology --since 2026-03-15`

### Design Considerations

**Session summaries in FTS5**: Currently, session close summaries live in `session_logs.summary`. For BM25 topic recall, these would need to be indexed. Options:
- Add a `sessions_fts` virtual table (clean separation)
- Extend `nodes_fts` to include session body content (simpler but conflates search scopes)
- Use `session_logs.summary` with SQL LIKE as a lightweight first pass, only building FTS for sessions if query volume justifies it

**Token budgeting**: Recall results can be large (weeks of session history). The existing `_token_budget_entries()` pattern from ContextAssembler should be applied — iteratively trim entries from the oldest until the payload fits within the budget.

**Relationship to @ArtemXTech's approach**: His system parses Claude Code's JSONL files — coupling to an undocumented format. ztlctl's approach is architecturally superior because sessions are first-class objects with structured metadata. The recall service queries ztlctl's own data rather than scraping an external tool's internals. This means recall works regardless of which AI client is used (Claude Code, Codex, or any MCP client).

---

## 3. Polaris Layer: Persistent Goals and Priority Documents

### The Gap

@jameesy describes a "Polaris" section — a dedicated vault area containing goals, aspirations, a "Life Razor" (one-sentence mission), and a "Top of Mind" note updated every few weeks. Claude uses these as persistent reference points:

- "How are my current actions aligned with what's top of mind?"
- "I am thinking about taking on X opportunity — how does this help or detract from my life razor?"
- "I have a few hours of spare focus time — what should I work on?" (generates an "idea report" grounded in Polaris context)

This pattern transforms the agent from a reactive tool into a proactive advisor that understands the user's priorities and can evaluate decisions against stated goals.

### Current Architecture

**The garden layer** (`garden/`) is human-owned and not machine-indexed by default. Within it, `garden/groves/` serves as the location for overview and organizational notes — described in the Obsidian profile as "patches of related garden work." This is the natural home for Polaris-type documents.

**MCP resources** currently expose garden content through:
- `ztlctl://garden/backlog` — enrichment signals (stale seeds, orphan notes)
- `ztlctl://review/dashboard` — themes, gaps, bridges, work queue

Neither provides access to user-defined priorities or goals.

**The identity template** (`self/identity.md.j2`) defines the agent's role and tone but doesn't reference user goals. The **methodology template** (`self/methodology.md.j2`) describes workflows and conventions but likewise doesn't incorporate a Polaris concept.

**ContextAssembler** builds 5-layer context for sessions. Layer 1 (operational state) includes work queue and recent decisions. Layer 4 (background signals) includes structural gaps. Neither layer incorporates user-stated priorities.

### What's Missing

There is no designated well-known document for user priorities, no MCP resource to expose it, and no integration with the context assembly pipeline that would make the agent naturally aware of the user's goals.

### Proposed Enhancement

**A Polaris convention** with three components: a well-known path, an MCP resource, and context assembly integration.

**Component 1: Well-Known Path**

Define `garden/groves/polaris.md` as a reserved path for the user's priority document. The Obsidian profile scaffolding (`plugins/builtins/obsidian.py`) would create a starter template during `ztlctl init`:

```yaml
---
title: "Polaris — North Star Priorities"
maturity: evergreen
tags: [meta/polaris]
---

## Life Razor
<!-- One sentence that defines your mission. The agent uses this to evaluate
     whether opportunities, tasks, and decisions align with your direction. -->


## Top of Mind
<!-- Updated every 1-2 weeks. What are you actively thinking about?
     The agent references this when generating idea reports or suggesting
     what to work on next. -->


## Current Goals
<!-- Concrete objectives you're working toward. The agent uses these to
     prioritize the work queue and assess decision alignment. -->


## Boundaries
<!-- What you've explicitly decided NOT to pursue right now.
     Helps the agent avoid suggesting work that conflicts with your focus. -->
```

This is scaffolded once, then owned by the user. ztlctl never modifies it — the agent reads it as context.

**Component 2: MCP Resource**

Register `ztlctl://polaris` as a new MCP resource:

```python
def polaris_impl(vault):
    polaris_path = vault.root / "garden" / "groves" / "polaris.md"
    if not polaris_path.exists():
        return {"exists": False, "hint": "Create garden/groves/polaris.md with your priorities"}
    content = polaris_path.read_text()
    return {"exists": True, "content": content, "modified": polaris_path.stat().st_mtime}
```

This gives agents direct access to the user's stated priorities without needing to search the vault. The resource returns the raw markdown — the agent interprets the structure.

**Component 3: Context Assembly Integration**

Modify ContextAssembler to include Polaris content in Layer 1 (operational state), alongside the work queue and recent decisions. This means every session naturally starts with awareness of the user's priorities:

```python
# In ContextAssembler._build_layer1()
polaris_content = self._read_polaris()
if polaris_content:
    layer1_parts.append(("polaris", polaris_content))
```

Token budgeting applies — if Polaris content is too large, truncate from the bottom (Boundaries section is least critical for moment-to-moment operations).

**Component 4: Decision Alignment Tool**

Register a `check_alignment` action that takes a proposed decision or opportunity and evaluates it against Polaris content:

Input: description of a decision or opportunity
Process:
1. Read Polaris document (life razor, top of mind, goals, boundaries)
2. Read the proposed decision/opportunity text
3. Return both texts in a structured format that the agent can reason about

This doesn't perform the evaluation itself (that's the agent's job) — it provides the structured context needed for the agent to give an informed alignment assessment. The pattern mirrors @jameesy's prompts: "How does this help or detract from my life razor?"

### Design Considerations

**Why garden/groves/ and not self/**: The self/ directory is machine-generated and regenerable from config. Polaris is human-authored and deeply personal — it belongs in the garden layer where ztlctl guarantees it won't be overwritten. Groves specifically are for organizational/overview notes, which is exactly what Polaris is.

**Why a well-known path and not a tag-based lookup**: A single known path (`garden/groves/polaris.md`) is simpler and more reliable than searching for notes tagged `meta/polaris`. The agent doesn't need to search for priorities — it reads from a fixed location. This mirrors how CLAUDE.md works: a well-known path that's always loaded.

**Why not make it a content type**: Polaris is inherently a single document, not a collection. Making it a content type with lifecycle rules would overengineer what is essentially a reference document. The garden layer already provides the right ownership semantics.

---

## 4. Contradiction Detection: Semantic Integrity Analysis

### The Gap

@arscontexta describes an agent that "notices when two notes contradict each other and flags the tension." This is qualitatively different from ztlctl's current integrity checking, which validates structural properties (orphaned links, missing frontmatter, invalid status transitions) but not semantic content.

In a growing vault, contradictions naturally emerge:
- A decision from Q1 conflicts with a decision from Q3 (context changed, neither was updated)
- Two knowledge notes make opposing claims about the same topic (different sources, different evidence)
- A reference's key findings contradict an established note's thesis (new evidence challenges old understanding)

These contradictions aren't bugs — they're valuable signals. Flagging them creates opportunities for synthesis, updating, or supersession.

### Current Architecture

**CheckService** (`src/ztlctl/services/check.py`) performs 5 categories of integrity checks:

1. **CAT_DB_FILE**: File-DB consistency (path exists, ID matches, hash unchanged)
2. **CAT_SCHEMA**: FK constraints, type validity, ID pattern matching
3. **CAT_GRAPH**: Dangling edges, orphaned nodes, circular self-edges
4. **CAT_STRUCTURAL**: Status transitions, maturity progression, session references
5. **CAT_GARDEN**: Aging seeds, evergreen readiness

All of these are structural — they verify that the vault's data is well-formed. None analyze whether the content of two notes is semantically contradictory.

**Conflict edge types exist** but are unused. In `src/ztlctl/services/context.py`, the ContextAssembler already distinguishes between `supporting_types` (relates, supports, supersedes, implements) and `conflict_types` (contradicts, opposes, conflicts). These edge types are defined in the schema but no automated process creates them — they must be manually added to frontmatter links.

**VectorService** (`src/ztlctl/services/vector.py`) provides the semantic similarity infrastructure:
- `search_similar(query_text, top_k)` — cosine similarity over embeddings
- `is_available()` — checks sqlite-vec extension
- Uses `all-MiniLM-L6-v2` (384-dim) by default

**ReweaveService** already uses multi-signal scoring (BM25, tags, graph, topic) to find related notes. The contradiction detector would use the same discovery mechanism but with a different evaluation: instead of "should these be linked?", the question becomes "do these make conflicting claims?"

### What's Missing

There is no automated way to:
1. Discover note pairs that might contradict each other
2. Flag potential contradictions for human review
3. Record confirmed contradictions as `contradicts` edges in the graph
4. Surface contradictions in the review dashboard

### Proposed Enhancement

**A contradiction detection pipeline** that extends CheckService with a new `CAT_SEMANTIC` category. The pipeline has three stages: discovery, evaluation, and reporting.

**Stage 1: Discovery — Finding Candidate Pairs**

Not every pair of notes needs contradiction checking. The discovery stage narrows the search:

1. **Topic-scoped pairs**: Notes sharing the same `topic` field are most likely to contain contradictory claims. Query all (topic, note_id) pairs and group by topic.

2. **High-similarity pairs**: Use VectorService to find notes with high semantic similarity (cosine > configurable threshold, e.g., 0.85). Notes that are very similar in meaning but not linked may contain subtle contradictions.

3. **Decision conflict pairs**: Decision notes (`subtype=decision`) with overlapping tags or topics are prime candidates — especially decisions in `accepted` status that were made at different times.

4. **Supersession gaps**: Notes linked via `supersedes` where the superseded note is still in `connected` status (not archived) may represent unresolved contradictions.

The discovery stage produces a candidate list of (note_A, note_B, reason) tuples.

**Stage 2: Evaluation — Assessing Contradiction**

This is where the design gets opinionated. Two approaches:

**Approach A: Heuristic signals** (no LLM required)

Compare key_points arrays between candidate pairs. Flag contradictions when:
- Two notes share a topic but have key_points with high BM25 similarity and opposing sentiment (detected via negation patterns — "X improves Y" vs "X degrades Y")
- A decision note's `Choice` section contradicts another decision's `Choice` on the same topic
- A reference's key_points contradict an established note's key_points

This is limited but runs locally with zero external dependencies.

**Approach B: Agent-assisted evaluation** (LLM required)

Surface candidate pairs as MCP resource content and let the agent evaluate them. The contradiction detection tool returns structured pairs with their content, and the agent determines which are genuine contradictions.

This is more accurate but requires an agent session. It integrates naturally with the review dashboard workflow — the agent reads `ztlctl://review/contradictions`, evaluates each pair, and uses `update` to add `contradicts` edges where confirmed.

**Recommended: Approach A for discovery/scoring, Approach B for confirmation.** The heuristic pass runs automatically (during `check` or session close). It produces candidate pairs with a confidence score. The agent reviews candidates and confirms or dismisses them.

**Stage 3: Reporting — Surfacing Results**

Confirmed contradictions become:
1. **Edges in the graph**: `contradicts` edge type between the two notes (bidirectional by convention)
2. **Review dashboard entries**: `ztlctl://review/contradictions` resource listing active contradictions with context
3. **CheckService findings**: `CAT_SEMANTIC` category in check results, with severity "info" for candidates and "warning" for confirmed contradictions
4. **Session enrichment signals**: If the current session creates content that contradicts existing notes, flag it during post-create enrichment

### Integration Points

- **CheckService**: New `_check_semantic()` method in the check pipeline, gated by `settings.check.semantic_analysis` (off by default — requires vector index)
- **VectorService**: New `find_similar_pairs(threshold, topic)` method for bulk similarity discovery
- **MCP resource**: `ztlctl://review/contradictions` listing candidate and confirmed contradiction pairs
- **ActionRegistry**: `check_contradictions` action (category: analysis) that runs the discovery pipeline
- **Edge types**: `contradicts` edge type already exists in the schema — no migration needed
- **Config**: `[check.semantic]` section with `enabled`, `similarity_threshold`, `max_candidates_per_topic`

### Design Considerations

**False positive management**: Contradiction detection will produce false positives. Two notes about the same topic with different perspectives aren't contradictions — they're complementary viewpoints. The two-phase design (heuristic discovery → agent confirmation) manages this by keeping humans in the loop for the judgment step.

**Performance**: Pairwise similarity computation scales as O(n²) within a topic. For large vaults, limit discovery to: notes modified in the last N days, notes within the current session's topic, or notes explicitly flagged for review. The `stale_days` pattern from vault_review provides precedent for time-bounded analysis.

**Why not just let agents find contradictions ad-hoc?** Because agents only see what's in their context window. A contradiction between a note from January and a note from March might never appear in the same session context. The discovery pipeline proactively surfaces pairs that would otherwise be invisible to any single session.

---

## 5. Methodology Guidance: Prose-as-Title and Title Quality

### The Gap

@nyk_builderz advocates "prose-as-title" — naming notes as claims rather than categories:

- NOT: `memory-systems.md` → YES: `memory graphs beat giant memory files.md`
- NOT: `retrieval-notes.md` → YES: `hybrid retrieval outperforms pure semantic search.md`

The argument: when Claude searches the vault, result titles alone tell it whether a note is relevant — before opening the file.

ztlctl's methodology templates don't currently advocate for any title convention. The `title` field is required but unconstrained. Since titles are the primary signal in FTS5 search results and MCP tool responses, title quality directly affects retrieval precision.

### Current Architecture

**FTS5 indexing** (`nodes_fts` virtual table) indexes both `title` and `body`:

```sql
CREATE VIRTUAL TABLE nodes_fts USING fts5(id UNINDEXED, title, body)
```

BM25 ranking naturally weights title matches higher than body matches when the query terms appear in the title (FTS5's default column weights). But this advantage only materializes if titles contain distinctive, meaningful terms.

**Content model validation** (`src/ztlctl/domain/content.py`) requires `title: str` on all content types but performs no quality assessment. A title of "Notes" passes validation just as readily as "Spreading activation outperforms BFS for knowledge graph traversal."

**The methodology template** (`src/ztlctl/templates/self/methodology.md.j2`) mentions atomic notes and clear ideas but doesn't prescribe title conventions. The research-partner tone advocates for "clear thesis" titles in passing but doesn't formalize the convention.

**Search result presentation**: QueryService returns items with title, type, status, and relevance score. MCP tools display these in list format. The agent sees a list of titles and must decide which to read — making title informativeness a bottleneck for retrieval efficiency.

### What's Missing

Two things:

1. **Convention guidance**: The methodology templates don't teach agents (or users) that claim-style titles improve retrieval. This is a documentation gap, not a code gap.

2. **Title quality signals**: There's no way to detect that a vault is accumulating low-quality titles that will degrade search performance over time. A note titled "Thoughts" is structurally valid but operationally harmful.

### Proposed Enhancement

**Component 1: Methodology Template Update**

Add a title convention section to `methodology.md.j2` (research-partner tone):

```markdown
## Title Convention

Titles should be claims or clear statements, not categories or labels.

**Strong titles** (searchable, self-documenting):
- "Spreading activation outperforms BFS for graph traversal"
- "Session close enrichment prevents orphan accumulation"
- "YAML round-trip preservation requires canonical key ordering"

**Weak titles** (vague, low retrieval value):
- "Graph notes"
- "Session thoughts"
- "YAML stuff"

A strong title lets you assess relevance from search results without opening the note.
When creating notes, frame the title as the note's central claim or finding.
```

This is a zero-code change — update the Jinja2 template text only. The guidance applies to both agents and humans reading the methodology document in Obsidian.

**Component 2: Title Quality Check**

Add a lightweight title quality heuristic to CheckService under `CAT_STRUCTURAL`:

```python
def _check_title_quality(self):
    """Flag notes with titles likely too short or generic to be useful."""
    issues = []
    for node in self._all_nodes():
        title = node["title"]
        words = title.split()
        # Single-word titles are almost always too vague
        if len(words) <= 2 and node["type"] in ("note", "reference"):
            issues.append(CheckIssue(
                category=CAT_STRUCTURAL,
                severity="info",
                node_id=node["id"],
                message=f"Title '{title}' is very short — consider a more descriptive claim-style title",
            ))
    return issues
```

Severity is `info`, not `warning` — this is advisory, not blocking. The check runs during `ztlctl check` and appears in the review dashboard. It creates gentle pressure toward better titles without enforcing a rigid convention.

**Component 3: Agent Title Improvement Suggestions**

Add title quality to the garden backlog resource (`ztlctl://garden/backlog`). When reporting stale seeds and orphans, also include notes with short or generic titles as candidates for title improvement:

```python
# In garden_backlog_impl()
weak_titles = [n for n in all_notes if len(n["title"].split()) <= 2]
backlog["title_improvements"] = weak_titles[:5]  # Top 5 candidates
```

This surfaces title quality alongside other enrichment signals, prompting the agent to suggest better titles during review workflows.

### Design Considerations

**Why not enforce claim-style titles in validation?** Because not all content types benefit from claim titles. Tasks ("Fix broken FTS5 index") and logs ("Session: graph refactoring") have naturally different title patterns. The convention should apply primarily to notes and references — the knowledge-bearing types. Making it advisory (info severity, methodology guidance) rather than enforced preserves flexibility.

**Why not use the prose-as-title filename convention?** ztlctl uses ID-based filenames (ztl_HASH.md), which is architecturally better than prose filenames. The title lives in frontmatter where it can contain any characters, be updated without breaking wikilinks, and have multiple aliases. Prose filenames create problems: renaming breaks links, special characters cause filesystem issues, and long filenames are unwieldy in terminals. ztlctl's separation of identity (ID) from display (title) is the right design — it just needs better guidance on what makes a good display title.

---

## Implementation Priority Matrix

| Proposal | Effort | Value | Dependencies | Recommended Phase |
|----------|--------|-------|-------------|-------------------|
| **Methodology guidance** (prose-as-title) | LOW — template text only | MEDIUM — improves search quality | None | Immediate |
| **Polaris layer** | LOW-MEDIUM — well-known path + MCP resource + context assembly | HIGH — transforms agent into proactive advisor | Obsidian profile update | Near-term |
| **Session recall** | MEDIUM — new service + 3 actions + MCP resource | HIGH — unlocks cross-session continuity | FTS5 for session summaries (optional) | Near-term |
| **Contradiction detection** | MEDIUM-HIGH — discovery pipeline + evaluation + reporting | HIGH — unique differentiator, no community tool does this | VectorService (sqlite-vec) | Mid-term |
| **Ingestion pipeline** | HIGH — transcription, source providers, plugin architecture | HIGH — solves upstream gap | External dependency (whisper) | Mid-term |

### Sequencing Rationale

1. **Methodology guidance first** because it's zero code and immediately improves every new note created.
2. **Polaris next** because it's small in scope but large in impact — every session becomes goal-aware.
3. **Session recall** because it builds on existing session infrastructure and fills the most frequently cited gap.
4. **Contradiction detection** because it requires the vector index (optional dependency) and benefits from a populated vault.
5. **Ingestion pipeline last** because it has the largest scope and external dependencies, but the vault needs to be rich enough for ingested content to connect meaningfully.
