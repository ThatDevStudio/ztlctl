# Garden Audit Reference

Reference for the MCP resources and tools used in the `ztl:garden-health` audit
workflow. Use this when interpreting tool output fields or choosing remediation options.

## ztlctl://garden/backlog resource

Returns the vault's maintenance backlog candidates:

- **stale_seeds**: notes with `maturity=seed`, age > 7 days, no body updates. Each
  entry includes `content_id`, `title`, `age_days`, and `last_modified`.
- **orphan_notes**: notes with 0 outgoing links and `status=draft`. Each entry
  includes `content_id`, `title`, `link_count` (always 0), and `created_at`.

## ztlctl://review/dashboard resource

Returns the external review workbench snapshot:

- **pending_reviews**: count and list of `captured` references awaiting annotation.
- **external_sources**: sources ingested via `ingest_source` still in `captured` status.
- **review_age**: age of oldest pending item in days. High age = external knowledge
  sitting unlinked.

## vault_review() output

`vault_review()` returns an aggregate snapshot of the vault:

- **total_notes**: count of non-archived notes across all content types.
- **stale_count**: notes with `maturity=seed`, age > 7 days.
- **orphan_count**: notes with 0 outgoing links and `status=draft`.
- **maturity_distribution**: dict with keys `seed`, `budding`, `evergreen`.
- **content_type_counts**: dict with keys `note`, `reference`, `task`.

A healthy vault has more `evergreen` than `seed` in `maturity_distribution`.

## graph_gaps() output

`graph_gaps(top=10)` returns structurally isolated clusters with no inter-cluster
edges (knowledge islands):

- Each entry: `cluster_id`, `node_count`, `note_titles` (top 3), `gap_score`.
- **gap_score**: higher = more isolated. Large clusters with high gap_score are
  significant knowledge domains that need a bridge note to integrate them.

## graph_bridges() output

`graph_bridges(top=10)` returns high-value bridge nodes whose removal would
disconnect clusters:

- Each entry: `content_id`, `title`, `bridge_score`, `connects_clusters` (count).
- **bridge_score**: higher = more critical. Score > 0.8 means loss of this note
  would fragment the graph. Add redundant links to reduce single-point dependency.

## Remediation options

**Connect orphans** — `reweave(content_id="<id>")`: reweave uses 4-signal scoring
to find link candidates. Review `reweave_suggestions` before writing links.

**Promote stale seeds** — `update_content(content_id="<id>", changes={"maturity": "budding"})`:
signals a seed idea is ready to connect. Add a sentence of context before promoting.

**Document gaps** — `create_note(title="<bridging topic>", tags=["<domain>"])`:
a bridge note with wikilinks into both isolated clusters reduces gap_score.
