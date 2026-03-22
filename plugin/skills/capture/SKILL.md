---
name: capture
description: >
  Use when the user wants to capture research, create a note about a topic,
  ingest an external source, or add knowledge to the vault. Guides structured
  content creation with duplicate detection and automatic linking.
version: 1.0.0
disable-model-invocation: true
---

# Research Capture

Capture knowledge into the vault with duplicate detection, proper metadata, and
automatic linking. This skill encodes the research capture recipe: search first,
then create.

## Iron Law

**Always search before creating.** Duplicates waste effort and fragment
knowledge. Step 1 is non-negotiable.

**Check `result.success` after every write.** If a create or ingest call fails,
stop and surface the error — do not proceed to the next step.

## Workflow

1. **`search(query="<topic>", limit=10)`** — check what already exists in the
   vault. If a near-duplicate title is found, ask the user: "Found existing note
   '<title>'. Create anyway or update existing?"

2. **Lightweight orientation** — if an active session is open, skip context
   assembly (already oriented). Otherwise, call
   `agent_context(topic="<topic>", budget=4000)` for lightweight topic context
   before creating.

3. **For external sources (articles, papers, tools, specs):**
   `ingest_source(title="<title>", content="<text>", input_kind="text", target_type="reference")`
   — creates a `captured` reference in the vault. Check `result.success` before
   proceeding.

4. **For synthesis or insights:**
   `create_note(title="<synthesis title>", tags=["<domain/scope>"], session=<session_id if active>)`
   — creates a note with session linking if a session is active. Reweave fires
   automatically via the Reweave plugin. Check `result.success`.

5. **Report** — surface the created content IDs, a link to the new content, any
   reweave suggestions from the create response, and duplicate warnings from
   step 1 (if any were dismissed).

## Content type decision

Choose the right creation tool before acting:

- **Insight, idea, or concept** → `create_note`
- **Decision with alternatives** → `create_note` with `subtype="decision"`
- **External article, paper, or tool** → `ingest_source` (creates a reference)
- **Follow-up action** → `create_task` with priority, impact, and effort set
- **Quick idea, not ready to develop** → `garden_seed` (maturity=seed, low-ceremony)

## Anti-patterns

Do NOT call `reweave` manually after `create_note` — the Reweave plugin fires
automatically on every create. Calling it manually causes double-reweave, which
wastes time and inflates link suggestions.

Do NOT skip the search step — always check for existing content before creating.
Even a brief search prevents note fragmentation.

Do NOT use generic tags — use `domain/scope` format (e.g., `research/methodology`
not `research`). Single-segment tags are valid but produce less useful filtering.

See `references/capture-workflow.md` for the full content type decision tree and
tagging conventions.
