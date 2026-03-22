# Contradiction Review Reference

Reference for the MCP resource, detection tools, and evaluation criteria used in
the `ztl:review-contradictions` workflow. Use this when interpreting candidate
scores, evaluating pairs, or understanding graceful degradation behavior.

## ztlctl://review/contradictions resource

Returns the current contradiction candidate list:

- **candidates**: list of pairs, each with `note_a` (ID), `note_b` (ID), `score`
  (float 0–1), and `signals` (conflicting phrases or claims extracted during detection).
- **generated_at**: timestamp of last detection run.

Candidates with `score > 0.5` are surfaced for review. Lower-scored pairs are
below the confidence threshold and excluded by default.

## check_contradictions() output

`check_contradictions(max_pairs=20)` runs fresh detection and returns new candidates:

- **max_pairs**: cap on returned pairs. Use 20 for routine review; higher for deep audits.
- **score field**: semantic similarity indicating potential conflict. Score gates which
  pairs to inspect — it does not confirm contradiction.
- **signals field**: specific phrases or claims extracted from both notes that conflict.
  Weak signals (topic overlap only) suggest false positive; strong signals (direct
  negations, conflicting numbers) suggest genuine contradiction.

## Evaluation criteria

**Genuine contradiction indicators:**
- Note A asserts claim X; Note B directly negates X
- Both notes are current — neither supersedes the other
- The `signals` field shows specific contradictory phrases, not just shared terminology
- The conflict is about facts, numbers, or conclusions (not framing)

**False positive indicators (do not confirm):**
- Temporal supersession: newer note updates the older claim (evolution, not contradiction)
- Scope mismatch: one note is general ("all X do Y"), the other is specific ("this X
  does not Y") — these are compatible claims
- Topic overlap without claim conflict: complementary, not opposing, points on the same topic

## confirm_contradiction() behavior

`confirm_contradiction(note_a="<id>", note_b="<id>")` inserts a **bidirectional
`contradicts` graph edge** between the two notes:

- The edge is **permanent** — there is no `undo_contradiction` action in the standard
  workflow. Removal requires direct graph manipulation.
- The edge surfaces in `graph_related` results and in the contradiction resource for
  both notes going forward.
- **Why per-pair approval is mandatory:** a false positive `contradicts` edge corrupts
  every future query, synthesis, and decision-support operation that traverses those nodes.

## Graceful degradation when sqlite-vec is absent

When sqlite-vec is not installed, `check_contradictions` falls back to **heuristic
scoring**: BM25 lexical similarity + tag overlap + negation pattern matching.

- **Accuracy impact:** more false positives. Apply stricter evaluation — require
  explicit contradictory phrases in the `signals` field before confirming.
- **Install hint:** `uv add sqlite-vec`, then `ztlctl vector index` to build embeddings.
- Degradation is surfaced as an informational note; the workflow continues normally.
