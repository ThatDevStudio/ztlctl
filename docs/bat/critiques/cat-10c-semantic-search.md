# Category 10c Critique: Semantic Search (BAT-118 to BAT-119)

## Test Summary

| Test | Description | Result |
|------|-------------|--------|
| BAT-118 | Semantic Search — Available | SKIP (extras not installed) |
| BAT-119 | Semantic Search — Unavailable | PASS |

## Graceful Degradation (BAT-119): Excellent

When semantic search extras (`sqlite-vec`, `sentence-transformers`) are not
installed, the system handles this gracefully at every level:

### CLI Level
```bash
$ ztlctl --json query search "concept" --rank-by semantic
{
  "ok": true,
  "warnings": ["Semantic search unavailable — falling back to FTS5"]
}
```
- The `--rank-by semantic` flag is accepted without error
- The search still returns `ok: true`
- A clear warning explains the fallback
- Results use FTS5 ranking automatically

### Vector Status Command
```bash
$ ztlctl --json vector status
{
  "ok": true,
  "data": {
    "available": false,
    "message": "Semantic search unavailable — install sqlite-vec and sentence-transformers"
  }
}
```
- Diagnostic command reports availability
- Provides actionable install instructions
- Does not fail or crash

### Vector Management Commands
The `vector` command group provides:
- `vector status` -- Check availability and index state
- `vector reindex` -- Rebuild the vector index

This gives users explicit control over the embedding pipeline.

## Architecture Assessment

### Dual-Dependency Guard Pattern

Semantic search requires two independent packages:
1. **sqlite-vec**: SQLite extension for vector storage and similarity queries
2. **sentence-transformers**: ML model for generating text embeddings

Both are guarded with try/except imports at module level:

```python
# infrastructure/embeddings.py
_st_available = False
try:
    import sentence_transformers
    _st_available = True
except ImportError:
    pass

# services/vector.py
def is_available(self) -> bool:
    try:
        import sqlite_vec
        sqlite_vec.load(raw)
        self._vec_available = True
    except Exception:
        self._vec_available = False
```

This pattern ensures:
- Core CLI functionality is never affected by missing extras
- The availability check happens once and is cached
- Both dependencies are checked independently

### EmbeddingProvider: Clean Wrapper

The `EmbeddingProvider` class wraps sentence-transformers with:
- **Lazy model loading**: The model is only loaded on first `embed()` call,
  avoiding multi-second startup delay when semantic search is not used
- **Batch support**: `embed_batch()` for efficient bulk indexing
- **Configurable model**: `all-MiniLM-L6-v2` default (384 dimensions, fast, good quality)
- **Static availability check**: `is_available()` without instantiation

### VectorService: Comprehensive

The `VectorService` provides:
- `is_available()` -- Check sqlite-vec extension loading
- `ensure_table()` -- Create `vec_items` virtual table
- `index_node(node_id, content)` -- Embed and store single node
- `remove_node(node_id)` -- Remove embedding
- `search_similar(query_text, limit)` -- Cosine distance search
- `reindex_all()` -- Bulk re-embedding of all non-archived nodes

All operations are guarded by `is_available()` and return gracefully when
semantic search is not configured.

### Integration with Query Pipeline

The search pipeline (`QueryService.search()`) uses `--rank-by` to select ranking:
- `relevance` (default) -- FTS5 BM25 ranking
- `semantic` -- Cosine distance from sqlite-vec
- `recency` -- Sort by modification date

When `semantic` is selected but unavailable, the fallback to FTS5 is automatic
with a warning. This is the correct behavior -- users should never see a crash
from selecting an unavailable ranking method.

## Strengths

1. **Zero-impact optional**: Semantic search adds zero overhead when not installed.
   No imports, no model loading, no database extensions. The core CLI is unaffected.

2. **Clear diagnostics**: The `vector status` command provides immediate feedback
   about availability and missing packages.

3. **Lazy model loading**: The sentence-transformers model (which can be 50-100MB)
   is only loaded when first needed, not at CLI startup.

4. **Automatic fallback**: `--rank-by semantic` silently degrades to FTS5 with
   a warning, rather than failing. This is the right UX choice.

5. **Configurable model**: The embedding model and dimension are configurable via
   `[search]` TOML config, supporting different quality/speed tradeoffs.

6. **Binary serialization**: The `_serialize_f32` function packs float vectors
   into compact binary for sqlite-vec, which is more efficient than JSON storage.

## Weaknesses and Recommendations

1. **Cannot test actual semantic search**: Without the extras installed, we cannot
   verify embedding quality, cosine distance calculations, or hybrid BM25+cosine
   ranking. Consider adding a CI job with `ztlctl[semantic]` extras.

2. **No embedding persistence diagnostics**: When `vector status` reports
   unavailable, there is no indication of whether the user needs to install
   Python packages or compile a SQLite extension. The error message could be
   more specific about which dependency is missing.

3. **Model download not managed**: The first `embed()` call may trigger a model
   download from Hugging Face (potentially hundreds of MB). There is no progress
   indicator, no offline mode documentation, and no pre-download command. A
   `vector setup` command that downloads the model proactively would improve UX.

4. **No hybrid ranking visible**: The project memory mentions "hybrid BM25+cosine
   ranking," but the CLI exposes `--rank-by semantic` and `--rank-by relevance`
   as separate modes. If hybrid mode exists, it should be exposed as
   `--rank-by hybrid` or documented as the default when semantic is available.

5. **sqlite-vec load on every operation**: Each `VectorService` method calls
   `sqlite_vec.load(raw)` on the raw SQLite connection. This could be optimized
   to load once per connection lifecycle.

6. **No incremental indexing**: The `reindex_all()` method rebuilds the entire
   index (DELETE + bulk INSERT). For large vaults, an incremental approach that
   only re-indexes modified content would be more efficient.

## Overall Assessment

Semantic search is a well-designed optional feature with excellent graceful
degradation. The architecture correctly treats it as an enhancement layer on
top of the existing FTS5 search pipeline, with zero impact on users who do not
install the extras. The main limitation is that we cannot test the actual
semantic functionality in this environment.

**Grade: B+**

The degradation path is flawless (automatic fallback, clear diagnostics, zero
overhead), which is arguably the harder design problem. The actual semantic
search functionality could not be tested, but the code structure is clean and
follows the same patterns (lazy loading, availability checking, service layer
abstraction) used successfully throughout the codebase. The deductions are for
untested functionality, model download management, and potential performance
optimizations.
