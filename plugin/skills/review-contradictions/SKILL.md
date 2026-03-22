---
name: review-contradictions
description: >
  Use when the user wants to review conflicting notes, find inconsistencies in
  the vault, check for contradictions between knowledge claims, or inspect
  semantically-close notes that may conflict. Runs the per-pair evaluation loop
  to surface genuine contradictions and dismiss false positives.
version: 1.0.0
disable-model-invocation: true
---

# Contradiction Review

Review conflicting note pairs and confirm genuine contradictions as permanent
graph edges. This skill uses the Loop pattern: enumerate candidates, inspect
each pair, propose a verdict, then wait for per-pair user approval before any
write fires.

## Iron Laws

**NEVER auto-confirm contradictions.** Each pair requires explicit user approval
before `confirm_contradiction` fires. Contradictions insert permanent bidirectional
graph edges — false positives corrupt the knowledge graph and are hard to undo.

**Gracefully degrade if sqlite-vec is absent.** If `check_contradictions` returns
an error mentioning sqlite-vec, surface: "Semantic contradiction detection requires
sqlite-vec. Install with: `uv add sqlite-vec`. Falling back to heuristic scoring."
Continue with heuristic results — do not error out.

**Check `result.success` after every MCP call.** Stop the loop and report progress
if a call fails unexpectedly.

## Workflow

1. **Read `ztlctl://review/contradictions`** — load the current candidate list:
   pending pairs with note IDs, similarity scores, and signals field (conflicting
   phrases or claims extracted during detection).

2. **If no candidates:** run `check_contradictions(max_pairs=20)` to generate a
   fresh candidate set. Check `result.success` — surface any sqlite-vec error with
   the install hint above. If candidates are still empty after detection, report
   "No contradiction candidates found. Vault claims appear consistent."

3. **For each candidate pair (score > 0.5):**

   a. **Fetch both notes in parallel:** `get_document(content_id="<note_a>")` and
      `get_document(content_id="<note_b>")`. Check `result.success` on both.

   b. **Evaluate the pair:** Do the notes make genuinely conflicting claims?
      Check the `signals` field for specific conflicting phrases. Consider:
      - Direct conflict: Note A asserts X, Note B asserts not-X
      - Temporal context: is the newer note superseding (not contradicting) the older?
      - Scope mismatch: is one claim specific and the other general (no contradiction)?

   c. **Present verdict to user:**
      - "Genuine contradiction: [brief reason]. Confirm?" — wait for approval
      - "False positive: [brief reason — compatible claims / scope mismatch / temporal supersession]. Dismiss?"

4. **On user approval:** `confirm_contradiction(note_a="<a>", note_b="<b>")`.
   Check `result.success`. Report the inserted edge.

5. **On user rejection:** note as false positive, move to next pair.

6. **Report results** — pairs reviewed, genuine contradictions confirmed (with
   IDs), false positives dismissed, pairs skipped (score ≤ 0.5).

---

See `references/contradiction-review.md` for scoring details, evaluation
criteria, and graceful degradation behavior.
