# Enrichment Pipeline Report

When `session_close` succeeds, ztlctl runs a 4-stage enrichment pipeline against all content created in the session. The result is returned in the `session_close` response.

## Pipeline Stages

**Stage 1: Cross-session reweave** — Reweaves all notes and references created in the session. Uses 4-signal scoring (BM25 lexical, Jaccard tag overlap, graph proximity, topic match) to discover connections to existing vault content. Session-linked items get priority scoring.

**Stage 2: Orphan sweep** — Finds notes with 0 outgoing links and attempts to connect them to related content via reweave. A note that enters the session as an orphan may exit connected.

**Stage 3: Integrity check** — Scans for structural problems: broken wikilinks (referenced notes that no longer exist), orphan edges (graph edges pointing to deleted nodes), missing files (markdown files without DB records). Reports `integrity_issues` count.

**Stage 4: Graph materialization** — Persists computed graph metrics to the database: PageRank scores, betweenness centrality, cluster IDs. These power the graph analysis tools (`graph_rank`, `graph_bridges`, `graph_themes`).

## Interpreting the Report

| Field | What it means |
|-------|--------------|
| `reweave_count > 0` | Notes were successfully linked to related existing content — the session added to the knowledge graph |
| `reweave_count = 0` | No strong connections found — content may be on a new topic, or tags/wikilinks are missing |
| `orphan_count > 0` | Previously isolated notes were connected — orphan sweep improved vault connectivity |
| `integrity_issues > 0` | Structural problems found — run `ztlctl check check` for the full report with remediation hints |
| `integrity_issues = 0` | Vault structure is clean after this session |

## When `integrity_issues > 0`

Surface this warning to the user:

> "Found [N] integrity issues during enrichment. Consider running `ztlctl check check` for details."

Do not attempt automated remediation within this skill — integrity repair is a separate workflow. The check service has its own repair and rebuild capabilities.
