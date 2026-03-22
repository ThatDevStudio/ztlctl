---
name: synthesize
description: >
  Use when the user wants to synthesize scattered notes into a unified artifact,
  consolidate knowledge on a topic, connect existing notes, find structural gaps,
  or create a synthesis note. Activates on "synthesize", "consolidate", "connect
  my notes on X", "summarize what I know about X", "find gaps in X", or
  "create synthesis".
version: 1.0.0
disable-model-invocation: true
---

# Knowledge Synthesis

Synthesize scattered vault knowledge into a single connected artifact. This skill
surveys existing content, surfaces structural gaps, drafts a synthesis note, and
writes it to the vault only after user approval.

## Iron Laws

**Always search before synthesizing.** Duplicate synthesis notes fragment
knowledge rather than consolidate it. Step 1 is non-negotiable — check what
exists first.

**Present draft to user before creating.** Never auto-write a synthesis note
without showing the draft and receiving explicit approval. The checkpoint in
step 5 is not optional.

**Check `result.success` after every MCP call.** If any step fails, stop and
surface the error — do not proceed to the write phase.

## Workflow

1. **`search(query="<topic>", limit=20)`** — survey existing content on the
   topic. If a mature synthesis note already exists, surface it and ask: "Found
   existing synthesis '<title>'. Update it instead of creating new?"

2. **`graph_gaps(top=10)`** — find structurally isolated clusters in the
   knowledge graph. Note which gap IDs are relevant to the topic — these surface
   areas where the synthesis should build bridges.

3. **`topic_packet(topic="<topic>", mode="learn")`** — get comprehensive topic
   context: related notes, bridge candidates, stale items, and identified gaps.
   This is the raw material for the synthesis.

4. **`draft_from_topic(topic="<topic>", target="note")`** — generate a draft
   synthesis note payload. If no draft is returned (topic too sparse), fall
   back to assembling key points from step 3 results manually.

5. **Present draft to user for approval.** Show: draft title, body, proposed
   tags, and connected note count. Ask: "Approve this synthesis, modify the
   title/content, or cancel?" Do not proceed until the user responds.

6. **`create_note(title="<approved title>", body="<approved draft>", tags=["<topic>"])`**
   — write the synthesis note to the vault. Reweave fires automatically via the
   Reweave plugin. Check `result.success` before reporting.

7. **Report** — note ID, notes connected by reweave, structural gaps surfaced
   in step 2, bridge candidates from topic packet.

## When NOT to use

- If the user wants to capture new research from an external source — use
  `ztl:capture` instead (synthesize consolidates existing vault content; capture
  adds new external content).
- If the user wants a quick search result, not an artifact — call `search`
  directly; this skill creates a new note.
- If the vault has fewer than 5 notes on the topic — synthesis needs raw
  material; orient and capture first.

See `references/synthesis-workflow.md` for graph_gaps output format, topic_packet
fields, and empty-result handling.
