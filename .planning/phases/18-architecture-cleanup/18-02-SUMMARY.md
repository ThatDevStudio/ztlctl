---
phase: 18-architecture-cleanup
plan: "02"
subsystem: infrastructure/services
tags: [tech-debt, embeddings, graph, performance]
dependency_graph:
  requires: []
  provides: [DEBT-01, DEBT-08]
  affects: [infrastructure/embeddings, services/graph, config/models]
tech_stack:
  added: []
  patterns: [module-level constant, k-approximation betweenness centrality]
key_files:
  created: []
  modified:
    - src/ztlctl/infrastructure/embeddings.py
    - src/ztlctl/config/models.py
    - src/ztlctl/services/graph.py
    - tests/infrastructure/test_embeddings.py
decisions:
  - "DEFAULT_EMBEDDING_DIM defined in embeddings.py; config/models.py uses literal 384 with comment pointing to canonical source (avoids potential future circular import, keeps config layer clean)"
  - "bridges() k-approximation uses identical pattern to _node_features(): exact for <=500 nodes, min(500, n) for larger graphs, seed=42 for reproducibility"
metrics:
  duration_minutes: 4
  completed_date: "2026-03-21"
  tasks_completed: 2
  files_changed: 4
---

# Phase 18 Plan 02: Embedding Constant and Bridges K-Approximation Summary

**One-liner:** DEFAULT_EMBEDDING_DIM module constant eliminates magic 384 literals; bridges() gains k-approximation matching the _node_features() pattern for large-vault performance.

## What Was Built

### DEBT-01: Centralize Embedding Dimension

Added `DEFAULT_EMBEDDING_DIM: int = 384` as a module-level constant in `src/ztlctl/infrastructure/embeddings.py`. Updated `EmbeddingProvider.__init__` to use `dim: int = DEFAULT_EMBEDDING_DIM` as its default. Added a cross-reference comment in `config/models.py` (`# Must match DEFAULT_EMBEDDING_DIM in ztlctl.infrastructure.embeddings`) so the constraint is visible at both sites without introducing an import dependency.

### DEBT-08: bridges() K-Approximation

Replaced the bare `nx.betweenness_centrality(g)` call in `GraphService.bridges()` with the same three-line pattern already used by `_node_features()`:

```python
node_count = g.number_of_nodes()
k_param = None if node_count <= 500 else min(500, node_count)
bc = nx.betweenness_centrality(g, k=k_param, seed=42)
```

This is transparent to callers — same return shape. Small graphs (<=500 nodes) use exact computation; larger graphs use k-approximation capped at 500 samples.

### Tests Updated

`tests/infrastructure/test_embeddings.py` imports `DEFAULT_EMBEDDING_DIM` and uses it in all assertions and provider constructions. Added `test_default_embedding_dim_constant` that explicitly asserts the constant equals 384.

## Commits

| Task | Description | Hash |
|------|-------------|------|
| 1 | feat(18-02): centralize embedding dim constant and add bridges k-approximation | 7d4637b |
| 2 | docs(18-02): mark DEBT-01 and DEBT-08 complete in REQUIREMENTS.md | 9886c73 |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Line too long in EmbeddingProvider.__init__ signature**
- **Found during:** Task 1 ruff check
- **Issue:** The updated constructor signature `def __init__(self, model_name: str = "all-MiniLM-L6-v2", dim: int = DEFAULT_EMBEDDING_DIM) -> None:` was 103 chars, exceeding the 100-char limit
- **Fix:** Split to multi-line form with trailing `-> None:` on its own line
- **Files modified:** src/ztlctl/infrastructure/embeddings.py

Otherwise — plan executed exactly as written.

## Known Stubs

None.

## Verification Results

- `DEFAULT_EMBEDDING_DIM` has 2 matches in embeddings.py: constant definition (line 16) + constructor default (line 41)
- `k_param` appears in both `bridges()` (line 386) and `_node_features()` (line 597)
- No bare `betweenness_centrality(g)` calls remain (all use `k=k_param, seed=42`)
- No bare `384` literals remain in production source
- 64 tests pass (6 embedding + 58 graph)
- ruff clean, mypy strict clean

## Self-Check: PASSED

Files exist:
- FOUND: src/ztlctl/infrastructure/embeddings.py
- FOUND: src/ztlctl/services/graph.py
- FOUND: tests/infrastructure/test_embeddings.py

Commits exist:
- FOUND: 7d4637b
- FOUND: 9886c73
