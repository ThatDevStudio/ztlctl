---
title: Configuration
---

# Configuration

ztlctl uses a `ztlctl.toml` file at the vault root. This file uses a sparse TOML contract — only include the settings you want to override. All defaults are baked into the source, so a fresh vault needs only `[vault] name` and `[agent] tone` to be functional.

Settings can also be overridden via `ZTLCTL_*` environment variables (see [Environment Variables](#environment-variables)).

## File Location

`ztlctl.toml` lives at the vault root — the directory returned by `ztlctl vault path`. Every ztlctl command walks up from the current directory until it finds this file.

```
my-vault/
  ztlctl.toml        ← configuration lives here
  .ztlctl/           ← database and backups (managed by ztlctl)
  self/              ← agent-facing vault identity
  notes/
  ops/
```

## Config Sections

### [vault]

Vault identity and workspace client.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `name` | string | `"my-vault"` | Vault display name used in exports and agent context |
| `client` | string | `"none"` | Deprecated compatibility field. Use `[workspace] profile` instead. |

```toml
[vault]
name = "research-vault"
```

> **Note**: `[vault].client` is a deprecated compatibility input. Legacy values `none` and `vanilla` map to `profile = "core"` during settings load.

---

### [workspace]

Workspace profile selection — controls which scaffold, templates, and integrations are active.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `profile` | string | `"core"` | Workspace profile. `core` is always available; additional profiles come from installed plugins. |

```toml
[workspace]
profile = "core"         # or "obsidian" for Obsidian starter kit
```

> **Note**: `workspace.profile = "obsidian"` enables the first-party Obsidian starter kit during `ztlctl init`. That scaffold writes `.obsidian/` config, `garden/` templates, and a plugin-install checklist, but it does not download Obsidian community plugins.

---

### [agent]

Controls how ztlctl communicates with and assembles context for AI agents.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `tone` | string | `"research-partner"` | Agent communication style. Options: `"research-partner"`, `"assistant"`, `"minimal"` |

```toml
[agent]
tone = "research-partner"
```

---

### [agent.context]

Token budget and layer sizing for the `ztlctl agent context` command.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `default_budget` | int | `8000` | Token budget for context assembly |
| `layer_0_min` | int | `500` | Minimum tokens reserved for Layer 0 (vault identity + current note) |
| `layer_1_min` | int | `1000` | Minimum tokens reserved for Layer 1 (direct links) |
| `layer_2_max_notes` | int | `10` | Maximum notes included in Layer 2 (topic cluster) |
| `layer_3_max_hops` | int | `1` | Graph traversal depth for Layer 3 (neighborhood) |

```toml
[agent.context]
default_budget = 16000   # Increase for larger context windows
layer_0_min = 500
layer_1_min = 1000
layer_2_max_notes = 10
layer_3_max_hops = 1
```

---

### [reweave]

Controls the automatic link discovery engine that runs after note creation and on session close.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `enabled` | bool | `true` | Enable or disable automatic link discovery |
| `min_score_threshold` | float | `0.6` | Minimum composite score to suggest a link (0.0–1.0) |
| `max_links_per_note` | int | `5` | Maximum outbound links reweave will add per note |
| `lexical_weight` | float | `0.35` | Weight for BM25 lexical similarity signal |
| `tag_weight` | float | `0.25` | Weight for Jaccard tag overlap signal |
| `graph_weight` | float | `0.25` | Weight for graph proximity signal |
| `topic_weight` | float | `0.15` | Weight for topic cluster membership signal |

All four weights should sum to 1.0.

```toml
[reweave]
enabled = true
min_score_threshold = 0.6
max_links_per_note = 5
lexical_weight = 0.35
tag_weight = 0.25
graph_weight = 0.25
topic_weight = 0.15
```

---

### [garden]

Thresholds for the knowledge garden health system. These values determine when notes are flagged as stale seeds or qualify for evergreen status.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `seed_age_warning_days` | int | `7` | Days before a seed note is flagged as stale |
| `evergreen_min_key_points` | int | `5` | Minimum key points required for evergreen qualification |
| `evergreen_min_bidirectional_links` | int | `3` | Minimum bidirectional links required for evergreen qualification |

```toml
[garden]
seed_age_warning_days = 7
evergreen_min_key_points = 5
evergreen_min_bidirectional_links = 3
```

---

### [search]

Hybrid search configuration controlling both lexical (BM25) and semantic (vector) retrieval.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `semantic_enabled` | bool | `false` | Enable vector-based semantic search (requires `ztlctl[semantic]` extra) |
| `embedding_model` | string | `"local"` | Embedding model to use. `"local"` uses bundled sentence-transformers model |
| `embedding_dim` | int | `384` | Embedding vector dimension — must match the chosen model |
| `half_life_days` | float | `30.0` | Time-decay half-life for recency boosting in search ranking |
| `semantic_weight` | float | `0.5` | Blend weight for semantic vs. lexical scoring in hybrid mode |

```toml
[search]
semantic_enabled = false
embedding_model = "local"
embedding_dim = 384
half_life_days = 30.0
semantic_weight = 0.5
```

To enable semantic search: `pip install ztlctl[semantic]` then set `semantic_enabled = true`.

---

### [ingest]

Controls the URL and file ingestion pipeline.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `enabled` | bool | `true` | Enable or disable the ingestion pipeline |
| `auto_reweave` | bool | `true` | Automatically reweave after each ingested note |
| `default_target_type` | string | `"reference"` | Default note type for ingested content |
| `providers` | table | `{}` | Per-provider configuration injected by source-provider plugins |

```toml
[ingest]
enabled = true
auto_reweave = true
default_target_type = "reference"

[ingest.providers]
# Provider-specific overrides live here when installed plugins support them
```

---

### [session]

Controls what happens when you run `ztlctl session close`.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `close_reweave` | bool | `true` | Run reweave on session close |
| `close_orphan_sweep` | bool | `true` | Connect orphan notes on session close |
| `close_integrity_check` | bool | `true` | Run integrity check on session close |
| `orphan_reweave_threshold` | float | `0.2` | Minimum score for orphan sweep connections (lower = more aggressive) |

```toml
[session]
close_reweave = true
close_orphan_sweep = true
close_integrity_check = true
orphan_reweave_threshold = 0.2
```

---

### [tags]

Controls automatic tag management.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `auto_register` | bool | `true` | Automatically register new tags in the tag index when notes are created |

```toml
[tags]
auto_register = true
```

---

### [check]

Controls backup retention for the vault integrity system.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `backup_retention_days` | int | `30` | Days to retain backups before pruning |
| `backup_max_count` | int | `10` | Maximum number of backups to keep regardless of age |

```toml
[check]
backup_retention_days = 30
backup_max_count = 10
```

---

### [plugins.git]

Configuration for the built-in Git plugin. This is a `[plugins.<name>]` sub-table — not a top-level `[git]` section.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `enabled` | bool | `true` | Enable or disable the Git plugin |
| `batch_commits` | bool | `true` | Batch commits to session close instead of committing per-operation |
| `auto_push` | bool | `false` | Automatically push after commit |
| `auto_ignore` | bool | `true` | Automatically add ztlctl-managed paths to `.gitignore` |
| `branch` | string | `"develop"` | Default branch for git operations |
| `commit_style` | string | `"conventional"` | Commit message format. Options: `"conventional"`, `"simple"` |

```toml
[plugins.git]
enabled = true
batch_commits = true
auto_push = false
auto_ignore = true
branch = "develop"
commit_style = "conventional"
```

See [Built-in Plugins](plugins.md) for full Git plugin documentation.

---

### [mcp]

Controls the MCP server launched by `ztlctl serve`.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `enabled` | bool | `true` | Enable or disable MCP server functionality |
| `transport` | string | `"stdio"` | MCP transport. `"stdio"` for Claude Desktop; `"http"` for remote clients |

```toml
[mcp]
enabled = true
transport = "stdio"
```

---

### [workflow]

Controls Copier-based workflow template scaffolding (used with `ztlctl workflow init`).

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `template` | string | `"claude-driven"` | Workflow template name or path |
| `skill_set` | string | `"research"` | Skill set profile injected into the generated workflow |

```toml
[workflow]
template = "claude-driven"
skill_set = "research"
```

---

### [exports.dashboard]

Controls what is included in the agent dashboard export generated by `ztlctl export`.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `include_work_queue` | bool | `true` | Include the work queue in dashboard output |
| `include_recent_decisions` | bool | `true` | Include recent decision notes |
| `include_garden_backlog` | bool | `true` | Include garden health backlog |
| `topic_dossier_limit` | int | `5` | Maximum number of topic dossiers to include |

```toml
[exports.dashboard]
include_work_queue = true
include_recent_decisions = true
include_garden_backlog = true
topic_dossier_limit = 5
```

---

## Environment Variables

### Standard Override Pattern

Any `ztlctl.toml` setting can be overridden with a `ZTLCTL_` prefix. Nested keys use double underscores (`__`) as separators:

```bash
ZTLCTL_REWEAVE__MIN_SCORE_THRESHOLD=0.4 ztlctl reweave
ZTLCTL_AGENT__CONTEXT__DEFAULT_BUDGET=16000 ztlctl agent context
ZTLCTL_SESSION__CLOSE_REWEAVE=false ztlctl session close
```

### ZTLCTL_DOCS_PATH

A special environment variable that overrides the documentation path for `ztlctl docs search`.

**When needed**: Non-editable (`pip install` without `-e`) installations where the package-relative path discovery fails to locate the `docs/` directory.

**How it works**: `ztlctl docs search` resolves docs by:
1. Checking `ZTLCTL_DOCS_PATH` first (if set and is a valid directory, uses it)
2. Falling back to a package-relative path: `<repo_root>/docs/`

**Fix for non-editable installs**:
```bash
# Point ztlctl to your local docs checkout
export ZTLCTL_DOCS_PATH=/path/to/ztlctl/docs
ztlctl docs search "your query"
```

You can persist this in your shell profile (`~/.zshrc`, `~/.bashrc`):
```bash
echo 'export ZTLCTL_DOCS_PATH=/path/to/ztlctl/docs' >> ~/.zshrc
```

---

## Real-World Examples

### Research-Heavy Vault

A vault optimized for deep research with aggressive link discovery, large agent context, and semantic search enabled:

```toml
[vault]
name = "research-vault"

[agent]
tone = "research-partner"

[agent.context]
default_budget = 16000
layer_0_min = 500
layer_1_min = 1000
layer_2_max_notes = 20
layer_3_max_hops = 2

[reweave]
enabled = true
min_score_threshold = 0.4   # Lower threshold — find more connections
max_links_per_note = 10     # Allow more links per note
lexical_weight = 0.30
tag_weight = 0.20
graph_weight = 0.30         # Prioritize graph proximity
topic_weight = 0.20

[search]
semantic_enabled = true     # Enable vector search (requires ztlctl[semantic])
embedding_model = "local"
half_life_days = 90.0       # Slower time decay for archival research
semantic_weight = 0.6       # Prefer semantic over lexical

[session]
orphan_reweave_threshold = 0.15   # More aggressive orphan connection
```

### Minimal Daily Notes Vault

A lightweight vault for daily journaling and quick capture — fast, no semantic overhead:

```toml
[vault]
name = "daily-notes"

[agent]
tone = "minimal"

[agent.context]
default_budget = 4000       # Small context for quick queries
layer_2_max_notes = 5

[reweave]
enabled = true
min_score_threshold = 0.7   # Higher threshold — only confident links
max_links_per_note = 3

[search]
semantic_enabled = false    # No vector search needed
half_life_days = 14.0       # Strong recency preference

[session]
close_reweave = true
close_integrity_check = false   # Skip integrity check for speed

[plugins.git]
enabled = true
batch_commits = true        # Commit at session close, not per-note
auto_push = false
```

---

## Complete Default Configuration

All settings with their defaults, ready to copy as a starting point:

```toml
[vault]
name = "my-vault"

[workspace]
profile = "core"

[agent]
tone = "research-partner"

[agent.context]
default_budget = 8000
layer_0_min = 500
layer_1_min = 1000
layer_2_max_notes = 10
layer_3_max_hops = 1

[reweave]
enabled = true
min_score_threshold = 0.6
max_links_per_note = 5
lexical_weight = 0.35
tag_weight = 0.25
graph_weight = 0.25
topic_weight = 0.15

[garden]
seed_age_warning_days = 7
evergreen_min_key_points = 5
evergreen_min_bidirectional_links = 3

[search]
semantic_enabled = false
embedding_model = "local"
embedding_dim = 384
half_life_days = 30.0
semantic_weight = 0.5

[ingest]
enabled = true
auto_reweave = true
default_target_type = "reference"

[session]
close_reweave = true
close_orphan_sweep = true
close_integrity_check = true
orphan_reweave_threshold = 0.2

[tags]
auto_register = true

[check]
backup_retention_days = 30
backup_max_count = 10

[plugins.git]
enabled = true
batch_commits = true
auto_push = false
auto_ignore = true
branch = "develop"
commit_style = "conventional"

[mcp]
enabled = true
transport = "stdio"

[workflow]
template = "claude-driven"
skill_set = "research"

[exports.dashboard]
include_work_queue = true
include_recent_decisions = true
include_garden_backlog = true
topic_dossier_limit = 5
```

---

## Notes

- `[vault].client` is a deprecated compatibility input. Legacy values `none` and `vanilla` map to `profile = "core"` during settings load.
- `[workspace].profile` is the canonical workspace selector. `core` is always available; additional profiles come from installed plugins.
- Core-managed paths are `ztlctl.toml`, `.ztlctl/`, `self/`, `notes/`, and `ops/`. Profile-associated scaffold paths identify workspace assets created by a profile during init, such as `.obsidian/`. Human-managed paths such as `garden/` remain outside default core indexing and mutation.
- `[plugins].obsidian` is obsolete and ignored when present in older configs. The only canonical built-in plugin config section today is `[plugins.git]`.
- URL ingestion is provider-backed. Base ztlctl supports text and markdown ingestion directly; remote fetching comes from installed source-provider plugins.
- Dashboard export still uses `--viewer` because it is a render target, not a workspace selector.
