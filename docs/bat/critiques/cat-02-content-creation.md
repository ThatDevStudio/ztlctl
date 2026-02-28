# Category 2: Content Creation — BAT Critique

**Tests**: BAT-10 through BAT-25
**Score**: 15/16 PASS

## Test Results

| BAT | Test | Result |
|-----|------|--------|
| BAT-10 | Create Plain Note | **PASS** |
| BAT-11 | ID Collision | **PASS** |
| BAT-12 | Knowledge Note | **PASS** |
| BAT-13 | Decision Note | **PASS** |
| BAT-14 | Article Reference | **PASS** |
| BAT-15 | Tool Reference | **PASS** |
| BAT-16 | Spec Reference | **PASS** |
| BAT-17 | Create Task | **PASS** |
| BAT-18 | Sequential Task IDs | **PASS** |
| BAT-19 | Batch Success | **PASS** |
| BAT-20 | Batch All-or-Nothing Failure | **FAIL** |
| BAT-21 | Batch Partial Mode | **PASS** |
| BAT-22 | Batch Invalid File | **PASS** |
| BAT-23 | Garden Seed | **PASS** |
| BAT-24 | Post-Create Reweave | **PASS** |
| BAT-25 | Reweave Disabled | **PASS** |

## Detailed Evaluation

### BAT-10: Create Plain Note — PASS
- **Correctness**: Note created with correct frontmatter (id, type:note, status:draft, title, tags, topic). File written to disk, indexed in DB with FTS5, tags registered.
- **Output quality**: JSON envelope is clean (`{ok, op, data, warnings, error, meta}`). Data includes id, path, title, type.
- **UX**: Fast execution, clear output.
- **Feature value**: Core functionality — essential and well-implemented.

### BAT-11: ID Collision — PASS
- **Correctness**: Correctly rejects duplicate title with `ID_COLLISION` error code.
- **UX**: Error message is clear about what happened and why.
- **Feature value**: Important safety feature. Content-hash IDs from titles make collisions predictable and informative.

### BAT-12: Knowledge Note — PASS
- **Correctness**: Created with `subtype: knowledge`. Advisory warning about missing `key_points`.
- **UX**: Warning teaches the system's conventions without blocking creation. Excellent advisory approach.
- **Feature value**: Subtypes provide meaningful classification without imposing rigid structure.

### BAT-13: Decision Note — PASS
- **Correctness**: Frontmatter has `subtype: decision`, `status: proposed`. Body contains all required sections (Context, Choice, Rationale, Alternatives, Consequences).
- **Feature value**: The ADR template scaffolding is impressive — one command produces a well-structured architectural decision record.

### BAT-14–16: Reference Subtypes — ALL PASS
- **Correctness**: Article, tool, and spec subtypes all created correctly with appropriate frontmatter.
- **Feature value**: Classification-only subtypes are lightweight and useful for filtering.

### BAT-17: Create Task — PASS
- **Correctness**: Task created with sequential ID (TASK-0001), correct frontmatter including priority/impact/effort matrix.
- **Feature value**: Priority matrix (priority × impact × effort) enables meaningful work-queue scoring.

### BAT-18: Sequential Task IDs — PASS
- **Correctness**: Second task gets TASK-0002. Counter increment is atomic.

### BAT-19: Batch Create — All-or-Nothing Success — PASS
- **Correctness**: Both items created, `data.created` has 2 items, `data.errors == []`.

### BAT-20: Batch Create — All-or-Nothing Failure — FAIL
- **Bug**: The batch "all-or-nothing" mode does NOT truly roll back. When item 1 fails, item 0 has already been persisted to both the filesystem and the database. The error code (`BATCH_FAILED`) and exit code (1) are correct, but side effects are not reversed. Default batch mode is functionally identical to `--partial` mode in terms of what gets written — the only difference is the error code.
- **Impact**: Agent workflows that depend on atomic batch semantics will silently get partial results.
- **Recommendation**: Implement true rollback (wrap in DB transaction, delete persisted files on failure) or document the limitation.

### BAT-21: Batch Create — Partial Mode — PASS
- **Correctness**: Good note created, bad type error captured. `data.created` has 1 item, `data.errors` has 1.

### BAT-22: Batch Create — Invalid File — PASS
- **Correctness**: Non-array JSON rejected with format error.
- **Minor note**: `op` field inconsistency: `"create_batch"` for normal ops vs `"batch_create"` for format errors.

### BAT-23: Garden Seed — PASS
- **Note**: `create note --maturity seed` is not a valid command. The correct entry point is `garden seed "Title"`. BAT spec was adapted.
- **Feature value**: Garden persona for cultivation-oriented note creation is a thoughtful UX layer.

### BAT-24: Post-Create Reweave — PASS
- **Correctness**: 4th note with shared tags/topics automatically linked to prior 3 notes. Wikilinks injected into body.
- **Feature value**: Automatic graph densification on creation is the standout feature. It turns isolated note creation into a connected knowledge graph operation.

### BAT-25: Post-Create Reweave Disabled — PASS
- **Correctness**: `--no-reweave` flag prevents link injection. No links section in frontmatter.
- **Feature value**: Essential escape hatch for when auto-linking is unwanted.

## Observations

**Strengths**:
- Consistent JSON envelope across all operations
- Advisory warning system teaches conventions without blocking work
- Post-create reweave is an impressive graph densification feature
- Content-hash IDs are deterministic and collision-informative
- Decision note scaffolding produces well-structured ADRs

**Weaknesses**:
- Batch all-or-nothing mode lacks true rollback (BAT-20 bug)
- `op` field naming inconsistency between `create_batch` and `batch_create`
- Error JSON appears duplicated on stdout + stderr for non-zero exit codes
- `garden seed` vs `create note --maturity seed` discoverability could be improved

## Usefulness Rating: 9/10

Content creation is the core value proposition and it delivers well. The create pipeline handles all content types cleanly, subtypes add meaningful classification, and post-create reweave is genuinely innovative. The batch rollback bug is the only significant issue.
