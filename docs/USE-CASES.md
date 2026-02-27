# Use Cases

> 76 business use cases for ztlctl Business Acceptance Testing (BAT).
> Each use case maps to a service method, CLI command, or MCP tool with key behaviors and invariants.

---

## Category 1: Vault Initialization & Setup

### UC-01 — Initialize Vault (Interactive)

| Field | Value |
|-------|-------|
| **Service** | `InitService.init_vault()` |
| **CLI** | `ztlctl init [path]` |
| **Key Behavior** | Prompt-driven setup: name, client (obsidian/vanilla), tone (research-partner/assistant/minimal), topics. Creates vault structure, generates `ztlctl.toml`, initializes SQLite DB + FTS5, renders `self/identity.md` and `self/methodology.md` via Jinja2, optionally creates `.obsidian/` client artifacts. |
| **Preconditions** | No `ztlctl.toml` exists at target path. `--no-interact` not set. |
| **Outputs** | `ServiceResult(ok=True, op="init_vault", data={vault_path, name, client, tone, topics, files_created})` |
| **Error Codes** | `VAULT_EXISTS` — vault already initialized at path |
| **Invariants** | Single write path. Files are truth. |

### UC-02 — Initialize Vault (Non-Interactive)

| Field | Value |
|-------|-------|
| **Service** | `InitService.init_vault()` |
| **CLI** | `ztlctl init --name "vault" --client obsidian --tone research-partner --topics "math,cs" --no-workflow` |
| **Key Behavior** | CLI flags supply all config; no prompts fired. Same pipeline as UC-01 but all parameters explicit. `--no-workflow` skips workflow-answers.yml creation. |
| **Preconditions** | No existing vault. `--no-interact` or all required flags supplied. |
| **Outputs** | Same as UC-01 |
| **Error Codes** | `VAULT_EXISTS` |
| **Invariants** | Same as UC-01 |

### UC-03 — Regenerate Agent Self-Documents

| Field | Value |
|-------|-------|
| **Service** | `InitService.regenerate_self()` / `InitService.check_staleness()` |
| **CLI** | `ztlctl agent regenerate` |
| **Key Behavior** | Re-renders `self/identity.md` and `self/methodology.md` from current `ztlctl.toml` config. Staleness detection compares rendered output to existing files — skips if unchanged. Supports per-vault Jinja2 template overrides from `.ztlctl/templates/`. |
| **Preconditions** | Vault exists with valid `ztlctl.toml`. |
| **Outputs** | `ServiceResult(ok=True, op="regenerate_self", data={files_updated, stale})` |
| **Error Codes** | `NO_CONFIG` — no `ztlctl.toml` found |

### UC-04 — Configure Vault Settings

| Field | Value |
|-------|-------|
| **Service** | `ZtlSettings` (Pydantic BaseSettings) |
| **CLI** | Global flags: `--json`, `-q`, `-v`, `--log-json`, `--no-interact`, `--no-reweave`, `-c`, `--sync` |
| **Key Behavior** | 4-tier priority: CLI flags > env vars (`ZTLCTL_*`) > TOML file (`ztlctl.toml` via walk-up discovery) > code defaults. Frozen Pydantic models enforce type safety. Sparse TOML — only user overrides stored. |
| **Preconditions** | None (defaults always available). |
| **Outputs** | `ZtlSettings` instance on `AppContext` |
| **Error Codes** | N/A (invalid config raises Pydantic validation error) |

### UC-05 — Template Overrides

| Field | Value |
|-------|-------|
| **Service** | `build_template_environment()` |
| **CLI** | N/A (affects `init`, `agent regenerate`, `create` implicitly) |
| **Key Behavior** | Custom Jinja2 templates in `.ztlctl/templates/` override packaged defaults. `ChoiceLoader` tries user overrides first (namespaced: `.ztlctl/templates/content/`, flat: `.ztlctl/templates/`), then packaged templates. Applies to both content templates and self-document templates. |
| **Preconditions** | Vault exists. User has placed `.j2` files in `.ztlctl/templates/`. |
| **Outputs** | Rendered content uses override template |

---

## Category 2: Content Creation

### UC-06 — Create Plain Note

| Field | Value |
|-------|-------|
| **Service** | `CreateService.create_note(title, tags=, topic=, session=, maturity=, aliases=)` |
| **CLI** | `ztlctl create note "Title" [--tags t1,t2] [--topic math] [--session LOG-0001]` |
| **Key Behavior** | 6-stage pipeline: VALIDATE → GENERATE → PERSIST → INDEX → EVENT → RESPOND. Hash ID (`ztl_` + 8 hex from SHA-256 of normalized title). Initial status=`draft` (0 links). Jinja2 body via `note.md.j2`. FTS5 index (title + body). Tag index. Post-create event dispatch. |
| **Preconditions** | Vault initialized. No ID collision. |
| **Outputs** | `ServiceResult(ok=True, op="create_note", data={id, path, title, type:"note"})` |
| **Error Codes** | `ID_COLLISION`, `VALIDATION_FAILED`, `UNKNOWN_TYPE` |
| **Invariants** | IDs are permanent. Single write path. |

### UC-07 — Create Knowledge Note

| Field | Value |
|-------|-------|
| **Service** | `CreateService.create_note(title, subtype="knowledge")` |
| **CLI** | `ztlctl create note "Title" --subtype knowledge` |
| **Key Behavior** | Same pipeline as UC-06. Uses `knowledge.md.j2` template. Advisory warning if `key_points` missing (non-blocking). `KnowledgeModel` registered in `CONTENT_REGISTRY` as `"knowledge"`. |
| **Preconditions** | Same as UC-06 |
| **Outputs** | Same shape as UC-06 with `subtype: "knowledge"` in frontmatter |
| **Error Codes** | Same as UC-06 |
| **Warnings** | `key_points` missing (advisory) |

### UC-08 — Create Decision Note

| Field | Value |
|-------|-------|
| **Service** | `CreateService.create_note(title, subtype="decision")` |
| **CLI** | `ztlctl create note "Title" --subtype decision` |
| **Key Behavior** | Strict validation: initial status must be `proposed` (enforced). Required body sections: Context, Choice, Rationale, Alternatives, Consequences. Uses `decision.md.j2` template. `DecisionModel` registered as `"decision"`. Immutability applies after `accepted` (see UC-29). |
| **Preconditions** | Same as UC-06 |
| **Outputs** | Same shape with `subtype: "decision"`, `status: "proposed"` |
| **Error Codes** | `VALIDATION_FAILED` — missing required sections or invalid initial status |

### UC-09 — Create Article Reference

| Field | Value |
|-------|-------|
| **Service** | `CreateService.create_reference(title, subtype="article", url=)` |
| **CLI** | `ztlctl create reference "Title" --subtype article [--url https://...]` |
| **Key Behavior** | Hash ID (`ref_` + 8 hex). Initial status=`captured`. Optional URL field. Uses `reference.md.j2` template. FTS5 + tag indexing. Post-create event dispatch. |
| **Preconditions** | Vault initialized. No ID collision. |
| **Outputs** | `ServiceResult(ok=True, op="create_reference", data={id, path, title, type:"reference"})` |
| **Error Codes** | `ID_COLLISION`, `VALIDATION_FAILED` |

### UC-10 — Create Tool Reference

| Field | Value |
|-------|-------|
| **Service** | `CreateService.create_reference(title, subtype="tool")` |
| **CLI** | `ztlctl create reference "Title" --subtype tool` |
| **Key Behavior** | Same pipeline as UC-09. `subtype: "tool"` — classification only (no extra required fields). |
| **Preconditions** | Same as UC-09 |
| **Outputs** | Same shape with `subtype: "tool"` |

### UC-11 — Create Spec Reference

| Field | Value |
|-------|-------|
| **Service** | `CreateService.create_reference(title, subtype="spec")` |
| **CLI** | `ztlctl create reference "Title" --subtype spec` |
| **Key Behavior** | Same pipeline as UC-09. `subtype: "spec"` — classification only. |
| **Preconditions** | Same as UC-09 |
| **Outputs** | Same shape with `subtype: "spec"` |

### UC-12 — Create Task

| Field | Value |
|-------|-------|
| **Service** | `CreateService.create_task(title, priority="medium", impact="medium", effort="medium")` |
| **CLI** | `ztlctl create task "Title" [--priority high] [--impact high] [--effort low]` |
| **Key Behavior** | Sequential ID (`TASK-NNNN` from atomic counter). Initial status=`inbox`. Priority/impact/effort matrix for work-queue scoring: `score = priority*2 + impact*1.5 + (4 - effort)`. Uses `task.md.j2` template. |
| **Preconditions** | Vault initialized. |
| **Outputs** | `ServiceResult(ok=True, op="create_task", data={id:"TASK-NNNN", path, title, type:"task"})` |
| **Error Codes** | `VALIDATION_FAILED` |

### UC-13 — Batch Content Creation

| Field | Value |
|-------|-------|
| **Service** | `CreateService.create_batch(items, partial=False)` |
| **CLI** | `ztlctl create batch <file.json> [--partial]` |
| **Key Behavior** | JSON array input. Two modes: **all-or-nothing** (default) — single failure aborts entire batch; **partial** (`--partial`) — continues past failures, reports errors. Returns `data={created: [...], errors: [...]}`. |
| **Preconditions** | Valid JSON file with top-level array. |
| **Outputs** | `ServiceResult(ok=True/False, op="create_batch", data={created, errors})` |
| **Error Codes** | `BATCH_FAILED` (all-or-nothing failure), `BATCH_PARTIAL` (partial with errors), `invalid_file` (unreadable), `invalid_format` (not array) |

### UC-14 — Create Garden Seed

| Field | Value |
|-------|-------|
| **Service** | `CreateService.create_note(title, maturity="seed")` |
| **CLI** | `ztlctl create note "Title" --maturity seed` |
| **Key Behavior** | Note with `maturity=seed` — entry to garden lifecycle. Body is protected from auto-modification (invariant: body text is human domain). Frontmatter links still enriched by reweave. Garden maturity is advisory and human-driven (seed → budding → evergreen). |
| **Preconditions** | Same as UC-06 |
| **Outputs** | Same shape with `maturity: "seed"` in frontmatter |
| **Invariants** | Body text is human domain when maturity is set. |

### UC-15 — Post-Create Reweave

| Field | Value |
|-------|-------|
| **Service** | `CreateService` (inline) + `ReweavePlugin` (event bus) |
| **CLI** | Automatic after `create note`/`create reference` (unless `--no-reweave`) |
| **Key Behavior** | After note/reference creation, automatic link suggestions via 4-signal scoring. Inline in CreateService for notes/references (gated by `settings.no_reweave`). Tasks excluded. ReweavePlugin also fires via event bus `post_create` hook. Decision notes skipped by ReweavePlugin (strict lifecycle). |
| **Preconditions** | `reweave.enabled=true` (default). `--no-reweave` not set. At least one other node in vault for candidates. |
| **Outputs** | Reweave suggestions in `warnings` or silently applied links |

---

## Category 3: Search & Retrieval

### UC-16 — Search by Relevance (BM25)

| Field | Value |
|-------|-------|
| **Service** | `QueryService.search(query, rank_by="relevance")` |
| **CLI** | `ztlctl query search "term" [--rank-by relevance]` |
| **Key Behavior** | FTS5 native BM25 ranking. Searches title and body. Results scored by pure BM25 rank. Filters: `--type`, `--tag`, `--space`. Default limit=20. |
| **Preconditions** | Vault with FTS5-indexed content. Non-empty query. |
| **Outputs** | `ServiceResult(ok=True, op="search", data={query, count, items:[{id, title, type, score}]})` |
| **Error Codes** | `EMPTY_QUERY` |

### UC-17 — Search by Recency

| Field | Value |
|-------|-------|
| **Service** | `QueryService.search(query, rank_by="recency")` |
| **CLI** | `ztlctl query search "term" --rank-by recency` |
| **Key Behavior** | BM25 × exponential time decay. Half-life configurable via `search.half_life_days`. Recently modified items boosted. |
| **Preconditions** | Same as UC-16 |
| **Outputs** | Same shape, different score ordering |

### UC-18 — Search by Graph Rank

| Field | Value |
|-------|-------|
| **Service** | `QueryService.search(query, rank_by="graph")` |
| **CLI** | `ztlctl query search "term" --rank-by graph` |
| **Key Behavior** | BM25 × PageRank boost. Warns if PageRank is all zeros (not yet materialized — run `graph materialize` first). |
| **Preconditions** | Same as UC-16. Graph metrics materialized for meaningful ranking. |
| **Outputs** | Same shape. Warning if PageRank uninitialized. |
| **Warnings** | "PageRank scores are all zero" if `graph materialize` not run |

### UC-19 — Semantic Search

| Field | Value |
|-------|-------|
| **Service** | `QueryService.search(query, rank_by="semantic")` via `VectorService` |
| **CLI** | `ztlctl query search "term" --rank-by semantic` |
| **Key Behavior** | Cosine similarity via embeddings (sqlite-vec + sentence-transformers). Vector-only search (no FTS5). Graceful degradation: falls back to BM25 if `search.semantic_enabled=false` or dependencies unavailable. |
| **Preconditions** | `search.semantic_enabled=true`. `ztlctl[semantic]` extra installed. Embeddings indexed. |
| **Outputs** | Same shape, cosine-based scores |
| **Error Codes** | `SEMANTIC_UNAVAILABLE` |

### UC-20 — Hybrid Search

| Field | Value |
|-------|-------|
| **Service** | `QueryService.search(query, rank_by="hybrid")` |
| **CLI** | `ztlctl query search "term" --rank-by hybrid` |
| **Key Behavior** | Min-max normalized BM25 + cosine blend. Weight controlled by `search.semantic_weight` config. Falls back to BM25-only if semantic unavailable. |
| **Preconditions** | Same as UC-19 |
| **Outputs** | Same shape, blended scores |

### UC-21 — Retrieve Single Item (Get)

| Field | Value |
|-------|-------|
| **Service** | `QueryService.get(content_id)` |
| **CLI** | `ztlctl query get <id>` |
| **Key Behavior** | Full document retrieval: node metadata, tags, body text, outgoing links (`out_links`), incoming backlinks (`in_links`). Body read from filesystem (files are truth). |
| **Preconditions** | Valid content ID. |
| **Outputs** | `ServiceResult(ok=True, op="get", data={id, title, type, status, tags, body, out_links, in_links, ...})` |
| **Error Codes** | `NOT_FOUND` |

### UC-22 — List with Filters

| Field | Value |
|-------|-------|
| **Service** | `QueryService.list_items(content_type=, status=, tag=, topic=, subtype=, maturity=, space=, since=, include_archived=)` |
| **CLI** | `ztlctl query list [--type note] [--status draft] [--tag math] [--topic algebra] [--sort recency] [--limit 50]` |
| **Key Behavior** | Composable filter grammar — all filters ANDed. Sort modes: `recency`, `title`, `type`, `priority`. Archived excluded by default. `limit=0` returns 0 items (use large limit for counting). |
| **Preconditions** | Vault initialized. |
| **Outputs** | `ServiceResult(ok=True, op="list_items", data={count, items:[{id, title, type, status}]})` |

### UC-23 — Work Queue

| Field | Value |
|-------|-------|
| **Service** | `QueryService.work_queue(space=)` |
| **CLI** | `ztlctl query work-queue` |
| **Key Behavior** | Priority-scored tasks with statuses `inbox`, `active`, `blocked` only. Score formula: `priority*2 + impact*1.5 + (4 - effort)`. Highest score = quick wins (high priority, high impact, low effort). Takes no parameters beyond optional space filter. |
| **Preconditions** | Tasks exist in vault. |
| **Outputs** | `ServiceResult(ok=True, op="work_queue", data={count, items:[{id, title, priority, impact, effort, score}]})` |

### UC-24 — Decision Support

| Field | Value |
|-------|-------|
| **Service** | `QueryService.decision_support(topic=, space=)` |
| **CLI** | `ztlctl query decision-support [--topic math]` |
| **Key Behavior** | Partitioned aggregation: `decisions` (proposed + accepted), `notes` (related), `references` (supporting evidence). Grouped by topic. Provides holistic view for decision-making. |
| **Preconditions** | Content exists in vault. |
| **Outputs** | `ServiceResult(ok=True, op="decision_support", data={topic, decisions, notes, references, counts})` |

---

## Category 4: Content Updates & Lifecycle

### UC-25 — Update Content Metadata

| Field | Value |
|-------|-------|
| **Service** | `UpdateService.update(content_id, changes={title:, tags:, status:, maturity:, topic:, body:})` |
| **CLI** | `ztlctl update <id> [--title X] [--tags t1] [--status X] [--topic X] [--body X] [--maturity X]` |
| **Key Behavior** | 5-stage pipeline: VALIDATE → APPLY → PROPAGATE → INDEX → RESPOND. Immutable fields (`id`, `type`, `created`) warned if changed. Frontmatter always updated. Body updated only if `maturity` is not set (garden protection). Re-indexes FTS5, tags, edges after changes. |
| **Preconditions** | Content exists. Valid changes. |
| **Outputs** | `ServiceResult(ok=True, op="update", data={id, path, fields_changed, status})` |
| **Error Codes** | `NOT_FOUND`, `UNKNOWN_TYPE`, `VALIDATION_FAILED`, `INVALID_TRANSITION`, `no_changes` |

### UC-26 — Note Status Transitions

| Field | Value |
|-------|-------|
| **Service** | `UpdateService.update()` — status recomputed |
| **CLI** | Implicit (never set directly) |
| **Key Behavior** | Note status is **machine-computed** from outgoing link count, never set by CLI. Thresholds: 0 links → `draft`, 1+ → `linked`, 3+ → `connected`. `compute_note_status()` called after every update. |
| **Transitions** | `draft → linked → connected` (terminal) |
| **Invariants** | Status computed, never set directly. |

### UC-27 — Task Status Transitions

| Field | Value |
|-------|-------|
| **Service** | `UpdateService.update(content_id, changes={"status": new_status})` |
| **CLI** | `ztlctl update TASK-0001 --status active` |
| **Key Behavior** | User-driven transitions validated against `TASK_TRANSITIONS`. Multi-branch state machine. |
| **Transitions** | `inbox → active/dropped`, `active → blocked/done/dropped`, `blocked → active/dropped`, `done → ∅`, `dropped → ∅` |
| **Error Codes** | `INVALID_TRANSITION` |

### UC-28 — Reference Status Transitions

| Field | Value |
|-------|-------|
| **Service** | `UpdateService.update(content_id, changes={"status": "annotated"})` |
| **CLI** | `ztlctl update ref_abc12345 --status annotated` |
| **Key Behavior** | Machine-computed from field completeness. Simple linear lifecycle. |
| **Transitions** | `captured → annotated` (terminal) |
| **Error Codes** | `INVALID_TRANSITION` |

### UC-29 — Decision Lifecycle

| Field | Value |
|-------|-------|
| **Service** | `UpdateService.update()` with `DecisionModel` validation |
| **CLI** | `ztlctl update ztl_abc12345 --status accepted` |
| **Key Behavior** | Strict lifecycle: `proposed → accepted → superseded`. After `accepted`, body is **immutable** — only `status`, `superseded_by`, `modified`, `tags`, `aliases`, `topic` can change. Violation returns `VALIDATION_FAILED`. |
| **Transitions** | `proposed → accepted → superseded` (terminal) |
| **Error Codes** | `VALIDATION_FAILED` — immutable field modification after acceptance |
| **Invariants** | Decisions are immutable after acceptance. |

### UC-30 — Archive Content

| Field | Value |
|-------|-------|
| **Service** | `UpdateService.archive(content_id)` |
| **CLI** | `ztlctl archive <id>` |
| **Key Behavior** | Soft delete: sets `archived=true` in file and DB. Edges preserved. Excluded from default queries (use `--include-archived` to see). Dispatches `post_close` event. |
| **Preconditions** | Content exists. |
| **Outputs** | `ServiceResult(ok=True, op="archive", data={id, path})` |
| **Error Codes** | `NOT_FOUND` |

### UC-31 — Supersede Decision

| Field | Value |
|-------|-------|
| **Service** | `UpdateService.supersede(old_id, new_id)` |
| **CLI** | `ztlctl supersede <old_id> <new_id>` |
| **Key Behavior** | Convenience wrapper: `update(old_id, changes={"status": "superseded", "superseded_by": new_id})`. Old decision gets `superseded_by` pointer. New decision should have `supersedes` pointer. Both must be decision-subtype notes. |
| **Preconditions** | Old decision in `accepted` status. New decision exists. |
| **Error Codes** | `INVALID_TRANSITION`, `NOT_FOUND` |

### UC-32 — Garden Maturity Progression

| Field | Value |
|-------|-------|
| **Service** | `UpdateService.update(content_id, changes={"maturity": new_level})` |
| **CLI** | `ztlctl update <id> --maturity budding` |
| **Key Behavior** | Advisory human-driven progression: `seed → budding → evergreen`. Setting maturity activates garden body protection — body changes rejected (warned, not error). Frontmatter links still enriched. |
| **Transitions** | `seed → budding → evergreen` (terminal) |
| **Invariants** | Body text is human domain when maturity is set. |

---

## Category 5: Graph Operations

### UC-33 — Related Content (Spreading Activation)

| Field | Value |
|-------|-------|
| **Service** | `GraphService.related(content_id, depth=2, top=20)` |
| **CLI** | `ztlctl graph related <id> [--depth 3] [--top 10]` |
| **Key Behavior** | BFS with 0.5 decay per hop on undirected view. Depth 1–5. Returns scored results sorted by activation score. |
| **Preconditions** | Node exists in graph. |
| **Outputs** | `ServiceResult(ok=True, op="related", data={source_id, count, items:[{id, title, type, score, depth}]})` |
| **Error Codes** | `NOT_FOUND` — node not in graph |

### UC-34 — Theme/Community Detection

| Field | Value |
|-------|-------|
| **Service** | `GraphService.themes()` |
| **CLI** | `ztlctl graph themes` |
| **Key Behavior** | Leiden algorithm on undirected view. Falls back to Louvain with warning if Leiden unavailable. Returns community memberships grouped by community_id. |
| **Preconditions** | Graph has edges (otherwise single communities). |
| **Outputs** | `ServiceResult(ok=True, op="themes", data={count, communities:[{community_id, size, members}]})` |
| **Warnings** | "Leiden unavailable, using Louvain fallback" |

### UC-35 — PageRank Ranking

| Field | Value |
|-------|-------|
| **Service** | `GraphService.rank(top=20)` |
| **CLI** | `ztlctl graph rank [--top 10]` |
| **Key Behavior** | NetworkX PageRank on directed graph. Top-N by importance score. |
| **Preconditions** | Graph has edges. |
| **Outputs** | `ServiceResult(ok=True, op="rank", data={count, items:[{id, title, type, score}]})` |

### UC-36 — Path Finding

| Field | Value |
|-------|-------|
| **Service** | `GraphService.path(source_id, target_id)` |
| **CLI** | `ztlctl graph path <source> <target>` |
| **Key Behavior** | Shortest path on undirected view. Returns step-by-step chain with hop count. |
| **Preconditions** | Both nodes exist in graph. Path exists. |
| **Outputs** | `ServiceResult(ok=True, op="path", data={source_id, target_id, length, steps:[{id, title, type}]})` |
| **Error Codes** | `NOT_FOUND` — node not in graph; `NO_PATH` — no path between nodes |

### UC-37 — Structural Gaps

| Field | Value |
|-------|-------|
| **Service** | `GraphService.gaps(top=20)` |
| **CLI** | `ztlctl graph gaps [--top 10]` |
| **Key Behavior** | Constraint centrality on undirected view. High constraint = tightly embedded (potential knowledge silos). Filters NaN/Inf (isolated/degree-1 nodes). |
| **Preconditions** | Graph has edges. |
| **Outputs** | `ServiceResult(ok=True, op="gaps", data={count, items:[{id, title, type, constraint}]})` |

### UC-38 — Bridge Detection

| Field | Value |
|-------|-------|
| **Service** | `GraphService.bridges(top=20)` |
| **CLI** | `ztlctl graph bridges [--top 10]` |
| **Key Behavior** | Betweenness centrality on undirected view. High betweenness = cluster connectors (bridge nodes linking different communities). |
| **Preconditions** | Graph has edges. |
| **Outputs** | `ServiceResult(ok=True, op="bridges", data={count, items:[{id, title, type, centrality}]})` |

### UC-39 — Unlink Nodes

| Field | Value |
|-------|-------|
| **Service** | `GraphService.unlink(source_id, target_id, both=False)` |
| **CLI** | `ztlctl graph unlink <source> <target> [--both]` |
| **Key Behavior** | Removes edge(s) from source to target. `--both` removes bidirectional. Updates DB edges, frontmatter links, and body wikilinks. Garden note protection: body untouched if maturity set (warns). Re-indexes FTS5 if body changed. |
| **Preconditions** | Both nodes exist. Link exists. |
| **Outputs** | `ServiceResult(ok=True, op="unlink", data={source_id, target_id, both, edges_removed})` |
| **Error Codes** | `NOT_FOUND` — node not found; `NO_LINK` — no link found |
| **Invariants** | Body text is human domain when maturity is set. |

### UC-40 — Materialize Metrics

| Field | Value |
|-------|-------|
| **Service** | `GraphService.materialize_metrics()` |
| **CLI** | `ztlctl graph materialize` |
| **Key Behavior** | Computes and persists to DB: PageRank, degree_in, degree_out, betweenness centrality, cluster_id. Flags bidirectional edges. Required before `--rank-by graph` search produces meaningful results. |
| **Preconditions** | Vault has content. |
| **Outputs** | `ServiceResult(ok=True, op="materialize_metrics", data={nodes_updated})` |

---

## Category 6: Reweave (Link Discovery)

### UC-41 — Reweave — Discover Links

| Field | Value |
|-------|-------|
| **Service** | `ReweaveService.reweave(content_id=, dry_run=False)` |
| **CLI** | `ztlctl reweave [--id <id>]` |
| **Key Behavior** | 4-signal scoring: (1) Lexical/BM25 (weight 0.35), (2) Tag overlap/Jaccard (0.25), (3) Graph proximity/inverse shortest path (0.25), (4) Topic co-occurrence/binary (0.15). Composite score ≥ `min_score_threshold` (default 0.6). Max links per note enforced. Candidates exclude self, archived, already-linked. If no `content_id`, targets most recently modified non-archived node. |
| **Preconditions** | `reweave.enabled=true`. Vault has ≥2 nodes. |
| **Outputs** | `ServiceResult(ok=True, op="reweave", data={target_id, connected:[{id, score}], count})` |
| **Error Codes** | `NOT_FOUND` |

### UC-42 — Reweave — Dry Run

| Field | Value |
|-------|-------|
| **Service** | `ReweaveService.reweave(content_id=, dry_run=True)` |
| **CLI** | `ztlctl reweave --dry-run [--id <id>]` |
| **Key Behavior** | Same scoring as UC-41 but no writes. Returns suggestions without connecting. Preview mode for user review. |
| **Preconditions** | Same as UC-41 |
| **Outputs** | `ServiceResult(ok=True, op="reweave", data={target_id, suggestions:[{id, score}], count})` |

### UC-43 — Reweave — Prune Stale Links

| Field | Value |
|-------|-------|
| **Service** | `ReweaveService.prune(content_id=, dry_run=False)` |
| **CLI** | `ztlctl reweave --prune [--id <id>]` |
| **Key Behavior** | Re-scores existing links. Links below `min_score_threshold` are removed. Audit trail logged in `reweave_log`. Dry-run available via `--dry-run`. |
| **Preconditions** | Target has existing links. |
| **Outputs** | `ServiceResult(ok=True, op="prune", data={target_id, pruned/stale:[{id, score}], count})` |
| **Error Codes** | `NOT_FOUND` |

### UC-44 — Reweave — Undo

| Field | Value |
|-------|-------|
| **Service** | `ReweaveService.undo(reweave_id=)` |
| **CLI** | `ztlctl reweave --undo [--undo-id N]` |
| **Key Behavior** | Reverses reweave operation via `reweave_log` audit trail. If `reweave_id=None`, undoes latest batch (same timestamp). Marks log entries as `undone=true`. |
| **Preconditions** | Reweave history exists. |
| **Outputs** | `ServiceResult(ok=True, op="undo", data={undone:[{id, source, target, action}], count})` |
| **Error Codes** | `NOT_FOUND` (specific reweave_id), `NO_HISTORY` (no operations to undo) |

---

## Category 7: Session Management

### UC-45 — Start Session

| Field | Value |
|-------|-------|
| **Service** | `SessionService.start(topic)` |
| **CLI** | `ztlctl agent session start <topic>` |
| **Key Behavior** | Single active session constraint — fails if another session open. Creates `LOG-NNNN` sequential ID. Creates JSONL file with initial entry. Inserts nodes row (type=log, status=open). Dispatches `post_session_start` event. |
| **Preconditions** | No active session. |
| **Outputs** | `ServiceResult(ok=True, op="session_start", data={id, topic, path, status:"open"})` |
| **Error Codes** | `ACTIVE_SESSION_EXISTS` |

### UC-46 — Log Session Entries

| Field | Value |
|-------|-------|
| **Service** | `SessionService.log_entry(message, pin=, cost=, detail=, entry_type=, subtype=, references=, metadata=)` |
| **CLI** | `ztlctl agent session log "message" [--pin] [--cost 100]` |
| **Key Behavior** | Appends entry to active session JSONL file and `session_logs` DB table. Supports: pinning (for extraction), cost tracking (token consumption), references (linked content IDs), metadata (arbitrary JSON). |
| **Preconditions** | Active session exists. |
| **Outputs** | `ServiceResult(ok=True, op="log_entry", data={entry_id, session_id, timestamp})` |
| **Error Codes** | `NO_ACTIVE_SESSION` |

### UC-47 — Close Session (with Enrichment)

| Field | Value |
|-------|-------|
| **Service** | `SessionService.close(summary=)` |
| **CLI** | `ztlctl agent session close [--summary "..."]` |
| **Key Behavior** | Enrichment pipeline: (1) LOG CLOSE, (2) CROSS-SESSION REWEAVE (gated by `session.close_reweave`), (3) ORPHAN SWEEP (gated by `session.close_orphan_sweep`), (4) INTEGRITY CHECK (gated by `session.close_integrity_check`), (5) GRAPH MATERIALIZATION, (6) DRAIN EVENT WAL (sync barrier). Dispatches `post_session_close` event. |
| **Preconditions** | Active session exists. |
| **Outputs** | `ServiceResult(ok=True, op="session_close", data={session_id, status:"closed", reweave_count, orphan_count, integrity_issues})` |
| **Error Codes** | `NO_ACTIVE_SESSION` |

### UC-48 — Reopen Session

| Field | Value |
|-------|-------|
| **Service** | `SessionService.reopen(session_id)` |
| **CLI** | `ztlctl agent session reopen <LOG-NNNN>` |
| **Key Behavior** | Reopens closed session. Fails if already open or if another active session exists. Appends reopen entry to JSONL. Log status `closed → open` (unique: bidirectional). |
| **Preconditions** | Session exists and is closed. No other active session. |
| **Outputs** | `ServiceResult(ok=True, op="session_reopen", data={id, status:"open"})` |
| **Error Codes** | `NOT_FOUND`, `ALREADY_OPEN`, `ACTIVE_SESSION_EXISTS` |

### UC-49 — Agent Context Assembly

| Field | Value |
|-------|-------|
| **Service** | `SessionService.context(topic=, budget=8000)` → `ContextAssembler.assemble()` |
| **CLI** | `ztlctl agent context [--topic X] [--budget 8000]` |
| **Key Behavior** | 5-layer token-budgeted context: Layer 0 (identity+methodology, always), Layer 1 (operational state, always), Layer 2 (topic-scoped, budget-dependent), Layer 3 (graph-adjacent, budget-dependent), Layer 4 (background signals, budget-dependent). Pressure tracking: normal (>15% remaining), caution (0-15%), exceeded (<0%). |
| **Preconditions** | Active session. |
| **Outputs** | `ServiceResult(ok=True, op="context", data={total_tokens, budget, remaining, pressure, layers:{...}})` |
| **Error Codes** | `NO_ACTIVE_SESSION` |

### UC-50 — Agent Brief/Orientation

| Field | Value |
|-------|-------|
| **Service** | `SessionService.brief()` → `ContextAssembler.build_brief()` |
| **CLI** | `ztlctl agent brief` |
| **Key Behavior** | Quick orientation: vault stats (node counts by type), active session info, recent activity, work queue count. No session required (returns stats even without session). |
| **Preconditions** | Vault initialized. |
| **Outputs** | `ServiceResult(ok=True, op="brief", data={session, vault_stats, recent_decisions, work_queue_count})` |

### UC-51 — Session Cost Tracking

| Field | Value |
|-------|-------|
| **Service** | `SessionService.cost(report=)` |
| **CLI** | `ztlctl agent session cost [--report <budget>]` |
| **Key Behavior** | Query mode (no `--report`): returns total cost and entry count. Report mode (`--report N`): adds budget, remaining, over_budget flag. Cost accumulated from `session_logs.cost` column. |
| **Preconditions** | Active session. |
| **Outputs** | `ServiceResult(ok=True, op="cost", data={session_id, total_cost, entry_count, [budget, remaining, over_budget]})` |
| **Error Codes** | `NO_ACTIVE_SESSION` |

---

## Category 8: Integrity & Maintenance

### UC-52 — Integrity Check

| Field | Value |
|-------|-------|
| **Service** | `CheckService.check()` |
| **CLI** | `ztlctl check` |
| **Key Behavior** | Read-only 4-category scan: (1) DB-file consistency (CAT_DB_FILE) — nodes without files, files without nodes; (2) Schema integrity (CAT_SCHEMA) — invalid IDs, missing fields, orphaned edges; (3) Graph health (CAT_GRAPH) — disconnected components, dangling references; (4) Structural validation (CAT_STRUCTURAL) — cyclic supersessions, invalid links. Each issue has severity, category, message, detail, optional `fix_action`. |
| **Preconditions** | Vault initialized. |
| **Outputs** | `ServiceResult(ok=True, op="check", data={issues, count})` |

### UC-53 — Integrity Fix (Safe)

| Field | Value |
|-------|-------|
| **Service** | `CheckService.fix(level="safe")` |
| **CLI** | `ztlctl check --fix [--level safe]` |
| **Key Behavior** | Non-destructive repairs. Creates DB backup first. Safe fixes: orphan rows, dangling edges, missing FTS entries, resync from files. Body text **never** modified. |
| **Preconditions** | Vault initialized. |
| **Outputs** | `ServiceResult(ok=True, op="fix", data={fixes, count})` |
| **Invariants** | Body text never modified by check. |

### UC-54 — Integrity Fix (Aggressive)

| Field | Value |
|-------|-------|
| **Service** | `CheckService.fix(level="aggressive")` |
| **CLI** | `ztlctl check --fix --level aggressive` |
| **Key Behavior** | Thorough reconstruction. Safe fixes plus: reindex edges, reorder frontmatter. Creates DB backup first. May remove data (orphaned edges without valid nodes). |
| **Preconditions** | Same as UC-53 |
| **Outputs** | Same shape as UC-53 |

### UC-55 — Full Rebuild from Files

| Field | Value |
|-------|-------|
| **Service** | `CheckService.rebuild()` |
| **CLI** | `ztlctl check --rebuild` |
| **Key Behavior** | Destructive rebuild. Clears nodes, edges, tags, FTS. 2-pass: (1) Insert all nodes from files (frontmatter parsing), (2) Index edges (links resolution). Materializes graph metrics after. Files are truth. |
| **Preconditions** | Vault initialized. Content files exist. |
| **Outputs** | `ServiceResult(ok=True, op="rebuild", data={nodes_indexed, edges_created, tags_found, nodes_materialized})` |
| **Invariants** | Files are truth. |

### UC-56 — Rollback to Backup

| Field | Value |
|-------|-------|
| **Service** | `CheckService.rollback()` |
| **CLI** | `ztlctl check --rollback` |
| **Key Behavior** | Restores DB from latest timestamped backup in `.ztlctl/backups/`. Backup naming: `ztlctl-YYYYMMDD-HHMMSS.db`. |
| **Preconditions** | Backup exists. |
| **Outputs** | `ServiceResult(ok=True, op="rollback", data={backup_path})` |
| **Error Codes** | `NO_BACKUPS` — no backup directory or no backup files |

### UC-57 — Database Upgrade

| Field | Value |
|-------|-------|
| **Service** | `UpgradeService.check_pending()` / `UpgradeService.apply()` |
| **CLI** | `ztlctl upgrade` |
| **Key Behavior** | Alembic migrations. `check_pending()` lists pending without applying. `apply()` pipeline: BACKUP → CHECK → MIGRATE → VALIDATE → REPORT. Pre-Alembic vault detection: tables exist but no version tracking → STAMP instead of CREATE TABLE. Validates integrity after migration. |
| **Preconditions** | Vault initialized. |
| **Outputs** | `ServiceResult(ok=True, op="upgrade_apply", data={applied_count, current, message})` |
| **Error Codes** | `CHECK_FAILED`, `BACKUP_FAILED`, `MIGRATION_FAILED`, `STAMP_FAILED` |

---

## Category 9: Export

### UC-58 — Export Markdown

| Field | Value |
|-------|-------|
| **Service** | `ExportService.export_markdown(output_dir)` |
| **CLI** | `ztlctl export markdown --output <dir>` |
| **Key Behavior** | Copies all content files to output directory preserving relative paths (`notes/`, `ops/`). |
| **Preconditions** | Vault has content. Output directory writable. |
| **Outputs** | `ServiceResult(ok=True, op="export_markdown", data={output_dir, file_count})` |

### UC-59 — Export Indexes

| Field | Value |
|-------|-------|
| **Service** | `ExportService.export_indexes(output_dir)` |
| **CLI** | `ztlctl export indexes --output <dir>` |
| **Key Behavior** | Generates index files: `index.md` (master with counts), `by-type/{type}.md` (per-type listings), `by-topic/{topic}.md` (per-topic listings). |
| **Preconditions** | Vault has content. |
| **Outputs** | `ServiceResult(ok=True, op="export_indexes", data={output_dir, files_created, node_count})` |

### UC-60 — Export Graph (DOT)

| Field | Value |
|-------|-------|
| **Service** | `ExportService.export_graph(fmt="dot")` |
| **CLI** | `ztlctl export graph --format dot` |
| **Key Behavior** | Graphviz DOT language output. Nodes labeled by title and type. Edges show relationship types. |
| **Preconditions** | Vault has content. |
| **Outputs** | `ServiceResult(ok=True, op="export_graph", data={format:"dot", content, node_count, edge_count})` |
| **Error Codes** | `INVALID_FORMAT` — unknown format |

### UC-61 — Export Graph (JSON)

| Field | Value |
|-------|-------|
| **Service** | `ExportService.export_graph(fmt="json")` |
| **CLI** | `ztlctl export graph --format json` |
| **Key Behavior** | D3/vis.js compatible JSON: `{"nodes": [...], "links": [...]}`. |
| **Preconditions** | Same as UC-60 |
| **Outputs** | Same shape with `format: "json"` |

---

## Category 10: Extensions & Integrations

### UC-62 — MCP — Creation Tools

| Field | Value |
|-------|-------|
| **Service** | MCP tools: `create_note`, `create_reference`, `create_task`, `create_log` |
| **MCP** | `ztlctl serve` → FastMCP |
| **Key Behavior** | Each tool delegates to corresponding service method via `_impl()` pattern. `create_note(title, subtype=, tags=, topic=)`, `create_reference(title, url=, tags=, topic=)`, `create_task(title, priority=, impact=, effort=, tags=)`, `create_log(topic)` (delegates to `SessionService.start`). |
| **Preconditions** | MCP server running. Vault initialized. |
| **Outputs** | ServiceResult JSON via MCP response |

### UC-63 — MCP — Query Tools

| Field | Value |
|-------|-------|
| **Service** | MCP tools: `search`, `get_document`, `get_related`, `agent_context` |
| **MCP** | `ztlctl serve` |
| **Key Behavior** | `search(query, content_type=, tag=, space=, rank_by=, limit=)`, `get_document(content_id)`, `get_related(content_id, depth=, top=)`, `agent_context(query=, limit=)` — dual-mode: tries SessionService.context first, falls back to QueryService direct queries if no session. |
| **Preconditions** | MCP server running. |
| **Outputs** | ServiceResult JSON |

### UC-64 — MCP — Lifecycle Tools

| Field | Value |
|-------|-------|
| **Service** | MCP tools: `update_content`, `close_content`, `reweave`, `session_close` |
| **MCP** | `ztlctl serve` |
| **Key Behavior** | `update_content(content_id, changes)`, `close_content(content_id)` (archive), `reweave(content_id=, dry_run=)`, `session_close(summary=)`. Same validation and lifecycle rules as CLI. |

### UC-65 — MCP — Resources

| Field | Value |
|-------|-------|
| **Service** | MCP resources (6 URIs) |
| **MCP** | `ztlctl serve` |
| **Key Behavior** | `ztlctl://context` (combined identity+methodology+overview JSON), `ztlctl://self/identity` (markdown), `ztlctl://self/methodology` (markdown), `ztlctl://overview` (vault counts+recent JSON), `ztlctl://work-queue` (scored tasks JSON), `ztlctl://topics` (topic directory list JSON). |
| **Preconditions** | MCP server running. |

### UC-66 — MCP — Prompts

| Field | Value |
|-------|-------|
| **Service** | MCP prompts (4 templates) |
| **MCP** | `ztlctl serve` |
| **Key Behavior** | `research_session(topic)` — 5-step research workflow; `knowledge_capture()` — general capture workflow; `vault_orientation()` — onboarding with identity+methodology+overview; `decision_record(topic)` — structured decision documentation. |

### UC-67 — Plugin Discovery & Registration

| Field | Value |
|-------|-------|
| **Service** | `PluginManager.discover_and_load()` |
| **Key Behavior** | Two-tier discovery: (1) Entry-point plugins (`ztlctl.plugins` setuptools group) — pip-installed; (2) Local directory (`.ztlctl/plugins/*.py`) — user-created. Register/unregister via `register_plugin()`/`unregister()`. Returns loaded plugin names. `register_content_models()` extension hook merges custom subtypes into `CONTENT_REGISTRY`. |
| **Preconditions** | Vault initialized. |

### UC-68 — Plugin Lifecycle Hooks

| Field | Value |
|-------|-------|
| **Service** | `PluginManager.hook` (pluggy HookRelay) |
| **Key Behavior** | 8 lifecycle hooks + 1 extension hook: `post_create(content_type, content_id, title, path, tags)`, `post_update(content_type, content_id, fields_changed, path)`, `post_close(content_type, content_id, path, summary)`, `post_reweave(source_id, affected_ids, links_added)`, `post_session_start(session_id)`, `post_session_close(session_id, stats)`, `post_check(issues_found, issues_fixed)`, `post_init(vault_name, client, tone)`, `register_content_models()`. |
| **Invariants** | Plugin failures are warnings, never errors. |

### UC-69 — Git Plugin

| Field | Value |
|-------|-------|
| **Service** | Built-in `GitPlugin` |
| **Key Behavior** | Implements all 8 lifecycle hooks. `post_create/update/close`: git add. Batch mode (default): commits at `post_session_close`. Immediate mode (`git.batch_commits=false`): commits after each operation. `post_session_close`: commit + optional push (`git.auto_push`). `post_init`: `.gitignore` + initial commit. Silent failure on missing git — subprocess errors logged, never raise. |
| **Config** | `[git] enabled=true, batch_commits=true, auto_push=false, auto_ignore=true` |
| **Invariants** | Plugin failures are warnings. |

### UC-70 — Event Bus Dispatch

| Field | Value |
|-------|-------|
| **Service** | `EventBus` (WAL-backed) |
| **Key Behavior** | WAL-backed async dispatch via ThreadPoolExecutor. Lifecycle: pending → (completed \| failed → retry → dead_letter). Max retries configurable (default 3). Sync mode (`--sync`). `drain()` at session close: wait for futures, retry pending/failed synchronously. Dead-letter events logged, never retried. `BaseService._dispatch_event()` wraps dispatch — failures are warnings. |
| **Invariants** | Async by default. Plugin failures are warnings. |

### UC-71 — Vector/Semantic Search

| Field | Value |
|-------|-------|
| **Service** | `VectorService` |
| **CLI** | `ztlctl vector <query>` |
| **Key Behavior** | Optional dependency-gated service (sqlite-vec + sentence-transformers). `is_available()` checks sqlite-vec loadability. `index_node()` embeds content. `search_similar()` KNN queries. `reindex_all()` batch re-embeds. Graceful degradation: all methods no-op if deps unavailable. |
| **Preconditions** | `ztlctl[semantic]` extra installed. `search.semantic_enabled=true`. |
| **Error Codes** | `SEMANTIC_UNAVAILABLE` |

---

## Category 11: Cross-Cutting Concerns

### UC-72 — JSON Output Mode

| Field | Value |
|-------|-------|
| **Service** | `format_result(result, settings=OutputSettings(json_output=True))` |
| **CLI** | `ztlctl --json <any command>` |
| **Key Behavior** | `--json` flag produces full Pydantic `model_dump_json(indent=2)`. Machine-parseable, no ANSI color codes. Includes `ok`, `op`, `data`, `warnings`, `error`, `meta` fields. Errors go to stderr, success to stdout. |
| **Outputs** | Structured JSON ServiceResult |

### UC-73 — Quiet/Verbose Output

| Field | Value |
|-------|-------|
| **Service** | `format_result()` with `quiet=True` or `verbose=True` |
| **CLI** | `ztlctl -q <command>` / `ztlctl -v <command>` |
| **Key Behavior** | **Quiet** (`-q`): Errors → `ERROR: <op> — <message>`. Lists → one ID per line. Mutations → `OK: <op>`. **Verbose** (`-v`): Default Rich output plus extra table columns (Modified dates), error details, meta blocks, telemetry span tree. Enables structlog DEBUG level. |

### UC-74 — Non-Interactive Mode

| Field | Value |
|-------|-------|
| **Service** | `ZtlSettings.no_interact` |
| **CLI** | `ztlctl --no-interact <command>` |
| **Key Behavior** | Suppresses all interactive prompts. Commands requiring user input use defaults or fail gracefully. Orthogonal with `--json`. Essential for scripting and CI/CD. |

### UC-75 — Telemetry — Verbose Spans

| Field | Value |
|-------|-------|
| **Service** | `@traced` decorator + `trace_span()` context manager |
| **CLI** | `ztlctl -v <command>` |
| **Key Behavior** | `@traced` on 45 public service methods. Hierarchical span tree: root spans from `@traced`, child spans from `trace_span()`. Zero overhead when disabled (~10ns ContextVar check). Duration color-coding: >1s red, >100ms yellow, <100ms dim. Telemetry injected into `ServiceResult.meta` via frozen-safe `model_copy()`. |

### UC-76 — Telemetry — JSON Logs

| Field | Value |
|-------|-------|
| **Service** | `configure_logging(log_json=True)` |
| **CLI** | `ztlctl --log-json <command>` |
| **Key Behavior** | `--log-json` outputs structured JSON lines to stderr via structlog `JSONRenderer`. All logs to stderr — never interferes with piped stdout. Complements `--json` (stdout) for machine-parseable dual-channel output. |

---

## Error Code Reference

| Code | Services | Trigger |
|------|----------|---------|
| `ACTIVE_SESSION_EXISTS` | SessionService | Start/reopen when session already open |
| `ALREADY_OPEN` | SessionService | Reopen already-open session |
| `BACKUP_FAILED` | UpgradeService | Backup creation error |
| `BATCH_FAILED` | CreateService | All-or-nothing batch failure |
| `BATCH_PARTIAL` | CreateService | Partial batch with errors |
| `CHECK_FAILED` | UpgradeService | Migration check error |
| `EMPTY_QUERY` | QueryService | Empty search string |
| `FILE_NOT_FOUND` | SessionService | Missing session JSONL file |
| `ID_COLLISION` | CreateService | Hash-based ID already exists |
| `INVALID_FORMAT` | ExportService, CLI | Unknown format or bad JSON |
| `INVALID_TRANSITION` | UpdateService | Illegal status change |
| `MIGRATION_FAILED` | UpgradeService | Alembic migration error |
| `NO_ACTIVE_SESSION` | SessionService | Operation without active session |
| `NO_BACKUPS` | CheckService | No backup files available |
| `NO_CONFIG` | InitService | Missing ztlctl.toml |
| `NO_HISTORY` | ReweaveService | No reweave log to undo |
| `NO_LINK` | GraphService | Edge not found for unlink |
| `NO_PATH` | GraphService | No graph path between nodes |
| `NOT_FOUND` | Multiple | Content ID not in DB/graph |
| `SEMANTIC_UNAVAILABLE` | VectorService, CLI | sqlite-vec not loadable |
| `STAMP_FAILED` | UpgradeService | Alembic stamp error |
| `UNKNOWN_TYPE` | CreateService, UpdateService | Invalid content type/subtype |
| `VALIDATION_FAILED` | CreateService, UpdateService | Model validation errors |
| `VAULT_EXISTS` | InitService | Vault already at path |
| `invalid_file` | CLI (batch) | Unreadable batch JSON file |
| `invalid_format` | CLI (batch) | JSON not a top-level array |
| `no_changes` | CLI (update) | No update flags specified |

---

## Invariant Reference

| # | Invariant | Enforcement |
|---|-----------|-------------|
| 1 | **Files are truth** — DB is derived index | CheckService.rebuild(), transaction compensation |
| 2 | **Single write path** — all content through create pipeline | No alternative creation APIs |
| 3 | **IDs are permanent** — never change after generation | Immutable field validation in UpdateService |
| 4 | **Decisions are immutable** — body locked after `accepted` | DecisionModel.validate_update() |
| 5 | **Body text is human domain** — garden notes protected | Maturity check in UpdateService, GraphService.unlink, ReweaveService |
| 6 | **Plugin failures are warnings** — never errors | BaseService._dispatch_event() try/except |
| 7 | **Async by default** — hooks never block user interaction | EventBus ThreadPoolExecutor |
| 8 | **ServiceResult is the contract** — universal return type | All service methods |
