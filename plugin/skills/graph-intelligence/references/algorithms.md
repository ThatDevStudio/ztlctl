# Graph Algorithm Reference

## Themes — Community Detection

**MCP tool**: `graph_themes`
**Algorithm**: Leiden (leidenalg) with Louvain fallback
**Graph view**: Undirected

### Output

```json
{
  "count": 3,
  "communities": [
    {
      "community_id": 0,
      "size": 12,
      "members": [{"id": "ztl_abc", "title": "...", "type": "note"}, ...]
    }
  ]
}
```

Communities are sorted by size (largest first).

### Interpretation

- **Large communities** = well-developed knowledge areas
- **Small communities (1-2 members)** = isolated ideas that need connecting
- **Number of communities** = breadth of your knowledge base
- Compare community topics — if two communities seem related but separate, you may be missing bridging notes

### Action Items

- Small communities: create bridging notes to connect them to larger clusters
- Single-member communities: these are orphans in disguise — link them
- Review cross-community connections — are the clusters too siloed?

## Rank — PageRank Importance

**MCP tool**: `graph_rank`
**Algorithm**: NetworkX PageRank
**Graph view**: Directed

### Output

```json
{
  "count": 20,
  "items": [
    {"id": "ztl_abc", "title": "...", "type": "note", "score": 0.042315}
  ]
}
```

Scores sum to ~1.0 across all nodes. Higher = more important.

### Interpretation

- **High PageRank** = many items link to this, directly or transitively. These are hub/anchor notes.
- **Surprisingly low PageRank** on a note you consider important = it's under-linked. Other notes should reference it.
- **References with high PageRank** = widely cited sources — these are foundational.
- **Tasks rarely rank high** — they tend to be leaf nodes (linked from, but not linking to much).

### Action Items

- Important topics with low rank: add links from related notes
- Extremely high rank (>0.1): consider if this note is doing too much — it might need splitting

## Path — Connection Chains

**MCP tool**: `graph_path`
**Algorithm**: Shortest path (undirected)
**Graph view**: Undirected

### Output

```json
{
  "source_id": "ztl_abc",
  "target_id": "ztl_xyz",
  "length": 3,
  "steps": [
    {"id": "ztl_abc", "title": "Source", "type": "note"},
    {"id": "ztl_mid1", "title": "Middle", "type": "note"},
    {"id": "ztl_mid2", "title": "Bridge", "type": "reference"},
    {"id": "ztl_xyz", "title": "Target", "type": "note"}
  ]
}
```

### Interpretation

- **Length 1** = directly connected
- **Length 2-3** = closely related, connection chain is clear
- **Length 4+** = loosely related, may benefit from a direct link
- **No path** = completely disconnected — a gap in the knowledge graph

### Action Items

- Long paths between related ideas: create a direct connecting note
- No path: this is a significant gap — write a bridging note
- Review intermediate nodes — they may be undervalued bridge notes

## Gaps — Structural Holes

**MCP tool**: `graph_gaps`
**Algorithm**: Burt's structural constraint (NetworkX)
**Graph view**: Undirected

### Output

```json
{
  "count": 20,
  "items": [
    {"id": "ztl_abc", "title": "...", "type": "note", "constraint": 0.875000}
  ]
}
```

Constraint range: 0.0–1.0. Higher = more constrained.

### Interpretation

- **High constraint (>0.7)** = node is tightly embedded in one cluster with few outside connections. This node represents a structural hole — an opportunity for cross-cutting links.
- **Low constraint (<0.3)** = node bridges multiple clusters — it's already well-connected across topic boundaries.
- **Filtered out**: isolated nodes (degree 0-1) are excluded since they'd have infinite/NaN constraint.

### Action Items

- High-constraint nodes: review and add links to notes in other topic areas
- These are your best ROI for knowledge graph improvement
- Creating just one cross-cluster link from a high-constraint node significantly improves graph connectivity

## Bridges — Betweenness Centrality

**MCP tool**: `graph_bridges` (Tier 2 — available when added)
**Algorithm**: Betweenness centrality (directed)
**Graph view**: Directed

### Output

```json
{
  "count": 20,
  "items": [
    {"id": "ztl_abc", "title": "...", "type": "note", "centrality": 0.123456}
  ]
}
```

### Interpretation

- **High betweenness** = this node sits on many shortest paths between other nodes. It's a bridge connecting different parts of the graph. Removing it would disconnect clusters.
- **Zero betweenness** = leaf node or member of a tight clique. Only nodes with centrality > 0 are returned.

### Action Items

- High-betweenness nodes are critical infrastructure — ensure they're high quality
- If a single node has very high betweenness, the graph is fragile — create alternative bridges
- Use in combination with `graph_themes` to understand which clusters the bridges connect

## Related — Spreading Activation

**MCP tool**: `get_related`
**Algorithm**: BFS with decay (activation × 0.5 per hop)
**Graph view**: Undirected

### Parameters

- `content_id`: starting node
- `depth`: max hops (1-5, default 2)
- `top`: max results (default 20)

### Interpretation

- **Score 1.0** = direct neighbor (1 hop)
- **Score 0.5** = 2 hops away
- **Score 0.25** = 3 hops away
- Results sorted by score descending — closest/most connected first
