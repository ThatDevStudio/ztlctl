# Session Enrichment Pipeline

When a session closes, ztlctl runs an automated enrichment pipeline. Understanding this pipeline helps you make better decisions about when to close sessions and what to expect.

## Pipeline Stages

### 1. Cross-Session Reweave

**What**: Runs reweave on every `note` and `reference` created during this session.

**Why**: New content may connect to existing vault items that weren't linked during capture.

**How it works**:
- Each item is scored against all unlinked candidates using the 4-signal system (BM25, tag overlap, graph proximity, topic match)
- Connections above the threshold (default 0.6) are created
- Garden notes (maturity set) get frontmatter links only — body is protected

**Controlled by**: `session.close_reweave` config (default: true)

### 2. Orphan Sweep

**What**: Finds all notes and references with 0 outgoing edges and attempts to connect them.

**Why**: Orphans are knowledge islands — they exist but aren't connected to anything. This is the weakest state in a zettelkasten.

**How it works**:
- Uses a lower reweave threshold (`orphan_reweave_threshold`, default 0.2) than normal reweave
- More aggressive because even weak connections are better than isolation
- Only targets items with zero outgoing links

**Controlled by**: `session.close_orphan_sweep` config (default: true)

### 3. Integrity Check

**What**: Scans the vault for structural problems.

**Why**: Catches issues early before they compound. Four categories checked:

| Category | What it checks |
|---|---|
| **Broken links** | Wikilinks or frontmatter links pointing to non-existent IDs |
| **Orphan edges** | DB edges with missing source or target nodes |
| **Missing files** | DB records with no corresponding file on disk |
| **Stale FTS** | Full-text search index out of sync with content |

**Controlled by**: `session.close_integrity_check` config (default: true)

### 4. Graph Materialization

**What**: Computes and persists graph metrics into the database.

**Metrics stored**:
| Metric | Purpose |
|---|---|
| `pagerank` | Importance/influence score |
| `betweenness` | Bridge potential between clusters |
| `degree_in` | How many items link TO this one |
| `degree_out` | How many items this links TO |
| `cluster_id` | Community membership |

**Why**: Pre-computed metrics enable fast `rank_by=graph` sorting and informed analysis without re-running expensive graph algorithms.

## Implications for Workflow

1. **Capture everything during the session** — enrichment only processes items created in the current session
2. **Use consistent tags and topics** — they directly influence reweave scoring
3. **Don't worry about orphans** — the sweep catches them
4. **Review integrity warnings** — they appear in the session close response
5. **Graph metrics are fresh after close** — best time to run analysis
