# Decision Workflow Reference

Detailed reference for `decision_support` output, `ztlctl://decision-queue`
resource format, and briefing structure for the ztl:decision-support skill.

## decision_support output format

`decision_support(topic="<topic>")` aggregates vault content relevant to a
decision topic:

- **`relevant_decisions`** — past decision notes (subtype=decision) matching
  the topic, sorted by recency
- **`open_tasks`** — tasks in the work queue that touch this topic
- **`relevant_references`** — captured references related to the decision space
- **`scores`** — relevance scores for each returned item (BM25 + semantic)

Scan `relevant_decisions` first — prior decisions on the same topic are the most
important context. If the vault has recorded a decision on this exact subject
before, surface it prominently in the briefing.

## ztlctl://decision-queue resource

The `ztlctl://decision-queue` MCP resource returns two sections:

**Recent decisions** — the 10 most recently created or updated decision notes
(subtype=decision). Provides a rolling window of strategic decisions made in the
vault. Differs from `decision_support` in scope: decision-queue is not filtered
by topic — it is a global recent-decisions log.

**Active work queue** — items from `work_queue()` with the highest composite
scores. Surfaces what is currently in progress. Use this to check whether related
work is already underway before recommending new action.

## topic_packet mode="decision"

`topic_packet(topic="<topic>", mode="decision")` returns a decision-focused packet:

- **`supporting_links`** — notes whose content agrees with or supports the
  proposed decision direction
- **`conflicting_links`** — notes whose content contradicts or raises objections
  to the proposed decision
- **`related_decisions`** — other decision notes in the same topical area
- **`open_questions`** — unresolved questions extracted from topic notes

Unlike `mode="learn"`, decision mode actively surfaces tension — it is optimized
for finding the hardest counter-arguments to a proposed direction. Use conflicting_links
as the most important section of the briefing.

## Briefing structure

Present the final briefing in this order:

- **Prior decisions** — "Found N prior decisions on '<topic>': [titles with dates]"
- **Active context** — "Currently in flight: [open tasks and recent decisions]"
- **Conflicting signals** — "Vault notes that push back: [conflicting_links summaries]"
- **Polaris alignment** — "This decision relates to [N] priorities: [list]. Reasoning: [reasoning]"
- **Recommended action** — your synthesis: should the user proceed, defer, or investigate further?

The briefing is a synthesis, not a raw data dump. Summarize the most important
items from each step rather than listing everything.

## Distinction from ztl:align

| Aspect | ztl:align | ztl:decision-support |
|---|---|---|
| MCP calls | 2 (polaris + check_alignment) | 5–6 (multi-source) |
| Output | Pass/fail alignment signal | Structured briefing |
| Use case | Quick "is this on-strategy?" | "What do I need to know before deciding?" |
| Writes | Optional decision note | Optional decision note |

## Optional decision note

Only create a decision note when the user explicitly requests it after reviewing
the briefing. Use:

`create_note(title="Decision: <title>", subtype="decision", body="<briefing summary>")`

The body should include: the proposed decision, alignment result, prior decisions
found, key conflicting signals, and the chosen direction. This builds the audit
trail that `decision_support` will query in future runs.
