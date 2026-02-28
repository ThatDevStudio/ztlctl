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
client = "obsidian"  # or "vanilla"

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
```

## Environment Variables

Any setting can be overridden with a `ZTLCTL_` prefix:

```bash
ZTLCTL_REWEAVE__MIN_SCORE_THRESHOLD=0.4 ztlctl reweave
ZTLCTL_AGENT__CONTEXT__DEFAULT_BUDGET=16000 ztlctl agent context
```

Nested keys use double underscores (`__`) as separators.
