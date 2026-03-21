---
title: Best Practices
---

# Best Practices

Opinionated guidance from building and maintaining ztlctl vaults. Each entry covers what goes wrong, why it happens, and the correct pattern. Cross-links point to authoritative pages for full context.

## Vault Initialization

**Always initialize with `ztlctl init`** — never create the database or config file manually.

```bash
# Correct: let init scaffold everything
ztlctl init my-vault --name "Research Notes" --profile obsidian

# Wrong: creating the directory yourself and adding files ad hoc
mkdir my-vault && touch my-vault/ztlctl.toml
```

Init writes the config, creates the SQLite index, sets up FTS5 and graph tables, and scaffolds the `self/`, `notes/`, and `ops/` directories in one atomic step. Skipping it leaves the index in an undefined state.

!!! warning "Anti-Pattern: Initializing in a deeply nested subdirectory"
    Init anchors the vault root at the chosen directory. If you initialize inside `~/work/project/docs/notes/vault/`, every relative path — CLI, config, and MCP — is relative to that anchor. Prefer `~/vaults/my-vault` or another shallow, stable location.

**Use a profile that matches your tools.** The `--profile obsidian` flag writes the Obsidian starter kit and `.obsidian/` community plugin config alongside vault scaffolding:

```bash
ztlctl init my-vault --profile obsidian  # Obsidian users
ztlctl init my-vault --profile core      # CLI-only
```

---

## Note Creation

**Choose content type before you create.** Content type cannot be changed after creation.

| Type | Use when | Initial status |
|------|----------|---------------|
| `note` | Synthesizing knowledge, recording insights | `draft` |
| `reference` | Capturing an external source (article, tool, spec) | `captured` |
| `task` | Tracking actionable work | `inbox` |

```bash
# Insight from reading → note
ztlctl create note "Transformer architecture trade-offs" --tags "ml/transformers"

# Source you read → reference
ztlctl create reference "Attention Is All You Need" --url "https://arxiv.org/abs/1706.03762" --subtype article

# Something to do → task
ztlctl create task "Implement attention visualization" --priority high
```

!!! warning "Anti-Pattern: Accumulating orphan notes"
    Notes with no outgoing links stay at `draft` status and score lower in graph-based queries. Every new note should link to at least one existing item — either explicitly with `--links "[[Target Title]]"` or by letting the Reweave plugin discover connections automatically. Run `ztlctl graph gaps` to find existing orphans.

**Use note subtypes for long-lived content.** The `knowledge` subtype signals a durable, ever-refining insight. The `decision` subtype triggers decision lifecycle rules — `proposed → accepted → superseded` — and disables auto-reweave:

```bash
ztlctl create note "GraphQL trade-offs" --subtype knowledge
ztlctl create note "Use GraphQL for nested APIs" --subtype decision
```

**Garden seeds are for raw captures, not permanent knowledge.** Seeds start at `maturity=seed` — useful for quick capture, but they age out of the work queue signal if left unattended. Promote or prune them within a week:

```bash
ztlctl garden seed "Idea: attention for code review" --tags "ml/attention"
ztlctl update ZTL-0042 --maturity budding  # once you've developed it
```

---

## Tagging

**Use `domain/scope` format for every tag.** Unscoped tags work but emit a warning and cannot be filtered with domain-prefix queries:

```bash
# Correct
--tags "lang/python,framework/fastapi,concept/async"

# Works but limited — can't filter by domain
--tags "python,fastapi,async"
```

Scoped tags unlock `--tag "lang/..."` wildcard filtering in `query list` and reweave's Jaccard overlap scoring:

```bash
ztlctl query list --tag "ml/transformers"   # exact scope
ztlctl query list --tag "ml/"              # all ml/* tags
```

**Keep domain taxonomy shallow.** Two-level (`domain/scope`) is the convention. Deeper nesting like `ml/transformers/attention` is not supported by the tag filter pattern and will be treated as a single unstructured string.

**Register tags before bulk import.** Tags are auto-registered on creation (`[tags] auto_register = true`). If you bulk-import content with non-standard tags and then rename, the old tags remain as index artifacts. Decide your taxonomy before large imports.

---

## Linking and Reweave

**Let reweave suggest connections — don't maintain all links manually.** The 4-signal scoring algorithm (BM25 35%, Jaccard tags 25%, graph proximity 25%, topic 15%) surfaces connections you would miss by hand. Review suggestions in sessions:

```bash
ztlctl reweave --dry-run           # preview what would be linked
ztlctl reweave --auto-link-related # apply discovered connections
```

**Tune thresholds only after your vault has 50+ notes.** The default `min_score_threshold = 0.6` is calibrated for medium-density vaults. Early vaults have sparse graphs and noisy BM25 scores — tuning too early optimizes for noise:

```toml
# ztlctl.toml — tune after 50+ notes
[reweave]
min_score_threshold = 0.6   # default: start here
max_links_per_note = 5      # default: raise for denser graphs
```

For high-quality, low-noise links:

```toml
[reweave]
min_score_threshold = 0.75
max_links_per_note = 3
```

!!! warning "Anti-Pattern: Disabling reweave globally when you only want to skip one note"
    `[reweave] enabled = false` turns off auto-reweave for all new content. Use `--no-reweave` to skip a single creation:

    ```bash
    ztlctl create note "Quick scratchpad" --no-reweave
    ```

**Decision notes are intentionally excluded from auto-reweave.** If you want to connect a decision note, run reweave manually:

```bash
ztlctl reweave --id ZTL-0042
```

---

## Session Management

**Close sessions after completing a work unit.** Sessions are operational coordination state. Leaving a session open blocks starting a new one and delays the session-close enrichment pipeline:

```bash
ztlctl agent session start "OAuth security research"
# ... do work ...
ztlctl agent session close --summary "Mapped OAuth 2.0 attack surface"
```

The close triggers reweave, orphan sweep, integrity check, and graph materialization — this is where connections are stitched together across the session's work.

!!! warning "Anti-Pattern: Running multiple concurrent sessions"
    Only one session can be open at a time. If you try to start a session while one is open, ztlctl returns an error. Close the existing session first:

    ```bash
    ztlctl agent session close --summary "Pausing work"
    ztlctl agent session start "New topic"
    ```

**Log reasoning during sessions, not just captures.** `session log` entries feed context assembly and decision extraction. Pinned entries persist in the work queue:

```bash
ztlctl agent session log "Key insight: token replay risk via HTTP" --pin
```

**Read the session-close enrichment report.** The JSON close result tells you how many new links were discovered and whether orphans were connected:

```bash
ztlctl agent session close --summary "Done" --json
# → reweave_count, orphan_count, integrity_issues
```

---

## Plugin Configuration

**Start with `batch_commits = true` and `auto_push = false`.** The git plugin's defaults are safe but aggressive — `auto_push = true` by default will push to remote on every session close:

```toml
[plugins.git]
batch_commits = true    # one commit per session close (recommended)
auto_push = false       # push manually when ready
```

Enable auto-push only when you're confident in your session discipline and your remote is always available.

**Understand batch mode before enabling it.** In batch mode, notes created outside an active session are staged but never committed — the commit trigger is `session close`. If you use ztlctl without sessions, switch to immediate mode:

```toml
[plugins.git]
batch_commits = false   # commit immediately after each operation
```

**Never edit vault files directly in git.** Bypass the CLI and all index state breaks — FTS5, the graph, tag index, and content ID counter all live in the SQLite database. Direct file edits create orphaned files that `check --rebuild` must recover:

```bash
# Never: vim notes/ztl_a1b2c3d4.md (edits bypass the DB)
# Always: ztlctl update ZTL-0001 --body "Updated content"
```

---

## Agent Workflows

**Always wrap agent work in a session.** Sessions provide the operational boundary for enrichment. Without a session, auto-reweave still fires per-note, but cross-session reweave, orphan sweep, and graph materialization do not run until a session closes:

```bash
# Agent start
ztlctl agent session start "Literature review: attention mechanisms"
# ... create notes and references ...
# Agent end
ztlctl agent session close --summary "Surveyed 12 papers, 5 synthesis notes"
```

**Check `.success` before proceeding on every ServiceResult.** Every CLI command returns a JSON envelope with `success`, `data`, and `meta`. Agents that ignore the success field risk chaining operations on failed state:

```bash
RESULT=$(ztlctl create note "My Note" --json)
echo $RESULT | jq '.success'  # check before using .data.id
```

**Use `.recovery` hints on failure.** Service errors include a `recovery` field that names the corrective action. Parse it before retrying or escalating:

```json
{
  "success": false,
  "error": {"message": "Vault not initialized", "recovery": "run ztlctl init"}
}
```

**Use `agent context` to orient before creating.** Fetch topic context before creating notes to avoid duplicates and to pick up related content for linking:

```bash
ztlctl agent context --topic "distributed-systems" --budget 4000 --json
```

**Use `--json` for all agent operations.** Rich terminal output is not machine-parseable. Pass `--json` to get structured ServiceResult envelopes on stdout:

```bash
ztlctl create note "Title" --json
ztlctl query search "topic" --json
ztlctl agent session close --json
```

---

## What Not to Do — Summary Table

| Anti-Pattern | Impact | Fix |
|-------------|--------|-----|
| Bare tags (`python` instead of `lang/python`) | Cannot filter by domain; poor reweave scoring | Use `domain/scope` format |
| Orphan notes (no outgoing links) | Graph gaps, missed connections, lower search rank | Always link on create or run `ztlctl reweave` |
| Direct file edits bypassing CLI | Breaks FTS5, graph, tag index, counters | Use `ztlctl update` and `ztlctl archive` |
| Manual DB edits | Corruption, broken FK constraints | Never touch `ztlctl.db` directly |
| Opening sessions without closing | Blocks new sessions; delays enrichment pipeline | Close all sessions before starting new work |
| Wrong content type | Cannot be changed post-creation | Match type to purpose before creating |
| `auto_push = true` without session discipline | Unexpected remote pushes mid-work | Set `auto_push = false` until workflow is stable |
| `--no-reweave` globally disabled | No automatic link discovery | Use `--no-reweave` per-note, not global disable |
| Creating notes without session (agent) | No cross-session enrichment | Wrap all agent work in `session start / close` |
| Ignoring `success: false` in JSON output | Chaining ops on failed state | Always check `.success` before using `.data` |

---

## Next Steps

- [Tutorial](tutorial.md) — step-by-step walkthrough of vault setup through export
- [Configuration](configuration.md) — full `ztlctl.toml` reference with all thresholds and defaults
- [Agentic Workflows](agentic-workflows.md) — session discipline, recipe walkthroughs, and MCP integration for agents
- [Built-in Plugins](plugins.md) — git and reweave plugin configuration deep-dive
