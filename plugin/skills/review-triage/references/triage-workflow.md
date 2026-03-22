# Triage Workflow Reference

## Work Queue Scoring

`work_queue()` returns items sorted by composite score — higher score means more urgent attention needed. The score considers:

- **Age**: time since creation (older = higher urgency)
- **Link count**: notes with 0 outgoing links score higher (orphan penalty)
- **Maturity stage**: seeds score higher than budding, budding higher than evergreen
- **Update recency**: items not updated in > 7 days score higher

Use the score to set scope: "high-priority only" means items above a threshold (e.g., score > 0.7). The threshold is a judgment call based on queue depth — if the queue has 50 items, use a stricter threshold than if it has 10.

## Evaluation Criteria

Classify each item into one of these categories to determine the right action:

**Stale seed** — `maturity=seed`, age > 7 days, no body updates since creation
- Low effort to promote: add a sentence of context and bump to `budding`
- If the idea is no longer relevant: archive
- Do not leave seeds languishing — they represent unfinished thinking

**Orphan note** — 0 outgoing links, `status=draft`
- Try `reweave(content_id="<id>")` first — reweave may find connections automatically
- If reweave finds no connections: the note may need more context, or may belong in a different category
- Archive if the note is no longer relevant

**Completed task** — task content with all subtasks done, or explicitly marked complete by the user
- Archive via `close_content` — tasks are designed to be closed, not promoted
- Do not promote tasks to budding/evergreen — that maturity model is for notes and references

**Decision note in draft** — `subtype=decision`, not yet accepted or rejected
- Surface to user for a decision: accept, reject, or defer
- Use `update_content` to set the decision outcome

**Draft needing attention** — has content but no tags and no outgoing links
- Recommend adding `domain/scope` tags via `update_content`
- Recommend adding wikilinks to connect to existing knowledge
- After adding links, status auto-promotes from draft to linked

## Batch vs Individual Processing

**Batch processing** is appropriate when:
- The queue has many similar items (e.g., 10 stale seeds) → process all at once with a single proposed action
- The user has explicitly requested "process everything"
- Items have clear, low-risk actions (promote maturity, close completed tasks)

**Individual processing** is appropriate when:
- Items need different evaluations (a mix of tasks, notes, and decisions)
- Items have higher-stakes actions (archives that cannot be easily undone)
- The user wants to review each item before any action

**Default:** Batch with the confirmation gate — present the full proposed set, let the user approve or prune.

## Status Transitions

Valid transitions for reference during triage:

**Maturity (notes, references):**
- `seed` → `budding` → `evergreen`
- Maturity is set explicitly via `update_content(changes={"maturity": "budding"})`

**Note status (auto-computed from link count):**
- `draft` (0 links) → `linked` (1+ links) → `connected` (3+ links)
- Status is not set directly — it updates automatically when links are added via reweave or wikilink

**Archive (soft-delete):**
- Any content can be archived via `close_content`
- Archives preserve graph edges but hide the item from default queries
- There is no unarchive in the standard workflow — treat archives as permanent during triage
