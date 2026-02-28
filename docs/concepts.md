---
title: Core Concepts
nav_order: 5
---

# Core Concepts

## Content Types

ztlctl manages four content types, each with its own lifecycle:

| Type | Purpose | Initial Status | ID Format |
|------|---------|---------------|-----------|
| **Note** | Ideas, knowledge, decisions | `draft` | `ztl_<hash>` |
| **Reference** | External sources (articles, tools, specs) | `captured` | `ref_<hash>` |
| **Task** | Actionable work items | `inbox` | `TSK-NNNN` |
| **Log** | Session journals (JSONL) | `open` | `LOG-NNNN` |

## Content Subtypes

Notes and references can be further classified:

- **Note subtypes**: `knowledge` (long-lived insight), `decision` (architectural/design choice)
- **Reference subtypes**: `article`, `tool`, `spec`
- **Garden maturity**: `seed` (raw capture) → `budding` (developing) → `evergreen` (polished)

## Lifecycle States

Each content type follows a defined state machine:

```
Note:      draft → linked (1+ outgoing link) → connected (3+ outgoing links)
Reference: captured → annotated
Task:      inbox → active → done | blocked | dropped
Decision:  proposed → accepted → superseded
Log:       open ↔ closed (reopenable)
```

Status transitions are enforced — you cannot skip states or make invalid transitions.

## Vault Structure

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

## Tags

Tags use a `domain/scope` format for structured categorization:

```bash
--tags "lang/python"        # domain=lang, scope=python
--tags "concept/concurrency" # domain=concept, scope=concurrency
--tags "status/wip"         # domain=status, scope=wip
```

Unscoped tags (e.g., `python`) work but generate a warning — the domain/scope format enables powerful filtering.

## Knowledge Graph

Every content item is a node. Edges are created through:

- **Frontmatter links**: Explicit `links:` in YAML frontmatter
- **Wikilinks**: `[[Note Title]]` references in body text
- **Reweave**: Automated link discovery via 4-signal scoring (BM25 lexical similarity, Jaccard tag overlap, graph proximity, topic match)

The graph powers `ztlctl graph` commands for traversal, analysis, and structural insight. See the [Command Reference](commands.md) for all graph commands.
