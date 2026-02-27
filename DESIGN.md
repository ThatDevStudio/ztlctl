# ztlctl — Complete Design Specification v1

> **For Claude:** This document is the authoritative design reference for ztlctl. When implementing any feature, read the relevant section here first. Sections are numbered by feature and cross-referenced — follow `→ Section N` markers to find related constraints. Key invariants are marked with `INVARIANT:` and must never be violated. Implementation order is in Section 20.

## Quick Reference — Invariants

These rules apply across the entire codebase. Violating any of them is a bug.

- **INVARIANT: Files are truth.** The filesystem is authoritative. The DB is a derived index. `ztlctl check --rebuild` must always be able to reconstruct the DB from files alone.
- **INVARIANT: Single write path.** All content enters through the create pipeline (→ Section 4). No alternative creation paths exist.
- **INVARIANT: IDs are permanent.** Once generated, an ID never changes — not on title rename, not on move, not on archive. (→ Section 7)
- **INVARIANT: Decisions are immutable.** After `status = accepted`, the body of a decision note cannot be modified. Supersede with a new decision instead. (→ Section 6)
- **INVARIANT: Body text is human domain.** Garden notes (maturity != null) never have their body text auto-modified. Frontmatter only. (→ Section 5)
- **INVARIANT: Plugin failures are warnings.** A broken plugin degrades the workflow. It never degrades the core tool. Never raise from plugin code. (→ Section 15)
- **INVARIANT: Async by default.** Workflow events dispatch to background threads. The user's foreground interaction is never blocked by hook execution. (→ Section 15)
- **INVARIANT: ServiceResult is the contract.** All service-layer methods return `ServiceResult`. The CLI, MCP adapter, and any future interface consume this type. (→ Section 10)

---

## 1. Overview

**ztlctl** ("zettel-control") is a Python CLI for knowledge graph management. It manages a zettelkasten as a structured vault: markdown files on disk, SQLite database for indexing and queries, NetworkX for in-memory graph algorithms.

### Architecture Layers

```
┌─────────────────────────────────────────────────────┐
│                Workflow Layer                         │
│   Claude Code plugin · MCP prompts · Skills · Hooks  │
├─────────────────────────────────────────────────────┤
│              Extension Layer (Feature 14)             │
│   Pluggy event bus · Plugin system · Git plugin      │
├─────────────────────────────────────────────────────┤
│                MCP Layer (Feature 15)                 │
│   Tools (12) · Resources (6) · Prompts (4) · stdio   │
├─────────────────────────────────────────────────────┤
│               Presentation Layer                      │
│   Click CLI · --json · --no-interact · Rich output   │
│   vector (status, reindex)                            │
├─────────────────────────────────────────────────────┤
│                Service Layer                          │
│   CreateService · QueryService · GraphService        │
│   SessionService · ReweaveService · CheckService     │
│   VectorService · EmbeddingProvider                  │
├─────────────────────────────────────────────────────┤
│                 Domain Layer                          │
│   Content models · ID generation · Frontmatter       │
│   Validation · Content registry · Lifecycle          │
├─────────────────────────────────────────────────────┤
│              Infrastructure Layer                     │
│   SQLite + FTS5 · NetworkX · Alembic · Filesystem    │
│   sqlite-vec · sentence-transformers                 │
└─────────────────────────────────────────────────────┘
```

Each layer is independently usable. `pip install ztlctl` provides everything through the service layer. The CLI, MCP adapter, and workflow layer are consumption interfaces over the same services.

### Package Structure

```
src/ztlctl/
├── cli.py                   # Root Click group + global flags
├── commands/                # Presentation: AppContext, 7 groups + 6 standalone commands
├── config/                  # Configuration: Pydantic models + TOML discovery
├── domain/                  # Domain: types, lifecycle, IDs, content models, frontmatter
├── infrastructure/          # Infrastructure: database/, graph/, filesystem
├── mcp/                     # MCP adapter (optional extra, import-guarded)
├── output/                  # Presentation: Rich/JSON formatters
├── plugins/                 # Extension: hookspecs, manager, builtins/
├── services/                # Service: result contract + 6 service classes
└── templates/               # Bundled Jinja2 templates (content/ + self/)
```

### Design Principles

1. **Files are truth, DB is index.** The filesystem is authoritative. The database accelerates queries. `ztlctl check --rebuild` reconstructs the DB from files.
2. **Graph insertion, not file creation.** Every operation should densify the knowledge graph. Creating an isolated note is the failure mode.
3. **One query, one answer.** Every query returns everything needed; the consumer interprets.
4. **Agents consume, never produce identity.** Self/ files are generated by the CLI from templates. Agents read them.
5. **Async by default.** Workflow events dispatch to background threads. The user is never interrupted.
6. **Tool provides primitives, workflow makes judgments.** ztlctl stores, retrieves, and reports. Context management, checkpointing, and orchestration live in the workflow layer.

### Technology Stack

- **Language:** Python 3.13+ (uses `StrEnum` for all enums)
- **CLI:** Click
- **Database:** SQLite (WAL mode) via SQLAlchemy Core
- **Graph:** NetworkX (in-memory, rebuilt per invocation)
- **Migrations:** Alembic (auto-generated from model diffs)
- **Templates:** Jinja2 (self/ generation)
- **Models:** Pydantic v2 (configuration, service contracts, frontmatter schemas)
- **Plugins:** pluggy (event bus)
- **Packaging:** uv, Hatchling, PyPI
- **Type checking:** strict mypy
- **MCP:** FastMCP (optional extra)

---

## 2. Content Model

### Types and Spaces

| Type | ID Pattern | Space | Format | Purpose |
|------|-----------|-------|--------|---------|
| **Note** | `ztl_{8 hex}` | `notes/` | Markdown | Knowledge — insights, syntheses, claims |
| **Reference** | `ref_{8 hex}` | `notes/` | Markdown | External sources — articles, papers, tools |
| **Log** | `LOG-NNNN` | `ops/logs/` | JSONL | Session records — append-only event streams |
| **Task** | `TASK-NNNN` | `ops/tasks/` | Markdown | Action items — with priority/impact/effort |

Three spaces: `self/` (generated identity, read by agents — → Section 11), `notes/` (growing knowledge graph — → Section 3), `ops/` (transient operational state).

### Note Subtypes and Content Models

Subtypes are enforced via a `ContentModel` class hierarchy with a `CONTENT_REGISTRY` for lookup. Each model subclass owns its frontmatter schema, validation rules, lifecycle transitions, and Jinja2 body templates — all as classmethods on the model itself.

| Subtype | Model class | Strictness | Key Rules |
|---------|-------------|-----------|-----------|
| `decision` | `DecisionModel` | Strict | Immutable after `accepted`. Required sections: Context, Choice, Rationale, Alternatives, Consequences. Status: `proposed → accepted → superseded`. |
| `knowledge` | `KnowledgeModel` | Advisory | Recommends `key_points` in frontmatter. Flexible structure. |
| (none) | `NoteModel` | None | Plain note. No additional constraints. |

Reference subtypes (`article`, `tool`, `spec`) are classification-only — useful for CLI filtering, no lifecycle enforcement.

```python
class ContentModel(BaseModel):
    """Base — attributes ARE frontmatter keys."""
    model_config = {"frozen": True}
    id: str; type: str; status: str; title: str; ...

    def write_body(self, **kwargs: Any) -> str: ...
    @classmethod
    def validate_create(cls, data: dict) -> ValidationResult: ...
    @classmethod
    def validate_update(cls, existing: dict, changes: dict) -> ValidationResult: ...
    @classmethod
    def required_sections(cls) -> list[str]: ...
    @classmethod
    def status_transitions(cls) -> dict[str, list[str]]: ...

class DecisionModel(NoteModel): ...  # strict validation, immutability
class KnowledgeModel(NoteModel): ... # advisory warnings
class ReferenceModel(ContentModel): ... # classification-only
class TaskModel(ContentModel): ...     # priority matrix

CONTENT_REGISTRY: dict[str, type[ContentModel]] = {
    "note": NoteModel, "knowledge": KnowledgeModel,
    "decision": DecisionModel, "reference": ReferenceModel,
    "task": TaskModel,
}
```

Lookup via `get_content_model(content_type, subtype)` — subtype takes priority, falls back to type. Models ship with bundled Jinja2 body-only templates. User-provided templates supported in future versions. No custom subtypes in v1 — shipped subtypes use the same extensibility mechanism, allowing us to tune before opening to users.

Machine-layer subtypes are **strict** (validation blocks creation if rules violated). Garden-layer content is **flexible** (advisory warnings, never blocking).

### Dual Lifecycle

**Machine lifecycle** (computed, enforced by the tool):
- Notes: `draft → linked → connected` (based on link count thresholds)
- References: `captured → annotated`
- Logs: `open → closed`
- Tasks: `inbox → active → blocked → done → dropped`

**Garden lifecycle** (advisory, human-driven via Obsidian):
- `seed → budding → evergreen` (maturity progression for notes)

Machine status is always computed from structural properties (link count, field completeness), never set by CLI command. Status transitions are validated in the update pipeline (→ Section 6).

### Sessions

Sessions are first-class organizational containers. Every content item links to its creation session.

```yaml
---
id: ztl_a1b2c3d4
type: note
subtype: knowledge
session: LOG-0042
tags: [domain/cognitive-science]
created: 2026-02-24
---
```

**Session lifecycle:** `open → closed` (reopenable via `session reopen`)

> **Implementation note (Phase 3):** The design originally specified `OPEN → ACTIVE → CLOSING → CLOSED`. The implementation simplified to two states (`open`, `closed`) since `ACTIVE` and `CLOSING` were intermediate states with no distinct behavior. The transition is bidirectional — closed sessions can be reopened.

**1:N with Claude sessions:** A ztlctl session is a logical research session persisting in the DB. It can span multiple Claude Code context windows. The `agent_context` tool loads session state at the start of each window, providing continuity.

### Task Priority Matrix

```yaml
---
id: TASK-0042
type: task
status: inbox
priority: high       # high | medium | low
impact: high         # high | medium | low
effort: medium       # high | medium | low
session: LOG-0042
---
```

Work queue scoring: `priority×2 + impact×1.5 + (4 − effort_weight)`. High/high/low = 10.5 (highest priority quick wins).

### Frontmatter Standards

**Canonical key ordering per type:** `id, type, subtype, status, maturity, title, session, tags, aliases, topic, links, created, modified`

**Frontmatter handling:** ruamel.yaml round-trip preserving comments and formatting.

---

## 3. Graph Architecture

### Two Link Layers

**Frontmatter links** — typed, structural:
```yaml
links:
  relates: [ztl_b3f2a1, ref_c4d5e6]
  supersedes: [ztl_old123]
```

**Body wikilinks** — inline, contextual:
```markdown
This builds on [[Transformer Architectures]] and contradicts [[ztl_a1b2c3d4]].
```

Both layers merge into a unified edge table (→ Section 9 for schema). Backlinks are computed (never stored in files).

### Wikilink Resolution

Title match → alias match → ID match. Ambiguous matches warn; no silent wrong resolution.

> **Implementation note (Phase 3):** Full 3-step resolution chain implemented: title match → alias match (via `json_each()` on the `aliases` JSON column) → ID match. Shared as a module-level function `_resolve_wikilink()` in `services/create.py`, reused by CheckService for rebuild/re-index operations.

### Edge Schema

```python
edges = Table("edges", metadata,
    Column("source_id", Text, ForeignKey("nodes.id"), nullable=False),
    Column("target_id", Text, ForeignKey("nodes.id"), nullable=False),
    Column("edge_type", Text, default="relates"),
    Column("source_layer", Text),        # frontmatter | body
    Column("weight", REAL, default=1.0),
    Column("bidirectional", Integer),     # materialized
    Column("created", Text, nullable=False),
    UniqueConstraint("source_id", "target_id", "edge_type"),
)
```

### Graph Algorithms

Six algorithms via NetworkX, computed on demand:

| Algorithm | Purpose | Command |
|-----------|---------|---------|
| Spreading activation | Find related content (BFS with 0.5 decay) | `ztlctl graph related` |
| Community detection (Leiden → Louvain fallback) | Discover topic clusters | `ztlctl graph themes` |
| PageRank | Identify important nodes | `ztlctl graph rank` |
| Shortest path | Find connection chains | `ztlctl graph path` |
| Structural holes | Find gaps in the graph | `ztlctl graph gaps` |
| Betweenness centrality | Find bridge nodes | `ztlctl graph bridges` |

### GraphEngine

Lazy rebuild from SQLite per invocation. No cross-invocation cache.

```python
class GraphEngine:
    def __init__(self, db: Engine):
        self._db = db
        self._graph: nx.DiGraph[str] | None = None

    @property
    def graph(self) -> nx.DiGraph[str]:
        if self._graph is None:
            self._graph = self._build_from_db()
        return self._graph

    def invalidate(self) -> None:
        self._graph = None
```

At vault scale (< 10K nodes), full rebuild takes < 10ms. Commands that don't need graph operations never build it.

---

## 4. Create Pipeline

### Five-Stage Pipeline

```
VALIDATE → GENERATE → PERSIST → INDEX → RESPOND
```

1. **Validate** — check type, required fields via `ContentModel.validate_create()`, tag format
2. **Generate** — compute ID (content-hash or sequential), build frontmatter, render template
3. **Persist** — write markdown file to disk
4. **Index** — import into SQLite (nodes, edges, tags, FTS5)
5. **Respond** — return `ServiceResult` with path, ID, warnings

Single write path. No fallback mechanism. If the pipeline fails, it fails with a clear error. Post-create, the event bus (→ Section 15) dispatches `post_create` asynchronously. Reweave (→ Section 5) runs unless `--no-reweave` is passed.

> **Implementation note (Phase 3):** The five-stage pipeline is complete for notes, references, and tasks. The RESPOND stage returns `{id, path, title, type}` plus warnings, rendered as human-readable key-value pairs or JSON. Post-create reweave invocation is available via ReweaveService. Event bus dispatch is deferred to Phase 6 (Extension) when the pluggy event system is implemented.

### Command Surface

```bash
ztlctl create note "Title" --tags "domain/topic" --topic "cognitive-science"
ztlctl create reference "Title" --url "https://..." --tags "domain/topic"
ztlctl create task "Title" --priority high --impact high --effort low
ztlctl garden seed "Half-formed idea"      # cultivation persona
ztlctl agent session start "Research topic" # session management
ztlctl extract LOG-0042                     # JSONL → markdown
```

### Three Interaction Profiles

- **Interactive (default):** Prompts for missing fields, suggests related content
- **Auto:** `--auto-link-related` skips confirmation for reweave links
- **Non-interactive:** `--no-interact` for scripting; `--json` for structured output (orthogonal flags)

### Batch Creation

```bash
ztlctl create --batch notes.json           # all-or-nothing by default
ztlctl create --batch notes.json --partial  # continue past failures
```

> **Implementation note (Phase 4):** `CreateService.create_batch()` is implemented in the service layer (all-or-nothing and partial modes). The `create batch` CLI subcommand is implemented — it reads a JSON file of item objects and passes them to the service. File read errors and format validation route through `app.emit(ServiceResult)` for structured JSON error output.

---

## 5. Reweave

### Algorithm

Five-stage graph densification, triggered post-create by default:

```
DISCOVER → SCORE → FILTER → PRESENT → CONNECT
```

### Scoring Model

Four signals, each normalized to 0.0–1.0, combined via weighted sum:

| Signal | Method | Default Weight |
|--------|--------|---------------|
| Lexical similarity | FTS5 BM25 (percentile normalized) | 0.35 |
| Tag overlap | Jaccard coefficient | 0.25 |
| Graph proximity | Inverse shortest path | 0.25 |
| Topic co-occurrence | Binary (same topic directory) | 0.15 |

**Percentile normalization:** BM25 scores are normalized relative to the top-N candidates for each note. The top score = 1.0. This handles the unbounded BM25 score problem across vault sizes.

**Default threshold:** `min_score_threshold = 0.6` (conservative — only strong matches). Users lower as confidence builds.

Weights are configurable with sensible static defaults in `ztlctl.toml`:

```toml
[reweave]
enabled = true
min_score_threshold = 0.6
max_links_per_note = 5
lexical_weight = 0.35
tag_weight = 0.25
graph_weight = 0.25
topic_weight = 0.15
```

### Link Lifecycle

- **Add and flag stale.** Reweave adds links and flags existing links that score below threshold as stale.
- **Optional prune.** `ztlctl reweave --prune` removes stale links. `ztlctl reweave --prune --id ztl_a1b2c3d4` targets specific notes.
- **CLI for targeted removal.** `ztlctl graph unlink ztl_source ztl_target` removes specific links.

### Garden Note Protection

Garden notes (maturity != null) receive frontmatter-only modifications. Body text is never auto-modified — the body is the human's domain.

```python
def should_modify_body(note) -> bool:
    return note.maturity is None  # machine notes only
```

### Safety

- `--dry-run` shows what would change
- `--undo` reverses via audit trail (`reweave_log` table)
- `--no-reweave` skips on any creation command

> **Implementation note (Phase 3+4):** ReweaveService implements `reweave()`, `prune()`, and `undo()`. All four scoring signals are implemented with configurable weights from `ReweaveConfig`. Garden note protection is enforced — body wikilinks are never added to notes with `maturity` set, but frontmatter `links.relates` entries are still added. The `reweave_log` table tracks all add/remove actions with timestamps for undo support. Undo can target a specific reweave ID (`--undo-id N`) or the most recent batch (`--undo`). CLI flags `--dry-run`, `--prune`, `--undo`, `--undo-id`, and `--id` are all implemented. Interactive confirmation implemented (Phase 5): preview → display table → `click.confirm()` → apply.

---

## 6. Update and Close Lifecycle

### Five-Stage Update Pipeline

```
VALIDATE → APPLY → PROPAGATE → INDEX → RESPOND
```

1. **Validate** — check transition legality via `ContentModel.validate_update()` (decision immutability)
2. **Apply** — modify file (frontmatter and/or body)
3. **Propagate** — downstream effects (cascade status, update edges)
4. **Index** — re-import modified node
5. **Respond** — return `ServiceResult`

### Session Close Pipeline

```
LOG CLOSE → CROSS-SESSION REWEAVE → ORPHAN SWEEP → INTEGRITY CHECK → DRAIN EVENT WAL → REPORT
```

Session close assumes incompleteness and performs maximum graph enrichment:
- **Cross-session reweave:** Re-scores all notes created this session against the full vault
- **Orphan sweep:** Finds notes with zero links, attempts reweave at lower threshold
- **Integrity check:** Quick consistency validation
- **Drain event WAL:** Sync barrier for async workflow events (wait for in-flight, retry failures, report)

### Archive, Never Delete

`ztlctl archive ztl_a1b2c3d4` sets `archived: true`. Edges preserved. Excluded from active queries by default. `--include-archived` flag to include.

### Decision Supersession

```bash
ztlctl create note "New approach" --subtype decision --supersedes ztl_old123
# Old decision: status → superseded, superseded_by → new ID
# New decision: supersedes → old ID
```

> **Implementation note (Phase 3+4):** UpdateService implements the full 5-stage pipeline with `update()`, `archive()`, and `supersede()`. All three have CLI commands: `ztlctl update` (with `--title`, `--status`, `--tags`, `--topic`, `--body`, `--maturity`), `ztlctl archive`, and `ztlctl supersede`. Status transitions are validated against lifecycle transition maps. Note status is automatically recomputed from outgoing edge count after any update (PROPAGATE stage). Garden note protection rejects body changes when `maturity` is set (warning instead of error). Decision immutability prevents body changes after `status=accepted`. FTS5 updates use DELETE + INSERT (virtual tables don't support UPDATE). Edge re-indexing re-extracts both frontmatter links and body wikilinks. SessionService implements start/close/reopen with close enrichment pipeline (cross-session reweave → orphan sweep → integrity check). Session lookup and close happen inside the same `VaultTransaction` to prevent TOCTOU races. SessionService methods `log_entry()`, `cost()`, and `context()` are fully implemented (Phase 7). `extract_decision()` extracts decision notes from session JSONL logs (Phase 7). `brief()` returns vault orientation without requiring an active session (Phase 7). Event WAL drain is implemented in Phase 6 via `EventBus.drain()`.

---

## 7. ID System

### Two Strategies

**Content-hash** (notes, references): SHA-256 of normalized title, truncated to 8 hex characters.

```python
def normalize_title(title: str) -> str:
    text = title.lower()
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r"[^\w\s]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def generate_content_hash(title: str, prefix: str) -> str:
    normalized = normalize_title(title)
    return f"{prefix}{hashlib.sha256(normalized.encode('utf-8')).hexdigest()[:8]}"
```

Title is the **seed** for a **permanent** identifier. The ID never changes, even if the title is later modified. Collision: error with guidance to differentiate the title.

**Sequential** (logs, tasks): Atomic counter from DB. `LOG-NNNN`, `TASK-NNNN`. Minimum 4 digits, grows naturally. Gaps consumed, not reusable.

### Validation

```python
ID_PATTERNS = {
    "note": re.compile(r"^ztl_[0-9a-f]{8}$"),
    "reference": re.compile(r"^ref_[0-9a-f]{8}$"),
    "log": re.compile(r"^LOG-\d{4,}$"),
    "task": re.compile(r"^TASK-\d{4,}$"),
}
```

### Counter Schema

```python
id_counters = Table("id_counters", metadata,
    Column("type_prefix", Text, primary_key=True),
    Column("next_value", Integer, nullable=False, default=1),
)
```

---

## 8. Query Surface

### Three Surfaces

**`ztlctl query`** — structured retrieval (search, list, get):
```bash
ztlctl query search "database architecture" --type note --tag engineering/architecture
ztlctl query get ztl_a1b2c3d4
ztlctl query list --type task --status active --sort priority
ztlctl query work-queue                    # prioritized task list
ztlctl query decision-support --topic "databases"  # notes + decisions + refs
```

**`ztlctl graph`** — traversal and analysis:
```bash
ztlctl graph related ztl_a1b2c3d4 --depth 2
ztlctl graph themes                        # Leiden community detection
ztlctl graph rank --top 20                 # PageRank
ztlctl graph path ztl_source ztl_target
ztlctl graph gaps                          # structural holes
ztlctl graph bridges                       # betweenness centrality
```

**`ztlctl agent`** — session and context management:
```bash
ztlctl agent session start "Research topic"
ztlctl agent session close --summary "..."
ztlctl agent session reopen LOG-0042
ztlctl agent session cost                  # accumulated token cost
ztlctl agent session cost --report 45000   # workflow reports context usage
ztlctl agent session log "Finding" --pin   # pinned log entry
ztlctl agent context --topic "databases" --budget 8000
ztlctl agent brief                         # quick orientation
ztlctl agent regenerate                    # re-derive self/ from config
```

### Unified Filter Grammar

Shared across all content-returning commands:

```bash
--type note|reference|log|task
--subtype decision|knowledge|article|tool|spec
--tag domain/scope                    # multiple --tag flags OR together
--topic cognitive-science
--status active|done|inbox|...
--maturity seed|budding|evergreen
--since 2026-01-01
--space notes|ops|self
--include-archived
--limit 20
--sort relevance|recency|graph|priority
```

> **Implementation note (Phase 4+5):** The `list` command implements all core filters: `--type`, `--status`, `--tag`, `--topic`, `--subtype`, `--maturity`, `--since`, `--include-archived`, `--space`, `--sort` (recency|title|type|priority), and `--limit`. Priority sort scores tasks using the existing weighted formula (priority×2 + impact×1.5 + (4−effort)), sorts in Python after DB fetch, and applies limit post-sort. The `search` command implements `--type`, `--tag`, `--space`, `--rank-by` (relevance|recency|graph), and `--limit`. The `--space` filter is shared across search, list, work-queue, and decision-support (Phase 5). The `graph` ranking mode multiplies BM25 scores by materialized PageRank values (Phase 5). The `recency` ranking uses BM25 × exponential time-decay with configurable `half_life_days` (Phase 5).

### Agent Context Protocol

Layered token-budgeted payload:

| Layer | Content | Priority |
|-------|---------|----------|
| 0 | Identity + methodology (self/ files) | Always included |
| 1 | Operational state: active session, recent decisions, work queue | Always included |
| 2 | Topic-scoped notes and references | Budget-dependent |
| 3 | Graph-adjacent content (1 hop from Layer 2) | Budget-dependent |
| 4 | Background: recent activity, garden signals, structural gaps | Budget-dependent |

### Session Context via Log-Based Checkpoints

**The tool provides primitives. The workflow makes judgments.**

All actions accept a `--cost` argument. Token cost is pre-computed per log entry and stored in the DB. Sessions expose accumulated cost on request.

**Checkpoint subtype:** A log entry with `subtype: checkpoint` captures accumulated context as a snapshot. The context service starts from the latest checkpoint by default.

**Log entry structure:**

```python
@dataclass
class LogEntry:
    id: int
    session_id: str
    timestamp: datetime
    type: str           # note_created | decision_made | search_performed | checkpoint | ...
    summary: str        # one-line (always retained under budget pressure)
    detail: str         # full context (dropped under budget pressure)
    cost: int           # pre-computed token count
    pinned: bool        # if True, never reduced
    references: list[str]
    metadata: dict
```

**Context retrieval with reduction:**

```
agent_context called
  → Find latest checkpoint in session
  → Load checkpoint content (accumulated snapshot)
  → Load log entries from checkpoint to now
  → If entries exceed budget: drop details first, then drop entries
  → Return: checkpoint context + reduced recent entries
```

The `--ignore-checkpoints` flag reads full history when needed.

### Search

- **Default:** FTS5 BM25 full-text search
- **Ranking:** Configurable via `--rank-by relevance|graph|recency`
  - `relevance`: BM25 score
  - `graph`: BM25 × PageRank
  - `recency`: BM25 × time decay
- **Semantic search:** Optional, feature-flagged (`[search] semantic_enabled = false`)

### Semantic Search

Optional vector similarity search using local embeddings and `sqlite-vec`.

**Components:**

| Component | Location | Purpose |
|-----------|----------|---------|
| `EmbeddingProvider` | `infrastructure/embeddings.py` | Pluggable embedding abstraction; wraps `sentence-transformers` |
| `VectorService` | `services/vector.py` | sqlite-vec `vec0` virtual table management, KNN queries |
| `vector` CLI group | `commands/vector.py` | `status` and `reindex` subcommands |

**Embedding pipeline:**

1. Content → `EmbeddingProvider.embed(text)` → `FLOAT[384]` vector
2. Vector → `sqlite-vec` `vec_items` virtual table (binary float32 format)
3. Query → KNN cosine distance search → ranked results

**Hybrid ranking:** `(1 - w) * bm25_norm + w * cosine_sim`, where `w = search.semantic_weight` (default 0.5).

**Graceful degradation:** When `sqlite-vec` or `sentence-transformers` is not installed, `VectorService.is_available()` returns False and all vector operations silently no-op. Falls back to BM25-only search.

**CLI commands:**

```bash
ztlctl vector status    # check availability and index stats
ztlctl vector reindex   # rebuild vector index for all content
```

**Configuration:** See `[search]` section in Configuration Reference (→ Section 17).

> **Implementation note (Phase 3+5+9):** Search supports `--rank-by relevance|recency|graph`. The `relevance` mode uses raw BM25 ordering. The `recency` mode applies BM25 × exponential time-decay (`exp(-age_days * ln2 / half_life_days)`) with configurable `half_life_days` in SearchConfig (Phase 5). The `graph` mode multiplies BM25 by materialized PageRank values from the nodes table (Phase 5). `GraphService.materialize_metrics()` computes and persists PageRank, degree centrality, and betweenness to the nodes table. `ztlctl graph materialize` triggers on demand; `ztlctl check --rebuild` also refreshes metrics. Semantic search (Phase 9, PR #57): `EmbeddingProvider` lazy-loads `all-MiniLM-L6-v2` model on first call (avoids startup cost when disabled). `VectorService` serializes vectors as compact binary (`struct.pack` float32) for sqlite-vec KNN queries. Integration points: `CreateService` auto-indexes via `VectorService.index_node()` when available; `QueryService` calls `VectorService.search_similar()` for hybrid ranking. Both `sqlite-vec` and `sentence-transformers` are optional dependencies in the `[semantic]` extra.

---

## 9. Database Layer

### Dual-Layer Architecture

**SQLite** — persistence, FTS5 full-text search, ACID transactions, WAL mode for concurrent reads.

**NetworkX** — in-memory graph algorithms (PageRank, Leiden, shortest path, betweenness). Rebuilt from SQLite per invocation. Lazy-loaded.

### Schema (SQLAlchemy Core)

```python
nodes = Table("nodes", metadata,
    Column("id", Text, primary_key=True),
    Column("title", Text, nullable=False),
    Column("type", Text, nullable=False),
    Column("subtype", Text),
    Column("status", Text, nullable=False),
    Column("maturity", Text),
    Column("topic", Text),
    Column("path", Text, nullable=False, unique=True),
    Column("aliases", Text),              # JSON array
    Column("session", Text),              # LOG-NNNN
    Column("archived", Integer, default=0),
    Column("created", Text, nullable=False),
    Column("modified", Text, nullable=False),
    # Materialized graph metrics
    Column("degree_in", Integer, default=0),
    Column("degree_out", Integer, default=0),
    Column("pagerank", REAL, default=0.0),
    Column("cluster_id", Integer),
    Column("betweenness", REAL, default=0.0),
)

edges = Table("edges", metadata,
    Column("source_id", Text, ForeignKey("nodes.id"), nullable=False),
    Column("target_id", Text, ForeignKey("nodes.id"), nullable=False),
    Column("edge_type", Text, default="relates"),
    Column("source_layer", Text),
    Column("weight", REAL, default=1.0),
    Column("bidirectional", Integer),
    Column("created", Text, nullable=False),
    UniqueConstraint("source_id", "target_id", "edge_type"),
)

# FTS5 virtual table — created via raw DDL since SQLAlchemy cannot express
# virtual tables natively. Standalone (no content= clause); the service
# layer manages inserts explicitly.
# CREATE VIRTUAL TABLE IF NOT EXISTS nodes_fts USING fts5(id UNINDEXED, title, body)

tags_registry = Table("tags_registry", metadata,
    Column("tag", Text, primary_key=True),
    Column("domain", Text, nullable=False),
    Column("scope", Text, nullable=False),
    Column("created", Text, nullable=False),
    Column("description", Text),
)

node_tags = Table("node_tags", metadata,
    Column("node_id", Text, ForeignKey("nodes.id"), nullable=False),
    Column("tag", Text, nullable=False),
    UniqueConstraint("node_id", "tag"),
)

id_counters = Table("id_counters", metadata,
    Column("type_prefix", Text, primary_key=True),
    Column("next_value", Integer, nullable=False, default=1),
)

reweave_log = Table("reweave_log", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("source_id", Text, nullable=False),
    Column("target_id", Text, nullable=False),
    Column("action", Text, nullable=False),
    Column("direction", Text),
    Column("timestamp", Text, nullable=False),
    Column("undone", Integer, default=0),
)

event_wal = Table("event_wal", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("hook_name", Text, nullable=False),
    Column("payload", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("error", Text),
    Column("retries", Integer, default=0),
    Column("session_id", Text),
    Column("created", Text, nullable=False),
    Column("completed", Text),
)

session_logs = Table("session_logs", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("session_id", Text, nullable=False),
    Column("timestamp", Text, nullable=False),
    Column("type", Text, nullable=False),
    Column("subtype", Text),
    Column("summary", Text, nullable=False),
    Column("detail", Text),
    Column("cost", Integer, default=0),
    Column("pinned", Integer, default=0),
    Column("references", Text),
    Column("metadata", Text),
)
```

### Indexes

Performance indexes on high-cardinality columns, created via `metadata.create_all()`:

| Index | Column | Table |
|-------|--------|-------|
| `ix_nodes_type` | `type` | `nodes` |
| `ix_nodes_status` | `status` | `nodes` |
| `ix_nodes_archived` | `archived` | `nodes` |
| `ix_nodes_topic` | `topic` | `nodes` |
| `ix_edges_source` | `source_id` | `edges` |
| `ix_edges_target` | `target_id` | `edges` |
| `ix_node_tags_tag` | `tag` | `node_tags` |

> **Note:** The `edges.bidirectional` column is reserved but not yet maintained by services. It exists in the schema for future bidirectional edge materialization.
>
> **Note:** All columns with `default=` also have `server_default=` to ensure `metadata.create_all()` and Alembic migrations produce identical DDL with `DEFAULT` clauses.

### Transaction Model

The `Vault.transaction()` context manager coordinates DB + file + graph writes:

- **DB**: Native SQLAlchemy `engine.begin()` with auto-commit/rollback.
- **Files**: Compensation-based — newly created files are deleted, modified files are restored from backup, on rollback. Rollback is best-effort per file to avoid masking the original exception.
- **Graph**: Cache is invalidated on transaction end (success or failure). Lazy-rebuilt from DB on next access.

**Warning:** Do not access `vault.graph` within a transaction block — the graph is built from committed DB state and will not reflect pending writes. Access the graph only *after* the transaction succeeds.

The `VaultTransaction` object yields a connection and tracked file I/O methods (`write_file()`, `write_content()`, `read_file()`, `read_content()`, `resolve_path()`). All write services must use `vault.transaction()` — not `engine.begin()` directly — to ensure coordinated rollback.

`ztlctl check` (→ Section 14) reconciles any remaining drift between files and DB.

### Migrations

Alembic with auto-generated migrations from model diffs:

```bash
ztlctl upgrade              # Run pending migrations
ztlctl upgrade --check      # Show pending without applying
```

**Upgrade pipeline:** BACKUP → MIGRATE → VALIDATE → RECONCILE → REPORT

DB stored at `{vault_root}/.ztlctl/ztlctl.db`. Tracked in git (clone gives working tool). Backups in `.ztlctl/backups/` (gitignored).

> **Implementation note (Phase 7):** Alembic migration infrastructure is fully implemented. Programmatic `build_config(db_url)` constructs Alembic `Config` without an `alembic.ini` file — `script_location` points to the bundled `infrastructure/database/migrations/` package. Baseline migration (`001_baseline.py`) creates all 8 tables matching `schema.py`. `UpgradeService` implements `check_pending()`, `apply()` (BACKUP → MIGRATE → VALIDATE → REPORT), and `stamp_current()`. Pre-Alembic vault detection: if tables exist but no `alembic_version`, stamp at head instead of running CREATE TABLE migrations. `stamp_head()` is called during `ztlctl init` to mark fresh databases at the current migration head.

---

## 10. CLI Interface

### Service Layer

All business logic returns `ServiceResult` — a frozen Pydantic `BaseModel` (not `dataclass`). This enables `model_dump_json()` for `--json` output and enforces immutability:

```python
class ServiceError(BaseModel):
    """Structured error payload."""
    model_config = {"frozen": True}

    code: str
    message: str
    detail: dict[str, Any] = Field(default_factory=dict)


class ServiceResult(BaseModel):
    """Universal return type for all service operations."""
    model_config = {"frozen": True}

    ok: bool
    op: str
    data: dict[str, Any] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    error: ServiceError | None = None
    meta: dict[str, Any] | None = None
```

The CLI is a thin presentation layer that renders `ServiceResult` for humans (Rich output, colors, icons, progress bars) or machines (`--json`).

### Global Flags

| Flag | Purpose |
|------|---------|
| `--json` | Structured JSON output |
| `--quiet / -q` | Minimal output |
| `--verbose / -v` | Detailed output with debug info |
| `--no-interact` | Non-interactive mode (no prompts) |
| `--no-reweave` | Skip reweave on creation |
| `--config / -c` | Override config file path |
| `--sync` | Force synchronous event dispatch |

`--json` and `--no-interact` are **orthogonal**. `--json` controls output format. `--no-interact` controls interactivity. Neither implies the other.

### ZtlSettings

All runtime state — CLI flags, env vars, TOML config sections, and resolved paths — is unified into a single frozen `ZtlSettings` object (Pydantic Settings v2). The CLI wraps `ZtlSettings` in an `AppContext` object stored on `click.Context.obj`:

```python
class ZtlSettings(BaseSettings):
    """Unified settings: CLI flags + env vars + TOML + code defaults."""
    model_config = {"frozen": True, "env_prefix": "ZTLCTL_"}

    # Resolved paths
    vault_root: Path = Field(default_factory=Path.cwd)
    config_path: Path | None = None

    # CLI flags
    json_output: bool = False
    quiet: bool = False
    verbose: bool = False
    no_interact: bool = False
    no_reweave: bool = False
    sync: bool = False

    # TOML sections (reuse existing frozen section models)
    vault: VaultConfig = Field(default_factory=VaultConfig)
    agent: AgentConfig = Field(default_factory=AgentConfig)
    reweave: ReweaveConfig = Field(default_factory=ReweaveConfig)
    # ... all 12 section models
```

**Priority chain** (highest to lowest): CLI flags → `ZTLCTL_*` env vars → `ztlctl.toml` (walk-up discovery) → code-baked defaults. Constructed via `ZtlSettings.from_cli()` which discovers the TOML file, resolves `vault_root`, and merges all sources. Thread-safe TOML path passing uses `threading.local()`.

### AppContext

The CLI stores an `AppContext` on `click.Context.obj` — not `ZtlSettings` directly. `AppContext` provides two features on top of raw settings:

1. **Lazy Vault** — `--help` and `--version` never touch the database. The `Vault` is constructed on first access via a cached property.
2. **Centralized `emit()`** — routes `ServiceResult` to stdout (ok) or stderr + `SystemExit(1)` (error), replacing the repeated 4-line output boilerplate across all command handlers.

```python
class AppContext:
    def __init__(self, settings: ZtlSettings) -> None:
        self.settings = settings
        self._vault: Vault | None = None

    @property
    def vault(self) -> Vault:
        if self._vault is None:
            self._vault = Vault(self.settings)
        return self._vault

    def emit(self, result: ServiceResult) -> None:
        output = format_result(result, json_output=self.settings.json_output)
        if result.ok:
            click.echo(output)
            # In JSON mode, warnings are already in the serialized payload.
            if not self.settings.json_output:
                for warning in result.warnings:
                    click.echo(f"WARNING: {warning}", err=True)
        else:
            click.echo(output, err=True)
            raise SystemExit(1)
```

Commands receive `AppContext` via `@click.pass_obj` and typically reduce to one or two lines:

```python
@query_group.command("get")
@click.argument("content_id")
@click.pass_obj
def get(app: AppContext, content_id: str) -> None:
    app.emit(QueryService(app.vault).get(content_id))
```

### Output Rendering

Three verbosity modes, all rendering `ServiceResult`:

| Mode | Flag | Rendering |
|------|------|-----------|
| Quiet | `--quiet` | One-line: `OK: create_note` or `ERROR: create_note — message` |
| Default | (none) | Rich Console: styled text, tables, icons, colored status |
| Verbose | `--verbose` | Default + debug details (timing, full error payloads) |
| JSON | `--json` | `ServiceResult.model_dump_json()` — structured, machine-readable |

The output layer (`output/renderers.py`) dispatches to `render_quiet()`, `render_default()`, or `render_verbose()` based on settings. Item lists render as Rich tables with auto-detected Score columns (present for both search results and priority-sorted lists). Warnings go to stderr in human mode (so they don't pollute piped output) and are included in the serialized payload in JSON mode.

> **Implementation note (Phase 4):** The original `format_result()` function was replaced by a Rich-based rendering layer. Three renderers share a common `_render_error()` helper. The `_render_item_table()` function auto-detects score columns via `"score" in items[0]`, avoiding the need for explicit sort-mode flags in the renderer.

### Vault

The `Vault` class is constructed from `ZtlSettings` and serves as the repository for all data access. It owns the database engine, graph engine, and filesystem operations. Services receive a `Vault` via `BaseService.__init__()`.

```python
class Vault:
    def __init__(self, settings: ZtlSettings) -> None:
        self._engine = init_database(self.root)  # idempotent
        self._graph = GraphEngine(self._engine)

    @contextmanager
    def transaction(self) -> Iterator[VaultTransaction]:
        """Coordinated DB + file + graph transaction."""
        ...

class BaseService:
    def __init__(self, vault: Vault) -> None:
        self._vault = vault
```

### Command Registration

Commands are registered via deferred imports in `register_commands()` to keep `ztlctl --help` fast as the codebase grows:

| Groups (7) | Standalone (8) |
|-----------|---------------|
| `create`, `query`, `graph`, `agent`, `garden`, `export`, `workflow` | `check`, `init`, `upgrade`, `reweave`, `archive`, `extract`, `update`, `supersede` |

> **Note:** The `init` command lives in `init_cmd.py` to avoid shadowing the Python builtin. It registers as `@click.command("init")`.

> **Implementation note (Phase 4):** All commands and groups use custom base classes `ZtlCommand` and `ZtlGroup` (in `commands/_base.py`). These support an `examples` kwarg that auto-registers an eager `--examples` flag — processed before argument validation, same pattern as Click's `--version`. `ZtlGroup` sets `command_class = ZtlCommand` so subcommands inherit the base class automatically. All service-layer errors in command handlers route through `app.emit(ServiceResult)` for consistent structured output in `--json` mode.

### Config Discovery

Walk up from cwd to find `ztlctl.toml` (like git). Override via `ZTLCTL_CONFIG` env var or `--config` flag.

### Plugin Extension

Python entry points (`ztlctl.plugins` group). Plugins register commands, hooks, MCP tools/resources.

```toml
# Third-party plugin registration
[project.entry-points."ztlctl.plugins"]
my-plugin = "my_package.plugin:MyPlugin"
```

---

## 11. Init and Self-Generation

### `ztlctl init`

Interactive by default. Creates vault + workflow (use `--no-workflow` to skip workflow setup).

```
$ ztlctl init
  Vault name [research]: my-research
  Client [obsidian]: obsidian           # vanilla | obsidian
  Tone [research-partner]: research-partner  # research-partner | assistant | minimal
  Initial topics: cognitive-science, engineering
```

### Self/ Generation

Jinja2 templates bundled with the package. Config values flow into templates:

- `self/identity.md` — role, critique protocol, contextual graduation, anti-patterns
- `self/methodology.md` — core principles, tool configuration, content types

The `research-partner` tone includes the full behavioral framework proven in the CONV-0017 workspace.

`ztlctl agent regenerate` re-derives self/ from current config. Staleness detection via timestamp comparison.

> **Implementation note (Phase 5+7):** `ztlctl init` supports both interactive (prompts) and non-interactive (`--name/--client/--tone/--topics`) modes. The init flow creates the vault directory structure, writes `ztlctl.toml`, initializes the database, stamps the Alembic migration head (Phase 7), generates `self/identity.md` and `self/methodology.md` from Jinja2 templates, and optionally scaffolds `.obsidian/` for Obsidian clients. `ztlctl agent regenerate` regenerates self/ documents from current config with staleness detection. Copier workflow templates (`ztlctl workflow init/update`) are deferred — the init command covers the core vault bootstrapping need.

### Vault Structure

```
{vault-root}/
├── ztlctl.toml
├── .ztlctl/
│   ├── ztlctl.db
│   ├── alembic/
│   ├── backups/
│   ├── plugins/
│   └── workflow-answers.yml
├── self/
│   ├── identity.md
│   └── methodology.md
├── notes/
│   └── {topics}/
├── ops/
│   ├── logs/
│   └── tasks/
└── .obsidian/              # if client = obsidian
    ├── snippets/ztlctl.css
    └── graph-colors.md
```

---

## 12. Progressive Disclosure

Cross-cutting pattern across all features.

**Four dimensions:**
1. **Command complexity:** Minimal args required → full flags available
2. **Output verbosity:** `--quiet` → default → `--verbose`
3. **Configuration:** Code-baked defaults → sparse TOML overrides → deep tuning
4. **Error detail:** Error code always present → `--verbose` adds detail block with suggestions

**Sparse TOML contract:** Defaults baked into typed dataclasses. TOML only contains user overrides. A fresh vault has a 4-line config.

**`--examples` flag** on every command: annotated real-world usage patterns.

---

## 13. Export

Thin, on-demand utility. No automatic triggers.

```bash
ztlctl export markdown --output ./export/  # Full vault as portable markdown
ztlctl export indexes --output ./export/   # For GitHub rendering
ztlctl export graph --format dot           # GraphViz visualization
ztlctl export graph --format json          # D3/vis.js compatible
```

> **Implementation note (Phase 5):** All three export subcommands are implemented. `export markdown` copies vault content into a portable directory tree. `export indexes` generates topic and tag index markdown files suitable for GitHub rendering. `export graph` supports both `dot` (GraphViz) and `json` (D3/vis.js) output formats. All commands accept `--output` to specify the target directory.

---

## 14. Integrity and Reconciliation

Single `ztlctl check` command following the linter pattern.

```bash
ztlctl check                              # Report issues
ztlctl check --fix                        # Safe automatic repairs
ztlctl check --fix --level aggressive     # Aggressive repairs
ztlctl check --rebuild                    # Full DB rebuild from files
ztlctl check --rollback                   # Restore from latest backup
```

**Four categories:** DB-file consistency, schema integrity, graph health, structural validation.

**Safety contract:** Body text NEVER modified by check. Frontmatter only re-read. Safe fixes only touch rebuildable/recomputable data.

**Backup strategy:** Automatic SQLite file-copy before destructive operations. Stored in `.ztlctl/backups/`.

> **Implementation note (Phase 3):** CheckService implements `check()`, `fix()`, `rebuild()`, and `rollback()`. All four check categories are implemented. Safe fixes cover orphan DB rows, dangling edges, missing FTS5 entries, and file-to-DB re-sync. Aggressive fixes add full edge re-indexing (clear and rebuild from files) and frontmatter key reordering via `order_frontmatter()`. Rebuild uses two-pass loading (nodes first, then edges) to maintain referential integrity. Fix and rebuild operations use `VaultTransaction` for atomic DB + file writes. Wikilink resolution during rebuild/re-index shares the 3-step `_resolve_wikilink()` function from CreateService. Backup naming uses `ztlctl-{YYYYMMDDTHHmmss}.db` format with configurable retention via `check.backup_max_count`. Rollback disposes the engine (releasing SQLite locks) before restoring.

---

## 15. Event System and Plugins

### Event Bus (pluggy)

Eight lifecycle events dispatched asynchronously via `ThreadPoolExecutor`:

| Event | Payload | When |
|-------|---------|------|
| `post_create` | type, id, title, path, tags | After content creation |
| `post_update` | type, id, fields_changed, path | After content update |
| `post_close` | type, id, path, summary | After close/archive |
| `post_reweave` | source_id, affected_ids, links_added | After reweave |
| `post_session_start` | session_id | After session begins |
| `post_session_close` | session_id, stats | After session closes |
| `post_check` | issues_found, issues_fixed | After integrity check |
| `post_init` | vault_name, client, tone | After vault init |

**Write-ahead log (WAL)** for reliability: events persist before dispatch, retry on failure, dead-letter after max retries. Session close drains the WAL as a sync barrier.

### Plugin System

**Discovery:** entry_points (pip-installed) + `.ztlctl/plugins/` (local).

**Capabilities:** Lifecycle hooks (`@hookimpl`), CLI commands, MCP tools, MCP resources, configuration schema.

Plugin failures are always warnings, never errors. A broken plugin degrades the workflow; it never degrades the core tool.

**Built-in plugin entry point:**

```toml
[project.entry-points."ztlctl.plugins"]
git = "ztlctl.plugins.builtins.git:GitPlugin"
```

### Git Plugin (Built-In)

```toml
[git]
enabled = true
branch = "main"
auto_push = true
commit_style = "conventional"
batch_commits = true           # true = per-session, false = per-operation
auto_ignore = true
```

**Batch mode (default):** Stage on each operation, commit once at session close. Session boundaries are the natural commit boundary for agent-driven workflows.

### Workflow Templates

`ztlctl workflow init` — interactive, CRA-style:

```
Source control: git | none
Viewer: obsidian | vanilla
Workflow: claude-driven | agent-generic | manual
Skill set: research | engineering | minimal
```

Powered by Copier. Composable template layers. `ztlctl workflow update` merges template improvements.

`ztlctl init` runs workflow init by default. `--no-workflow` to skip.

### Packaging

```bash
pip install ztlctl            # Core + event bus + plugins + git + templates
pip install ztlctl[mcp]       # Adds MCP adapter
```

Claude Code plugin ships as a separate artifact (plugin.json + skills/ + hooks/) with an independent release cycle.

> **Implementation note (Phase 6+9):** EventBus is implemented with WAL-backed async dispatch (`ThreadPoolExecutor`, configurable `max_workers=2`). Events persist to `event_wal` table before dispatch, retry on failure (configurable `max_retries=3`), and transition to `dead_letter` status after exhausting retries. `--sync` flag forces synchronous dispatch for deterministic testing. `drain()` retries all pending/failed events synchronously — called as a sync barrier at session close. PluginManager uses `pluggy.load_setuptools_entrypoints("ztlctl.plugins")` for discovery; built-in GitPlugin is registered explicitly via `register_plugin()` in `Vault.init_event_bus()`. GitPlugin implements all 8 hooks with subprocess-based git operations; all calls are wrapped in `try/except (OSError, CalledProcessError)` so a missing git binary silently degrades. `BaseService._dispatch_event()` is the fire-and-forget helper — plugin failures are captured as warnings in the ServiceResult, never propagated. Local directory plugin discovery (Phase 9, PR #56): `PluginManager.discover_and_load(local_dir=...)` scans `.ztlctl/plugins/*.py` for classes with `@hookimpl`-decorated methods; files are loaded via `importlib.util.spec_from_file_location()` with module name `ztlctl_local_plugin_{stem}`. Underscore-prefixed files are excluded. Load errors are warnings, not failures. Copier workflow templates remain deferred.

---

## 16. MCP Adapter

Optional extra (`pip install ztlctl[mcp]`). Thin adapter over the service layer.

The MCP module uses `try/except ImportError` with a module-level `mcp_available` flag. When the `mcp` extra is not installed, the module loads without error but `create_server()` raises `RuntimeError` with install instructions.

### Tools (12)

| Category | Tools |
|----------|-------|
| Creation | `create_note`, `create_reference`, `create_log`, `create_task` |
| Lifecycle | `update_content`, `close_content`, `reweave` |
| Query | `search`, `get_document`, `get_related`, `agent_context` |
| Session | `session_close` |

### Resources (6)

| URI | Content |
|-----|---------|
| `ztlctl://context` | Full vault context |
| `ztlctl://self/identity` | Agent identity |
| `ztlctl://self/methodology` | Vault methodology |
| `ztlctl://overview` | Vault statistics |
| `ztlctl://work-queue` | Prioritized tasks |
| `ztlctl://topics` | Topic listing |

### Prompts (4)

`research_session`, `knowledge_capture`, `vault_orientation`, `decision_record` — portable workflows for any MCP client.

### Transport

Three transport options:

| Transport | Flag | Use Case |
|-----------|------|----------|
| `stdio` (default) | `--transport stdio` | Sub-ms latency, local integration |
| `sse` | `--transport sse --host 127.0.0.1 --port 8000` | Server-Sent Events over HTTP |
| `streamable-http` | `--transport streamable-http --host 127.0.0.1 --port 8000` | HTTP streaming for remote access |

### Tool Proliferation Guard

At 15+ tools (from plugin registration), activate `discover_tools` meta-tool for progressive discovery by category.

> **Implementation note (Phase 6+9):** All 12 tools, 6 resources, and 4 prompts are implemented as thin service adapters. Each has a `_<name>_impl(vault, **params) -> dict` function that is testable without the `mcp` package installed. `register_tools()`, `register_resources()`, and `register_prompts()` wrap these with `@server.tool()` / `@server.resource()` / `@server.prompt()` FastMCP decorators. `create_server(vault_root, host, port)` creates a `ZtlSettings` + `Vault` from the vault root and registers all components. `ztlctl serve --transport {stdio|sse|streamable-http}` is the CLI entry point with `--host` and `--port` options for HTTP transports (Phase 9, PR #56). Transport is passed to `server.run(transport=...)` at runtime. The tool proliferation guard (discover_tools meta-tool) is deferred.

---

## 17. Configuration Reference

### Configuration Models

All configuration sections are frozen Pydantic `BaseModel` classes. Defaults are code-baked; TOML only contains user overrides. Sections are composed into `ZtlSettings` (Pydantic Settings v2), which merges CLI flags, env vars, TOML, and defaults into a single frozen object via `ZtlSettings.from_cli()`.

| TOML Section | Pydantic Model | Key Fields |
|-------------|----------------|------------|
| `[vault]` | `VaultConfig` | `name`, `client` |
| `[agent]` | `AgentConfig` | `tone`, `context` (nested `AgentContextConfig`) |
| `[reweave]` | `ReweaveConfig` | `enabled`, weights, thresholds |
| `[garden]` | `GardenConfig` | `seed_age_warning_days`, evergreen criteria |
| `[search]` | `SearchConfig` | `semantic_enabled`, `semantic_weight`, `embedding_model`, `embedding_dim`, `half_life_days` |
| `[session]` | `SessionConfig` | `close_reweave`, `close_orphan_sweep` |
| `[tags]` | `TagsConfig` | `auto_register` |
| `[check]` | `CheckConfig` | `backup_retention_days`, `backup_max_count` |
| `[plugins]` | `PluginsConfig` | `git`, `obsidian` (dicts) |
| `[git]` | `GitConfig` | `enabled`, `branch`, `auto_push`, `batch_commits` |
| `[mcp]` | `McpConfig` | `enabled`, `transport` |
| `[workflow]` | `WorkflowConfig` | `template`, `skill_set` |

`ZtlSettings` composes all section models plus CLI flags (`no_reweave`, `sync`, `log_json`, `verbose`) and resolved paths. All models are frozen.

**Config discovery:** Walk up from cwd looking for `ztlctl.toml`. `ZTLCTL_CONFIG` env var overrides walk-up. `--config` CLI flag overrides both. No file found → all-defaults `ZtlSettings()`.

**Priority chain:** Init kwargs (CLI flags) → `ZTLCTL_*` env vars → TOML file → code defaults. Thread-safe TOML path passing via `threading.local()`.

### Minimal Config (Fresh Vault)

```toml
[vault]
name = "my-research"
client = "obsidian"

[agent]
tone = "research-partner"
```

### Full Config (All Sections)

```toml
[vault]
name = "my-research"
client = "obsidian"

[agent]
tone = "research-partner"

[agent.context]
default_budget = 8000
layer_0_min = 500
layer_1_min = 1000
layer_2_max_notes = 10
layer_3_max_hops = 1

[reweave]
enabled = true
min_score_threshold = 0.6
max_links_per_note = 5
lexical_weight = 0.35
tag_weight = 0.25
graph_weight = 0.25
topic_weight = 0.15

[garden]
seed_age_warning_days = 7
evergreen_min_key_points = 5
evergreen_min_bidirectional_links = 3

[search]
semantic_enabled = false
embedding_model = "local"
embedding_dim = 384
semantic_weight = 0.5
half_life_days = 30.0

[session]
close_reweave = true
close_orphan_sweep = true
close_integrity_check = true
orphan_reweave_threshold = 0.2

[tags]
auto_register = true

[check]
backup_retention_days = 30
backup_max_count = 10

[plugins]
git = { enabled = true }
obsidian = { enabled = true }

[git]
branch = "main"
auto_push = true
commit_style = "conventional"
batch_commits = true
auto_ignore = true

[mcp]
enabled = true
transport = "stdio"

[workflow]
template = "claude-driven"
skill_set = "research"
```

---

## 18. Dependencies

### Required

```toml
dependencies = [
    "click>=8.1",
    "pydantic>=2.0",
    "sqlalchemy>=2.0",
    "alembic>=1.13",
    "networkx>=3.0",
    "ruamel.yaml>=0.18",
    "jinja2>=3.1",
    "pluggy>=1.4",
    "rich>=13.0",
    "structlog>=24.0",
    "scipy>=1.17.1",
]
```

### Optional

```toml
[project.optional-dependencies]
mcp = ["mcp>=1.0", "anyio>=4.0"]
community = ["leidenalg"]
semantic = ["sqlite-vec>=0.1", "sentence-transformers>=2.2"]
```

---

## 19. Decision Log

Decisions made during the design process (CONV-0017):

| ID | Decision | Rationale |
|----|----------|-----------|
| DEC-0021 | Reweave scoring: percentile normalization, high threshold (0.6), add-and-flag-stale | Conservative default prevents noise; percentile handles vault size variance; flag-not-prune keeps humans in control |
| DEC-0022 | Subtypes: ContentModel class hierarchy, strict machine / flexible garden | Validation as classmethods on model subclasses; build internally first, tune before exposing to users |
| DEC-0023 | Session context: log-based checkpoints, tool provides primitives | Tool never guesses; checkpoints bound reduction windows; workflow makes judgment calls |
| — | Layered architecture (services → presentation) | Same logic backs CLI, MCP, and future interfaces |
| — | SQLite + NetworkX dual-layer DB | SQLite for persistence/FTS; NetworkX for graph algorithms; rebuilt per invocation |
| — | SQLAlchemy Core, not ORM | CLI = short-lived processes; no session management payoff |
| — | Git as plugin, not core | ztlctl is a KMS tool, not a VCS tool; allows alternative VCS |
| — | Async-by-default event dispatch | Never interrupt user; data safety via DB write; workflow via async hooks |
| — | Session as first-class container | Replaces conversation concept; 1:N with Claude sessions; replaces memory bank |
| — | Content-hash IDs: title seeds permanent ID | 8 hex chars from SHA-256; collision = error; no reverse computation |
| — | One query, one answer | Minimize agent round-trips; composed queries over granular |
| — | Copier for workflow templates | Template updates merge with user customizations |
| — | MCP prompts for portability | Workflows available to any MCP client, not locked to Claude Code |
| — | Progressive disclosure across all dimensions | Sparse TOML, `--examples`, verbosity levels |
| — | Session close as graph enrichment | Cross-session reweave + orphan sweep + integrity check + WAL drain |
| — | Materialization eliminated | Every use case has a better native solution via CLI+DB |
| — | `ztlctl upgrade` as first-class command | Worst-case schema migration with backup/rollback |
| — | Batch commits by default | Session = natural commit boundary for agent workflows |
| — | Claude Code plugin as separate artifact | Skills evolve faster than tool schemas; independent release cycle |
| — | Pydantic BaseModel for ServiceResult, not dataclass | Frozen models provide JSON serialization via `model_dump_json()`, validation, and immutability |
| — | ServiceError as separate model | Structured `code`/`message`/`detail` instead of bare dict enables consistent error handling |
| — | StrEnum (Python 3.13+) for all enums | Values serialize cleanly to strings without `.value`; replaces `(str, Enum)` pattern |
| — | ZtlSettings (Pydantic Settings v2) replaces ZtlConfig | Single frozen object merges CLI flags, env vars, TOML, and code defaults; eliminates separate config object |
| — | ContentModel hierarchy replaces SubtypeRule strategy pattern | Validation, required sections, and status transitions live as classmethods on model subclasses; eliminates parallel hierarchy since types map 1:1 to classes |
| — | CONTENT_REGISTRY dict replaces SubtypeRule registry | Simple `dict[str, type[ContentModel]]` with `get_content_model()` lookup; subtype priority with type fallback |
| — | ValidationResult frozen dataclass | Replaces SubtypeValidation; `valid`, `errors`, `warnings` fields; returned by validate_create/validate_update classmethods |
| — | Vault as repository with ACID transaction coordination | DB (native SQLAlchemy), files (compensation-based rollback), graph (cache invalidation); single dependency for all services |
| — | BaseService with Vault injection | All services inherit `BaseService(vault)` and use `self._vault.transaction()` for data access |
| — | Thread-local TOML path for ZtlSettings construction | `threading.local()` scopes TOML path between `from_cli()` and `settings_customise_sources()`; avoids class-level mutation |
| — | ForeignKey constraints on edges and node_tags | Referential integrity enforced at DB level; edges.source_id/target_id → nodes.id, node_tags.node_id → nodes.id |
| — | Best-effort file rollback in Vault transactions | Per-file try/except in rollback prevents cascading failures from masking the original exception |
| — | `write_body(**kwargs)` uniform signature | All content models accept kwargs; DecisionModel uses named sections (context, choice, etc.); allows future typing refinement |
| — | Deferred imports in command registration | `register_commands()` uses local imports to keep `ztlctl --help` fast at scale |
| — | `init_cmd.py` naming for init command | Avoids shadowing Python's `init` builtin; registers as `@click.command("init")` |
| — | MCP import guard with `mcp_available` flag | `try/except ImportError` prevents optional extra from breaking core CLI |
| — | AppContext wraps ZtlSettings on `ctx.obj` | Lazy Vault (--help never touches DB) + centralized `emit()` for exit codes and stderr routing; separates CLI adapter concerns from configuration |
| — | `_generate_id()` returns `None` instead of raising | Service methods never raise on bad input; caller converts to `ServiceResult(ok=False)`, maintaining the no-exceptions-cross-service-boundary contract |
| — | Leiden → Louvain fallback for community detection | `leidenalg` is an optional extra; Louvain (bundled with NetworkX) provides adequate results; warn in `ServiceResult.warnings` |
| — | FTS5 standalone DDL (no `content=` clause, no `Table()`) | SQLAlchemy cannot express virtual tables natively; standalone FTS avoids `content=` sync issues; service layer manages inserts explicitly |
| — | BaseService exposes `_vault` only (no public `.vault` property) | Services access vault via `self._vault`; no public accessor since external callers should use service methods, not reach through to the repository |
| — | GraphEngine loads node attributes (type, title) | Graph algorithms need node metadata for result building; avoids per-node DB lookups in service methods |
| — | Reweave 4-signal scoring with percentile normalization | BM25 (percentile), Jaccard tags, graph proximity, topic co-occurrence; configurable weights; conservative 0.6 threshold |
| — | Reweave audit trail via `reweave_log` table | Every add/remove tracked with timestamp; enables undo of specific operations or latest batch |
| — | Garden note body protection in reweave | Frontmatter `links.relates` added but body wikilinks never injected when `maturity` is set |
| — | UpdateService note status propagation | Automatic recompute from outgoing edge count after any update; prevents status drift without explicit commands |
| — | FTS5 DELETE + INSERT for updates | FTS5 virtual tables don't support UPDATE; service layer manages sync explicitly |
| — | CheckService two-pass rebuild | Nodes inserted first, then edges; ensures referential integrity during full rebuild from files |
| — | CheckService backup before destructive ops | Timestamped `ztlctl-{YYYYMMDDTHHmmss}.db` copies; configurable retention via `check.backup_max_count` |
| — | SessionService TOCTOU fix: read+write in one transaction | Session lookup and status update inside same `VaultTransaction` block; prevents race where session state changes between read and write |
| — | Stub service methods return `ServiceResult`, not `NotImplementedError` | Maintains no-exceptions-cross-service-boundary contract; `NOT_IMPLEMENTED` error code for graceful CLI/MCP handling. All stubs replaced with implementations in Phase 7 |
| — | Database indexes on high-cardinality columns | 7 indexes across nodes, edges, node_tags; improves query performance for filtered listing and edge traversal |
| — | Path traversal guard in `resolve_content_path()` | `path.resolve().is_relative_to(vault_root.resolve())` prevents crafted topic/content_id from escaping vault |
| — | Human-readable output: Rich styled tables and text | Phase 4 replaced `OK:` prefix format with Rich Console rendering; quiet mode retains one-line prefix format; JSON mode unchanged |
| — | Command stubs receive `AppContext`, not `ZtlSettings` | Ensures correct type flow through Click context; lazy Vault and `emit()` available to all commands |
| — | TOML parse errors surface as `ClickException` | `tomllib.TOMLDecodeError` caught and wrapped with file path context; prevents cryptic stack traces |
| — | Shared wikilink resolution function `_resolve_wikilink()` | Title → alias (`json_each`) → ID; shared between CreateService (indexing) and CheckService (rebuild/re-index) |
| — | Shared test helpers in `conftest.py` | `create_note()`, `create_reference()`, `create_task()`, `create_decision()`, `start_session()` as plain functions with deferred imports |
| — | ZtlCommand/ZtlGroup base classes with eager `--examples` | Same pattern as Click's `--version`; `is_eager=True` + `expose_value=False` processes before argument parsing; `command_class = ZtlCommand` on groups for subcommand inheritance |
| — | Rich output layer with 3 verbosity modes | `--quiet` (one-line), default (styled tables/text), `--verbose` (debug details); renderer dispatches on `AppContext.settings` flags |
| — | Score column auto-detection in renderer | `"score" in items[0]` check renders Score column for both search results and priority-sorted list results; no explicit flag needed |
| — | Shared `services/_helpers.py` for date/tag utilities | `today_iso()`, `now_iso()`, `now_compact()`, `parse_tag_parts()`; eliminates 5× `_today()` and 3× `_now_iso()` (with format inconsistency) duplication |
| — | Two timestamp formats: `now_iso()` vs `now_compact()` | Standard ISO for audit trails/session logs; compact (no colons) for backup filenames; makes distinction explicit after fixing silent format divergence |
| — | All command errors route through `app.emit(ServiceResult)` | Ensures `--json` mode outputs structured error payloads; replaces `raise SystemExit(1)` bypass in update and batch commands |
| — | Priority sort: Python-side scoring with post-sort limit | No SQL `ORDER BY` for priority; fetch all matching rows, score in Python using frontmatter fields, sort, then apply limit; same pattern as `work_queue()` |
| — | Programmatic Alembic config (no alembic.ini) | `build_config(db_url)` sets `script_location` and `sqlalchemy.url` on `Config()` object; works for embedded CLI tool without config file management |
| — | Pre-Alembic vault detection via `_tables_exist()` | Stamp at head instead of running CREATE TABLE migrations when tables exist but no `alembic_version`; handles upgrade path for existing users |
| — | `extract_decision` pipeline: create + overwrite + FTS5 | Uses CreateService pipeline for ID/indexing/frontmatter, then overwrites body with extracted JSONL content, updates FTS5, creates `derived_from` edge |
| — | `brief()` works without active session | Returns ok=True with session=null and vault stats; orientation is useful even outside a session |
| — | `garden seed` reuses create pipeline with maturity="seed" | No new service method; passes maturity through existing `create_note()` → `_create_content()` path |
| — | JSONL and DB entry types must stay in sync | `log_entry()` JSONL writes `entry_type` parameter, not hardcoded `"log_entry"`; enables `extract_decision()` to match entries by type in JSONL |
| — | `extract_decision` FTS5 + edge in single transaction | Prevents partial state if edge insert fails after FTS5 update; atomic write of all derived data |
| — | `server_default` alongside `default` on all schema columns | Ensures `metadata.create_all()` and Alembic migration produce identical DDL; prevents divergent DEFAULT clauses between init and upgrade paths |
| — | Init stamp failures surface as warnings, not silent | `ServiceResult.warnings` carries stamp failure message; user knows to run `ztlctl upgrade` without having to diagnose |

---

## 20. Implementation Backlog

| BL | Feature | Priority | Status | Scope |
|----|---------|----------|--------|-------|
| BL-0019 | Content Model (F1) | high | **done** | Types, spaces, IDs, lifecycle, ContentModel hierarchy, validation, registry |
| BL-0020 | Graph Architecture (F2) | high | **done** | 6 algorithms (related, themes, rank, path, gaps, bridges), CLI subcommands, node attribute loading |
| BL-0021 | Create Pipeline (F3) | high | **done** | 5-stage pipeline (notes, references, tasks), tag/link indexing, batch (service + CLI). Alias resolution complete (Phase 3). Batch CLI subcommand added (Phase 4). Event bus dispatch (Phase 6) |
| BL-0022 | Reweave (F4) | high | **done** | 4-signal scoring (BM25, Jaccard, graph proximity, topic), prune, undo with audit trail. CLI: `--dry-run`, `--prune`, `--undo`, `--undo-id`, `--id` all implemented (Phase 4). Interactive confirmation (Phase 5) |
| BL-0023 | Update & Close (F5) | high | **done** | 5-stage update pipeline, archive, supersede — all with CLI commands (Phase 4). Session close with enrichment (Phase 3). Event WAL drain (Phase 6). Session stubs (log_entry, cost, context, brief) fully implemented (Phase 7) |
| BL-0024 | ID System (F6) | high | **done** | Hashing, counters, validation |
| BL-0025 | Query Surface (F7) | high | **done** | 5 methods (search, get, list, work-queue, decision-support), CLI subcommands. Extended filters: `--subtype`, `--maturity`, `--since`, `--include-archived`, `--sort priority` (Phase 4). `--space` filter across search/list/work-queue/decision-support, `--rank-by` graph sort mode, BM25×time-decay recency ranking (Phase 7) |
| BL-0026 | Progressive Disclosure (F8) | medium | **done** | Rich output with 3 verbosity modes (quiet/default/verbose), `--examples` flag on all implemented commands, ZtlCommand/ZtlGroup base classes. Sparse TOML config unchanged |
| BL-0027 | Database Layer (F9) | high | **done** | SQLite, NetworkX, Alembic, upgrade. Indexes on nodes (type, status, archived, topic), edges (source, target), node_tags (tag) |
| BL-0028 | Export (F10) | low | **done** | Markdown, indexes, graph export. 3 export subcommands with format options |
| BL-0029 | Integrity (F11) | high | **done** | 4-category check (DB-file, schema, graph, structural), safe/aggressive fix, full rebuild, rollback. Uses VaultTransaction for atomicity |
| BL-0030 | CLI Interface (F12) | high | **done** | Rich rendering (tables, styled text, icons), 3 verbosity modes, structured JSON errors, ZtlCommand/ZtlGroup base classes, all service operations have CLI commands. Consolidated `_helpers.py` for shared service utilities |
| BL-0031 | Init & Self-Generation (F13) | high | **done** | Init flow, Jinja2 templates, Obsidian scaffolding, agent regenerate. Deferred: Copier workflow templates |
| BL-0032 | Event System & Plugins (F14) | high | **done** | WAL-backed EventBus, pluggy hookspecs, PluginManager with entry-point + local directory discovery, Git plugin (all 8 hooks). Deferred: Copier workflow templates |
| BL-0033 | MCP Adapter (F15) | high | **done** | 12 tools, 6 resources, 4 prompts, `ztlctl serve` with stdio/sse/streamable-http transports. Deferred: tool proliferation guard |
| BL-0034 | Verbose Telemetry (F16) | medium | **done** | structlog dual-output, `@traced` decorator, `trace_span()` context manager, `--verbose`/`--log-json` CLI flags |
| BL-0035 | Semantic Search (F17) | high | **done** | EmbeddingProvider, VectorService, sqlite-vec vec0 table, hybrid BM25+cosine ranking, `vector` CLI group |

### Implementation Dependency Graph

Features have hard dependencies. This is the recommended build order:

```
Phase 0 — CLI Structural Foundation (complete):
  Package structure, all layers as stub modules
  Config: Pydantic model hierarchy, TOML discovery
  CLI: Root Click group, global flags, 7 groups + 6 commands
  Domain: StrEnum types, lifecycle transitions, ID system
  Services: ServiceResult/ServiceError (Pydantic), 6 service stubs
  Infrastructure: SQLite engine (WAL mode), GraphEngine (lazy NetworkX)
  Plugins: 8 hookspecs, manager scaffold, Git plugin stub
  MCP: Import-guarded server scaffold
  Templates: Content + self Jinja2 templates
  Output: ServiceResult formatter with --json support

Phase 1 — Foundation (complete):
  F9  Database Layer:
    - 8 SQLAlchemy Core tables with ForeignKey constraints
    - FTS5 virtual table (standalone, no content= clause)
    - init_database() — idempotent, creates .ztlctl/ dirs, seeds counters
    - next_sequential_id() — atomic read-and-increment for LOG/TASK IDs
  F6  ID System:
    - Content-hash (ztl_/ref_ + 8 hex) and sequential (LOG-/TASK-NNNN)
    - normalize_title(), generate_content_hash(), validate_id()
  F1  Content Model:
    - ContentModel hierarchy (NoteModel, KnowledgeModel, DecisionModel,
      ReferenceModel, TaskModel) with frozen Pydantic models
    - Validation classmethods: validate_create(), validate_update(),
      required_sections(), status_transitions()
    - CONTENT_REGISTRY + get_content_model() lookup
    - Frontmatter parsing (ruamel.yaml round-trip, CRLF normalization)
    - Body-only Jinja2 templates with write_body(**kwargs)
  Architecture:
    - ZtlSettings (Pydantic Settings v2) — unified CLI/env/TOML/defaults
    - Vault — repository with ACID transaction coordination (DB + files + graph)
    - BaseService — abstract foundation with Vault injection
    - Filesystem — file I/O, path resolution, content discovery
    - GraphEngine — lazy NetworkX rebuild from edges table

  233 tests, mypy strict, ruff clean.

Phase 2 — Core Pipeline (complete):
  F3  Create Pipeline:
    - Five-stage pipeline (VALIDATE → GENERATE → PERSIST → INDEX → RESPOND)
    - Three creation paths: notes (with subtypes), references (with URL), tasks (with priority matrix)
    - Link extraction: frontmatter links and [[wikilinks]] → edges table
    - Tag indexing: auto-register tags, unscoped tag warnings
    - Batch creation: all-or-nothing and partial modes (service layer; CLI subcommand added in Phase 4)
    - ID generation: content-hash (notes/refs) returns None on unknown type; sequential (tasks)
  F7  Query Surface:
    - FTS5 search with BM25 ranking (relevance, recency)
    - Single-item retrieval with tags, body, and graph neighbors
    - Filtered listing with sort modes (recency, title, type)
    - Scored work queue: priority×2 + impact×1.5 + (4 − effort)
    - Decision support: notes + decisions + references partitioned by topic
  F2  Graph Architecture:
    - GraphEngine loads node attributes (type, title) from nodes table
    - Spreading activation: BFS with 0.5 decay per hop, undirected traversal
    - Community detection: Leiden (leidenalg) → Louvain (NetworkX) fallback
    - PageRank importance scoring, structural holes (constraint), bridge nodes (betweenness)
    - Shortest path on undirected view
  Architecture:
    - AppContext pattern: lazy Vault on ctx.obj, centralized emit() for exit codes
    - Commands reduced to 1–2 line handlers via AppContext
    - BaseService: _vault only (no public property)
    - Domain links module: extract_wikilinks(), extract_frontmatter_links()

  419 tests, mypy strict, ruff clean.

Phase 3 — Enrichment (complete):
  F4  Reweave:
    - 4-signal scoring: BM25 (percentile normalized), Jaccard tags, graph proximity, topic co-occurrence
    - Weighted sum with configurable weights (default: 0.35/0.25/0.25/0.15)
    - Prune: removes stale edges below threshold, updates frontmatter + body
    - Undo: reverses via audit trail (reweave_log table), supports specific ID or latest batch
    - Garden note protection: adds frontmatter links but never modifies body text
    - Dry-run mode: returns suggestions without modifying data
  F5  Update & Close:
    - UpdateService: 5-stage pipeline (VALIDATE → APPLY → PROPAGATE → INDEX → RESPOND)
    - Status transitions validated per content type via lifecycle transition maps
    - Decision immutability: body cannot change after status=accepted
    - Garden note protection: rejects body changes when maturity is set
    - Note status propagation: automatic recompute from outgoing edge count
    - Archive: soft delete (archived=true), preserves edges, excluded from active queries
    - Supersede: old decision status → superseded, adds superseded_by field, bidirectional links
    - SessionService: start/close/reopen with JSONL append-only event streams
    - Close enrichment pipeline: cross-session reweave → orphan sweep → integrity check → report
    - TOCTOU fix: session lookup + update inside same VaultTransaction
  F11 Integrity:
    - 4-category check: DB-file consistency, schema integrity, graph health, structural validation
    - Safe fix: remove orphan DB rows, remove dangling edges, re-insert missing FTS5, re-sync from files
    - Aggressive fix: adds full edge re-indexing + frontmatter key reordering
    - Full rebuild: two-pass (nodes first, then edges) from filesystem
    - Rollback: restore from timestamped backup
    - Backup: automatic before fix/rebuild, retention by count
    - Uses VaultTransaction for atomic fix/rebuild operations
    - Wikilink resolution: shares 3-step chain (title → alias → ID) with CreateService
  Architecture:
    - VaultTransaction used consistently across all write services
    - Path traversal guard on filesystem operations
    - Human-readable output: OK/ERROR prefix + indented key-value data
    - Warnings emitted to stderr (human mode) or included in JSON payload
    - Database indexes on high-cardinality columns (7 indexes total)
    - Command stubs use AppContext (not ZtlSettings) for correct type flow
    - TOML parse errors surface as ClickException with file path

  557 tests, mypy strict, ruff clean.

Phase 4 — Presentation (complete):
  F12 CLI Interface:
    - Rich output layer: styled text, tables, icons via Rich Console
    - 3 verbosity modes: quiet (one-line), default (Rich formatted), verbose (debug details)
    - JSON mode: structured ServiceResult serialization unchanged
    - Score column auto-detection for priority-sorted and search results
  F8  Progressive Disclosure:
    - `--examples` flag on all implemented commands (eager callback, skips argument validation)
    - ZtlCommand/ZtlGroup base classes with `examples=` kwarg and `command_class` inheritance
    - All stub commands updated to use ZtlCommand/ZtlGroup for consistency
  CLI Commands:
    - `update` — standalone command with --title, --status, --tags, --topic, --body, --maturity
    - `supersede` — standalone command with OLD_ID, NEW_ID positional args
    - `create batch` — subcommand reading JSON files with --partial flag
    - `reweave --undo-id` — undo specific reweave log entry by ID
  Query Extensions:
    - `list` extended with --subtype, --maturity, --since, --include-archived filters
    - `list --sort priority` — weighted scoring with Python-side sort and post-sort limit
    - `maturity` field now included in list result dicts
  Refactoring:
    - Shared `services/_helpers.py`: today_iso(), now_iso(), now_compact(), parse_tag_parts()
    - Eliminated _today() duplication (5 files) and _now_iso() format inconsistency (3 files)
    - AppContext imports aligned to TYPE_CHECKING guard across all command files
    - Error handling in update/batch routed through app.emit(ServiceResult) for --json support
  Architecture:
    - All commands use ZtlCommand/ZtlGroup base classes (no plain click.command/group)
    - 7 groups + 8 standalone commands registered
    - Command stubs receive AppContext, deferred service imports in function bodies

  715 tests, mypy strict, ruff clean.

Phase 5 — Lifecycle (complete):
  F13 Init & Self-Generation:
    - Interactive `ztlctl init` with prompts for name, client, tone, topics
    - Non-interactive `--name/--client/--tone/--topics` flags for scripting
    - Vault scaffolding: ztlctl.toml, .ztlctl/, notes/, ops/, self/
    - Obsidian client: .obsidian/ with graph colors and CSS snippets
    - Jinja2 templates for self/identity.md and self/methodology.md
    - `ztlctl agent regenerate` with staleness detection (timestamp comparison)
    - Database initialization integrated into init flow
  F10 Export:
    - `export markdown` — full vault as portable markdown directory tree
    - `export indexes` — topic and tag index files for GitHub rendering
    - `export graph` — dot (GraphViz) and JSON (D3/vis.js) formats
    - ExportService with format-specific renderers
    - All commands support --output directory option

  797 tests, mypy strict, ruff clean.

Phase 6 — Extension (complete):
  F14 Event System & Plugins:
    - EventBus: WAL-backed async dispatch via pluggy + ThreadPoolExecutor
    - Write-ahead log: events persist before dispatch, retry on failure, dead-letter after max retries
    - Sync mode (--sync flag) for deterministic testing
    - Drain barrier: session close flushes pending events synchronously
    - PluginManager: entry-point discovery via pluggy load_setuptools_entrypoints
    - register_plugin/unregister for runtime plugin management
    - Git plugin (built-in): all 8 hookspecs implemented
      - post_create/update/close: git add + optional immediate commit
      - post_session_close: batch commit of all staged changes, optional auto-push
      - post_init: .gitignore generation, git init, initial commit
      - All subprocess calls wrapped in try/except (missing git silently fails)
    - BaseService._dispatch_event(): fire-and-forget with safety net (failures → warnings)
    - Vault.init_event_bus() called from AppContext on vault creation
    - Event dispatch integrated into all 6 service modules (create, update, reweave, session, check, init)
  F15 MCP Adapter:
    - 12 tools: create (note, reference, task, log), lifecycle (update, close, reweave),
      query (search, get_document, get_related, agent_context), session (session_close)
    - 6 resources: context, self/identity, self/methodology, overview, work-queue, topics
    - 4 prompts: research_session, knowledge_capture, vault_orientation, decision_record
    - _impl function pattern: testable without mcp package installed
    - register_tools/resources/prompts wraps _impl functions with FastMCP decorators
    - `ztlctl serve --transport stdio` command with mcp install guard
    - Deferred: tool proliferation guard (discover_tools meta-tool), streamable HTTP transport

  882 tests, mypy strict, ruff clean.

Phase 7 — Stub Command Completion (complete):
  Agent CLI Commands:
    - `agent session cost` — accumulated token cost with optional --report budget mode
    - `agent session log` — append JSONL log entries with --pin and --cost flags
    - `agent context` — token-budgeted 5-layer context payload with --topic and --budget
    - `agent brief` — vault orientation (works without active session): stats, decisions, work queue
  Garden Seed:
    - `garden seed` — quick capture via CreateService.create_note with maturity="seed"
    - Maturity parameter threaded through create pipeline (_create_content node_row)
  Extract Decision:
    - `extract` — JSONL log parsing, pinned entry filtering, decision note creation
    - Creates note via CreateService pipeline, overwrites body, updates FTS5
    - Adds derived_from edge linking decision to source session
  Upgrade Command:
    - Alembic migration infrastructure: programmatic Config, env.py, baseline migration
    - UpgradeService: check_pending(), apply() (BACKUP → MIGRATE → VALIDATE → REPORT), stamp_current()
    - Pre-Alembic vault detection: stamp instead of migrate when tables exist without version tracking
    - stamp_head() integrated into init flow for fresh databases
  Renderers:
    - 4 new Rich renderers: _render_cost, _render_context, _render_brief, _render_upgrade
    - 2 existing renderers reused: log_entry → _render_mutation, extract_decision → _render_mutation
  Fixes (code review):
    - JSONL entry type now reflects entry_type parameter (was hardcoded "log_entry")
    - extract_decision FTS5 update and edge insert merged into single transaction
    - schema.py columns now have server_default alongside default for DDL parity with migration
    - init_vault stamp failures surfaced as ServiceResult warnings instead of silently swallowed

  1014 tests, mypy strict, ruff clean.

Phase 8 — Verbose Telemetry (complete, PR #50):
  F16 Verbose Telemetry:
    - structlog dual-output: Rich console (human) + JSON (machine), all to stderr
    - `@traced` decorator on 45 public service methods across 11 files
    - `trace_span()` context manager: 28 sub-stage spans (create, check, update, reweave, session, graph, context)
    - ContextVar wiring: `_verbose_enabled` + `_current_span` — zero-signature-change propagation
    - `--verbose` CLI flag: hierarchical span tree rendering with duration color-coding
    - `--log-json` CLI flag: structured JSON logs to stderr
    - Idempotent `configure_logging()` (clears root logger handlers)
    - ~10ns overhead when disabled (single ContextVar.get() check)
  Fixes:
    - Frozen ServiceResult + telemetry: `result.model_copy(update={"meta": merged})` pattern
    - `@staticmethod` must be outside `@traced` (decorator order matters)
    - Cross-service `@traced` calls create independent root spans

  ~1095 tests, mypy strict, ruff clean.

Phase 9 — Quick Wins + Semantic Search (complete, PRs #51–#57):
  Feature Gaps (PRs #51, #53, #55):
    - Post-create automatic reweave: inline in CreateService for notes/references, gated by `no_reweave`
    - `graph unlink` command: remove edge + frontmatter + body wikilink
    - `--ignore-checkpoints` flag on `agent context`
    - Bidirectional edge materialization in `materialize_metrics()`
    - `cluster_id` materialization via Leiden → Louvain community detection
    - Interactive create prompts (TTY-aware, respects `--no-interact`)
    - Garden advisory features: seed age warnings, evergreen readiness checks
    - `--cost` flag on all content-modifying commands
  Infrastructure (PR #56):
    - MCP HTTP/SSE transport: `--transport {stdio|sse|streamable-http}` with `--host`/`--port`
    - Local plugin discovery: `.ztlctl/plugins/*.py` via importlib, @hookimpl scanning
    - Alembic migration tests: forward migration, pre-Alembic detection, stamp_current
  Semantic Search (PR #57):
    - EmbeddingProvider: pluggable abstraction, `sentence-transformers` default, `all-MiniLM-L6-v2`
    - VectorService: sqlite-vec `vec0` virtual table, FLOAT[384], KNN cosine distance
    - Hybrid ranking: `(1-w) * bm25_norm + w * cosine_sim`, configurable `semantic_weight`
    - Graceful degradation: `is_available()` check, silent no-op when deps missing
    - `vector status` and `vector reindex` CLI commands
    - Pipeline integration: auto-index on create, hybrid search in query
  Docs:
    - Archived completed plan files
    - `--examples` flag coverage on all commands/groups
    - `type: ignore` audit (23 FastMCP stubs, 5 justified)

  1198 tests, mypy strict, ruff clean.
```

When implementing a feature, read its section in this document completely before writing code. Cross-reference the schema in Section 9 for all DB table definitions, and the `ServiceResult` contract in Section 10 for all return types.
