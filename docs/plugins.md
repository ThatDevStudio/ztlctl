---
title: Built-in Plugins
---

# Built-in Plugins

ztlctl ships two built-in plugins that run automatically in the background: the Git plugin for automatic version control and the Reweave plugin for automatic link discovery. Both are enabled by default. This page explains exactly what they do, when they run, and how to configure them.

## Git Plugin

The Git plugin provides automatic version control for vault operations. When you create a note, the plugin stages the file and — depending on configuration — either commits immediately or batches the commit for session close.

### Prerequisites

!!! note
    The Git plugin requires `git` to be installed and available on your PATH. If git is not found, the plugin logs a debug message and continues silently — vault operations never fail due to git errors.

Verify git is available:

```bash
git --version
```

### What Gets Committed Automatically

Every vault operation that creates or modifies a markdown file triggers a git stage. Commit timing depends on the `batch_commits` setting (see [Configuration](#git-plugin-configuration) below).

| Action | Commit Message Format |
|--------|-----------------------|
| `ztlctl create note` | `feat: create note {id} — {title}` |
| `ztlctl create reference` | `feat: create reference {id} — {title}` |
| `ztlctl create task` | `feat: create task {id} — {title}` |
| `ztlctl update` | `docs: update {id} ({fields_changed})` |
| `ztlctl close` / `ztlctl archive` | `docs: close {id} — {summary}` |
| `ztlctl agent session close` | `docs: session {id} — N created, N updated` |
| `ztlctl init` | `feat: initialize vault '{name}'` |

Operations that are **no-ops** for the Git plugin: `reweave`, `session start`, `check`, `check rebuild`. These do not stage or commit any files.

### Batch Mode vs Immediate Mode

| Mode | Behavior | When to use |
|------|----------|-------------|
| **Batch (default)** | Files are staged on each operation; one commit is made at session close | Session-based workflows — clean history with one commit per session |
| **Immediate** | Files are staged AND committed after every individual operation | Headless or no-session workflows — each note creation is its own commit |

!!! warning
    In batch mode, creating notes outside an active session stages files but never commits them — the commit trigger is `session close`. If you work without sessions, set `batch_commits = false`.

**What git status looks like in batch mode (before session close):**

```bash
$ git status
On branch develop
Changes to be committed:
  (use "git restore --staged <file>..." to unstage)
        new file:   notes/ZTL-0001.md
        new file:   notes/ZTL-0002.md
        modified:   notes/ZTL-0003.md
```

After `ztlctl agent session close`, all staged changes are committed in one operation:

```
docs: session LOG-0001 — 2 created, 1 updated
```

### Git Plugin Configuration

In `ztlctl.toml`:

```toml
[plugins.git]
enabled = true
batch_commits = true      # true = commit at session close, false = commit immediately
auto_push = false         # push to remote on session close
auto_ignore = true        # write .gitignore during vault init
```

**All config fields:**

| Field | Default | Meaning |
|-------|---------|---------|
| `enabled` | `true` | Enable or disable the entire plugin |
| `batch_commits` | `true` | Batch all changes into one session-close commit |
| `auto_push` | `true` | Push to remote after session-close commit |
| `auto_ignore` | `true` | Write .gitignore during `ztlctl init` |
| `branch` | `"develop"` | Target branch (informational — plugin does not enforce branch) |
| `commit_style` | `"conventional"` | Commit message format (currently only `"conventional"`) |

The auto-generated `.gitignore` excludes:

```
# ztlctl vault gitignore
.ztlctl/backups/
*.db-journal
```

### Common Scenarios

**Disable automatic commits entirely:**

```toml
[plugins.git]
enabled = false
```

**Use immediate commits (one commit per note):**

```toml
[plugins.git]
batch_commits = false
```

**Push to remote automatically on session close:**

```toml
[plugins.git]
auto_push = true
```

---

## Reweave Plugin

The Reweave plugin automatically discovers connections for new notes and references the moment they are created. It runs the full 4-signal scoring algorithm against all existing content and creates graph edges for items above the threshold.

### What It Does

When you create a note or reference, the Reweave plugin immediately calls the reweave pipeline on the new item. This means your vault's link graph is always up to date without any manual `ztlctl reweave` call.

```bash
# When you run this:
ztlctl create note "Attention mechanisms" --tags "ml/transformers"

# The Reweave plugin automatically runs the equivalent of:
ztlctl reweave --id ZTL-0042
# → finds related notes via BM25 + tag overlap + graph proximity + shared topic
# → creates edges for items scoring above 0.6 (default threshold)
```

### When It Runs (and When It Doesn't)

**Fires for:** `create note`, `create reference` only.

**Does not fire for:** `create task`, `update`, `close`, `archive`, `session close`, or `reweave` (manual reweave is not re-triggered).

**Skip conditions (checked in order):**

1. The create operation failed — skip
2. The created item has no ID — skip
3. `subtype = "decision"` — skip (decision notes have strict lifecycle and must not be auto-mutated)
4. `--no-reweave` flag was passed — skip for this invocation only
5. `[reweave] enabled = false` in config — skip globally

!!! note
    Decision notes (`ztlctl create note --subtype decision`) are intentionally excluded from auto-reweave. Decision notes represent deliberate choices and must not be auto-linked by background processes. Run `ztlctl reweave --id {id}` manually if you want to connect a decision note.

### 4-Signal Scoring

The reweave algorithm scores candidate links using four signals:

| Signal | Default Weight | What It Measures |
|--------|---------------|-----------------|
| BM25 lexical similarity | 0.35 | Shared vocabulary between note bodies |
| Jaccard tag overlap | 0.25 | Proportion of tags in common |
| Graph proximity | 0.25 | How closely connected via existing edges |
| Shared topic directory | 0.15 | Whether notes share a topic routing prefix |

A link is created when the combined score exceeds `min_score_threshold` (default: 0.6).

### Reweave Plugin Configuration

In `ztlctl.toml`:

```toml
[reweave]
enabled = true
min_score_threshold = 0.6   # raise to 0.75 for fewer, higher-quality links
max_links_per_note = 5      # raise for denser graphs
lexical_weight = 0.35
tag_weight = 0.25
graph_weight = 0.25
topic_weight = 0.15
```

**All config fields:**

| Field | Default | Meaning |
|-------|---------|---------|
| `enabled` | `true` | Global enable/disable for auto-reweave |
| `min_score_threshold` | `0.6` | Minimum combined score (0.0–1.0) to create a link |
| `max_links_per_note` | `5` | Maximum new links per auto-reweave run |
| `lexical_weight` | `0.35` | BM25 signal weight |
| `tag_weight` | `0.25` | Tag overlap signal weight |
| `graph_weight` | `0.25` | Graph proximity signal weight |
| `topic_weight` | `0.15` | Topic directory signal weight |

Weights do not need to sum to 1.0 — they are relative, not normalized.

### Common Scenarios

**Disable auto-reweave for a single note:**

```bash
ztlctl create note "Quick capture" --no-reweave
```

**Disable auto-reweave globally:**

```toml
[reweave]
enabled = false
```

**Tune for fewer, higher-quality links:**

```toml
[reweave]
min_score_threshold = 0.75
max_links_per_note = 3
```

**Emphasize tag-based connections (lower lexical weight):**

```toml
[reweave]
lexical_weight = 0.20
tag_weight = 0.45
```

**Run reweave manually for an existing note:**

```bash
ztlctl reweave --id ZTL-0042
```

---

## Next Steps

- See [Agentic Workflows](agentic-workflows.md) for how plugins interact with sessions and MCP recipes
- See [Configuration](configuration.md) for the full ztlctl.toml reference including all plugin config schemas
- See [Obsidian Starter Kit](obsidian.md) for setting up the Obsidian integration
