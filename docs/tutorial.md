---
title: Tutorial
nav_order: 4
---

# Tutorial: Building Your Knowledge Vault

This tutorial walks through creating and managing a complete knowledge vault from scratch.

## Step 1: Initialize Your Vault

```bash
ztlctl init research-vault --name "Research Notes" --topics "ml,systems,papers"
cd research-vault
```

This creates the directory structure, config file, SQLite database, and agent identity files. The `--topics` flag pre-creates subdirectories under `notes/`.

**Options:**
- `--name TEXT` — Vault display name
- `--client [obsidian|vanilla]` — Client integration (Obsidian adds `.obsidian/` config)
- `--tone [research-partner|assistant|minimal]` — Agent personality for self/ files
- `--topics TEXT` — Comma-separated topic directories
- `--no-workflow` — Skip workflow template setup

## Step 2: Capture Knowledge

**Create a note** — your primary unit of knowledge:

```bash
ztlctl create note "Transformer Architecture" \
  --tags "ml/transformers,concept/architecture" \
  --topic ml
```

**Create a reference** — link to an external source:

```bash
ztlctl create reference "Attention Is All You Need" \
  --url "https://arxiv.org/abs/1706.03762" \
  --subtype article \
  --tags "ml/transformers,papers/seminal"
```

**Quick capture with garden seed** — when you want minimal friction:

```bash
ztlctl garden seed "Idea: attention mechanisms for code review" \
  --tags "ml/attention" --topic ml
```

Seeds start at `seed` maturity and can grow to `budding` then `evergreen` as you develop them.

## Step 3: Work with Tasks

```bash
ztlctl create task "Read BERT paper" --priority high --impact high --effort low
ztlctl create task "Implement attention visualization" --priority medium
```

View your prioritized work queue:

```bash
ztlctl query work-queue
```

Tasks are scored by priority x impact / effort and presented in actionable order.

## Step 4: Connect Knowledge

**Automatic link discovery** — reweave analyzes all content and suggests connections:

```bash
ztlctl reweave --auto-link-related
```

**Dry run** to preview what would change:

```bash
ztlctl reweave --dry-run
```

**Target a specific note:**

```bash
ztlctl reweave --id ztl_a1b2c3d4
```

Reweave uses a 4-signal scoring algorithm:
1. **BM25** (35%) — lexical similarity between content bodies
2. **Tag Jaccard** (25%) — tag overlap between items
3. **Graph Proximity** (25%) — existing network distance
4. **Topic Match** (15%) — shared topic directory

## Step 5: Query and Explore

**Full-text search:**

```bash
ztlctl query search "transformer attention" --rank-by relevance
ztlctl query search "python async" --rank-by recency --type note
ztlctl query search "architecture" --rank-by graph  # PageRank-boosted
```

**List with filters:**

```bash
ztlctl query list --type note --status draft
ztlctl query list --tag "ml/transformers" --sort recency
ztlctl query list --maturity seed --since 2025-01-01
ztlctl query list --include-archived --sort title
```

**Get a specific item:**

```bash
ztlctl query get ztl_a1b2c3d4
```

**Decision support** — aggregate context for a decision:

```bash
ztlctl query decision-support --topic architecture
```

## Step 6: Analyze the Graph

**Find related content** via spreading activation:

```bash
ztlctl graph related ztl_a1b2c3d4 --depth 2 --top 10
```

**Discover topic clusters:**

```bash
ztlctl graph themes
```

**Find the most important nodes** (PageRank):

```bash
ztlctl graph rank --top 20
```

**Find the shortest path** between two ideas:

```bash
ztlctl graph path ztl_a1b2c3d4 ztl_e5f6g7h8
```

**Find structural gaps** — orphan notes with no connections:

```bash
ztlctl graph gaps --top 10
```

**Find bridge nodes** — key connectors between clusters:

```bash
ztlctl graph bridges --top 10
```

## Step 7: Update and Evolve

**Update metadata:**

```bash
ztlctl update ztl_a1b2c3d4 --title "New Title" --tags "new/tag"
ztlctl update ztl_a1b2c3d4 --status linked
ztlctl update ztl_a1b2c3d4 --maturity budding  # Grow a garden note
```

**Archive** — soft-delete that preserves graph edges:

```bash
ztlctl archive ztl_a1b2c3d4
```

**Supersede a decision:**

```bash
ztlctl supersede ztl_old_decision ztl_new_decision
```

## Step 8: Export and Share

**Export markdown** — portable copy of all content:

```bash
ztlctl export markdown --output ./export/
```

**Generate indexes** — type and topic groupings:

```bash
ztlctl export indexes --output ./indexes/
```

**Export the knowledge graph:**

```bash
ztlctl export graph --format dot --output graph.dot  # For Graphviz
ztlctl export graph --format json --output graph.json # For D3.js / vis.js
```

## Step 9: Maintain Integrity

**Check vault health:**

```bash
ztlctl check
```

**Auto-fix detected issues:**

```bash
ztlctl check --fix
ztlctl check --fix --level aggressive  # More thorough repairs
```

**Full rebuild** — re-derive the entire database from files:

```bash
ztlctl check --rebuild
```

**Rollback** to the last backup:

```bash
ztlctl check --rollback
```

## Next Steps

- [Core Concepts](concepts.md) — Deeper understanding of content types and lifecycle
- [Agentic Workflows](agentic-workflows.md) — Using ztlctl with AI agents
- [Knowledge Paradigms](paradigms.md) — Zettelkasten, second brain, and garden approaches
