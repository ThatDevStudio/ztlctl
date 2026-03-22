# Polaris Alignment Reference

Reference for the polaris document structure and `check_alignment` response
format. Use this when the SKILL.md workflow steps need deeper explanation.

## Polaris document structure

The `ztlctl://polaris` resource returns the vault's polaris document with
three sections:

**Mission statement** — one sentence describing the vault owner's overarching
goal. The north star against which all priorities are measured. Stable over time.

**Priorities** — an ordered list. Each priority has a title and a description.
Order is intentional: priority 1 matters more than priority 5 when trade-offs
arise. Priorities change as strategy evolves; reload `ztlctl://polaris`
periodically to stay current.

**Decision principles** — rules for breaking ties. When two courses of action
both align with multiple priorities, decision principles determine which wins.
Examples: "prefer reversible over irreversible", "prefer learning over shipping".

## check_alignment response

The `check_alignment` tool returns:

- **`relevant_priorities`** — list of priorities whose descriptions overlap
  with the proposed decision. Empty list means no match found.

- **`reasoning`** — text explaining why the listed priorities match (or why
  no match was found). Surface this reasoning verbatim — it was derived from
  the vault owner's own priority descriptions.

- **`alignment_score`** — numeric score (when available). Higher is more
  aligned. Treat as a rough signal, not an absolute measure. Two decisions
  with similar scores may have very different qualitative alignment.

## Decision audit trail

Creating a `decision` subtype note after alignment check builds a permanent,
queryable record of strategic decisions.

The note body should contain:

1. The decision or proposed action (verbatim, as submitted to `check_alignment`)
2. The alignment result — `relevant_priorities` list and reasoning
3. The rationale for proceeding (or not proceeding)
4. Any dissenting considerations or trade-offs acknowledged

This pattern builds a history of strategic decisions that `decision_support`
can query later. Over time, the audit trail reveals patterns — which priorities
drive the most decisions, where scope expansion happens, and whether stated
priorities match actual decisions.

The decision note is always optional — create it only when the alignment check
was for a significant, non-trivial decision. Routine actions do not need
decision notes.
