---
title: Core Concepts
---

# Core Concepts

## Content Types

ztlctl manages three durable authored artifact types plus one operational session type:

| Type | Purpose | Initial Status | ID Format |
|------|---------|---------------|-----------|
| **Note** | Ideas, knowledge, decisions | `draft` | `ztl_XXXXXXXX` |
| **Reference** | External sources (articles, tools, specs) | `captured` | `ref_XXXXXXXX` |
| **Task** | Actionable work items | `inbox` | `TASK-NNNN` |
| **Log** | Session coordination and session entries | `open` | `LOG-NNNN` |

Notes, references, and tasks are the file-first durability contract. Sessions, session logs, generated `self/` files, and event/WAL state are internal or generated mechanisms that can be rebuilt or regenerated.

Ingested references may also carry a durable source bundle under `sources/<reference-id>/`. That bundle is an attached source artifact for the reference, not a separate top-level knowledge item.

v3.0 extends the content model with three new capabilities:

- **Session recall** — Sessions now support temporal, topic, and topology querying via `ztlctl session recall-temporal`, `recall-topic`, and `recall-topology`. Use recall to reload context from past work before starting a new session. See [Session recall](session-recall.md).
- **Contradiction detection** — The integrity scanner surfaces pairs of notes that may contain conflicting claims via semantic analysis. Confirmed contradictions are stored as `contradicts` edges in the knowledge graph. See [Contradiction detection](contradiction-detection.md).
- **Media ingestion** — Audio, video, and transcript files can be ingested directly via `ztlctl ingest media`. ztlctl transcribes the content locally (using faster-whisper for audio/video) and creates a `captured` reference ready for annotation. See [Media ingestion](media-ingestion.md).

### A Concrete Example

A note capturing Python decorator patterns:

```
ID:     ztl_a1b2c3d4
Title:  Python Decorator Patterns
Status: linked           # computed from outgoing link count (1+ links)
Tags:   lang/python, pattern/decorator
Links:  ztl_e5f6g7h8     # links to "Asyncio Event Loop" note
Topic:  python/
File:   notes/python/ztl_a1b2c3d4.md
```

A reference capturing its source:

```
ID:     ref_deadbeef
Title:  PEP 318 — Decorators for Functions and Methods
URL:    https://peps.python.org/pep-0318/
Status: captured
Tags:   lang/python, concept/meta
File:   notes/python/ref_deadbeef.md
```

## Content Subtypes

Notes and references can be further classified:

- **Note subtypes**: `knowledge` (long-lived insight), `decision` (architectural/design choice)
- **Reference subtypes**: `article`, `tool`, `spec`
- **Garden maturity**: `seed` (raw capture) → `budding` (developing) → `evergreen` (polished)

Custom subtypes are supported via the plugin system — see [Plugin Authoring](plugin-guide.md) for details.

For the prose-as-title convention and title quality standards that apply to all note and reference subtypes, see [Methodology guidance](methodology.md).

## ID Patterns

IDs are permanent — once generated, an ID never changes.

| Content Type | Format | Generation |
|---|---|---|
| Note | `ztl_XXXXXXXX` | SHA-256 of normalized title (8 hex chars) |
| Reference | `ref_XXXXXXXX` | SHA-256 of normalized title (8 hex chars) |
| Task | `TASK-NNNN` | Sequential counter from DB (minimum 4 digits) |
| Log | `LOG-NNNN` | Sequential counter from DB (minimum 4 digits) |

Content-hash IDs (notes, references) are deterministic — creating a note with the same title twice produces the same ID. Sequential IDs (tasks, logs) increment atomically.

## Lifecycle States

Each content type follows a defined state machine. Transitions are enforced — invalid transitions are rejected.

### Note States

```
draft → linked → connected
```

| State | Condition |
|---|---|
| `draft` | Fewer than 1 outgoing link |
| `linked` | 1 or more outgoing links |
| `connected` | 3 or more outgoing links |

Note status is computed automatically from structural properties — it is never set directly by CLI command. Run `ztlctl reweave run` to add links and advance note status.

### Reference States

```
captured → annotated
```

| State | Meaning |
|---|---|
| `captured` | Source stored, not yet annotated |
| `annotated` | Annotations and links added |

### Task States

```
inbox → active → done
             ↕
           blocked
inbox → dropped
active → dropped
blocked → dropped
```

| State | Meaning |
|---|---|
| `inbox` | Captured, not yet started |
| `active` | In progress |
| `blocked` | Waiting on something |
| `done` | Completed (terminal) |
| `dropped` | Abandoned (terminal) |

### Log States (Sessions)

```
open ↔ closed
```

Sessions are reopenable — `ztlctl session reopen LOG-NNNN` transitions `closed` back to `open`.

### Decision States (Note Subtype)

```
proposed → accepted → superseded
```

Decision notes track architectural or design choices through their full lifecycle.

## Vault Structure

```
my-vault/
├── ztlctl.toml          # Configuration
├── .ztlctl/
│   └── ztlctl.db        # SQLite index, session state, graph data, FTS5
├── self/
│   ├── identity.md      # Generated agent identity
│   └── methodology.md   # Generated agent methodology
├── notes/
│   ├── python/
│   │   ├── ztl_a1b2c3d4.md    # Note: Python Decorator Patterns
│   │   └── ref_deadbeef.md    # Reference: PEP 318
│   └── architecture/
│       └── ztl_e5f6g7h8.md    # Note: Asyncio Event Loop
├── sources/
│   └── ref_deadbeef/
│       ├── bundle.json         # Captured source metadata
│       └── normalized.md       # Normalized source text
└── ops/
    └── tasks/
        └── TASK-0001.md
```

`ztlctl check --rebuild` reconstructs durable authored artifacts and derived indexes from the markdown files. It does not treat session rows or other operational state as part of the file-first guarantee.

## Tags

Tags use a `domain/scope` format for structured categorization:

```bash
--tags "lang/python"          # domain=lang, scope=python
--tags "concept/concurrency"  # domain=concept, scope=concurrency
--tags "status/wip"           # domain=status, scope=wip
```

Unscoped tags (e.g., `python`) work but generate a warning — the `domain/scope` format enables powerful filtering via `--tag` in search and list commands.

## Knowledge Graph

Every content item is a node. Edges are created through:

- **Frontmatter links**: Explicit `links:` in YAML frontmatter
- **Wikilinks**: `[[Note Title]]` references in body text
- **Reweave**: Automated link discovery using 4-signal scoring — BM25 lexical similarity, Jaccard tag overlap, graph proximity, and topic match

Contradiction edges (`contradicts`) record confirmed conflicts between notes — see [Contradiction detection](contradiction-detection.md) for the scoring and confirmation workflow.

### Graph Commands

```bash
ztlctl graph related ztl_a1b2c3d4   # find notes related to a specific note
ztlctl graph path ztl_a1b2 ztl_c3d4 # shortest path between two notes
ztlctl graph rank                    # PageRank-based importance ranking
ztlctl graph gaps                    # identify weakly connected clusters
ztlctl graph bridges                 # find structural bridge nodes
```

See the [Command Reference](commands.md) for all graph commands and options.

## Relationships Between Concepts

The content type, lifecycle, and graph systems work together:

1. You create a note (`draft`) or reference (`captured`)
2. Reweave scores the note against existing content and adds graph edges
3. As edges accumulate, note status advances: `draft` → `linked` → `connected`
4. Sessions group work into coordination logs and trigger enrichment on close
5. Polaris priorities guide agent decisions — `ztlctl://polaris` provides strategic alignment context (see [Polaris priorities](polaris.md))

For the workflow patterns that build on these primitives, see [Knowledge Paradigms](paradigms.md).
