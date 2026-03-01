---
name: graph-intelligence
description: >
  Use when analyzing vault structure, finding connections between ideas,
  identifying knowledge gaps, or understanding the shape of a knowledge base.
  Guides interpretation of graph analysis results.
version: 1.0.0
---

# Graph Intelligence for ztlctl Vaults

The ztlctl knowledge graph tracks every connection between content items. Graph analysis tools reveal patterns invisible at the individual note level.

## When to Use Graph Analysis

| Situation | Tool | What it reveals |
|---|---|---|
| "What topics cluster together?" | `graph_themes` | Community structure |
| "What are the most important notes?" | `graph_rank` | Influence via PageRank |
| "How are these two ideas connected?" | `graph_path` | Shortest connection chain |
| "Where is knowledge thin?" | `graph_gaps` | Structural holes |
| "What notes bridge different topics?" | `graph_bridges` | Cross-cluster connectors |
| "What's related to this note?" | `get_related` | Spreading activation |

## Decision Guide

**Start with `graph_themes`** when exploring — it gives you the big picture of how knowledge clusters.

**Use `graph_rank`** to find anchor notes — high PageRank items are the most referenced/connected and make good starting points for any topic.

**Use `graph_path`** when a user asks "how does X relate to Y?" — it shows the chain of connections.

**Use `graph_gaps`** to find improvement opportunities — high-constraint nodes are tightly embedded in their local cluster and would benefit from cross-cutting links to other areas.

**Use `get_related`** for focused exploration around a single item — it uses spreading activation with decay to find nearby nodes.

## Interpreting Results

See `references/algorithms.md` for detailed interpretation of each algorithm's output — what the scores mean, what to look for, and how to act on findings.

## Combining Analysis

The most powerful insights come from combining multiple analyses:

1. Run `graph_themes` → identify clusters
2. Run `graph_gaps` → find where clusters are isolated
3. Run `graph_rank` within each cluster → find anchor notes
4. Use `graph_path` → verify connections between clusters
5. Create notes that bridge gaps → strengthen the knowledge structure
