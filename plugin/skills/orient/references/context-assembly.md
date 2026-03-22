# Context Assembly Reference

Reference for the `agent_context` tool parameters and the 5-layer payload it
returns. Use this when tuning orientation depth or debugging missing context.

## The 5-layer context payload

`agent_context` returns a structured payload assembled from five sources, each
serving a distinct role in grounding agent work:

**Layer 1: Polaris priorities**
Always included regardless of topic or budget. Contains the vault owner's
mission statement, ordered priorities, and decision principles. Agents should
check polaris first — it establishes what matters before surfacing what exists.

**Layer 2: Related notes**
Notes matching the topic via BM25 lexical search and semantic (vector) search.
Higher budget allocates more tokens to this layer. These are the notes most
directly relevant to the current work topic.

**Layer 3: Graph neighbors**
One-hop connections of the highest-ranked related notes. Surfaces adjacent
concepts that the topic notes are already linked to. Helps agents understand
how a topic fits into the broader knowledge graph.

**Layer 4: Session history**
Recent session summaries — what work has been done and what conclusions were
reached. Prevents repeating prior analysis. Especially valuable on recurring
topics where the vault has accumulated session records.

**Layer 5: Methodology guidance**
Content from the vault's `self/` directory — the vault owner's documented
working style, note type preferences, and domain-specific conventions. Ensures
agent behavior matches the vault's established patterns.

## Budget parameter

The `budget` parameter controls how many tokens of related content are included
across Layers 2–4. Layer 1 (polaris) and Layer 5 (methodology) are always
included regardless of budget.

- `budget=4000` — lightweight orientation. Fewer related notes, shallower graph
  traversal. Use when time-constrained or when the topic is narrow.
- `budget=8000` — standard orientation. Good default for initial vault entry.
  Balances coverage with context window cost.
- `budget=16000` — deep-dive orientation. Use when the user needs comprehensive
  context before a complex synthesis or decision task. Reserve for situations
  where missing context would be costly.

## Topic parameter

The `topic` parameter focuses the context payload on a specific domain.

- **Omit topic** for general vault orientation — Layer 2 and Layer 3 draw from
  recent activity and high-PageRank notes rather than a query.
- **Include topic** to focus on a specific domain — topic drives the BM25 and
  semantic search in Layer 2, and sets the seed node for Layer 3 graph traversal.
- **Specificity matters** — "python async patterns" surfaces more useful context
  than "python" alone. Match the topic to the granularity of the current task.
