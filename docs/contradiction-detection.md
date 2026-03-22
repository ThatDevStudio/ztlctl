---
title: Contradiction detection
---

# Contradiction detection

Contradiction detection surfaces pairs of notes that may contain opposing or incompatible claims. It uses a three-signal heuristic — vector similarity, negation density, and key-points divergence — to rank candidate pairs without requiring a language model. Once you review a candidate pair, you confirm it as a `contradicts` graph edge so the relationship persists in your vault.

## How contradiction detection works

The algorithm identifies candidates in two phases: discovery and scoring.

**Discovery** filters the full note set down to plausible pairs using three sequential checks:

1. Only non-archived notes (type `note` or `reference`) are considered.
2. Both notes must have a cosine similarity above `--similarity-threshold` (default `0.85`) — meaning they discuss the same topic at the sentence-embedding level.
3. The pair must share at least one tag — an extra signal that the notes are intentionally related.

**Scoring** combines three weighted signals for each qualifying pair:

| Signal | Weight | What it measures |
|--------|--------|-----------------|
| Cosine similarity | 40% | How semantically close the two notes are in embedding space |
| Negation density | 30% | Count of negation words (`not`, `but`, `however`, `disagree`, etc.) across both notes |
| Key-points divergence | 30% | Whether the notes share topic words in their `key_points` frontmatter but reach different conclusions |

The final score is a float in `[0, 1]`. Higher scores indicate stronger contradiction signals. Pairs are returned sorted by score descending.

!!! note
    Contradiction detection requires a populated vector index. If `sqlite-vec` and `sentence-transformers` are not installed or the index is empty, the service returns an empty candidate list with a warning. Run `ztlctl vector index` to build or rebuild the index.

## Running contradiction checks

### With the CLI

The `ztlctl check contradictions` command runs a full scan and returns the ranked candidate list:

```bash
$ ztlctl check contradictions
$ ztlctl check contradictions --similarity-threshold 0.90
$ ztlctl check contradictions --max-pairs 10
```

**Options:**

| Flag | Default | Description |
|------|---------|-------------|
| `--similarity-threshold FLOAT` | `0.85` | Minimum cosine similarity (0.0–1.0) to include a pair |
| `--max-pairs INTEGER` | `20` | Maximum number of candidate pairs to return |

Each result includes the note IDs (`note_a`, `note_b`), their titles, the composite score, and a `signals` list describing what contributed to the score (e.g. `negation_density:3_keywords`, `cosine_similarity:0.912`, `key_points_divergence:overlap=[...]`).

### As part of `ztlctl check`

Contradiction candidates are also surfaced through the `CAT_SEMANTIC` (semantic analysis) category when you run the general integrity scanner:

```bash
$ ztlctl check check
$ ztlctl check check --min-severity info
```

The `CAT_SEMANTIC` category reports contradiction candidates as informational issues alongside the structural, graph, and DB-consistency categories. Use `ztlctl check contradictions` directly when you want the full scored candidate list.

## Confirming contradictions

After reviewing a candidate pair, use `ztlctl check confirm-contradiction` to record the contradiction permanently:

```bash
$ ztlctl check confirm-contradiction ZTL-0042 ZTL-0099
```

**Arguments:**

| Argument | Required | Description |
|----------|----------|-------------|
| `NOTE_A` | Yes | ID of the first note in the contradiction pair |
| `NOTE_B` | Yes | ID of the second note in the contradiction pair |

Confirming a contradiction inserts two `contradicts` edges in the graph — one from `NOTE_A → NOTE_B` and one from `NOTE_B → NOTE_A` — with `source_layer=user` and today's date. Duplicate edges are silently skipped, so confirming the same pair twice is safe.

!!! tip
    You can dismiss a candidate pair by simply not running `confirm-contradiction` on it. There is no explicit "dismiss" action — unconfirmed pairs remain as candidates until the vault content changes or the vector index is rebuilt.

## Graph edges

Confirmed contradictions are stored as `contradicts` edges in the knowledge graph. They are bidirectional: both `A contradicts B` and `B contradicts A` edges are written. This makes them visible to graph traversal tools:

```bash
# See all edges connected to a note, including contradicts edges
$ ztlctl graph related ZTL-0042 --depth 1

# Find notes connected by contradicts edges in the decision support context
$ ztlctl query decision-support --topic your-topic
```

The `source_layer` field on each edge is set to `user`, distinguishing contradiction edges from auto-woven `reweave` edges (`source_layer=system`). You can filter or inspect this in custom graph queries via `ztlctl graph`.

!!! warning
    Contradiction edges are not removed automatically if a note is updated or archived. If you resolve a contradiction by editing a note's content, you should archive or update both notes accordingly. There is currently no `remove-contradiction` command — edges persist until vault rebuild.

## MCP tools and resources

Agents interact with contradiction detection through two MCP tools and one MCP resource.

### MCP tools

| Tool | Side effect | Description |
|------|-------------|-------------|
| `check_contradictions` | read | Find candidate note pairs that may contradict each other |
| `confirm_contradiction` | write | Record a confirmed contradiction between two notes as graph edges |

**`check_contradictions` parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `similarity_threshold` | float | `0.85` | Minimum cosine similarity to consider a pair (0.0–1.0) |
| `max_pairs` | int | `20` | Maximum number of candidate pairs to return |

**`confirm_contradiction` parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `note_a` | string | Yes | ID of the first note (e.g. `ZTL-0042`) |
| `note_b` | string | Yes | ID of the second note (e.g. `ZTL-0099`) |

Common error: `NOT_FOUND` — one or both note IDs do not exist in the vault.

### MCP resource

`ztlctl://review/contradictions` returns the full scored candidate list as JSON:

```json
{
  "candidates": [
    {
      "note_a": "ZTL-0042",
      "note_b": "ZTL-0099",
      "title_a": "Async improves throughput under I/O load",
      "title_b": "Async adds overhead and should be avoided",
      "score": 0.7823,
      "signals": [
        "negation_density:4_keywords",
        "cosine_similarity:0.912",
        "key_points_divergence:overlap=['throughput', 'performance']"
      ]
    }
  ],
  "count": 1
}
```

Agents read this resource to get the full candidate list before deciding which pairs to confirm.

## Agent review workflow

A typical agent contradiction-review loop:

1. **Read the resource** to fetch all current candidates.

   ```
   GET ztlctl://review/contradictions
   ```

2. **Inspect each candidate pair.** For each entry, call `get_document` on both `note_a` and `note_b` to read their full content and key points.

   ```
   get_document(content_id="ZTL-0042")
   get_document(content_id="ZTL-0099")
   ```

3. **Evaluate** whether the two notes genuinely contradict each other based on their content. Check the `signals` field to understand what drove the score.

4. **Confirm or skip.** If the contradiction is real, call `confirm_contradiction`. If the pair is a false positive (same topic, compatible claims), skip it.

   ```
   confirm_contradiction(note_a="ZTL-0042", note_b="ZTL-0099")
   ```

5. **Optional:** After confirming contradictions, run `check_contradictions` again with a higher `max_pairs` to ensure no further candidates remain.

!!! tip
    Contradiction review pairs well with `ztlctl://review/dashboard` and the `decision_support` tool. Decision notes often surface contradictions — checking alignment before confirming a decision is a useful pre-confirmation step.

## What's next

- [Concepts](concepts.md) — understand notes, references, graph edges, and lifecycle
- [Agentic workflows](agentic-workflows.md) — orchestration recipes and MCP tool composition
- [Commands](commands.md) — full reference for all CLI commands including `ztlctl check`
