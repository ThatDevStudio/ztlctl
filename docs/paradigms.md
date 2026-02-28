---
title: Knowledge Paradigms
nav_order: 9
---

# Knowledge Paradigms

ztlctl integrates three complementary note-taking paradigms:

## Zettelkasten (Atomic Notes + Links)

The zettelkasten method treats each note as a single, self-contained idea connected to others through links.

**How ztlctl supports it:**

- Each note gets a unique content-hash ID (`ztl_a1b2c3d4`)
- Notes link to each other via `[[wikilinks]]` in body text and explicit frontmatter links
- `ztlctl graph related` implements spreading activation to find connected ideas
- `ztlctl graph path` traces connection chains between any two notes
- Note status evolves automatically: `draft` → `linked` (1+ outgoing) → `connected` (3+ outgoing)

**Workflow:**

```bash
# Capture atomic ideas
ztlctl create note "Immutability reduces bugs" --tags "concept/fp"
ztlctl create note "Pure functions are easier to test" --tags "concept/fp"

# Let reweave connect them
ztlctl reweave --auto-link-related

# Explore the connections
ztlctl graph related ztl_abc123 --depth 2
```

## Second Brain (PARA + Capture Everything)

The second brain approach (inspired by Tiago Forte's PARA method) captures everything and organizes by actionability.

**How ztlctl supports it:**

- **Projects** → Tasks with priority/impact/effort scoring and `work-queue`
- **Areas** → Topic directories (`--topic`) for ongoing domains
- **Resources** → References with URL, subtype (article/tool/spec), and tags
- **Archive** → `ztlctl archive` soft-deletes while preserving graph edges
- Sessions provide temporal organization — every piece of content links to its creation session

**Workflow:**

```bash
# Capture everything during a research session
ztlctl agent session start "System design research"

# Resources (articles, tools, specs you encounter)
ztlctl create reference "CAP Theorem Explained" --subtype article --url "..."
ztlctl create reference "Redis Documentation" --subtype tool --url "..."

# Knowledge (your synthesized understanding)
ztlctl create note "Trade-offs in distributed caching" --subtype knowledge

# Tasks (actions that emerge)
ztlctl create task "Evaluate Redis vs Memcached" --priority high --impact high

# Review your work queue
ztlctl query work-queue
```

## Knowledge Garden (Seeds to Evergreen)

The digital garden metaphor treats notes as living things that grow over time through tending.

**How ztlctl supports it:**

- **Maturity levels**: `seed` (raw capture) → `budding` (developing) → `evergreen` (polished)
- `ztlctl garden seed` — quick capture with minimal friction
- `ztlctl update --maturity budding` — promote as you develop ideas
- `ztlctl graph gaps` — find notes that need tending (no outgoing links)
- Garden notes protect body content from accidental overwrites

**Workflow:**

```bash
# Quick-capture seeds throughout the day
ztlctl garden seed "Idea: use event sourcing for audit trail"
ztlctl garden seed "Question: how does CRDT conflict resolution work?"

# Later, tend your garden — find seeds that need attention
ztlctl query list --maturity seed --sort recency

# Develop a seed into a budding note
ztlctl update ztl_abc123 --maturity budding \
  --tags "architecture/event-sourcing,pattern/cqrs"

# Promote to evergreen when fully developed
ztlctl update ztl_abc123 --maturity evergreen
```

## Combining Paradigms

These paradigms work together naturally:

1. **Capture** with garden seeds and references (Second Brain + Garden)
2. **Connect** via reweave and wikilinks (Zettelkasten)
3. **Develop** by promoting seeds through maturity levels (Garden)
4. **Act** on tasks surfaced by the work queue (Second Brain)
5. **Decide** by extracting decisions from sessions (Zettelkasten + Second Brain)
6. **Review** via graph analysis to find gaps and bridges (All three)
