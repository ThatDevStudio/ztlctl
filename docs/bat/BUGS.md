# ztlctl BAT Bug Report

**Date**: 2026-02-27
**Version**: 0.1.0 (develop, commit 6065358)
**Source**: Business Acceptance Test suite (130 tests)

---

## Non-Passing Tests

### BUG-01: Regenerate Without Config Succeeds — BAT-06 [FAIL]

**Category**: Vault Initialization
**Severity**: Medium

**Impact**: Running `ztlctl agent regenerate` in any directory — even `/tmp` — creates orphan `self/identity.md` and `self/methodology.md` files from default settings. This pollutes arbitrary directories, gives no indication that no real vault was found, and produces identity documents referencing a phantom vault named "zettelkasten" (the default). Agent workflows that check for vault presence before regenerating will be misled by the exit 0.

**Recreation**:
```bash
mkdir /tmp/empty-dir && cd /tmp/empty-dir
ztlctl --json agent regenerate
```

**Actual Result**:
```json
{
  "ok": true,
  "op": "regenerate_self",
  "data": {
    "files_written": ["self/identity.md", "self/methodology.md"],
    "changed": ["identity.md", "methodology.md"],
    "vault_path": "/tmp/empty-dir"
  }
}
```
Exit code: 0. Two files created in `/tmp/empty-dir/self/`.

**Expected Result**:
```json
{
  "ok": false,
  "error": { "code": "NO_CONFIG", "message": "No ztlctl.toml found" }
}
```
Exit code: 1.

**Root Cause**: `regenerate_self()` uses `vault.settings` which falls back to default `ZtlSettings` when no `ztlctl.toml` is found. It does not call `check_staleness()` (which has the `NO_CONFIG` guard) and proceeds directly with defaults.

**Fix**: Add a vault-existence check in `regenerate_self()` or the Click command — verify `ztlctl.toml` exists before proceeding.

---

### BUG-02: Batch All-or-Nothing Lacks True Rollback — BAT-20 [FAIL]

**Category**: Content Creation
**Severity**: Medium

**Impact**: Agent workflows that depend on atomic batch semantics will silently get partial results. The default batch mode is advertised as "all-or-nothing" but is functionally identical to `--partial` mode in terms of what gets written — the only difference is the error code. If item 0 succeeds and item 1 fails, item 0 remains persisted to both filesystem and database despite the `BATCH_FAILED` error.

**Recreation**:
```bash
# In an initialized vault
cat > batch_fail.json <<'EOF'
[
  {"type": "note", "title": "Good Note"},
  {"type": "invalid_type", "title": "Bad Item"}
]
EOF
ztlctl --json create batch batch_fail.json
```

**Actual Result**:
```json
{
  "ok": false,
  "op": "create_batch",
  "error": { "code": "BATCH_FAILED" }
}
```
Exit code: 1. **But**: "Good Note" has been persisted to disk and indexed in the database. Running `ztlctl --json query list` returns it.

**Expected Result**:
Exit code: 1 with `BATCH_FAILED` **and** no items persisted — "Good Note" should not exist on disk or in the database.

**Root Cause**: The batch pipeline processes items sequentially, persisting each to filesystem and database individually. There is no wrapping transaction or cleanup logic when a later item fails.

**Fix**: Wrap the batch in a DB transaction, collect filesystem writes, and delete persisted files on failure. Or document the limitation and rename the default mode.

---

### BUG-03: Note Status Auto-Computation Off-by-One — BAT-43 [FAIL]

**Category**: Updates & Lifecycle
**Severity**: Medium

**Impact**: After adding wikilinks via body update, note status reflects the *previous* edge count, not the current one. Users or agents who add links and immediately check status will see stale values. The status "catches up" on the next update, which is confusing and could mislead agent decision-making (e.g., an agent checking if a note has reached "connected" status would get false negatives).

**Recreation**:
```bash
# In an initialized vault
ztlctl --json create note "A" --tags "test"
ztlctl --json create note "B" --tags "test"
ztlctl --json create note "C" --tags "test"
ztlctl --json create note "D" --tags "test"

# Get the IDs
A_ID=$(ztlctl -q query list --sort created --limit 4 | head -1)
B_ID=$(ztlctl -q query list --sort created --limit 4 | sed -n '2p')
C_ID=$(ztlctl -q query list --sort created --limit 4 | sed -n '3p')
D_ID=$(ztlctl -q query list --sort created --limit 4 | sed -n '4p')

# Step 1: A has 0 links → status should be "draft"
ztlctl --json query get $A_ID | jq .data.status  # "draft" ✓

# Step 2: Add 1 wikilink (A→B)
ztlctl --json update $A_ID --body "Link to [[$B_ID]]"
ztlctl --json query get $A_ID | jq .data.status  # "draft" ✗ (should be "linked")

# Step 3: Add 3 wikilinks (A→B, A→C, A→D)
ztlctl --json update $A_ID --body "Link to [[$B_ID]] and [[$C_ID]] and [[$D_ID]]"
ztlctl --json query get $A_ID | jq .data.status  # "linked" ✗ (should be "connected")

# Step 4: Trivial update triggers catch-up
ztlctl --json update $A_ID --tags "trigger"
ztlctl --json query get $A_ID | jq .data.status  # "connected" ✓ (finally correct)
```

**Actual Progression**: draft → draft → linked → connected (requires extra update)
**Expected Progression**: draft → linked → connected

**Root Cause**: In `UpdateService.update()`, the PROPAGATE stage (which reads edges from DB to compute status) runs **before** the INDEX stage (which deletes old edges and re-indexes new ones from wikilinks). Status is computed from stale edge data.

**Fix**: Move status recomputation after edge re-indexing, or add a second propagation pass after INDEX for notes with body changes.

---

### BUG-04: Config Priority Chain — Env Var Untested — BAT-07 [PARTIAL PASS]

**Category**: Vault Initialization
**Severity**: Low (testing gap, not a code bug)

**Impact**: The `ZTLCTL_*` environment variable override mechanism could not be verified. If env var config loading is broken, users deploying ztlctl with environment-based configuration (containers, CI) would have no way to override TOML settings without modifying files.

**Recreation**:
```bash
# In an initialized vault with ztlctl.toml containing [reweave] min_score_threshold = 0.8
ZTLCTL_REWEAVE__MIN_SCORE_THRESHOLD=0.5 ztlctl --json -v create note "Config Test"
# Inspect verbose output for resolved min_score_threshold value
```

**Actual Result**: Core note creation succeeds (exit 0). Env var override could not be verified in sandboxed test environment.

**Expected Result**: Verbose output should show `min_score_threshold = 0.5` (env var) overriding TOML value of 0.8.

**Root Cause**: Sandbox environment restricted environment variable injection during testing. The code may be correct — this is a verification gap.

**Fix**: Add a unit test that verifies `ZtlSettings.from_cli()` respects `ZTLCTL_*` env vars.

---

### BUG-05: Integrity Check Warns on Clean Vault — BAT-89 [PARTIAL PASS]

**Category**: Integrity & Maintenance
**Severity**: Low

**Impact**: A freshly created vault with standard content reports 4 warnings on `check`, making it impossible for automation to distinguish "vault is healthy" from "vault has best-practice suggestions." Any CI pipeline that checks `data.count == 0` as a health gate will always fail, even on healthy vaults. The isolated-task-node warning is particularly aggressive — a newly created task with no links is a normal state.

**Recreation**:
```bash
mkdir bat-89 && cd bat-89
ztlctl init --name "test" --client vanilla --tone minimal --topics "test" --no-workflow
ztlctl --json create note "Alpha" --tags "test"
ztlctl --json create note "Beta" --tags "test"
ztlctl --json create note "Gamma" --tags "test"
ztlctl --json create task "Test Task"
ztlctl --json check
```

**Actual Result**:
```json
{
  "ok": true,
  "data": {
    "count": 4,
    "issues": [
      {"category": "graph_health", "severity": "warning", "node_id": "TASK-0001",
       "message": "Isolated node with zero connections: TASK-0001"},
      {"category": "structural_validation", "severity": "warning", "node_id": "ztl_*",
       "message": "Tag 'test' missing domain/scope format (e.g. 'domain/scope')"},
      // ... 2 more tag warnings
    ]
  }
}
```
Exit code: 0, count: 4.

**Expected Result**: Exit code 0, `data.count == 0`, `data.issues == []`.

**Root Cause**: The check command includes tag format suggestions (warning severity) and graph health advisories (warning severity) alongside actual corruption errors. No severity filter is available.

**Fix**: Add `--min-severity error` or `--errors-only` flag to filter out advisory warnings. Or classify tag-format and isolated-node checks as `info` severity rather than `warning`.

---

### BUG-06: Plugin Custom Subtypes Blocked by CLI — BAT-111 [PARTIAL PASS]

**Category**: Plugins & Event Bus
**Severity**: Low

**Impact**: Plugin-registered content subtypes work at the service layer and via MCP tools, but are inaccessible from the CLI. The `--subtype` option on `ztlctl create note` uses a hardcoded `click.Choice(["knowledge", "decision"])`, rejecting any plugin-provided subtypes. This breaks the extensibility contract — plugins can register types but users can't use them through the primary interface.

**Recreation**:
```bash
# Create plugin that registers "experiment" subtype
mkdir -p .ztlctl/plugins
cat > .ztlctl/plugins/custom_content.py <<'EOF'
from ztlctl.plugins.hookspecs import hookimpl
from ztlctl.domain.models import NoteModel

class ExperimentModel(NoteModel):
    pass

class CustomContentPlugin:
    @hookimpl
    def register_content_models(self):
        return {"experiment": ExperimentModel}
EOF

# Try to use the registered subtype via CLI
ztlctl --json --sync create note "Experiment" --subtype experiment
```

**Actual Result**:
```
Error: Invalid value for '--subtype': 'experiment' is not one of 'knowledge', 'decision'.
```
Exit code: 2.

**Expected Result**: Note created with `subtype: experiment`, using the plugin-registered `ExperimentModel`.

**Root Cause**: `click.Choice(["knowledge", "decision"])` is hardcoded at command definition time. Plugins load after CLI parsing, so their registered subtypes are never added to the choice list.

**Fix**: Use a callback validator instead of `click.Choice`, or dynamically build the choice list from `CONTENT_REGISTRY` at command invocation time.

---

### BUG-07: MCP Transport Layer Untested — BAT-103 through BAT-109 [PARTIAL PASS × 7]

**Category**: MCP Adapter
**Severity**: Low (testing gap)

**Impact**: The 7 MCP BAT tests (BAT-103 through BAT-109) could not exercise the actual MCP transport layer because the `mcp` extra is not installed. All `_impl` functions were tested directly and work correctly, confirming the business logic is sound. However, the FastMCP decorator wrappers, argument marshaling, and MCP protocol formatting remain unverified at the integration level.

**Recreation**:
```bash
ztlctl serve --transport stdio
# Output: "MCP not installed. Install with: pip install ztlctl[mcp]"
```

**Actual Result**: All 7 tests graded PARTIAL PASS. The `_impl` functions produce correct `{ok, op, data, warnings}` responses identical to CLI output. The serve command gracefully reports the missing dependency. But no actual MCP protocol exchange was tested.

**Expected Result**: Full MCP tool invocation via stdio transport, verifying argument marshaling, response formatting, and error propagation through the MCP protocol layer.

**Root Cause**: The `mcp` package is an optional extra (`ztlctl[mcp]`) not installed in the test environment.

**Fix**: Add a CI job that installs `ztlctl[mcp]` and runs MCP integration tests via stdio transport.

---

### BUG-08: Git Plugin Without Git — Untestable — BAT-114 [SKIP]

**Category**: Plugins & Event Bus
**Severity**: Informational (testing gap only)

**Impact**: The behavior of the Git plugin when `git` is not installed could not be tested at runtime. Code inspection confirms correct error handling — all subprocess calls catch `OSError` (parent of `FileNotFoundError`) and `subprocess.CalledProcessError`, failures are logged at debug level, and no exceptions propagate to the caller.

**Recreation**: Requires a system without `git` installed, or PATH manipulation that would affect all subprocess calls.

**Actual Result**: SKIP. Verified by code inspection only.

**Expected Result**: Exit code 0, note created, no git errors visible to user.

**Root Cause**: Cannot simulate missing git binary without affecting the entire test environment.

**Fix**: The existing unit test suite covers this path. No action needed beyond confirming unit test coverage.

---

### BUG-09: Semantic Search Untestable — BAT-118 [SKIP]

**Category**: Semantic Search
**Severity**: Informational (testing gap only)

**Impact**: Semantic search with actual embeddings could not be tested because `sqlite-vec` and `sentence-transformers` extras are not installed. Graceful degradation was confirmed — `--rank-by semantic` falls back to FTS5 with a clear warning, and `vector status` reports availability correctly.

**Recreation**:
```bash
pip install ztlctl[semantic]  # or: uv add ztlctl[semantic]
ztlctl --json query search "concept" --rank-by semantic
```

**Actual Result**: SKIP. Fallback to FTS5 confirmed. `vector status` reports `available: false` with install instructions.

**Expected Result**: Results ranked by embedding cosine similarity, no fallback warning.

**Root Cause**: `sqlite-vec` and `sentence-transformers` are optional extras not installed in the test environment.

**Fix**: Add a CI job that installs `ztlctl[semantic]` and runs semantic search integration tests.

---

## Cross-Cutting Bugs (Observed During Testing)

These bugs were observed across multiple BAT tests but are not tied to specific test failures.

### BUG-10: Duplicate JSON Output on Error [CLI-Wide]

**Severity**: Low

**Impact**: When `--json` is used and a command fails (exit 1), the error JSON appears on both stdout and stderr. Agents or scripts that naively read all of stderr as a single JSON document will encounter parse errors. Affects all error paths across all categories.

**Recreation**:
```bash
ztlctl --json query get ztl_nonexistent 2>stderr.txt
cat stderr.txt  # JSON error appears here
# stdout also has the same JSON error
```

**Expected**: Error JSON on stderr only (or stdout only), not both.

**Root Cause**: The `emit()` function in `_context.py` writes to stderr on failure, and Click's error handling may re-emit to stdout, or the JSON formatter writes to both streams.

---

### BUG-11: GitPlugin.post_create() Signature Mismatch [Plugin]

**Severity**: Low

**Impact**: The Git plugin's `post_create` hook fails with `missing 1 required positional argument: 'tags'` whenever notes are created in a git-enabled vault. The failure is gracefully isolated (note creation succeeds), but the git staging/commit functionality is silently broken. This means auto-git-add on note creation does not work.

**Recreation**:
```bash
cd /path/to/git-enabled-vault
ztlctl -v --json create note "Test" --tags "test"
# stderr: "Hook post_create failed: GitPlugin.post_create() missing 1 required positional argument: 'tags'"
```

**Expected**: No hook error. Note should be staged with `git add`.

**Root Cause**: The hookspec `post_create()` signature may have been updated (adding a `tags` parameter) without updating the GitPlugin implementation, or pluggy dispatch is not passing keyword arguments correctly.

---

### BUG-12: Session Close Integrity False Positive [Sessions]

**Severity**: Low

**Impact**: Session close reports `integrity_issues: 1` in near-empty vaults, even when no actual corruption exists. This erodes trust in the integrity system and can trigger unnecessary investigation in automated workflows.

**Recreation**:
```bash
mkdir test-vault && cd test-vault
ztlctl init --name "test" --client vanilla --tone minimal --topics "test" --no-workflow
ztlctl --json session start
ztlctl --json session close
# Response includes: "integrity_issues": 1
```

**Expected**: `integrity_issues: 0` for a vault with no corruption.

---

### BUG-13: Unlink Leaves Whitespace Artifacts [Graph]

**Severity**: Low

**Impact**: When `graph unlink` removes a wikilink from body text, it leaves a double space where the `[[Link]]` was. For example, `"Links to [[Node B]] and [[Node C]]"` becomes `"Links to  and [[Node C]]"` (note double space). Cosmetic but degrades file quality over time.

**Recreation**:
```bash
# Create two linked notes
ztlctl --json create note "A" --body "Links to [[ztl_B]] and [[ztl_C]]"
ztlctl --json graph unlink ztl_A ztl_B
cat notes/ztl_A.md  # Body: "Links to  and [[ztl_C]]"
```

**Expected**: `"Links to and [[ztl_C]]"` or `"Links to [[ztl_C]]"` (smart whitespace cleanup).

---

### BUG-14: Maturity Field Missing from Query Get Response [Query]

**Severity**: Low

**Impact**: The `query get` JSON response omits the `maturity` field, even though maturity is stored in both the database and frontmatter. Programmatic consumers (agents, scripts) cannot inspect a note's garden maturity without reading the file directly.

**Recreation**:
```bash
ztlctl --json create note "Garden Note" --maturity seed
ztlctl --json query get ztl_XXXX | jq .data.maturity
# null — field not present
```

**Expected**: `.data.maturity == "seed"`.

---

### BUG-15: op Field Naming Inconsistency [Content]

**Severity**: Low

**Impact**: The `op` field in batch create responses uses `"create_batch"` for successful operations but `"batch_create"` for format validation errors (e.g., non-array JSON input). Agents that route responses by `op` value may fail to match error responses.

**Recreation**:
```bash
echo '{"not": "an array"}' > bad.json
ztlctl --json create batch bad.json
# op: "batch_create"

echo '[{"type":"note","title":"OK"}]' > good.json
ztlctl --json create batch good.json
# op: "create_batch"
```

**Expected**: Consistent `op` value regardless of success/failure path.

---

### BUG-16: post_init Hook Not Wired [Plugin]

**Severity**: Low

**Impact**: The GitPlugin implements `post_init()` (which would auto-initialize a git repo and create an initial commit on `ztlctl init`), but `InitService` never dispatches the `post_init` event. The hook implementation is dead code.

**Recreation**:
```bash
mkdir new-vault && cd new-vault
git init
ztlctl init --name "test" --client vanilla --tone minimal --topics "test"
git log  # No auto-commit from init — only manual commits exist
```

**Expected**: A git commit with message like `"chore: initialize vault"` should be created automatically by the GitPlugin.

**Root Cause**: `InitService` does not call `self._dispatch_event("post_init", ...)`.

---

## Summary

| ID | BAT | Verdict | Severity | Type |
|----|-----|---------|----------|------|
| BUG-01 | BAT-06 | FAIL | Medium | Missing guard |
| BUG-02 | BAT-20 | FAIL | Medium | Missing rollback |
| BUG-03 | BAT-43 | FAIL | Medium | Pipeline ordering |
| BUG-04 | BAT-07 | PARTIAL | Low | Test gap |
| BUG-05 | BAT-89 | PARTIAL | Low | No severity filter |
| BUG-06 | BAT-111 | PARTIAL | Low | Hardcoded CLI choice |
| BUG-07 | BAT-103–109 | PARTIAL × 7 | Low | Test gap (MCP extra) |
| BUG-08 | BAT-114 | SKIP | Info | Untestable |
| BUG-09 | BAT-118 | SKIP | Info | Test gap (semantic extra) |
| BUG-10 | Cross-cutting | Observed | Low | Duplicate JSON output |
| BUG-11 | Cross-cutting | Observed | Low | Plugin signature |
| BUG-12 | Cross-cutting | Observed | Low | False positive |
| BUG-13 | Cross-cutting | Observed | Low | Cosmetic |
| BUG-14 | Cross-cutting | Observed | Low | Missing field |
| BUG-15 | Cross-cutting | Observed | Low | Naming inconsistency |
| BUG-16 | Cross-cutting | Observed | Low | Dead code |

**3 hard failures** (BUG-01, BUG-02, BUG-03) — all medium severity, clear fixes identified
**7 partial passes** — 2 code issues (BUG-05, BUG-06), 5 testing gaps
**2 skips** — environment limitations
**7 cross-cutting bugs** — all low severity, observed during testing
