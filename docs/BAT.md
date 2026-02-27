# Business Acceptance Tests

> Exhaustive end-to-end test specifications for ztlctl.
> Each spec maps to a user journey in [USER-JOURNEYS.md](USER-JOURNEYS.md) and use case in [USE-CASES.md](USE-CASES.md).

---

## Conventions

- **CLI commands** assume a pre-initialized vault unless stated otherwise.
- **`$VAULT`** refers to the vault root directory.
- **`--json` assertions** check parsed JSON output from stdout.
- **DB assertions** query SQLite directly: `.ztlctl/ztlctl.db`.
- **FS assertions** check file existence and content on disk.
- **Exit code 0** = success, **exit code 1** = failure.

---

## Category 1: Vault Initialization & Setup

### BAT-01: Initialize Vault (Interactive)

**Preconditions:** Empty directory `$VAULT`. No `ztlctl.toml`.

**Steps:**
1. `cd $VAULT && ztlctl init` (provide interactive inputs: name="test-vault", client="obsidian", tone="research-partner", topics="math,physics")

**Expected Outcomes:**
- Exit code 0
- Directory structure created:
  - `$VAULT/ztlctl.toml` exists
  - `$VAULT/.ztlctl/ztlctl.db` exists (SQLite WAL mode)
  - `$VAULT/self/identity.md` exists, contains "test-vault"
  - `$VAULT/self/methodology.md` exists
  - `$VAULT/notes/` exists
  - `$VAULT/notes/math/` exists
  - `$VAULT/notes/physics/` exists
  - `$VAULT/ops/logs/` exists
  - `$VAULT/ops/tasks/` exists
  - `$VAULT/.obsidian/snippets/ztlctl.css` exists
  - `$VAULT/.ztlctl/workflow-answers.yml` exists

**Assertions:**
- `ztlctl.toml` contains `[vault]` section with `name = "test-vault"`
- DB tables exist: `nodes`, `edges`, `tags_registry`, `node_tags`, `id_counters`, `reweave_log`, `event_wal`, `session_logs`
- FTS5 virtual table `nodes_fts` exists
- `id_counters` seeded: `LOG-` → 1, `TASK-` → 1
- `identity.md` contains tone-specific content ("research-partner")

### BAT-02: Initialize Vault (Non-Interactive)

**Preconditions:** Empty directory `$VAULT`.

**Steps:**
1. `cd $VAULT && ztlctl init --name "ci-vault" --client vanilla --tone minimal --topics "test" --no-workflow`

**Expected Outcomes:**
- Exit code 0
- No `.obsidian/` directory (client=vanilla)
- No `.ztlctl/workflow-answers.yml` (--no-workflow)
- `notes/test/` directory exists
- `identity.md` contains minimal persona

**Assertions:**
- `ztlctl.toml` contains `name = "ci-vault"`, `client = "vanilla"`, `tone = "minimal"`

### BAT-03: Init Vault Already Exists

**Preconditions:** Initialized vault at `$VAULT`.

**Steps:**
1. `ztlctl --json init --name "duplicate"`

**Expected Outcomes:**
- Exit code 1
- JSON stderr: `{"ok": false, "op": "init_vault", "error": {"code": "VAULT_EXISTS", ...}}`

**Assertions:**
- `error.code == "VAULT_EXISTS"`
- `error.detail.path` contains `$VAULT`

### BAT-04: Regenerate Self-Documents (Stale)

**Preconditions:** Initialized vault. Manually edit `ztlctl.toml` to change `tone = "minimal"`.

**Steps:**
1. `ztlctl --json agent regenerate`

**Expected Outcomes:**
- Exit code 0
- `self/identity.md` content changed to reflect "minimal" tone
- JSON: `data.stale == true`, `data.files_updated` includes "identity.md"

### BAT-05: Regenerate Self-Documents (Not Stale)

**Preconditions:** Initialized vault. No config changes since last render.

**Steps:**
1. `ztlctl --json agent regenerate`

**Expected Outcomes:**
- Exit code 0
- JSON: `data.stale == false`, `data.files_updated == []`

### BAT-06: Regenerate Without Config

**Preconditions:** Directory without `ztlctl.toml`.

**Steps:**
1. `ztlctl --json agent regenerate`

**Expected Outcomes:**
- Exit code 1
- JSON stderr: `error.code == "NO_CONFIG"`

### BAT-07: Config Priority Chain

**Preconditions:** Initialized vault with `ztlctl.toml` containing `[reweave] min_score_threshold = 0.8`.

**Steps:**
1. `ZTLCTL_REWEAVE__MIN_SCORE_THRESHOLD=0.5 ztlctl --json -v create note "Config Test"`
2. Inspect resolved settings from verbose output

**Expected Outcomes:**
- Env var (0.5) overrides TOML (0.8) but CLI flags override both
- Verbose logging enabled (CLI `-v` flag)

### BAT-08: Config Walk-Up Discovery

**Preconditions:** `ztlctl.toml` at `$VAULT/`. CWD is `$VAULT/notes/math/`.

**Steps:**
1. `cd $VAULT/notes/math && ztlctl --json query list --limit 1`

**Expected Outcomes:**
- Exit code 0 (found `ztlctl.toml` two levels up)

### BAT-09: Template Override

**Preconditions:** Initialized vault. Create `$VAULT/.ztlctl/templates/content/note.md.j2` with custom content "CUSTOM TEMPLATE".

**Steps:**
1. `ztlctl create note "Template Test"`
2. Read created file

**Expected Outcomes:**
- Note body contains "CUSTOM TEMPLATE"
- Packaged template not used

---

## Category 2: Content Creation

### BAT-10: Create Plain Note

**Preconditions:** Initialized vault.

**Steps:**
1. `ztlctl --json create note "Database Design" --tags "db/schema,engineering" --topic engineering`

**Expected Outcomes:**
- Exit code 0
- JSON: `ok == true`, `op == "create_note"`
- `data.id` matches `ztl_[0-9a-f]{8}`
- `data.type == "note"`
- `data.path` ends with `.md`

**Assertions:**
- FS: File exists at `data.path`
- FS: Frontmatter contains `id`, `type: note`, `status: draft`, `title: Database Design`, `tags: [db/schema, engineering]`, `topic: engineering`
- DB: `nodes` row with matching id, type="note", status="draft"
- DB: `nodes_fts` row with matching id
- DB: `node_tags` rows for "db/schema" and "engineering"
- DB: `tags_registry` entries for both tags

### BAT-11: Create Note — ID Collision

**Preconditions:** Note "Database Design" already created (BAT-10).

**Steps:**
1. `ztlctl --json create note "Database Design"`

**Expected Outcomes:**
- Exit code 1
- JSON stderr: `error.code == "ID_COLLISION"`

### BAT-12: Create Knowledge Note

**Preconditions:** Initialized vault.

**Steps:**
1. `ztlctl --json create note "Learning Theory" --subtype knowledge`

**Expected Outcomes:**
- Exit code 0
- JSON: `warnings` contains string about missing "key_points"
- FS: Frontmatter `subtype: knowledge`

### BAT-13: Create Decision Note

**Preconditions:** Initialized vault.

**Steps:**
1. `ztlctl --json create note "Use PostgreSQL" --subtype decision`

**Expected Outcomes:**
- Exit code 0
- FS: Frontmatter `subtype: decision`, `status: proposed`
- FS: Body contains sections: Context, Choice, Rationale, Alternatives, Consequences

### BAT-14: Create Article Reference

**Preconditions:** Initialized vault.

**Steps:**
1. `ztlctl --json create reference "REST Best Practices" --subtype article --url "https://example.com/rest"`

**Expected Outcomes:**
- Exit code 0
- `data.id` matches `ref_[0-9a-f]{8}`
- FS: Frontmatter `type: reference`, `subtype: article`, `status: captured`, `url: https://example.com/rest`

### BAT-15: Create Tool Reference

**Preconditions:** Initialized vault.

**Steps:**
1. `ztlctl --json create reference "PostgreSQL" --subtype tool`

**Expected Outcomes:**
- Exit code 0
- FS: Frontmatter `subtype: tool`, `status: captured`

### BAT-16: Create Spec Reference

**Preconditions:** Initialized vault.

**Steps:**
1. `ztlctl --json create reference "RFC 7231" --subtype spec`

**Expected Outcomes:**
- Exit code 0
- FS: Frontmatter `subtype: spec`

### BAT-17: Create Task

**Preconditions:** Initialized vault.

**Steps:**
1. `ztlctl --json create task "Implement Auth" --priority high --impact high --effort low`

**Expected Outcomes:**
- Exit code 0
- `data.id` matches `TASK-\d{4,}`
- FS: Frontmatter `type: task`, `status: inbox`, `priority: high`, `impact: high`, `effort: low`
- DB: `id_counters` row for "TASK-" incremented

### BAT-18: Create Task — Sequential IDs

**Preconditions:** BAT-17 completed (TASK-0001 exists).

**Steps:**
1. `ztlctl --json create task "Second Task"`

**Expected Outcomes:**
- `data.id == "TASK-0002"`

### BAT-19: Batch Create — All-or-Nothing Success

**Preconditions:** Initialized vault. Create `batch.json`:
```json
[
  {"type": "note", "title": "Batch Note 1"},
  {"type": "task", "title": "Batch Task 1"}
]
```

**Steps:**
1. `ztlctl --json create batch batch.json`

**Expected Outcomes:**
- Exit code 0
- JSON: `data.created` has 2 items, `data.errors == []`
- Both items exist in DB and FS

### BAT-20: Batch Create — All-or-Nothing Failure

**Preconditions:** Initialized vault. Create `batch_fail.json`:
```json
[
  {"type": "note", "title": "Good Note"},
  {"type": "invalid_type", "title": "Bad Item"}
]
```

**Steps:**
1. `ztlctl --json create batch batch_fail.json`

**Expected Outcomes:**
- Exit code 1
- `error.code == "BATCH_FAILED"`
- No items created (all-or-nothing)

### BAT-21: Batch Create — Partial Mode

**Preconditions:** Same as BAT-20.

**Steps:**
1. `ztlctl --json create batch batch_fail.json --partial`

**Expected Outcomes:**
- `error.code == "BATCH_PARTIAL"`
- `data.created` has 1 item (the good note)
- `data.errors` has 1 item (the invalid type)

### BAT-22: Batch Create — Invalid File

**Preconditions:** Create `not_array.json`: `{"title": "not an array"}`

**Steps:**
1. `ztlctl --json create batch not_array.json`

**Expected Outcomes:**
- Exit code 1
- `error.code == "invalid_format"`

### BAT-23: Create Garden Seed

**Preconditions:** Initialized vault.

**Steps:**
1. `ztlctl --json create note "Quantum Ideas" --maturity seed`

**Expected Outcomes:**
- Exit code 0
- FS: Frontmatter `maturity: seed`

### BAT-24: Post-Create Reweave

**Preconditions:** Vault with 3 existing notes containing overlapping tags/topics.

**Steps:**
1. `ztlctl --json create note "Related Topic" --tags "shared-tag" --topic "shared-topic"`
2. Read created file

**Expected Outcomes:**
- Note created successfully
- Frontmatter may contain `links.relates` with suggested IDs (if scoring passes threshold)
- No reweave errors (warnings at most)

### BAT-25: Post-Create Reweave Disabled

**Preconditions:** Same as BAT-24.

**Steps:**
1. `ztlctl --json --no-reweave create note "No Reweave"`
2. Read created file

**Expected Outcomes:**
- No `links` section in frontmatter
- No reweave-related warnings

---

## Category 3: Search & Retrieval

### BAT-26: Search by Relevance

**Preconditions:** Vault with notes: "Database Design" (tags: db), "Database Optimization" (tags: db), "Frontend Design" (tags: ui).

**Steps:**
1. `ztlctl --json query search "database"`

**Expected Outcomes:**
- `data.count == 2`
- Both database notes returned
- Sorted by BM25 score (highest first)
- "Frontend Design" not in results

**Assertions:**
- Each item has `id`, `title`, `type`, `score`
- Scores are numeric and > 0

### BAT-27: Search Empty Query

**Preconditions:** Initialized vault.

**Steps:**
1. `ztlctl --json query search ""`

**Expected Outcomes:**
- Exit code 1
- `error.code == "EMPTY_QUERY"`

### BAT-28: Search No Results

**Preconditions:** Initialized vault with content.

**Steps:**
1. `ztlctl --json query search "xyznonexistent"`

**Expected Outcomes:**
- Exit code 0
- `data.count == 0`, `data.items == []`

### BAT-29: Search with Filters

**Preconditions:** Vault with notes and references about "database".

**Steps:**
1. `ztlctl --json query search "database" --type note --tag db --limit 1`

**Expected Outcomes:**
- Only notes returned (no references)
- Only tagged with "db"
- Max 1 result

### BAT-30: Search by Recency

**Preconditions:** Two notes about "database": one created today, one created a week ago.

**Steps:**
1. `ztlctl --json query search "database" --rank-by recency`

**Expected Outcomes:**
- Today's note ranked higher than week-old note
- Both have non-zero scores

### BAT-31: Search by Graph Rank (No Materialize)

**Preconditions:** Vault with notes. `graph materialize` NOT run.

**Steps:**
1. `ztlctl --json query search "database" --rank-by graph`

**Expected Outcomes:**
- Exit code 0
- `warnings` contains PageRank zero warning

### BAT-32: Search by Graph Rank (Materialized)

**Preconditions:** Vault with linked notes. `ztlctl graph materialize` already run.

**Steps:**
1. `ztlctl --json query search "database" --rank-by graph`

**Expected Outcomes:**
- Highly-connected notes ranked higher
- No PageRank zero warning

### BAT-33: Get Single Item

**Preconditions:** Note `ztl_abc12345` exists.

**Steps:**
1. `ztlctl --json query get ztl_abc12345`

**Expected Outcomes:**
- Exit code 0
- `data.id == "ztl_abc12345"`
- `data.title`, `data.type`, `data.status`, `data.tags` present
- `data.body` contains file body content
- `data.out_links` and `data.in_links` are arrays

### BAT-34: Get Not Found

**Preconditions:** Initialized vault.

**Steps:**
1. `ztlctl --json query get ztl_nonexist`

**Expected Outcomes:**
- Exit code 1
- `error.code == "NOT_FOUND"`

### BAT-35: List with Filters

**Preconditions:** Vault with mixed content types, statuses, and tags.

**Steps:**
1. `ztlctl --json query list --type note --status draft --sort recency --limit 5`

**Expected Outcomes:**
- Only notes with status=draft
- Max 5 results
- Sorted by recency (newest first)
- Archived excluded (default)

### BAT-36: List Include Archived

**Preconditions:** Vault with 1 archived note, 2 non-archived.

**Steps:**
1. `ztlctl --json query list --include-archived`

**Expected Outcomes:**
- All 3 items returned (including archived)

### BAT-37: List Empty Vault

**Preconditions:** Initialized vault, no content.

**Steps:**
1. `ztlctl --json query list`

**Expected Outcomes:**
- `data.count == 0`, `data.items == []`

### BAT-38: Work Queue

**Preconditions:** Tasks: TASK-0001 (inbox, high/high/low), TASK-0002 (active, medium/medium/medium), TASK-0003 (done, critical/high/low).

**Steps:**
1. `ztlctl --json query work-queue`

**Expected Outcomes:**
- Only TASK-0001 and TASK-0002 returned (done excluded)
- TASK-0001 scored higher (high/high/low = better than medium/medium/medium)
- Each item has `score` field

### BAT-39: Decision Support

**Preconditions:** Vault with: decision "Use PostgreSQL" (proposed), note "DB Comparison", reference "PostgreSQL Docs", all topic="database".

**Steps:**
1. `ztlctl --json query decision-support --topic database`

**Expected Outcomes:**
- `data.decisions` contains "Use PostgreSQL"
- `data.notes` contains "DB Comparison"
- `data.references` contains "PostgreSQL Docs"
- `data.counts` has totals per category

---

## Category 4: Content Updates & Lifecycle

### BAT-40: Update Metadata

**Preconditions:** Note `ztl_abc` exists with tags ["old-tag"].

**Steps:**
1. `ztlctl --json update ztl_abc --title "Updated Title" --tags "new-tag"`

**Expected Outcomes:**
- Exit code 0
- `data.fields_changed` includes "title", "tags"
- FS: Frontmatter title changed, tags changed
- DB: nodes row updated
- DB: FTS5 re-indexed (title changed)
- DB: node_tags updated

### BAT-41: Update No Changes

**Preconditions:** Note exists.

**Steps:**
1. `ztlctl --json update ztl_abc`

**Expected Outcomes:**
- Exit code 1
- `error.code == "no_changes"`

### BAT-42: Update Not Found

**Preconditions:** Initialized vault.

**Steps:**
1. `ztlctl --json update ztl_nonexist --title "X"`

**Expected Outcomes:**
- Exit code 1
- `error.code == "NOT_FOUND"`

### BAT-43: Note Status Auto-Computation

**Preconditions:** Note `ztl_A` exists with 0 links (status=draft).

**Steps:**
1. Create notes `ztl_B`, `ztl_C`, `ztl_D`
2. Add link A→B: `ztlctl --json update ztl_A --links '{"relates":["ztl_B"]}'`
3. Verify status
4. Add links A→C, A→D (total 3 outgoing)
5. Verify status

**Expected Outcomes:**
- After step 2: status transitions to `linked` (1 link ≥ NOTE_LINKED_THRESHOLD)
- After step 4: status transitions to `connected` (3 links ≥ NOTE_CONNECTED_THRESHOLD)

**Assertions:**
- Status never set via `--status` flag for notes
- DB and FS status values match

### BAT-44: Task Status Transitions — Valid

**Preconditions:** Task TASK-0001 in `inbox` status.

**Steps:**
1. `ztlctl --json update TASK-0001 --status active` → exit 0
2. `ztlctl --json update TASK-0001 --status blocked` → exit 0
3. `ztlctl --json update TASK-0001 --status active` → exit 0
4. `ztlctl --json update TASK-0001 --status done` → exit 0

**Assertions:**
- All transitions succeed
- Each step: FS frontmatter status matches, DB nodes.status matches

### BAT-45: Task Status Transitions — Invalid

**Preconditions:** Task TASK-0001 in `inbox` status.

**Steps:**
1. `ztlctl --json update TASK-0001 --status done`

**Expected Outcomes:**
- Exit code 1
- `error.code == "INVALID_TRANSITION"`
- Message mentions "inbox" and "done"

### BAT-46: Task Terminal States

**Preconditions:** Task TASK-0001 in `done` status.

**Steps:**
1. `ztlctl --json update TASK-0001 --status active`

**Expected Outcomes:**
- Exit code 1
- `error.code == "INVALID_TRANSITION"` (done is terminal)

### BAT-47: Reference Status Transition

**Preconditions:** Reference `ref_abc` in `captured` status.

**Steps:**
1. `ztlctl --json update ref_abc --status annotated` → exit 0
2. `ztlctl --json update ref_abc --status captured` → exit 1

**Assertions:**
- Step 1: success, status=annotated
- Step 2: `INVALID_TRANSITION` (annotated is terminal)

### BAT-48: Decision Acceptance

**Preconditions:** Decision note `ztl_dec` in `proposed` status.

**Steps:**
1. `ztlctl --json update ztl_dec --status accepted`

**Expected Outcomes:**
- Exit code 0
- FS: `status: accepted`

### BAT-49: Decision Immutability After Acceptance

**Preconditions:** Decision note `ztl_dec` in `accepted` status (BAT-48).

**Steps:**
1. `ztlctl --json update ztl_dec --title "New Title"` → exit 1
2. `ztlctl --json update ztl_dec --tags "allowed-tag"` → exit 0

**Assertions:**
- Step 1: `error.code == "VALIDATION_FAILED"` (title is immutable after acceptance)
- Step 2: success (tags are allowed after acceptance)

### BAT-50: Archive Content

**Preconditions:** Note `ztl_abc` exists, not archived.

**Steps:**
1. `ztlctl --json archive ztl_abc`
2. `ztlctl --json query list`
3. `ztlctl --json query get ztl_abc`

**Assertions:**
- Step 1: exit 0, `data.id == "ztl_abc"`
- Step 2: `ztl_abc` NOT in results (excluded by default)
- Step 3: exit 0, item still retrievable by direct ID
- DB: `nodes.archived == true`
- FS: frontmatter contains `archived: true`

### BAT-51: Supersede Decision

**Preconditions:** Decision `ztl_old` in `accepted` status. Decision `ztl_new` exists.

**Steps:**
1. `ztlctl --json supersede ztl_old ztl_new`

**Assertions:**
- Exit code 0
- FS (old): `status: superseded`, `superseded_by: ztl_new`
- DB (old): status="superseded"

### BAT-52: Garden Maturity — Body Protection

**Preconditions:** Note `ztl_garden` with `maturity: seed`.

**Steps:**
1. `ztlctl --json update ztl_garden --body "New body text"`

**Expected Outcomes:**
- Exit code 0 (warning, not error)
- `warnings` contains body protection message
- FS: body text UNCHANGED (garden protection)

### BAT-53: Garden Maturity Progression

**Preconditions:** Note `ztl_garden` with `maturity: seed`.

**Steps:**
1. `ztlctl --json update ztl_garden --maturity budding` → exit 0
2. `ztlctl --json update ztl_garden --maturity evergreen` → exit 0

**Assertions:**
- Each step: FS frontmatter maturity updated
- Body protected throughout (maturity always set)

---

## Category 5: Graph Operations

### BAT-54: Related Content

**Preconditions:** Graph: A→B, A→C, B→D. All are notes.

**Steps:**
1. `ztlctl --json graph related ztl_A --depth 2 --top 10`

**Expected Outcomes:**
- `data.source_id == "ztl_A"`
- `data.items` includes B (depth=1, score=0.5), C (depth=1, score=0.5), D (depth=2, score=0.25)
- Sorted by score descending

### BAT-55: Related — Node Not Found

**Preconditions:** Initialized vault.

**Steps:**
1. `ztlctl --json graph related ztl_nonexist`

**Expected Outcomes:**
- Exit code 1
- `error.code == "NOT_FOUND"`

### BAT-56: Related — Isolated Node

**Preconditions:** Note `ztl_isolated` with no edges.

**Steps:**
1. `ztlctl --json graph related ztl_isolated`

**Expected Outcomes:**
- `data.count == 0`, `data.items == []`

### BAT-57: Theme Detection

**Preconditions:** Vault with 2 clusters: {A,B,C} interconnected, {D,E} interconnected, no cross-cluster edges.

**Steps:**
1. `ztlctl --json graph themes`

**Expected Outcomes:**
- `data.communities` has 2 entries
- One community has members [A,B,C], other has [D,E]

### BAT-58: PageRank Ranking

**Preconditions:** Graph: A→B, C→B, D→B (B has 3 incoming links).

**Steps:**
1. `ztlctl --json graph rank --top 5`

**Expected Outcomes:**
- B ranked highest (most incoming links)
- All items have `score` > 0

### BAT-59: Path Finding — Success

**Preconditions:** Graph: A→B→C→D.

**Steps:**
1. `ztlctl --json graph path ztl_A ztl_D`

**Expected Outcomes:**
- `data.length == 3` (3 hops)
- `data.steps` = [A, B, C, D]

### BAT-60: Path Finding — No Path

**Preconditions:** Graph: {A→B} and {C→D} (disconnected).

**Steps:**
1. `ztlctl --json graph path ztl_A ztl_C`

**Expected Outcomes:**
- Exit code 1
- `error.code == "NO_PATH"`

### BAT-61: Path Finding — Node Not Found

**Preconditions:** Initialized vault.

**Steps:**
1. `ztlctl --json graph path ztl_nonexist ztl_A`

**Expected Outcomes:**
- Exit code 1
- `error.code == "NOT_FOUND"`

### BAT-62: Structural Gaps

**Preconditions:** Graph with varied connectivity.

**Steps:**
1. `ztlctl --json graph gaps --top 5`

**Expected Outcomes:**
- Items with `constraint` values
- Isolated/degree-1 nodes filtered (no NaN/Inf)

### BAT-63: Bridge Detection

**Preconditions:** Two clusters connected by a single bridge node.

**Steps:**
1. `ztlctl --json graph bridges --top 5`

**Expected Outcomes:**
- Bridge node has highest `centrality`

### BAT-64: Unlink Nodes

**Preconditions:** Note `ztl_A` has frontmatter `links: {relates: [ztl_B]}` and body `See also: [[B Title]]`.

**Steps:**
1. `ztlctl --json graph unlink ztl_A ztl_B`

**Expected Outcomes:**
- Exit code 0
- `data.edges_removed >= 1`
- FS: `links.relates` no longer contains `ztl_B`
- FS: `[[B Title]]` removed from body
- DB: edge row deleted
- DB: FTS5 re-indexed

### BAT-65: Unlink — Garden Note Body Protection

**Preconditions:** Garden note `ztl_garden` (maturity: seed) links to `ztl_B` in frontmatter and body.

**Steps:**
1. `ztlctl --json graph unlink ztl_garden ztl_B`

**Expected Outcomes:**
- `data.edges_removed >= 1`
- FS: frontmatter link removed
- FS: body wikilink PRESERVED (garden protection)
- `warnings` contains body protection message

### BAT-66: Unlink — No Link

**Preconditions:** Two unlinked notes.

**Steps:**
1. `ztlctl --json graph unlink ztl_A ztl_C`

**Expected Outcomes:**
- Exit code 1
- `error.code == "NO_LINK"`

### BAT-67: Materialize Metrics

**Preconditions:** Vault with linked notes.

**Steps:**
1. `ztlctl --json graph materialize`

**Expected Outcomes:**
- `data.nodes_updated > 0`
- DB: `nodes.pagerank` populated (non-null)
- DB: `nodes.degree_in`, `nodes.degree_out` populated
- DB: `nodes.betweenness` populated
- DB: `nodes.cluster_id` populated

---

## Category 6: Reweave (Link Discovery)

### BAT-68: Reweave — Discover Links

**Preconditions:** Notes with overlapping tags and topics. `reweave.enabled=true`.

**Steps:**
1. `ztlctl --json reweave --id ztl_target`

**Expected Outcomes:**
- Exit code 0
- `data.target_id == "ztl_target"`
- `data.connected` has items with `id` and `score` (score ≥ threshold)
- FS: frontmatter `links.relates` updated
- DB: edges created
- DB: `reweave_log` entries added

### BAT-69: Reweave — Dry Run

**Preconditions:** Same as BAT-68.

**Steps:**
1. `ztlctl --json reweave --dry-run --id ztl_target`

**Expected Outcomes:**
- `data.suggestions` has items (not `connected`)
- FS: no frontmatter changes
- DB: no new edges
- DB: no reweave_log entries

### BAT-70: Reweave — No Candidates

**Preconditions:** Vault with 1 note only.

**Steps:**
1. `ztlctl --json reweave --id ztl_only`

**Expected Outcomes:**
- `data.count == 0`
- No links added

### BAT-71: Reweave — Prune

**Preconditions:** Note with 3 existing links, 1 scores below threshold after re-evaluation.

**Steps:**
1. `ztlctl --json reweave --prune --id ztl_target`

**Expected Outcomes:**
- `data.pruned` has 1 item
- FS: removed link from frontmatter
- DB: edge deleted
- DB: `reweave_log` entry with action="prune"

### BAT-72: Reweave — Undo Latest

**Preconditions:** BAT-68 completed (reweave created links).

**Steps:**
1. `ztlctl --json reweave --undo`

**Expected Outcomes:**
- `data.undone` has items matching BAT-68's connected links
- FS: frontmatter links removed
- DB: edges deleted
- DB: `reweave_log.undone == true`

### BAT-73: Reweave — Undo No History

**Preconditions:** No reweave operations performed.

**Steps:**
1. `ztlctl --json reweave --undo`

**Expected Outcomes:**
- Exit code 1
- `error.code == "NO_HISTORY"`

---

## Category 7: Session Management

### BAT-74: Start Session

**Preconditions:** No active session.

**Steps:**
1. `ztlctl --json agent session start "ML Research"`

**Expected Outcomes:**
- Exit code 0
- `data.id` matches `LOG-\d{4,}`
- `data.topic == "ML Research"`
- `data.status == "open"`
- FS: `ops/logs/LOG-NNNN.jsonl` exists with initial entry
- DB: nodes row with type="log", status="open"

### BAT-75: Start Session — Already Active

**Preconditions:** BAT-74 completed (session active).

**Steps:**
1. `ztlctl --json agent session start "Another Topic"`

**Expected Outcomes:**
- Exit code 1
- `error.code == "ACTIVE_SESSION_EXISTS"`

### BAT-76: Log Session Entry

**Preconditions:** Active session.

**Steps:**
1. `ztlctl --json agent session log "Found interesting paper" --pin --cost 500`

**Expected Outcomes:**
- Exit code 0
- `data.session_id` matches active session
- FS: JSONL file has new line with `pin: true`, `cost: 500`
- DB: `session_logs` row with cost=500, pinned=true

### BAT-77: Log Entry — No Active Session

**Preconditions:** No active session.

**Steps:**
1. `ztlctl --json agent session log "orphan entry"`

**Expected Outcomes:**
- Exit code 1
- `error.code == "NO_ACTIVE_SESSION"`

### BAT-78: Close Session

**Preconditions:** Active session with created content.

**Steps:**
1. `ztlctl --json agent session close --summary "Completed ML research"`

**Expected Outcomes:**
- Exit code 0
- `data.status == "closed"`
- `data.session_id` matches
- `data.reweave_count` is int (≥0)
- `data.orphan_count` is int (≥0)
- `data.integrity_issues` is int (≥0)
- FS: JSONL has close entry
- DB: nodes.status changed to "closed"

### BAT-79: Close Session — No Active

**Preconditions:** No active session.

**Steps:**
1. `ztlctl --json agent session close`

**Expected Outcomes:**
- Exit code 1
- `error.code == "NO_ACTIVE_SESSION"`

### BAT-80: Reopen Session

**Preconditions:** Session LOG-0001 closed. No other active session.

**Steps:**
1. `ztlctl --json agent session reopen LOG-0001`

**Expected Outcomes:**
- Exit code 0
- `data.status == "open"`
- FS: JSONL has reopen entry
- DB: nodes.status changed back to "open"

### BAT-81: Reopen — Already Open

**Preconditions:** Session LOG-0001 already open.

**Steps:**
1. `ztlctl --json agent session reopen LOG-0001`

**Expected Outcomes:**
- Exit code 1
- `error.code == "ALREADY_OPEN"`

### BAT-82: Reopen — Other Session Active

**Preconditions:** LOG-0001 closed. LOG-0002 open.

**Steps:**
1. `ztlctl --json agent session reopen LOG-0001`

**Expected Outcomes:**
- Exit code 1
- `error.code == "ACTIVE_SESSION_EXISTS"`

### BAT-83: Agent Context Assembly

**Preconditions:** Active session on topic "ML". Vault has ML-tagged content.

**Steps:**
1. `ztlctl --json agent context --topic ML --budget 8000`

**Expected Outcomes:**
- Exit code 0
- `data.total_tokens` is int > 0
- `data.budget == 8000`
- `data.remaining` is int (budget - total_tokens)
- `data.pressure` is one of "normal", "caution", "exceeded"
- `data.layers` has keys: identity, methodology, session, etc.

### BAT-84: Agent Context — No Session

**Preconditions:** No active session.

**Steps:**
1. `ztlctl --json agent context`

**Expected Outcomes:**
- Exit code 1
- `error.code == "NO_ACTIVE_SESSION"`

### BAT-85: Agent Brief

**Preconditions:** Initialized vault with content. No session required.

**Steps:**
1. `ztlctl --json agent brief`

**Expected Outcomes:**
- Exit code 0
- `data.vault_stats` has counts by type

### BAT-86: Session Cost — Query Mode

**Preconditions:** Active session with log entries (cost: 100, 200).

**Steps:**
1. `ztlctl --json agent session cost`

**Expected Outcomes:**
- `data.total_cost == 300`
- `data.entry_count == 2`

### BAT-87: Session Cost — Report Mode

**Preconditions:** Same as BAT-86.

**Steps:**
1. `ztlctl --json agent session cost --report 500`

**Expected Outcomes:**
- `data.total_cost == 300`
- `data.budget == 500`
- `data.remaining == 200`
- `data.over_budget == false`

### BAT-88: Session Cost — Over Budget

**Preconditions:** Active session with cost=1000.

**Steps:**
1. `ztlctl --json agent session cost --report 500`

**Expected Outcomes:**
- `data.over_budget == true`
- `data.remaining == -500`

---

## Category 8: Integrity & Maintenance

### BAT-89: Integrity Check — Clean

**Preconditions:** Healthy vault, all files and DB in sync.

**Steps:**
1. `ztlctl --json check`

**Expected Outcomes:**
- Exit code 0
- `data.count == 0`
- `data.issues == []`

### BAT-90: Integrity Check — Issues Found

**Preconditions:** Manually delete a content file that has a DB node entry.

**Steps:**
1. `ztlctl --json check`

**Expected Outcomes:**
- `data.count >= 1`
- `data.issues` contains item with `category: "db_file"` (node without file)

### BAT-91: Integrity Fix (Safe)

**Preconditions:** BAT-90 state (missing file detected).

**Steps:**
1. `ztlctl --json check --fix`

**Expected Outcomes:**
- Exit code 0
- `data.fixes` has entries
- DB: orphan node row removed
- FS: backup created in `.ztlctl/backups/`

### BAT-92: Integrity Fix (Aggressive)

**Preconditions:** Vault with multiple integrity issues.

**Steps:**
1. `ztlctl --json check --fix --level aggressive`

**Expected Outcomes:**
- More fixes than safe mode
- Backup created

### BAT-93: Full Rebuild

**Preconditions:** Vault with content files. DB may be corrupted.

**Steps:**
1. `ztlctl --json check --rebuild`

**Expected Outcomes:**
- Exit code 0
- `data.nodes_indexed > 0`
- `data.edges_created >= 0`
- `data.tags_found >= 0`
- DB: all tables rebuilt from filesystem
- DB: FTS5 rebuilt

### BAT-94: Rollback to Backup

**Preconditions:** Backup exists in `.ztlctl/backups/`.

**Steps:**
1. `ztlctl --json check --rollback`

**Expected Outcomes:**
- Exit code 0
- DB replaced with backup content

### BAT-95: Rollback — No Backups

**Preconditions:** `.ztlctl/backups/` directory empty or nonexistent.

**Steps:**
1. `ztlctl --json check --rollback`

**Expected Outcomes:**
- Exit code 1
- `error.code == "NO_BACKUPS"`

### BAT-96: Database Upgrade — Check Pending

**Preconditions:** Vault with pending migrations.

**Steps:**
1. `ztlctl --json upgrade`

**Expected Outcomes:**
- `data.pending_count >= 0`
- `data.pending` is array of `{revision, description}`

### BAT-97: Database Upgrade — Apply

**Preconditions:** Vault with pending migrations.

**Steps:**
1. `ztlctl --json upgrade --apply`

**Expected Outcomes:**
- Backup created
- Migrations applied
- `data.applied_count > 0`

---

## Category 9: Export

### BAT-98: Export Markdown

**Preconditions:** Vault with content in `notes/` and `ops/`.

**Steps:**
1. `ztlctl --json export markdown --output /tmp/bat-export-md`

**Expected Outcomes:**
- Exit code 0
- `data.file_count > 0`
- FS: `/tmp/bat-export-md/notes/` has markdown files
- FS: directory structure mirrors vault

### BAT-99: Export Indexes

**Preconditions:** Vault with notes (topic: math, engineering) and tasks.

**Steps:**
1. `ztlctl --json export indexes --output /tmp/bat-export-idx`

**Expected Outcomes:**
- Exit code 0
- FS: `index.md` exists
- FS: `by-type/note.md`, `by-type/task.md` exist
- FS: `by-topic/math.md`, `by-topic/engineering.md` exist

### BAT-100: Export Graph DOT

**Preconditions:** Vault with linked content.

**Steps:**
1. `ztlctl --json export graph --format dot`

**Expected Outcomes:**
- `data.format == "dot"`
- `data.content` starts with "digraph" or "graph"
- `data.node_count > 0`

### BAT-101: Export Graph JSON

**Preconditions:** Same as BAT-100.

**Steps:**
1. `ztlctl --json export graph --format json`

**Expected Outcomes:**
- `data.format == "json"`
- `data.content` parses as JSON with `nodes` and `links` arrays

### BAT-102: Export Graph — Invalid Format

**Preconditions:** Initialized vault.

**Steps:**
1. `ztlctl --json export graph --format xml`

**Expected Outcomes:**
- Exit code 1
- `error.code == "INVALID_FORMAT"`
- `error.detail.valid == ["dot", "json"]`

---

## Category 10: Extensions & Integrations

### BAT-103: MCP — Create Note Tool

**Preconditions:** MCP server running (`ztlctl serve --transport stdio`).

**Steps:**
1. Send MCP tool call: `create_note(title="MCP Note", tags=["mcp-test"])`

**Expected Outcomes:**
- Response contains ServiceResult JSON with `ok: true`
- Note exists in vault FS and DB

### BAT-104: MCP — Search Tool

**Preconditions:** MCP server running. Vault has content.

**Steps:**
1. Send MCP tool call: `search(query="test", limit=5)`

**Expected Outcomes:**
- Response contains search results

### BAT-105: MCP — Agent Context (With Session)

**Preconditions:** MCP server running. Active session.

**Steps:**
1. Send MCP tool call: `agent_context(query="test")`

**Expected Outcomes:**
- Response from SessionService.context()
- Contains layer structure

### BAT-106: MCP — Agent Context (No Session — Fallback)

**Preconditions:** MCP server running. No active session.

**Steps:**
1. Send MCP tool call: `agent_context(query="test")`

**Expected Outcomes:**
- Fallback response from QueryService
- Contains `total_items`, `recent`, `work_queue`

### BAT-107: MCP — Resources

**Preconditions:** MCP server running.

**Steps:**
1. Read resource `ztlctl://self/identity`
2. Read resource `ztlctl://overview`
3. Read resource `ztlctl://work-queue`
4. Read resource `ztlctl://topics`

**Expected Outcomes:**
- Identity: markdown content from identity.md
- Overview: JSON with type counts
- Work-queue: JSON with scored tasks
- Topics: JSON with topic list

### BAT-108: MCP — Prompts

**Preconditions:** MCP server running.

**Steps:**
1. Get prompt `research_session(topic="ML")`
2. Get prompt `vault_orientation()`

**Expected Outcomes:**
- Research session: structured multi-step workflow text
- Orientation: includes identity + methodology content

### BAT-109: MCP — Discover Tools

**Preconditions:** MCP server running.

**Steps:**
1. Send MCP tool call: `discover_tools()`

**Expected Outcomes:**
- Response lists all 13 tools grouped by category
- Categories include: creation, query, lifecycle, session, discovery

### BAT-110: Plugin Discovery

**Preconditions:** Vault with `.ztlctl/plugins/test_plugin.py` containing a `@hookimpl post_create` method.

**Steps:**
1. Start vault (triggers plugin discovery)
2. Create a note

**Expected Outcomes:**
- Plugin loaded during discovery
- Plugin's `post_create` method called (verify via side-effect)

### BAT-111: Plugin — Custom Content Type

**Preconditions:** Plugin implements `register_content_models()` returning `{"custom": CustomNoteModel}`.

**Steps:**
1. Start vault
2. `ztlctl --json create note "Custom" --subtype custom`

**Expected Outcomes:**
- Note created with `subtype: custom`
- Custom model's template used (if provided)

### BAT-112: Plugin — Failure Isolation

**Preconditions:** Plugin `post_create` raises an exception.

**Steps:**
1. `ztlctl --json create note "Plugin Fail Test"`

**Expected Outcomes:**
- Exit code 0 (creation succeeds)
- `warnings` contains plugin failure message
- Note exists in DB and FS despite plugin error

### BAT-113: Git Plugin — Batch Mode

**Preconditions:** `[git] enabled=true, batch_commits=true`. Git initialized in vault.

**Steps:**
1. Start session
2. Create 3 notes
3. Close session

**Expected Outcomes:**
- After each create: `git add` called (file staged)
- After session close: `git commit` called once with batch message
- Git log shows single commit for all 3 notes

### BAT-114: Git Plugin — No Git Installed

**Preconditions:** `[git] enabled=true`. Git NOT installed/available.

**Steps:**
1. `ztlctl --json create note "No Git Test"`

**Expected Outcomes:**
- Exit code 0 (creation succeeds)
- No git errors visible to user (silent failure)

### BAT-115: Event Bus — Async Dispatch

**Preconditions:** Event bus initialized (default async mode).

**Steps:**
1. `ztlctl --json create note "Event Test"`
2. Check DB: `event_wal` table

**Expected Outcomes:**
- `event_wal` row with `hook_name: "post_create"`, `status: "completed"`
- Payload contains content_type, content_id, title

### BAT-116: Event Bus — Sync Mode

**Preconditions:** `--sync` flag set.

**Steps:**
1. `ztlctl --json --sync create note "Sync Event"`

**Expected Outcomes:**
- Event processed synchronously (same thread)
- `event_wal` row with `status: "completed"`

### BAT-117: Event Bus — Drain at Session Close

**Preconditions:** Active session. Event bus has pending events.

**Steps:**
1. Close session

**Expected Outcomes:**
- `drain()` called
- All pending/failed events retried
- `event_wal` statuses updated

### BAT-118: Semantic Search — Available

**Preconditions:** `ztlctl[semantic]` installed. `search.semantic_enabled=true`.

**Steps:**
1. `ztlctl --json query search "concept" --rank-by semantic`

**Expected Outcomes:**
- Results based on embedding similarity
- No `SEMANTIC_UNAVAILABLE` error

### BAT-119: Semantic Search — Unavailable

**Preconditions:** `search.semantic_enabled=true` but sqlite-vec NOT installed.

**Steps:**
1. `ztlctl --json query search "concept" --rank-by semantic`

**Expected Outcomes:**
- Fallback to BM25 or `SEMANTIC_UNAVAILABLE` error

---

## Category 11: Cross-Cutting Concerns

### BAT-120: JSON Output Mode

**Preconditions:** Initialized vault.

**Steps:**
1. `ztlctl --json create note "JSON Test" 2>/dev/null` (capture stdout)
2. Parse stdout as JSON

**Expected Outcomes:**
- Valid JSON
- Has keys: `ok`, `op`, `data`, `warnings`, `error`, `meta`
- `ok == true`, `op == "create_note"`
- No ANSI escape codes in output

### BAT-121: JSON Output — Error

**Preconditions:** Initialized vault.

**Steps:**
1. `ztlctl --json query get ztl_nonexist 2>&1 1>/dev/null` (capture stderr)
2. Parse stderr as JSON

**Expected Outcomes:**
- Valid JSON on stderr
- `ok == false`, `error.code == "NOT_FOUND"`
- Exit code 1

### BAT-122: Quiet Output — Mutation

**Preconditions:** Initialized vault.

**Steps:**
1. `ztlctl -q create note "Quiet Test"` (capture stdout)

**Expected Outcomes:**
- Output is single line: `OK: create_note`

### BAT-123: Quiet Output — List

**Preconditions:** Vault with 3 notes.

**Steps:**
1. `ztlctl -q query list`

**Expected Outcomes:**
- One ID per line (3 lines)
- No table formatting

### BAT-124: Quiet Output — Error

**Preconditions:** Initialized vault.

**Steps:**
1. `ztlctl -q query get ztl_nonexist` (capture stderr)

**Expected Outcomes:**
- stderr: `ERROR: get — No content found with ID 'ztl_nonexist'`

### BAT-125: Verbose Output — Telemetry Tree

**Preconditions:** Initialized vault.

**Steps:**
1. `ztlctl -v create note "Verbose Test"` (capture stdout)

**Expected Outcomes:**
- Output includes Rich-formatted result
- Telemetry span tree visible (CreateService.create_note with children)
- Duration values shown

### BAT-126: Non-Interactive Mode

**Preconditions:** Empty vault directory.

**Steps:**
1. `ztlctl --no-interact init --name "ci-vault" --client vanilla --tone minimal`

**Expected Outcomes:**
- No prompts fired
- Vault created successfully

### BAT-127: Telemetry — Verbose Spans

**Preconditions:** Initialized vault.

**Steps:**
1. `ztlctl --json -v create note "Span Test"`
2. Parse JSON result

**Expected Outcomes:**
- `meta.telemetry` present in JSON
- `meta.telemetry.name == "CreateService.create_note"`
- `meta.telemetry.duration_ms > 0`
- `meta.telemetry.children` is array (sub-spans)

### BAT-128: Telemetry — JSON Logs

**Preconditions:** Initialized vault.

**Steps:**
1. `ztlctl --log-json -v create note "Log Test" 2>/tmp/bat-logs.jsonl`
2. Parse `/tmp/bat-logs.jsonl` lines

**Expected Outcomes:**
- Each line is valid JSON
- Lines contain `event`, `level`, `timestamp` keys
- DEBUG-level entries present (verbose enabled)
- stderr only (stdout unaffected)

### BAT-129: Dual Machine Output

**Preconditions:** Initialized vault.

**Steps:**
1. `ztlctl --json --log-json create note "Dual Test" 1>/tmp/bat-stdout.json 2>/tmp/bat-stderr.jsonl`

**Expected Outcomes:**
- `/tmp/bat-stdout.json`: valid ServiceResult JSON
- `/tmp/bat-stderr.jsonl`: structured JSON log lines
- Both machine-parseable independently

### BAT-130: Telemetry Disabled — Zero Overhead

**Preconditions:** Initialized vault.

**Steps:**
1. `ztlctl --json create note "No Telemetry"` (no `-v` flag)

**Expected Outcomes:**
- `meta` is null (no telemetry injected)
- Performance: no measurable overhead from `@traced` decorator

---

## Verification Checklist

| Requirement | BAT Coverage |
|-------------|-------------|
| All 76 use cases have happy-path test | BAT-01 through BAT-130 |
| All content types tested | Note (BAT-10), Knowledge (BAT-12), Decision (BAT-13), Article (BAT-14), Tool (BAT-15), Spec (BAT-16), Task (BAT-17), Garden (BAT-23) |
| All content subtypes tested | knowledge, decision, article, tool, spec (BAT-12–16) |
| All status transitions tested | Note computed (BAT-43), Task valid/invalid/terminal (BAT-44–46), Reference (BAT-47), Decision (BAT-48–49) |
| All error codes exercised | VAULT_EXISTS (BAT-03), NO_CONFIG (BAT-06), ID_COLLISION (BAT-11), EMPTY_QUERY (BAT-27), NOT_FOUND (BAT-34,55,61), INVALID_TRANSITION (BAT-45–47), VALIDATION_FAILED (BAT-49), NO_PATH (BAT-60), NO_LINK (BAT-66), NO_HISTORY (BAT-73), ACTIVE_SESSION_EXISTS (BAT-75,82), NO_ACTIVE_SESSION (BAT-77,79,84), ALREADY_OPEN (BAT-81), NO_BACKUPS (BAT-95), INVALID_FORMAT (BAT-102), BATCH_FAILED (BAT-20), BATCH_PARTIAL (BAT-21), invalid_file/format (BAT-22), no_changes (BAT-41), SEMANTIC_UNAVAILABLE (BAT-119) |
| All DESIGN.md invariants tested | Files-are-truth (BAT-93), IDs permanent (BAT-43), Decision immutability (BAT-49), Body protection (BAT-52,65), Plugin failure isolation (BAT-112), Async default (BAT-115), ServiceResult contract (BAT-120) |
| Cross-cutting: JSON output | BAT-120, BAT-121, BAT-129 |
| Cross-cutting: Quiet output | BAT-122, BAT-123, BAT-124 |
| Cross-cutting: Verbose output | BAT-125, BAT-127 |
| Cross-cutting: Non-interactive | BAT-126 |
| Cross-cutting: Telemetry spans | BAT-127 |
| Cross-cutting: JSON logs | BAT-128, BAT-129 |
| MCP tools tested | BAT-103, BAT-104, BAT-105, BAT-106, BAT-109 |
| MCP resources tested | BAT-107 |
| MCP prompts tested | BAT-108 |
| Plugin discovery tested | BAT-110, BAT-111 |
| Plugin failure isolation | BAT-112 |
| Git plugin tested | BAT-113, BAT-114 |
| Event bus tested | BAT-115, BAT-116, BAT-117 |
| Semantic search tested | BAT-118, BAT-119 |
| Garden lifecycle tested | BAT-23, BAT-52, BAT-53, BAT-65 |
| Reweave full cycle tested | BAT-68 (discover), BAT-69 (dry-run), BAT-71 (prune), BAT-72 (undo), BAT-73 (no history) |
| Session full cycle tested | BAT-74 (start), BAT-76 (log), BAT-78 (close), BAT-80 (reopen) |
| Export all formats tested | BAT-98 (markdown), BAT-99 (indexes), BAT-100 (DOT), BAT-101 (JSON) |
