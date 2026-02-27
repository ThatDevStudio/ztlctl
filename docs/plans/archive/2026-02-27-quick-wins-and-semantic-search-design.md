# Quick Wins Batch + Semantic Search — Design Document

## Overview

Two deliverables in one session:

1. **Quick wins batch** (one PR): MCP HTTP transport, local plugin discovery, Alembic migration tests
2. **Semantic search** (separate PR): sqlite-vec vector storage with local sentence-transformers embeddings, hybrid BM25+cosine ranking

---

## Quick Wins

### T-012: MCP Streamable HTTP Transport

**Problem**: `ztlctl serve` only supports `--transport stdio`. FastMCP v1.26.0 supports `stdio`, `sse`, and `streamable-http` natively.

**Design**: CLI wiring only — no transport implementation needed.

- Expand `--transport` choices to `["stdio", "sse", "streamable-http"]`
- Add `--host` (default `127.0.0.1`) and `--port` (default `8000`) options
- Pass host/port through `create_server(vault_root, host, port)` → `FastMCP("ztlctl", host=host, port=port)`
- Host/port are only meaningful for non-stdio transports (FastMCP ignores them for stdio)

### T-009: Local Plugin Discovery

**Problem**: Plugin discovery only scans pip-installed entry points. No way to load plugins from `.ztlctl/plugins/`.

**Design**: Add `_discover_local(local_dir)` to `PluginManager`.

- `discover_and_load()` accepts optional `local_dir: Path | None`
- New `_discover_local()`: scans `*.py` files via `importlib.util.spec_from_file_location` + `module_from_spec`
- For each loaded module, scan for classes implementing any `ZtlctlHookSpec` method (using `pluggy.HookimplMarker` detection)
- Load order: entry-points first, then local (local can augment or override)
- Graceful error handling: log warning on import failure, continue with remaining plugins
- Returns list of loaded local plugin names

### T-024: Alembic Migration Testing

**Problem**: `UpgradeService` has 3 methods and 0 tests.

**Design**: Integration tests using isolated vault fixtures.

- `test_check_pending_on_fresh_stamped_db` — 0 pending after stamp
- `test_check_pending_detects_unstamped` — tables exist, no Alembic tracking → pending > 0
- `test_apply_on_fresh_db` — successful migration
- `test_apply_already_current` — "already up to date" message
- `test_stamp_current` — stamps at head
- `test_pre_alembic_detection` — `_tables_exist()` returns True/False correctly

---

## Semantic Search (T-015)

### Architecture

**Approach A**: sqlite-vec + local sentence-transformers embeddings.

```
User query
    │
    ▼
QueryService.search(rank_by="semantic" | "hybrid")
    │
    ├─► FTS5 BM25 search (existing) ──► bm25_scores
    │
    ├─► VectorService.search_similar(query_embedding, limit)
    │       │
    │       ├─ Embed query via EmbeddingProvider
    │       └─ sqlite-vec knn search ──► cosine_scores
    │
    └─► Hybrid merge: α * bm25_norm + (1-α) * cosine_norm
            │
            ▼
        Ranked results
```

### Components

**1. EmbeddingProvider** (`src/ztlctl/infrastructure/embeddings.py`)

Simple class wrapping sentence-transformers:
- `__init__(model_name, dim)` — lazy model loading (first call)
- `embed(text) → list[float]` — single text → vector
- `embed_batch(texts) → list[list[float]]` — batch embedding
- Guarded import: `sentence-transformers` only loaded when `semantic_enabled=True`

Model: `all-MiniLM-L6-v2` (384 dimensions, ~80MB, fast inference).

**2. Vector Storage** (`vec_items` virtual table via sqlite-vec)

```sql
CREATE VIRTUAL TABLE IF NOT EXISTS vec_items USING vec0(
    node_id TEXT PRIMARY KEY,
    embedding FLOAT[384]
);
```

- Created alongside FTS5 table in `init_db()` when `semantic_enabled=True`
- sqlite-vec loaded via `conn.execute("SELECT load_extension('vec0')")` or `sqlite_vec.load(conn)`
- Alembic migration: new migration `002_vector_table.py` (conditional on sqlite-vec availability)

**3. VectorService** (`src/ztlctl/services/vector.py`)

New service:
- `index_node(node_id, text)` — embed and upsert into vec_items
- `remove_node(node_id)` — delete from vec_items
- `search_similar(query_text, limit) → list[dict]` — embed query, knn search
- `reindex_all()` — batch re-embed all non-archived nodes
- `is_available() → bool` — check if sqlite-vec extension loads

All methods gated by `SearchConfig.semantic_enabled`.

**4. QueryService Integration**

Add `rank_by="semantic"` option to `search()`:
- `"semantic"` — vector-only similarity search (no FTS5 query needed)
- `"hybrid"` — weighted merge of BM25 + cosine scores
- Hybrid weight configurable via new `SearchConfig.semantic_weight: float = 0.5`

Score normalization: min-max normalize both BM25 and cosine scores before weighted merge.

**5. Indexing Pipeline**

Embeddings computed during content creation:
- `CreateService`: after PERSIST stage, if `semantic_enabled`, call `VectorService.index_node()`
- `UpdateService`: re-index on title/body changes
- `VectorService.reindex_all()` for bulk re-indexing (exposed via CLI)

**6. CLI Surface**

- `ztlctl search "query" --rank-by semantic` — new rank_by option value
- `ztlctl search "query" --rank-by hybrid` — new rank_by option value
- `ztlctl vector reindex` — new command group for bulk operations
- `ztlctl vector status` — show index stats (count, model, availability)

### Configuration

Existing `SearchConfig` fields already aligned:

```toml
[search]
semantic_enabled = true          # default: false
embedding_model = "local"        # default: "local"
embedding_dim = 384              # default: 384
semantic_weight = 0.5            # NEW — weight for hybrid ranking
```

### Dependencies

- `sqlite-vec` — already declared as optional extra `semantic = ["sqlite-vec"]`
- `sentence-transformers` — needs to be added to semantic extra
- `torch` — transitive via sentence-transformers (CPU-only sufficient)

### Error Handling

- If `semantic_enabled=True` but sqlite-vec not installed → `ServiceResult(ok=False, error="SEMANTIC_UNAVAILABLE")`
- If embedding model download fails → graceful fallback warning, FTS5-only results
- If vec_items table doesn't exist → skip vector search, return FTS5-only

### Testing

- Mock `EmbeddingProvider` in unit tests (avoid downloading model in CI)
- Integration tests with real sqlite-vec if available, skip otherwise
- Test hybrid ranking math with known score values
