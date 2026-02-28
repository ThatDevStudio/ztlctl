# Category 6: Reweave — BAT Critique

**Tests**: BAT-68 through BAT-73
**Vault(s)**: `.bat/bat-68/` (shared for 68, 69, 71, 72), `.bat/bat-70/`, `.bat/bat-73/`
**Date**: 2026-02-27

## Summary

| Test | Description | Result |
|------|-------------|--------|
| BAT-68 | Reweave — Discover Links | PASS |
| BAT-69 | Reweave — Dry Run | PASS |
| BAT-70 | Reweave — No Candidates | PASS |
| BAT-71 | Reweave — Prune | PASS |
| BAT-72 | Reweave — Undo Latest | PASS |
| BAT-73 | Reweave — Undo No History | PASS |

**Overall: 6/6 PASS**

## Detailed Observations

### BAT-68: Reweave — Discover Links

The reweave command (with `--auto-link-related`) successfully identified and linked related notes based on shared tags. The 4-signal scoring system (lexical, tag_overlap, graph_proximity, topic) correctly prioritized notes with the most tag overlap. Out of 5 notes sharing `shared-tag`, it connected the target (Machine Learning Basics, tags: shared-tag, ml) to Reinforcement Learning (shared-tag, ml, rl) and Deep Learning Networks (shared-tag, ml, neural) — the two notes sharing the `ml` tag.

**Observation**: The response shape when `--auto-link-related` is used returns `connected` (applied links) rather than `suggestions` (proposed links). This is intentional — auto-link bypasses confirmation and applies directly. However, the `connected` items do not include individual `score` or `signals` breakdowns, only `id` and `title`. Including scores in the response would aid auditability without requiring a separate dry-run call.

### BAT-69: Reweave — Dry Run

Dry-run correctly returned suggestions without modifying the filesystem or database. The response includes the full signal breakdown per suggestion (`lexical`, `tag_overlap`, `graph_proximity`, `topic`), which is excellent for transparency.

**Verification**: Post-run inspection of the note's frontmatter confirmed `links: {}` was unchanged. The graph already had edges from BAT-68's reweave, but no new edges were introduced by the dry-run.

**Observation**: The `dry_run: true` flag in the response payload is a clean programmatic indicator. Good design for automation consumers.

### BAT-70: Reweave — No Candidates

Single-note vault correctly returned `count: 0` with an empty `suggestions` array. No error, no warning — a clean "nothing to do" response. This is the right behavior: zero candidates is a valid result, not an error.

### BAT-71: Reweave — Prune

Prune returned 0 pruned items since all links were freshly created and still relevant. The `op` field correctly changes to `"prune"` (distinct from `"reweave"`), which aids programmatic routing.

**Limitation**: This test could not exercise actual pruning because there were no stale links to remove. A more rigorous test would create links, delete one of the target notes, then run prune. The prune logic was not stress-tested here.

### BAT-72: Reweave — Undo Latest

Undo successfully reversed the 2 links created in BAT-68. The audit trail is thorough — each undone entry includes `log_id`, `source_id`, `target_id`, the original `action` ("add"), and the reversal `reversed` ("remove"). Post-verification confirmed the graph was empty for the target note.

**Strength**: The undo mechanism is fully deterministic and traceable. The audit trail in the response allows exact reconstruction of what was reversed.

### BAT-73: Reweave — Undo No History

Correctly returned exit code 1 with error code `NO_HISTORY` and a clear message. The error contract is clean and machine-parseable.

**Issue (minor)**: Error output appears duplicated — the same JSON block is printed twice. This is because `emit()` writes to stderr on failure (line 75 of `_context.py`), and Click's error handling may echo the SystemExit. This affects all error responses across the CLI, not just reweave. See cross-cutting concerns below.

## Cross-Cutting Concerns

### 1. Duplicated Error Output

All error responses (BAT-73 and others) emit the JSON error payload twice when `--json` is used. The `emit()` method writes to stderr, then raises `SystemExit(1)`. The bash tool's stderr capture shows the block twice, suggesting the JSON is written to both stderr and stdout, or Click's exit handling re-emits. For agents or scripts parsing JSON from stderr, this duplication could cause parse errors if they naively read all of stderr as a single JSON document.

**Recommendation**: Investigate whether a `\n`-delimited parse or a single-write approach would eliminate the duplication. Alternatively, document that error JSON goes to stderr only and tools should parse the first complete JSON object.

### 2. Response Schema Inconsistency

The reweave command uses different `data` shapes depending on the operation mode:

| Mode | Data key | Items include scores? |
|------|----------|-----------------------|
| `--dry-run` | `suggestions` | Yes (score + signals) |
| `--auto-link-related` | `connected` | No (id + title only) |
| No flags (interactive) | `suggestions` | Yes (score + signals) |
| `--prune` | `pruned` | N/A |
| `--undo` | `undone` | N/A |

This is reasonable from a semantic standpoint (suggestions vs. connected vs. pruned are different concepts), but agents consuming JSON programmatically must handle 5 different response shapes from a single command. A wrapper `items` key with a `mode` discriminator would simplify parsing.

### 3. Tag Format Warnings

All note creation commands emit `WARNING: Tag 'X' missing domain/scope format` for simple tags. These warnings are informational and do not block creation. This is correct behavior, but in automated pipelines where tags may intentionally lack the `domain/scope` format, the warnings add noise. A `--no-warn-tags` flag or a config option to suppress tag format warnings would be useful for agents.

## Verdict

The reweave subsystem is solid. All core operations (discover, dry-run, prune, undo) work correctly with proper error handling. The 4-signal scoring system provides excellent transparency. The undo audit trail is thorough. The main areas for improvement are cosmetic: duplicated error output and response schema inconsistency across modes.
