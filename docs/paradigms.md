---
title: Knowledge Paradigms
---

# Knowledge Paradigms

ztlctl uses a two-layer model instead of collapsing every knowledge method into one workflow. The first layer — capture and synthesis — is where agents and humans work together to collect sources, build references, and develop rough understanding. The second layer — enrichment — is where the human user takes over to deepen, reorganize, and mature that foundation. Second-brain and knowledge-garden approaches are not competing methods: they map naturally to these two layers, and ztlctl supports both simultaneously.

## Second-Brain vs Knowledge Garden

### At a Glance

| Dimension | Second-Brain (Capture Layer) | Knowledge Garden (Enrichment Layer) |
|-----------|------------------------------|--------------------------------------|
| Primary question | "What did I learn?" | "What do I understand?" |
| Capture style | Broad, fast, reference-driven | Selective, slow, insight-driven |
| Content types | Notes, references, tasks, ingested sources | Garden seeds, budding notes, evergreen notes |
| Organization | Topic routing, session batching | Maturity tiers, backlink structure |
| Enrichment | Automated (reweave, sessions) | Human-led (Obsidian, dashboard review) |
| ztlctl commands | `create`, `ingest`, `session`, `query search` | `garden seed`, `update --maturity`, `export dashboard`, `query packet --mode review` |
| Agent role | Agent captures, synthesizes, triages | Agent assists conversationally, does not garden |

Both approaches coexist in a single vault. Content captured in the machine layer (`notes/`, `ops/`) is indexed, searchable, and reweaved automatically. Garden content lives in `garden/` — ztlctl never indexes or mutates that directory. The two layers complement rather than replace each other.

## Choose Your Path

**"I want to research a new technology or topic"**

Use the second-brain capture-first approach. Start a focused session, ingest sources and create synthesis notes as understanding develops, and let reweave connect the material automatically.

→ See [Scenario 1: Researching a New Technology](#scenario-1-researching-a-new-technology-second-brain-approach)

---

**"I have captured material and want to deepen my understanding"**

Use the knowledge-garden enrichment-first approach. Surface seed notes waiting for attention, review the work queue for stale or actionable items, and promote notes as understanding matures.

→ See [Scenario 2: Tending Existing Knowledge](#scenario-2-tending-existing-knowledge-knowledge-garden-approach)

---

**"I want both — capture now, tend later"**

They coexist by design. Capture in the machine layer (`notes/`, `ops/`) using `create`, `ingest`, and `session`. Tend in the garden layer (`garden/`) using Obsidian or `ztlctl update`. ztlctl never indexes or mutates `garden/` content, so the two workflows never interfere.

→ See [Scenario 3: Agent-Assisted Hybrid](#scenario-3-agent-assisted-hybrid-both-paradigms)

---

## Scenario 1: Researching a New Technology (Second-Brain Approach)

You're investigating OAuth security. Start a focused session to keep context anchored, ingest sources as you find them, and build synthesis notes as understanding develops.

```bash
# Start a focused research session
ztlctl agent session start "oauth security"
```

The session creates a coordination log and anchors all subsequent work to the `oauth security` topic context.

```bash
# Ingest sources as references
ztlctl ingest text "RFC 6749 notes" --stdin --as reference --tags "auth/oauth"
```

Each ingested source becomes a `reference` in the machine layer with a stored source bundle under `sources/`.

```bash
# Create synthesis notes as understanding develops
ztlctl create note "OAuth 2.0 threat model" \
  --tags "auth/oauth,security" \
  --topic auth
```

Notes start at `draft` status and progress through `linked` → `connected` as reweave adds links.

```bash
# Build a learning packet from captured material
ztlctl query packet --topic auth --mode learn
```

The learning packet aggregates your captured references and notes into a structured context block for review or agent handoff.

```bash
# Draft a synthesis note from the packet
ztlctl query draft --topic auth --target note
```

```bash
# Close session — triggers reweave, orphan sweep, and integrity check automatically
ztlctl agent session close --summary "Mapped OAuth threat surface"
```

!!! note
    At session close, ztlctl automatically runs cross-session reweave to connect the new notes, an orphan sweep to link any isolated notes, and an integrity check. No manual step needed.

---

## Scenario 2: Tending Existing Knowledge (Knowledge-Garden Approach)

You have a vault with captured material and want to deepen your understanding of the auth topic. Surface what needs attention, review the work queue, and promote notes as understanding matures.

```bash
# Surface seed notes waiting for enrichment
ztlctl query list --maturity seed --sort recency
```

Seed notes are raw captures — garden seeds you planted but haven't developed yet.

```bash
# Review the work queue for stale or actionable items
ztlctl query work-queue
```

The work queue scores all actionable items by priority, impact, and effort, presenting them in the order most worth your attention.

```bash
# Get a review packet for the topic you're tending
ztlctl query packet --topic auth --mode review
```

The review packet surfaces stale notes, weakly connected items, and decision-support context for the topic — machine-layer signals to guide where human tending is most valuable.

```bash
# Promote a note as understanding deepens
ztlctl update ZTL-0001 --maturity budding
```

Maturity tiers — `seed` → `budding` → `evergreen` — track how thoroughly a note has been developed.

```bash
# Export a dashboard for visual review in Obsidian
ztlctl export dashboard --viewer obsidian --output ./dashboard
```

!!! note
    Garden work happens in Obsidian (the `garden/` directory) or directly via `ztlctl update`. The exported dashboard is a review workbench — machine-layer signals to guide where human tending is most valuable, not a mirror of `garden/` state.

---

## Scenario 3: Agent-Assisted Hybrid (Both Paradigms)

You're working alongside an agent. The agent captures research in the machine layer; you tend connections and deepen notes in the garden layer. Neither workflow disrupts the other.

```bash
# Agent captures research in the machine layer
ztlctl create note "Distributed consensus trade-offs" --tags "systems/consensus" --topic systems
```

```bash
# Human reviews agent-captured seeds and promotes them
ztlctl query list --maturity seed --sort recency
ztlctl update ZTL-0042 --maturity budding
```

```bash
# Human tends connections in Obsidian's garden/ layer (no ztlctl command needed)
# ztlctl does not index or mutate garden/ content
```

!!! tip
    The garden layer is entirely human-owned. Agents can assist conversationally — answering questions against captured knowledge — but they do not create or modify garden content. This separation ensures your long-form insight work stays under your control.

---

## How The Paradigms Map

| Paradigm | ztlctl role |
|----------|-------------|
| **Zettelkasten** | Durable note/reference creation, graph links, reweave, related-content traversal |
| **Second brain** | Broad capture, references, tasks, topic organization, agent-assisted retrieval |
| **Knowledge garden** | Human-led enrichment, maturity tracking, backlog review, and dashboard-guided tending from machine-layer review signals |

## What ztlctl Does Not Claim

- It does not force PARA or any other organizational method as the canonical ontology.
- It does not treat garden work as fully automatable.
- It does not treat operational session state as equivalent to durable knowledge artifacts.

## Anti-Patterns

Avoid these common mistakes when setting up a ztlctl workflow.

!!! warning "Don't mix paradigm tags without namespacing"
    Using `python` as a tag across both a second-brain research vault and a knowledge-garden vault makes retrieval ambiguous. Use namespaced tags (`lang/python`, `project/my-app`) so filters work cleanly across paradigms.

!!! warning "Don't force one paradigm for all content"
    Not every piece of knowledge needs to go through the full enrichment pipeline. Quick captures, ephemeral tasks, and reference-only notes belong in the machine layer. Reserve the garden layer for content you genuinely intend to develop into long-form insight.

!!! warning "Don't let agents garden"
    Agents operate on the machine layer (`notes/`, `ops/`). They do not create or modify content in `garden/`. Granting agents write access to garden content undermines the human-led quality guarantee that makes garden notes trustworthy.

## Intended Flow

1. Capture sources and rough synthesis quickly.
2. Use search, packets, and reweave to stabilize the foundation knowledge layer.
3. Use packets, drafts, and dashboard dossiers to turn captured evidence into reviewable work.
4. Enrich that foundation through slower, human-led garden work.

## Next Steps

- Follow the [Tutorial](tutorial.md) to build your first vault end-to-end
- Read [Core Concepts](concepts.md) for the full content type, ID format, and lifecycle state reference
- Read [Best Practices](best-practices.md) for workflow patterns and anti-pattern deep dives
- See [Agentic Workflows](agentic-workflows.md) for session lifecycle, recipe walkthroughs, and MCP integration
- See [Plugin Authoring](plugin-guide.md) to extend paradigm support with custom note types
