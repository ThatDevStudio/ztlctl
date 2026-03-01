---
title: Knowledge Paradigms
nav_order: 9
---

# Knowledge Paradigms

ztlctl uses a two-layer model instead of collapsing every knowledge method into one workflow.

## Capture and Synthesis

This layer is where agents and humans work together to capture sources, create durable references and notes, and assemble enough context for learning or decision-making.

It draws most heavily from:

- **Zettelkasten** for atomic notes, explicit links, and graph-driven discovery
- **Second-brain patterns** for broad capture, topic routing, and action-oriented follow-up
- **Agentic workflows** for structured research sessions, ingestion, topic packets, and review loops

Typical commands:

```bash
ztlctl agent session start "oauth architecture"
ztlctl ingest text "OAuth RFC Notes" --stdin --as reference
ztlctl create note "Token exchange trade-offs" --topic auth
ztlctl query packet --topic auth --mode learn
ztlctl query draft --topic auth --target note
ztlctl reweave
```

## Enrichment

This layer is where the human user takes over to deepen, reorganize, and mature the captured foundation knowledge.

It is closest to the knowledge-garden model:

- promote notes from `seed` to `budding` to `evergreen`
- revisit weakly connected or stale notes
- refine wording, structure, and pedagogy
- use agents conversationally against captured knowledge rather than asking them to replace the garden work

Typical commands:

```bash
ztlctl garden seed "Question: what breaks token rotation?"
ztlctl query list --maturity seed --sort recency
ztlctl query packet --topic auth --mode review
ztlctl export dashboard --viewer obsidian --output ./dashboard
ztlctl update ztl_abc123 --maturity budding
```

## How The Paradigms Map

| Paradigm | ztlctl role |
|----------|-------------|
| **Zettelkasten** | Durable note/reference creation, graph links, reweave, related-content traversal |
| **Second brain** | Broad capture, references, tasks, topic organization, agent-assisted retrieval |
| **Knowledge garden** | Human-led enrichment, maturity tracking, backlog review, dashboard-driven tending |

## What ztlctl Does Not Claim

- It does not force PARA or any other organizational method as the canonical ontology.
- It does not treat garden work as fully automatable.
- It does not treat operational session state as equivalent to durable knowledge artifacts.

The intended flow is:

1. Capture sources and rough synthesis quickly.
2. Use search, packets, and reweave to stabilize the foundation knowledge layer.
3. Use packets, drafts, and dashboard dossiers to turn captured evidence into reviewable work.
4. Enrich that foundation through slower, human-led garden work.
