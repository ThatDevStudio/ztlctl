---
title: Configuration
nav_order: 7
---

# Configuration

ztlctl uses a `ztlctl.toml` file at the vault root. Settings can be overridden via CLI flags or `ZTLCTL_*` environment variables.

## Key Configuration Sections

```toml
[vault]
name = "my-vault"

[workspace]
profile = "obsidian"  # workspace profile: obsidian or core

[agent]
tone = "research-partner"  # or "assistant", "minimal"

[agent.context]
default_budget = 8000      # Token budget for context assembly
layer_2_max_notes = 10     # Max notes in topic layer
layer_3_max_hops = 1       # Graph traversal depth

[reweave]
enabled = true
min_score_threshold = 0.6  # Minimum score to suggest a link
max_links_per_note = 5
lexical_weight = 0.35      # BM25 weight
tag_weight = 0.25          # Tag Jaccard weight
graph_weight = 0.25        # Graph proximity weight
topic_weight = 0.15        # Topic match weight

[garden]
seed_age_warning_days = 7
evergreen_min_key_points = 5
evergreen_min_bidirectional_links = 3

[search]
half_life_days = 30.0      # Time-decay half-life for recency ranking
semantic_weight = 0.5      # Hybrid lexical/semantic weighting

[ingest]
enabled = true
auto_reweave = true
default_target_type = "reference"

[ingest.providers]
# Provider-specific overrides live here when installed plugins support them

[session]
close_reweave = true       # Reweave on session close
close_orphan_sweep = true  # Connect orphan notes on close
close_integrity_check = true

[check]
backup_retention_days = 30
backup_max_count = 10

[git]
enabled = true
auto_push = true
commit_style = "conventional"

[mcp]
enabled = true
transport = "stdio"

[exports.dashboard]
include_work_queue = true
include_recent_decisions = true
include_garden_backlog = true
topic_dossier_limit = 5
```

## Environment Variables

Any setting can be overridden with a `ZTLCTL_` prefix:

```bash
ZTLCTL_REWEAVE__MIN_SCORE_THRESHOLD=0.4 ztlctl reweave
ZTLCTL_AGENT__CONTEXT__DEFAULT_BUDGET=16000 ztlctl agent context
```

Nested keys use double underscores (`__`) as separators.

## Notes

- `[workspace].profile` is the canonical workspace selector. Built-in Phase 1 profiles are `obsidian` and `core`.
- `[vault].client` is a deprecated compatibility input. Legacy values `none` and `vanilla` map to `profile = "core"` during settings load.
- `workspace.profile = "obsidian"` does not mean ztlctl owns your full `.obsidian/` state. In Phase 1 it means the built-in Obsidian profile applies the minimal `.obsidian/snippets/ztlctl.css` scaffold during `ztlctl init`.
- `[plugins].obsidian` is obsolete and ignored when present in older configs. The only canonical built-in plugin config section today is `[plugins].git`.
- URL ingestion is provider-backed. Base ztlctl supports text and markdown ingestion directly; remote fetching comes from installed source-provider plugins.
- Core-managed paths are `ztlctl.toml`, `.ztlctl/`, `self/`, `notes/`, and `ops/`. Profile-managed paths are profile-owned workspace assets such as `.obsidian/`. Human-managed paths such as `garden/` remain outside default core indexing and mutation.
- Dashboard export still uses `--viewer` because it is a render target, not a workspace selector.
