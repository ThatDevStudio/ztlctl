# Synthesis Workflow Reference

Detailed reference for `graph_gaps`, `topic_packet`, and `draft_from_topic` outputs
used in the ztl:synthesize skill. Use this when SKILL.md workflow guidance is
insufficient for interpreting tool responses.

## graph_gaps output format

`graph_gaps(top=10)` returns the most structurally isolated clusters in the
knowledge graph. Each gap entry contains:

- **`gap_id`** — unique identifier for the isolated cluster
- **`node_ids`** — list of note IDs in this isolated cluster
- **`isolation_score`** — float (0–1). Higher means more isolated. Score 1.0
  means the cluster has no connections to the rest of the vault.
- **`centroid_title`** — title of the most central note in the cluster

"Structural isolation" means the cluster shares no graph edges with the main
connected component. These are areas of vault knowledge that have not yet been
linked to related content — prime candidates for synthesis bridges.

When reporting gap results, focus on isolation_score > 0.5 — lower scores indicate
clusters that are loosely connected but not truly isolated.

## topic_packet output format

`topic_packet(topic="<topic>", mode="learn")` returns a comprehensive topic
context object with the following fields:

- **`related_notes`** — notes most relevant to the topic (BM25 + semantic)
- **`gaps`** — list of structural gap IDs touching this topic area
- **`bridges`** — high-value bridge notes: removing them would disconnect clusters
- **`stale`** — notes on this topic that have not been updated recently
- **`open_questions`** — unanswered questions extracted from note content

`mode="learn"` optimizes for broad coverage. It surfaces more related notes and
emphasizes bridge candidates — useful for building a synthesis that connects
scattered knowledge.

`mode="decision"` is used by ztl:decision-support. It surfaces supporting and
conflicting note links specific to a proposed decision, not general topic coverage.

## draft_from_topic output

`draft_from_topic(topic="<topic>", target="note")` returns a draft payload:

- **`title`** — suggested synthesis note title
- **`body`** — prose synthesis of the topic, drawing from related notes
- **`tags`** — suggested tag list in `domain/scope` format
- **`source_ids`** — IDs of notes incorporated into the draft body

`target="note"` produces a synthesis note draft. `target="reference"` produces a
reference summary instead — use "note" for synthesis artifacts.

If the topic is too sparse (fewer than 3 related notes), `draft_from_topic` may
return an empty payload or minimal body. Fall back to manually assembling key
points from the `topic_packet` related_notes list.

## Checkpoint pattern for draft approval

Present the draft to the user with this structure:

```
Proposed synthesis note:
- Title: "<draft title>"
- Tags: [<tag list>]
- Connected notes: N (source_ids)
- Draft body:
  <draft body>

Approve, modify (provide changes), or cancel?
```

The user can modify: title, body content, tags, or cancel entirely. If the user
modifies the body, use the modified version in `create_note`, not the original
draft.

## Empty results handling

**Search returns 0 results (step 1):** The topic is new to the vault. Proceed
to `graph_gaps` and `topic_packet` — they may still find structurally relevant
context. Report to user: "No existing notes on '<topic>' — this synthesis will
be the first entry on this topic."

**graph_gaps returns no isolated clusters:** The vault is well-connected on this
topic. Skip gap reporting and proceed directly to topic_packet and draft.

**draft_from_topic returns empty body:** Not enough raw material. Report: "The
vault has too few notes on '<topic>' to generate a meaningful synthesis draft.
Suggest capturing more source material first with `ztl:capture`."
