# User Journeys

> Happy paths, edge cases, and error paths for each of the 76 use cases.
> Each journey maps to a concrete test scenario in [BAT.md](BAT.md).

---

## Category 1: Vault Initialization & Setup

### UC-01 — Initialize Vault (Interactive)

**Happy Path:**
1. User runs `ztlctl init` in an empty directory
2. Prompted for vault name → enters "research-vault"
3. Prompted for client → selects "obsidian"
4. Prompted for tone → selects "research-partner"
5. Prompted for topics → enters "math,physics"
6. Vault structure created: `.ztlctl/`, `self/`, `notes/math/`, `notes/physics/`, `ops/logs/`, `ops/tasks/`
7. `ztlctl.toml` generated with sparse config
8. SQLite DB initialized with tables + FTS5
9. `self/identity.md` and `self/methodology.md` rendered
10. `.obsidian/snippets/ztlctl.css` created (Obsidian client)
11. `.ztlctl/workflow-answers.yml` saved
12. Returns success with file list

**Edge Cases:**
- Empty topics list → no topic subdirectories created, notes/ still exists
- Unicode vault name → handled (NFKC normalization not applied to vault name)
- Path with spaces → quoted path handled correctly
- `init` in home directory → allowed (walk-up stops at root)
- `.ztlctl/` directory partially exists → fails with VAULT_EXISTS

**Error Paths:**
- E1: `ztlctl.toml` already exists → `VAULT_EXISTS` error with path in detail
- E2: Directory not writable → OS-level permission error

### UC-02 — Initialize Vault (Non-Interactive)

**Happy Path:**
1. User runs `ztlctl init --name "my-vault" --client obsidian --tone research-partner --topics "math,cs" --no-workflow`
2. No prompts fired — all parameters from flags
3. Same structure as UC-01 minus `workflow-answers.yml`
4. Returns success

**Edge Cases:**
- `--client vanilla` → no `.obsidian/` directory created
- `--tone minimal` → identity.md has minimal agent persona
- `--topics ""` (empty) → no topic subdirectories
- Path argument provided → creates vault at specified path (not cwd)

**Error Paths:**
- Same as UC-01

### UC-03 — Regenerate Agent Self-Documents

**Happy Path:**
1. Vault exists with valid `ztlctl.toml`
2. User runs `ztlctl agent regenerate`
3. Current `self/identity.md` and `self/methodology.md` compared to fresh renders
4. Files differ (config changed since last render) → stale=true
5. Files re-rendered from Jinja2 templates
6. Returns `files_updated: ["identity.md", "methodology.md"]`

**Edge Cases:**
- Files already up-to-date → stale=false, no files written, `files_updated: []`
- Custom templates in `.ztlctl/templates/self/` → override packaged templates
- Missing `self/` directory → recreated during regeneration
- Config tone changed from "research-partner" to "minimal" → content structurally different

**Error Paths:**
- E1: No `ztlctl.toml` found → `NO_CONFIG`

### UC-04 — Configure Vault Settings

**Happy Path:**
1. `ztlctl.toml` exists with `[vault] name = "my-vault"`
2. User sets `ZTLCTL_VERBOSE=true` env var
3. User runs `ztlctl --json create note "Test"`
4. Priority chain resolves: CLI `--json=true` > env `verbose=true` > TOML `name="my-vault"` > defaults
5. Both JSON output and verbose logging active

**Edge Cases:**
- No `ztlctl.toml` → all defaults used (valid state)
- `ZTLCTL_CONFIG=/custom/path.toml` → overrides walk-up discovery
- `-c /custom/path.toml` CLI flag → overrides env var
- Nested env vars: `ZTLCTL_REWEAVE__MIN_SCORE_THRESHOLD=0.8` → sets reweave config
- Invalid TOML value → Pydantic validation error at startup
- Walk-up finds `ztlctl.toml` three directories up → uses that vault root

**Error Paths:**
- E1: Invalid Pydantic value → Click UsageError at startup

### UC-05 — Template Overrides

**Happy Path:**
1. Vault has `.ztlctl/templates/content/note.md.j2` (custom template)
2. User creates note: `ztlctl create note "Test"`
3. `ChoiceLoader` finds user override first → uses custom template
4. Note body reflects custom template, not packaged default

**Edge Cases:**
- Override in flat layout (`.ztlctl/templates/note.md.j2`) → also found
- Override only for `decision.md.j2` → other templates use packaged defaults
- Template syntax error → Jinja2 render error (propagated as service error)
- Missing `.ztlctl/templates/` directory → falls through to packaged

**Error Paths:**
- E1: Jinja2 syntax error in override template → creation fails with render error

---

## Category 2: Content Creation

### UC-06 — Create Plain Note

**Happy Path:**
1. User runs `ztlctl create note "Database Design" --tags "db/schema,engineering" --topic engineering`
2. Title normalized → SHA-256 → `ztl_a1b2c3d4`
3. Validation passes (NoteModel.validate_create)
4. Frontmatter rendered with canonical key order
5. Body rendered via `note.md.j2`
6. File written to `notes/engineering/ztl_a1b2c3d4.md`
7. DB: nodes row inserted
8. FTS5: title + body indexed
9. Tags: "db/schema" (domain=db, scope=schema), "engineering" (domain=unscoped)
10. Event: `post_create` dispatched
11. Returns success with id, path, title

**Edge Cases:**
- No tags → valid (empty tag list)
- No topic → file goes to `notes/ztl_a1b2c3d4.md` (no subdirectory)
- Unicode title "数据库设计" → valid, NFKC normalized for ID generation
- Very long title (>200 chars) → truncated for ID hash, full title preserved in frontmatter
- Tags with `/` separator → parsed as domain/scope
- Session parameter → `session: LOG-0001` in frontmatter
- Interactive mode: prompted for tags and topic when flags omitted

**Error Paths:**
- E1: Title duplicates existing note (same normalized hash) → `ID_COLLISION`
- E2: Unknown subtype → `UNKNOWN_TYPE`
- E3: Empty title → `VALIDATION_FAILED`

### UC-07 — Create Knowledge Note

**Happy Path:**
1. User runs `ztlctl create note "Learning Theory" --subtype knowledge`
2. `KnowledgeModel` looked up from `CONTENT_REGISTRY`
3. Validation: advisory warning "key_points missing"
4. Body rendered via `knowledge.md.j2`
5. Frontmatter includes `subtype: knowledge`
6. File created, indexed, event dispatched
7. Returns success with warning about missing key_points

**Edge Cases:**
- `key_points` cannot be provided at creation time (CLI doesn't expose it) → always warns
- Subsequent update adds key_points → warning clears

**Error Paths:**
- Same as UC-06

### UC-08 — Create Decision Note

**Happy Path:**
1. User runs `ztlctl create note "Use PostgreSQL" --subtype decision`
2. `DecisionModel` looked up from `CONTENT_REGISTRY`
3. Validation enforces: initial status must be `proposed`
4. Body rendered via `decision.md.j2` with required sections
5. Frontmatter: `status: proposed`, `subtype: decision`
6. File created, indexed
7. Post-create reweave skipped by ReweavePlugin (decision notes excluded)
8. Returns success

**Edge Cases:**
- Body template pre-fills Context/Choice/Rationale/Alternatives/Consequences sections
- Decision note can have `supersedes` field pointing to older decision
- Tags and aliases enriched normally

**Error Paths:**
- E1: Somehow set initial status ≠ proposed → `VALIDATION_FAILED`

### UC-09 — Create Article Reference

**Happy Path:**
1. User runs `ztlctl create reference "REST API Design" --subtype article --url https://example.com/api`
2. Hash ID: `ref_e5f6g7h8`
3. Initial status: `captured`
4. URL stored in frontmatter
5. File written to `notes/ref_e5f6g7h8.md` (references go to notes/)
6. Returns success

**Edge Cases:**
- No URL → valid (URL is optional)
- No subtype → defaults to generic reference (ReferenceModel)
- Duplicate URL on different title → allowed (different ID)

**Error Paths:**
- Same as UC-06

### UC-10 — Create Tool Reference

**Happy Path:**
1. User runs `ztlctl create reference "PostgreSQL" --subtype tool`
2. Classification only — no extra required fields beyond title
3. Returns success

**Edge Cases:**
- Same as UC-09 but subtype="tool"

### UC-11 — Create Spec Reference

**Happy Path:**
1. User runs `ztlctl create reference "RFC 7231" --subtype spec`
2. Classification only
3. Returns success

**Edge Cases:**
- Same as UC-10 but subtype="spec"

### UC-12 — Create Task

**Happy Path:**
1. User runs `ztlctl create task "Implement auth" --priority high --impact high --effort low`
2. Sequential ID: `TASK-0001` (from atomic counter)
3. Initial status: `inbox`
4. Score = high(3)*2 + high(3)*1.5 + (4 - low(1)) = 6 + 4.5 + 3 = 13.5
5. File written to `ops/tasks/TASK-0001.md`
6. Returns success with task metadata

**Edge Cases:**
- Defaults: priority=medium, impact=medium, effort=medium
- Sequential IDs never gap (counter monotonically increases)
- Task IDs grow past 4 digits: TASK-10000
- No tags → valid

**Error Paths:**
- E1: Invalid priority value → `VALIDATION_FAILED`

### UC-13 — Batch Content Creation

**Happy Path (all-or-nothing):**
1. User creates `batch.json`: `[{"type":"note","title":"A"},{"type":"task","title":"B"}]`
2. Runs `ztlctl create batch batch.json`
3. Both items created successfully
4. Returns `data={created: [item1, item2], errors: []}`

**Happy Path (partial mode):**
1. User creates `batch.json` with 3 items, one with invalid type
2. Runs `ztlctl create batch batch.json --partial`
3. 2 items created, 1 error recorded
4. Returns `ok=False` with `BATCH_PARTIAL` error

**Edge Cases:**
- Empty array `[]` → returns success with `created: [], errors: []`
- Single item array → works like single create
- Mixed types (notes, references, tasks) in one batch
- 100+ items → all processed (no hard limit)
- Batch item missing required "title" field → item fails validation

**Error Paths:**
- E1: File not readable → `invalid_file`
- E2: JSON not array → `invalid_format`
- E3: All items fail (all-or-nothing) → `BATCH_FAILED`
- E4: Some items fail (partial) → `BATCH_PARTIAL`

### UC-14 — Create Garden Seed

**Happy Path:**
1. User runs `ztlctl create note "Quantum Computing" --maturity seed`
2. Note created with `maturity: seed`
3. Body protected from auto-modification from this point
4. Returns success

**Edge Cases:**
- Creating with maturity=evergreen → allowed (skips seed/budding stages)
- maturity without tags → valid
- Subsequent reweave: frontmatter links added, body wikilinks NOT added

**Error Paths:**
- E1: Invalid maturity value → `VALIDATION_FAILED`

### UC-15 — Post-Create Reweave

**Happy Path:**
1. Vault has 5 existing notes
2. User creates a new note
3. After creation, reweave runs automatically
4. 4-signal scoring finds 2 candidates above threshold
5. Frontmatter `links.relates` updated with suggested IDs
6. Body may get wikilinks (if not a garden note)
7. `post_create` event fires → ReweavePlugin also runs via event bus

**Edge Cases:**
- `--no-reweave` flag → inline reweave skipped; ReweavePlugin also checks this
- Only 1 node in vault → no candidates, reweave is no-op
- All candidates below threshold → no links added
- Task creation → reweave excluded (tasks don't get auto-linked)
- Decision note → ReweavePlugin skips (strict lifecycle)
- Garden note (maturity set) → frontmatter links added, body untouched

**Error Paths:**
- Reweave failure is warning-only (never blocks creation)

---

## Category 3: Search & Retrieval

### UC-16 — Search by Relevance (BM25)

**Happy Path:**
1. Vault has 10 notes, 3 contain "database"
2. User runs `ztlctl query search "database"`
3. FTS5 BM25 ranks results by term frequency
4. Returns 3 items sorted by BM25 score

**Edge Cases:**
- Query with special FTS5 operators (AND, OR, NOT) → handled via quoting
- Query matches only in body, not title → still found
- No matches → `data={query, count:0, items:[]}`
- `--type note` filter → only notes returned
- `--tag engineering` filter → only tagged items
- `--space ops` → only ops/ content
- `--limit 1` → returns top result only
- `--limit 0` → returns 0 items

**Error Paths:**
- E1: Empty query string → `EMPTY_QUERY`

### UC-17 — Search by Recency

**Happy Path:**
1. User runs `ztlctl query search "database" --rank-by recency`
2. BM25 scores multiplied by time-decay factor
3. Recently modified notes boosted above older ones
4. Returns reordered results vs. pure BM25

**Edge Cases:**
- All notes created at the same time → decay identical, order same as BM25
- Very old notes → decay approaches zero, pushed to bottom
- `search.half_life_days` config controls decay rate

### UC-18 — Search by Graph Rank

**Happy Path:**
1. User runs `ztlctl graph materialize` first
2. Then `ztlctl query search "database" --rank-by graph`
3. BM25 scores multiplied by PageRank
4. Highly-connected notes boosted

**Edge Cases:**
- PageRank never materialized → all scores zero → warning emitted
- Single node with no edges → PageRank = 1/N (minimal)
- `graph materialize` then add new notes → new notes have pagerank=0 until next materialize

**Error Paths:**
- Warning (not error) if PageRank uninitialized

### UC-19 — Semantic Search

**Happy Path:**
1. `search.semantic_enabled=true`, embeddings installed and indexed
2. User runs `ztlctl query search "relational data storage" --rank-by semantic`
3. Query embedded, KNN cosine similarity search
4. Returns semantically related results (may differ from keyword results)

**Edge Cases:**
- Dependencies not installed → `SEMANTIC_UNAVAILABLE`
- Embeddings not indexed → empty results
- Model not cached → first query slower (model download)

**Error Paths:**
- E1: `SEMANTIC_UNAVAILABLE` if sqlite-vec missing

### UC-20 — Hybrid Search

**Happy Path:**
1. User runs `ztlctl query search "data storage" --rank-by hybrid`
2. BM25 and cosine scores min-max normalized to [0,1]
3. Blended: `(1-semantic_weight)*bm25 + semantic_weight*cosine`
4. Returns results combining keyword and semantic relevance

**Edge Cases:**
- Semantic unavailable → falls back to BM25-only
- `search.semantic_weight=0.0` → pure BM25
- `search.semantic_weight=1.0` → pure semantic

### UC-21 — Retrieve Single Item (Get)

**Happy Path:**
1. User runs `ztlctl query get ztl_a1b2c3d4`
2. Node looked up in DB
3. Body read from filesystem
4. Tags, outgoing links, incoming backlinks assembled
5. Returns full document data

**Edge Cases:**
- Note with no links → `out_links: [], in_links: []`
- Note with 10 backlinks → all listed
- Archived note → still retrievable by ID
- Body contains wikilinks → displayed as-is

**Error Paths:**
- E1: Invalid/nonexistent ID → `NOT_FOUND`

### UC-22 — List with Filters

**Happy Path:**
1. User runs `ztlctl query list --type note --status draft --tag engineering --sort recency --limit 10`
2. All filters ANDed
3. Returns matching items sorted by recency

**Edge Cases:**
- No filters → returns all non-archived items (up to limit)
- `--include-archived` → includes archived items
- `--sort priority` → reads frontmatter for priority (file I/O per task)
- `--since 2026-01-01` → only items modified after date
- `--subtype decision` → only decision notes
- `--maturity evergreen` → only evergreen garden notes
- `limit=0` → returns 0 items (SQL LIMIT 0)
- Empty vault → `count: 0, items: []`

### UC-23 — Work Queue

**Happy Path:**
1. Vault has 5 tasks: 2 inbox, 2 active, 1 done
2. User runs `ztlctl query work-queue`
3. Only inbox/active/blocked tasks returned (done excluded)
4. Sorted by score descending (quick wins first)

**Edge Cases:**
- No tasks → `count: 0, items: []`
- All tasks done/dropped → empty queue
- `--space ops` filter → only ops/ tasks
- Equal scores → secondary sort by creation date

### UC-24 — Decision Support

**Happy Path:**
1. Vault has decisions, notes, references on topic "architecture"
2. User runs `ztlctl query decision-support --topic architecture`
3. Returns partitioned: `decisions: [proposed, accepted]`, `notes: [related]`, `references: [evidence]`
4. Counts summary included

**Edge Cases:**
- No topic filter → aggregates all decisions
- No decisions in vault → `decisions: []`
- Topic with no content → all sections empty

---

## Category 4: Content Updates & Lifecycle

### UC-25 — Update Content Metadata

**Happy Path:**
1. User runs `ztlctl update ztl_a1b2c3d4 --title "New Title" --tags "new-tag"`
2. Node found in DB
3. Validation passes
4. Frontmatter updated with new title and tags
5. FTS5 re-indexed (title changed)
6. Tags re-indexed (tags changed)
7. `post_update` event dispatched
8. Returns `fields_changed: ["title", "tags"]`

**Edge Cases:**
- Changing only tags → body untouched, only tag index updated
- Changing topic → file may move to different subdirectory
- Immutable fields (`id`, `type`, `created`) in changes → warned, not applied
- Empty tags list → removes all tags
- Updating archived content → allowed

**Error Paths:**
- E1: Content not found → `NOT_FOUND`
- E2: Unknown type/subtype → `UNKNOWN_TYPE`
- E3: Validation failure → `VALIDATION_FAILED`
- E4: No changes supplied → `no_changes`

### UC-26 — Note Status Transitions

**Happy Path:**
1. Note has 0 outgoing links → status is `draft`
2. User adds 1 link via update or reweave
3. `compute_note_status()` returns `linked`
4. Status automatically updated in frontmatter and DB
5. User adds 2 more links (total 3)
6. Status becomes `connected`

**Edge Cases:**
- Removing links: connected (3 links) → remove 1 → still connected (2 ≥ threshold? No, threshold is 3, so goes back to linked)
- Actually: `NOTE_CONNECTED_THRESHOLD = 3`, so 2 links → `linked`
- 0 links → `draft` regardless of previous status
- Status never set manually — always computed

### UC-27 — Task Status Transitions

**Happy Path:**
1. Task created as `inbox`
2. `ztlctl update TASK-0001 --status active` → success
3. `ztlctl update TASK-0001 --status blocked` → success
4. `ztlctl update TASK-0001 --status active` → success (back from blocked)
5. `ztlctl update TASK-0001 --status done` → success (terminal)

**Edge Cases:**
- `inbox → done` → `INVALID_TRANSITION` (must go through active first)
- `done → active` → `INVALID_TRANSITION` (terminal state)
- `dropped → active` → `INVALID_TRANSITION` (terminal state)
- `blocked → done` → `INVALID_TRANSITION` (must go through active first)

**Error Paths:**
- E1: Invalid transition → `INVALID_TRANSITION` with current and attempted status in message

### UC-28 — Reference Status Transitions

**Happy Path:**
1. Reference created as `captured`
2. `ztlctl update ref_abc12345 --status annotated` → success

**Edge Cases:**
- `annotated → captured` → `INVALID_TRANSITION` (no backward)
- `annotated` is terminal

### UC-29 — Decision Lifecycle

**Happy Path:**
1. Decision created as `proposed`
2. `ztlctl update ztl_abc12345 --status accepted` → success
3. Decision is now immutable (body locked)
4. Only `tags`, `aliases`, `topic`, `status`, `superseded_by`, `modified` changeable
5. `ztlctl update ztl_abc12345 --status superseded` → `INVALID_TRANSITION` (must use supersede command)

**Edge Cases:**
- After acceptance: `--title "New Title"` → `VALIDATION_FAILED` (immutable)
- After acceptance: `--body "New body"` → `VALIDATION_FAILED` (immutable)
- After acceptance: `--tags "new-tag"` → success (allowed)
- `proposed → superseded` → `INVALID_TRANSITION` (must accept first)

**Error Paths:**
- E1: Body modification after acceptance → `VALIDATION_FAILED`
- E2: Invalid transition → `INVALID_TRANSITION`

### UC-30 — Archive Content

**Happy Path:**
1. User runs `ztlctl archive ztl_a1b2c3d4`
2. `archived: true` set in file frontmatter and DB
3. Edges preserved in DB
4. `post_close` event dispatched
5. Node excluded from default queries

**Edge Cases:**
- Archive already-archived content → idempotent (no error)
- Archive then query without `--include-archived` → not found in list
- Archive then `query get <id>` → still retrievable by direct ID
- Backlinks from archived nodes still visible on linked nodes

**Error Paths:**
- E1: Content not found → `NOT_FOUND`

### UC-31 — Supersede Decision

**Happy Path:**
1. Old decision `ztl_old12345` in `accepted` status
2. New decision `ztl_new12345` exists
3. User runs `ztlctl supersede ztl_old12345 ztl_new12345`
4. Old: `status=superseded`, `superseded_by=ztl_new12345`
5. New should have `supersedes=ztl_old12345` (set during creation or update)

**Edge Cases:**
- Old decision in `proposed` → `INVALID_TRANSITION` (must be accepted first)
- Supersession chain: A → B → C (A superseded by B, B superseded by C)
- Cyclic supersession (A supersedes B, B supersedes A) → detected by integrity check

**Error Paths:**
- E1: Old not found → `NOT_FOUND`
- E2: Old in wrong status → `INVALID_TRANSITION`

### UC-32 — Garden Maturity Progression

**Happy Path:**
1. Note created with `maturity=seed`
2. `ztlctl update ztl_abc --maturity budding` → success
3. Body now protected: `--body "new text"` → warned, body unchanged
4. `ztlctl update ztl_abc --maturity evergreen` → success (terminal)

**Edge Cases:**
- `evergreen → seed` → allowed? (maturity transitions are advisory, not enforced)
- Setting maturity on existing note without maturity → activates body protection
- Removing maturity (set to null) → deactivates body protection
- Body change attempted on garden note → warning, not error

---

## Category 5: Graph Operations

### UC-33 — Related Content (Spreading Activation)

**Happy Path:**
1. Node A linked to B and C; B linked to D
2. `ztlctl graph related ztl_A --depth 2`
3. Hop 1: B (score=0.5), C (score=0.5)
4. Hop 2: D (score=0.25, via B)
5. Results sorted by score descending

**Edge Cases:**
- depth=1 → only direct neighbors
- depth=5 → deep traversal (max allowed)
- Isolated node (no edges) → `count: 0, items: []`
- Undirected: follows both incoming and outgoing edges
- `--top 1` → only highest-scored result
- Circular graph (A→B→C→A) → visited set prevents infinite loops

**Error Paths:**
- E1: Node not in graph → `NOT_FOUND`

### UC-34 — Theme/Community Detection

**Happy Path:**
1. Vault has 3 clusters of connected notes
2. `ztlctl graph themes`
3. Leiden algorithm detects 3 communities
4. Each community has members list and size

**Edge Cases:**
- Single node → 1 community of size 1
- Fully connected graph → 1 community
- No edges → each node is its own community
- Leiden unavailable → Louvain fallback with warning

### UC-35 — PageRank Ranking

**Happy Path:**
1. `ztlctl graph rank --top 5`
2. PageRank computed on directed graph
3. Returns top 5 by importance score

**Edge Cases:**
- Empty graph → `count: 0`
- Single node → PageRank = 1.0
- `--top` exceeds node count → returns all nodes

### UC-36 — Path Finding

**Happy Path:**
1. `ztlctl graph path ztl_A ztl_D`
2. Shortest path found: A → B → D (length=2)
3. Returns step-by-step chain

**Edge Cases:**
- Source = target → length=0, steps=[source]
- Multiple shortest paths → one returned (NetworkX picks first)
- Undirected: A→B edge means B→A path also valid

**Error Paths:**
- E1: Source/target not in graph → `NOT_FOUND`
- E2: No path exists (disconnected components) → `NO_PATH`

### UC-37 — Structural Gaps

**Happy Path:**
1. `ztlctl graph gaps --top 10`
2. Constraint centrality computed
3. High constraint nodes = tightly embedded = potential silos

**Edge Cases:**
- Isolated nodes → NaN constraint (filtered out)
- Degree-1 nodes → Inf constraint (filtered out)
- All nodes equally connected → similar constraint values

### UC-38 — Bridge Detection

**Happy Path:**
1. `ztlctl graph bridges --top 10`
2. Betweenness centrality computed
3. High betweenness = cluster connectors

**Edge Cases:**
- No bridges (single cluster) → all low centrality
- Star topology → center node has highest centrality
- Linear chain → middle nodes have highest centrality

### UC-39 — Unlink Nodes

**Happy Path:**
1. A has frontmatter `links.relates: [ztl_B]` and body `[[B Title]]`
2. `ztlctl graph unlink ztl_A ztl_B`
3. Edge removed from DB
4. `links.relates` updated in frontmatter
5. `[[B Title]]` removed from body
6. FTS5 re-indexed (body changed)

**Edge Cases:**
- `--both` flag → removes A→B and B→A edges
- Garden note (maturity set) as source → body untouched, only frontmatter updated, warning emitted
- Multiple edge types between same nodes → all removed
- Body has multiple wikilinks to same target → all removed

**Error Paths:**
- E1: Source not found → `NOT_FOUND`
- E2: Target not found → `NOT_FOUND`
- E3: No link between nodes → `NO_LINK`

### UC-40 — Materialize Metrics

**Happy Path:**
1. `ztlctl graph materialize`
2. PageRank, degree_in, degree_out, betweenness, cluster_id computed
3. Written to nodes table columns
4. Returns `nodes_updated: N`

**Edge Cases:**
- Empty graph → `nodes_updated: 0`
- Graph changed since last materialize → fresh computation
- Bidirectional edges flagged in edges table

---

## Category 6: Reweave (Link Discovery)

### UC-41 — Reweave — Discover Links

**Happy Path:**
1. Note `ztl_A` has no links, vault has 10 other notes
2. `ztlctl reweave --id ztl_A`
3. 4-signal scoring against all candidates
4. 3 candidates score above 0.6 threshold
5. `max_links_per_note` allows all 3
6. Frontmatter `links.relates` updated
7. Body gets wikilinks (if not garden note)
8. Operations logged in `reweave_log`
9. `post_reweave` event dispatched

**Edge Cases:**
- No `--id` → targets most recently modified non-archived node
- All candidates below threshold → no links added, `count: 0`
- `max_links_per_note=5` and note already has 4 links → max 1 new link
- Archived candidates excluded
- Self excluded from candidates
- Already-linked candidates excluded
- `min_score_override=0.3` → overrides config threshold for this run
- BM25 scoring uses quoted words (OR-joined) to prevent FTS5 operator interpretation

**Error Paths:**
- E1: Content ID not found → `NOT_FOUND`
- E2: `reweave.enabled=false` → no-op (gated)

### UC-42 — Reweave — Dry Run

**Happy Path:**
1. `ztlctl reweave --dry-run --id ztl_A`
2. Same scoring as UC-41
3. Returns `suggestions` instead of `connected`
4. No files modified, no DB changes, no audit log

**Edge Cases:**
- Dry run with no candidates → `suggestions: []`
- Dry run shows what would happen without commitment

### UC-43 — Reweave — Prune Stale Links

**Happy Path:**
1. Note `ztl_A` has 5 links, 2 score below threshold after re-scoring
2. `ztlctl reweave --prune --id ztl_A`
3. 2 stale links removed from frontmatter and edges
4. Body wikilinks removed (if not garden note)
5. Audit trail logged

**Edge Cases:**
- No stale links → `pruned: []`
- All links stale → all removed
- `--dry-run --prune` → preview stale links without removing
- Garden note → body untouched, only frontmatter links removed

### UC-44 — Reweave — Undo

**Happy Path:**
1. Previous reweave added 3 links
2. `ztlctl reweave --undo`
3. Latest batch (same timestamp) reversed
4. Links removed from frontmatter and edges
5. Log entries marked `undone=true`

**Edge Cases:**
- `--undo-id 42` → undoes specific reweave_log entry
- Already undone → `NOT_FOUND`
- No reweave history → `NO_HISTORY`
- Undo after content was further modified → best-effort removal

---

## Category 7: Session Management

### UC-45 — Start Session

**Happy Path:**
1. No active session
2. `ztlctl agent session start "Research ML"`
3. `LOG-0001` created with sequential ID
4. JSONL file created at `ops/logs/LOG-0001.jsonl`
5. Initial entry written to JSONL
6. Nodes row: type=log, status=open
7. `post_session_start` event dispatched

**Edge Cases:**
- First session ever → `LOG-0001`
- 10th session → `LOG-0010`
- Topic with special characters → preserved in frontmatter

**Error Paths:**
- E1: Another session already open → `ACTIVE_SESSION_EXISTS`

### UC-46 — Log Session Entries

**Happy Path:**
1. Active session LOG-0001 exists
2. `ztlctl agent session log "Found relevant paper" --pin --cost 500`
3. Entry appended to JSONL: `{timestamp, message, pin:true, cost:500}`
4. Entry inserted to `session_logs` DB table
5. Cost accumulated for budget tracking

**Edge Cases:**
- No pin, no cost → defaults: pin=false, cost=0
- `--references "ztl_A,ref_B"` → links entries to content
- `--detail "extra context"` → additional detail field
- Multiple log entries → all appended chronologically

**Error Paths:**
- E1: No active session → `NO_ACTIVE_SESSION`

### UC-47 — Close Session (with Enrichment)

**Happy Path:**
1. Active session with 5 created notes
2. `ztlctl agent session close --summary "Explored ML topics"`
3. Pipeline: (1) Log close entry, (2) Cross-session reweave on session notes, (3) Orphan sweep for 0-link notes, (4) Integrity check, (5) Graph materialization, (6) Drain event WAL
4. `post_session_close` event dispatched with stats
5. Returns enrichment summary

**Edge Cases:**
- `session.close_reweave=false` → reweave step skipped
- `session.close_orphan_sweep=false` → orphan sweep skipped
- `session.close_integrity_check=false` → integrity check skipped
- No notes created during session → enrichment steps find nothing
- Event bus has pending/failed events → drain retries them

**Error Paths:**
- E1: No active session → `NO_ACTIVE_SESSION`

### UC-48 — Reopen Session

**Happy Path:**
1. Session LOG-0001 is closed
2. No other active session
3. `ztlctl agent session reopen LOG-0001`
4. Status: `closed → open`
5. Reopen entry appended to JSONL

**Edge Cases:**
- Reopen then close again → second close runs enrichment pipeline again
- Reopen → create more notes → close → enrichment covers new notes

**Error Paths:**
- E1: Session not found → `NOT_FOUND`
- E2: Session already open → `ALREADY_OPEN`
- E3: Different session already active → `ACTIVE_SESSION_EXISTS`

### UC-49 — Agent Context Assembly

**Happy Path:**
1. Active session on topic "ML"
2. `ztlctl agent context --topic ML --budget 8000`
3. Layer 0: identity.md + methodology.md (always)
4. Layer 1: session summary, recent decisions, work queue, log entries
5. Layer 2: ML-scoped notes/references/decisions (budget-dependent)
6. Layer 3: Graph-adjacent to layer 2 items (budget-dependent)
7. Layer 4: Background signals (budget-dependent)
8. Returns total_tokens, budget, remaining, pressure

**Edge Cases:**
- Budget=1000 → only layers 0-1 fit, layers 2-4 empty
- No topic → layer 2 uses general content
- Pressure: >15% remaining → "normal", 0-15% → "caution", <0% → "exceeded"
- `--ignore-checkpoints` → reads full session history (not from checkpoint)

**Error Paths:**
- E1: No active session → `NO_ACTIVE_SESSION`

### UC-50 — Agent Brief/Orientation

**Happy Path:**
1. `ztlctl agent brief`
2. Returns: vault stats (10 notes, 3 references, 5 tasks), active session info, recent decisions, work queue count
3. No session required — works without active session

**Edge Cases:**
- No active session → session info omitted, stats still returned
- Empty vault → all counts zero
- Recent decisions → last N accepted decisions

### UC-51 — Session Cost Tracking

**Happy Path (query mode):**
1. Active session with 3 log entries (costs: 100, 200, 300)
2. `ztlctl agent session cost`
3. Returns `total_cost: 600, entry_count: 3`

**Happy Path (report mode):**
1. `ztlctl agent session cost --report 1000`
2. Returns `total_cost: 600, budget: 1000, remaining: 400, over_budget: false`

**Edge Cases:**
- No cost entries → `total_cost: 0`
- Over budget → `over_budget: true, remaining: -100`
- `--report 0` → immediately over budget

**Error Paths:**
- E1: No active session → `NO_ACTIVE_SESSION`

---

## Category 8: Integrity & Maintenance

### UC-52 — Integrity Check

**Happy Path:**
1. `ztlctl check`
2. 4-category scan finds: 1 node without file, 1 orphaned edge
3. Returns `issues: [{severity:"error", category:"db_file", ...}, ...]`

**Edge Cases:**
- Clean vault → `issues: [], count: 0`
- Mixed severities: errors and warnings
- Each issue has optional `fix_action` hint
- Check is read-only — no modifications

### UC-53 — Integrity Fix (Safe)

**Happy Path:**
1. `ztlctl check --fix`
2. Backup created: `.ztlctl/backups/ztlctl-20260227-120000.db`
3. Safe fixes applied: orphan rows removed, dangling edges cleaned, FTS resynced
4. Returns `fixes: [{action, detail}, ...], count: N`

**Edge Cases:**
- No issues → no fixes, backup still created
- Body text never modified (invariant)
- Backup retention: old backups cleaned per `check.backup_retention_days`

### UC-54 — Integrity Fix (Aggressive)

**Happy Path:**
1. `ztlctl check --fix --level aggressive`
2. Backup created
3. Safe fixes + edge reindexing + frontmatter reordering
4. Returns extended fix list

**Edge Cases:**
- May remove orphaned edges that have no valid source/target nodes
- Frontmatter reordered to canonical key order

### UC-55 — Full Rebuild from Files

**Happy Path:**
1. `ztlctl check --rebuild`
2. DB tables cleared (nodes, edges, tags, FTS)
3. Pass 1: walk all content files, parse frontmatter, insert nodes
4. Pass 2: resolve links, create edges
5. Graph metrics materialized
6. Returns `nodes_indexed: N, edges_created: M, tags_found: T`

**Edge Cases:**
- Files with invalid frontmatter → skipped with warning
- No content files → empty DB rebuilt
- JSONL log files → parsed differently from markdown
- Sequential ID counters recalculated from existing IDs

### UC-56 — Rollback to Backup

**Happy Path:**
1. `ztlctl check --rollback`
2. Latest backup found in `.ztlctl/backups/`
3. Current DB replaced with backup

**Edge Cases:**
- Multiple backups → latest timestamp selected
- Rollback then check → may find new inconsistencies (files changed since backup)

**Error Paths:**
- E1: No backup directory → `NO_BACKUPS`
- E2: No backup files in directory → `NO_BACKUPS`

### UC-57 — Database Upgrade

**Happy Path (check pending):**
1. `ztlctl upgrade` (check mode)
2. Walks Alembic revision graph
3. Returns `pending_count: 2, pending: [{revision, description}]`

**Happy Path (apply):**
1. `ztlctl upgrade --apply`
2. Backup created
3. Pending migrations applied
4. Integrity validated after migration
5. Returns `applied_count: 2, current: "rev123", message: "..."`

**Edge Cases:**
- Pre-Alembic vault (tables exist, no version tracking) → STAMP instead of CREATE TABLE
- No pending migrations → `pending_count: 0`
- Integrity check after migration finds issues → warning in result

**Error Paths:**
- E1: Migration check fails → `CHECK_FAILED`
- E2: Backup fails → `BACKUP_FAILED`
- E3: Migration fails → `MIGRATION_FAILED` with backup path in detail
- E4: Stamp fails → `STAMP_FAILED`

---

## Category 9: Export

### UC-58 — Export Markdown

**Happy Path:**
1. `ztlctl export markdown --output /tmp/export`
2. All content files copied preserving relative paths
3. `notes/engineering/ztl_a1b2c3d4.md` → `/tmp/export/notes/engineering/ztl_a1b2c3d4.md`
4. Returns `file_count: N`

**Edge Cases:**
- Empty vault → `file_count: 0`
- Output directory doesn't exist → created
- Output directory has existing files → overwritten

### UC-59 — Export Indexes

**Happy Path:**
1. `ztlctl export indexes --output /tmp/indexes`
2. `index.md` — master with counts
3. `by-type/note.md`, `by-type/reference.md`, etc.
4. `by-topic/engineering.md`, `by-topic/math.md`, etc.
5. Returns `files_created, node_count`

**Edge Cases:**
- No topics → no `by-topic/` files
- Single content type → only that `by-type/` file

### UC-60 — Export Graph (DOT)

**Happy Path:**
1. `ztlctl export graph --format dot`
2. Returns DOT language string in `data.content`
3. Nodes labeled with title, edges show relationship types

**Edge Cases:**
- Empty graph → minimal DOT with no nodes
- Special characters in titles → escaped

**Error Paths:**
- E1: Unknown format → `INVALID_FORMAT`

### UC-61 — Export Graph (JSON)

**Happy Path:**
1. `ztlctl export graph --format json`
2. Returns `{"nodes": [...], "links": [...]}` in `data.content`
3. D3/vis.js compatible format

**Edge Cases:**
- Same as UC-60

---

## Category 10: Extensions & Integrations

### UC-62 — MCP — Creation Tools

**Happy Path:**
1. MCP server running via `ztlctl serve`
2. Client calls `create_note(title="Test", tags=["research"])`
3. Delegates to CreateService.create_note()
4. Returns ServiceResult JSON

**Edge Cases:**
- MCP extra not installed → `ztlctl serve` errors with helpful message
- All creation tools mirror CLI behavior
- `create_log(topic)` delegates to SessionService.start (not CreateService)

### UC-63 — MCP — Query Tools

**Happy Path:**
1. Client calls `search(query="database", limit=5)`
2. Delegates to QueryService.search()
3. Returns search results

**Edge Cases:**
- `agent_context` dual-mode: tries SessionService.context first, falls back to QueryService if no session
- Fallback context includes total_items, recent, work_queue

### UC-64 — MCP — Lifecycle Tools

**Happy Path:**
1. Client calls `update_content(content_id="ztl_abc", changes={"tags":["new"]})`
2. Same validation as CLI
3. Returns ServiceResult

**Edge Cases:**
- `close_content` delegates to archive (not session close)
- `session_close` is separate tool for closing sessions

### UC-65 — MCP — Resources

**Happy Path:**
1. Client reads `ztlctl://context`
2. Returns combined identity + methodology + overview JSON
3. Client reads `ztlctl://self/identity`
4. Returns identity.md markdown content

**Edge Cases:**
- `ztlctl://work-queue` → delegates to QueryService.work_queue
- `ztlctl://topics` → scans notes/ for subdirectories
- `ztlctl://overview` → vault counts by type + recent items

### UC-66 — MCP — Prompts

**Happy Path:**
1. Client uses `research_session(topic="ML")`
2. Returns 5-step structured workflow prompt

**Edge Cases:**
- `vault_orientation()` → reads identity + methodology + overview
- `decision_record(topic)` → guides structured decision documentation

### UC-67 — Plugin Discovery & Registration

**Happy Path:**
1. Vault has `.ztlctl/plugins/my_plugin.py` with `@hookimpl` methods
2. pip-installed plugin registered via `ztlctl.plugins` entry point
3. `PluginManager.discover_and_load()` finds both
4. `register_content_models()` called → custom subtypes merged into `CONTENT_REGISTRY`

**Edge Cases:**
- No plugins directory → only entry-point plugins loaded
- Plugin with syntax error → skipped with warning
- Duplicate plugin names → last registration wins
- `register_content_models()` returns None → no custom types

### UC-68 — Plugin Lifecycle Hooks

**Happy Path:**
1. Plugin implements `post_create` hook
2. User creates note
3. Event bus dispatches `post_create`
4. Plugin's `post_create()` called with content_type, content_id, title, path, tags

**Edge Cases:**
- Plugin raises exception → caught, logged as warning, never blocks operation
- Multiple plugins implement same hook → all called (pluggy fan-out)
- Hook signatures must match spec exactly (pluggy validation)

### UC-69 — Git Plugin

**Happy Path (batch mode — default):**
1. Session starts
2. 3 notes created → `git add` after each
3. Session closes → `git commit` with summary, optionally `git push`

**Happy Path (immediate mode):**
1. `git.batch_commits=false`
2. Note created → `git add` + `git commit` immediately

**Edge Cases:**
- No git installed → all git operations silently fail
- `git.auto_ignore=true` at init → `.gitignore` created
- `git.auto_push=false` (default) → no push after commit
- Git operation fails (e.g., dirty working tree) → warning, never error

### UC-70 — Event Bus Dispatch

**Happy Path:**
1. CreateService calls `_dispatch_event("post_create", payload)`
2. EventBus writes WAL entry (status=pending)
3. ThreadPoolExecutor runs hook asynchronously
4. Hook succeeds → status=completed

**Edge Cases:**
- Hook fails → retries (max 3), then dead_letter
- `--sync` flag → synchronous execution (no ThreadPoolExecutor)
- Session close → drain() retries pending/failed events
- Dead-letter events: logged, never retried
- EventBus not initialized (e.g., --help) → _dispatch_event is no-op

### UC-71 — Vector/Semantic Search

**Happy Path:**
1. `ztlctl[semantic]` installed, `search.semantic_enabled=true`
2. `VectorService.is_available()` returns true
3. `VectorService.index_node()` embeds content into vec_items
4. `VectorService.search_similar("query")` returns KNN results

**Edge Cases:**
- Dependencies missing → `is_available()` returns false → all methods no-op
- `reindex_all()` batch re-embeds all non-archived nodes
- Embedding model configurable via `search.embedding_model`
- First use may download model (slow)

**Error Paths:**
- E1: `SEMANTIC_UNAVAILABLE` if deps missing

---

## Category 11: Cross-Cutting Concerns

### UC-72 — JSON Output Mode

**Happy Path:**
1. `ztlctl --json create note "Test"`
2. Output: `{"ok":true, "op":"create_note", "data":{...}, "warnings":[], "error":null, "meta":null}`
3. Machine-parseable, no ANSI codes

**Edge Cases:**
- Error result → JSON to stderr, exit code 1
- Combined with `--verbose` → meta includes telemetry
- Warnings included in JSON (not separate stderr lines)

### UC-73 — Quiet/Verbose Output

**Happy Path (quiet):**
1. `ztlctl -q create note "Test"` → `OK: create_note`
2. `ztlctl -q query list` → one ID per line

**Happy Path (verbose):**
1. `ztlctl -v create note "Test"`
2. Extra columns in tables
3. Telemetry span tree rendered with color-coded durations

**Edge Cases:**
- `-q` and `-v` are mutually exclusive (last flag wins)
- `-q` error → `ERROR: op — message`
- `-v` error → full error details + stack-like info

### UC-74 — Non-Interactive Mode

**Happy Path:**
1. `ztlctl --no-interact init --name "vault" --client obsidian --tone minimal`
2. No prompts fired
3. Missing optional fields use defaults

**Edge Cases:**
- Missing required fields without `--no-interact` → prompts for input
- Combined with `--json` → fully scriptable pipeline
- Init without name flag in `--no-interact` → uses default name

### UC-75 — Telemetry — Verbose Spans

**Happy Path:**
1. `ztlctl -v create note "Test"`
2. `@traced` creates root span: `CreateService.create_note`
3. `trace_span()` creates children: validate, generate, persist, index
4. Spans rendered as tree with durations
5. Color coding: >1s red, >100ms yellow, <100ms dim

**Edge Cases:**
- Telemetry disabled (no `-v`) → zero overhead (~10ns ContextVar check)
- Cross-service calls create independent root spans
- Span data injected into `ServiceResult.meta.telemetry`

### UC-76 — Telemetry — JSON Logs

**Happy Path:**
1. `ztlctl --log-json create note "Test"`
2. Structured JSON lines emitted to stderr
3. Each line: `{"event":"...", "level":"...", "timestamp":"...", ...}`
4. stdout contains normal output (Rich or JSON depending on `--json`)

**Edge Cases:**
- `--log-json` + `--json` → stderr=JSON logs, stdout=JSON result (dual machine-parseable)
- `--log-json` without `--verbose` → WARNING-level logs only
- `--log-json` with `--verbose` → DEBUG-level logs (more verbose)
- Non-TTY stderr → no ANSI in JSON renderer
