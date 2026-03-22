# Capture Workflow Reference

Detailed reference for content type decisions, tagging conventions, and session
integration. Use this when the quick decision guide in SKILL.md is insufficient.

## Content type decision tree

Before calling any creation tool, work through the decision tree:

**Is it an idea, concept, or insight?**
→ `create_note`
  - Is it a decision with evaluated alternatives? → `create_note` with `subtype="decision"`
  - Does it extract key points from learning material? → `create_note` with `subtype="knowledge"`

**Is it an external source (article, paper, tool, spec)?**
→ `ingest_source` with `target_type="reference"`
  - Classify with `input_kind="text"` for raw text, `input_kind="url"` for links
  - Created references start in `captured` status — annotate them during the session

**Is it a follow-up action?**
→ `create_task` with priority, impact, and effort fields
  - `priority`: 1–5 (5 = urgent)
  - `impact`: 1–5 (5 = high value)
  - `effort`: 1–5 (5 = high effort)
  - Task score = (priority × impact) / effort — higher is surfaced first in `work_queue`

**Is it a quick idea, not ready to develop?**
→ `garden_seed`
  - Maturity defaults to `seed` — low-ceremony, just a title and optional tags
  - Seeds are time-tracked: vault warns if unattended for more than 7 days
  - Progress seeds to `budding` → `evergreen` as you develop them

## Tagging conventions

Use hierarchical `domain/scope` format for all tags:

- `math/algebra` — domain is "math", scope is "algebra"
- `python/stdlib` — domain is "python", scope is "stdlib"
- `research/methodology` — domain is "research", scope is "methodology"

Single-segment tags (e.g., `important`) are valid but are classified as
`unscoped`. They work but produce less useful filtering in `search` and
`work_queue` results. Prefer domain/scope format for anything more specific
than a single orthogonal label.

Consistent tagging enables cross-cutting discovery — a `search` for
`python/stdlib` returns all notes tagged with that exact scope, not just
lexically matching notes.

## Session integration

When a session is active, pass `session=<session_id>` to all create calls.
The session ID is returned by `session_start` and surfaces in `session_status`.

Session-linked content benefits from the enrichment pipeline on session close:

1. **Cross-session reweave** — reweaves all notes and references created in
   this session, not just the most recently created ones
2. **Orphan sweep** — attempts to link any session-created content with 0
   outgoing links
3. **Integrity check** — validates that all session-created content is
   self-consistent

If no session is active, content is still created correctly — it simply misses
the session-close enrichment pipeline benefits. For multi-step research work,
always wrap capture in a session.
