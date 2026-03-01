# Linking Patterns Reference

## Wikilinks

Inline links in note bodies using double-bracket syntax:

```markdown
See [[Machine Learning Fundamentals]] for background.
Related to [[ML Basics|the basics]] (with display text).
Cross-ref [[ztl_a1b2c3d4]] (by ID).
```

### Resolution Order

When indexing wikilinks, targets resolve in order:
1. **Title match** — exact title of a content item
2. **Alias match** — `aliases` frontmatter field (searched via `json_each`)
3. **ID match** — direct content ID (`ztl_`, `ref_`, `TASK-`, `LOG-`)

### Frontmatter Links

Structured links in YAML frontmatter:

```yaml
links:
  relates: [ztl_b3f2a1, ref_c4d5e6]
  supersedes: [ztl_old123]
  derived_from: [LOG-0001]
```

Keys are edge types; values are lists of target IDs. The `relates` type is used by reweave.

## Reweave — Automated Link Discovery

Reweave finds and creates connections between related content using a 4-signal scoring system.

### Pipeline: DISCOVER → SCORE → FILTER → CONNECT

**DISCOVER**: Finds the target node and all unlinked candidate nodes (non-archived).

**SCORE**: Each candidate gets a composite score from 4 weighted signals:

| Signal | Method | Weight | Range |
|---|---|---|---|
| Lexical (S1) | BM25 via FTS5 | 0.35 | 0.0–1.0 |
| Tag overlap (S2) | Jaccard similarity | 0.25 | 0.0–1.0 |
| Graph proximity (S3) | 1/shortest_path | 0.25 | 0.0–1.0 |
| Topic match (S4) | Same topic field | 0.15 | 0.0 or 1.0 |

Composite = `S1*0.35 + S2*0.25 + S3*0.25 + S4*0.15`

**FILTER**: Drops below `min_score_threshold` (default 0.6). Caps at `max_links_per_note` (default 5) minus existing links.

**CONNECT** (unless dry_run):
1. Adds target IDs to `links.relates` in frontmatter
2. Appends `[[Title]]` wikilinks to body (skipped for garden notes)
3. Inserts `relates` edges in DB
4. Writes audit entry to `reweave_log`

### Special Behaviors

- **Garden notes** (maturity set): Body wikilinks are NOT injected — only frontmatter links are added
- **Prune mode**: Re-scores existing links, removes those below threshold
- **Undo**: Reverses the most recent reweave batch using the audit trail
- **Post-create**: Notes and references are auto-reweaved after creation (unless `no_reweave` is set)

## Best Practices

1. **Write wikilinks as you write** — don't rely solely on reweave
2. **Use titles over IDs** in wikilinks — more readable, same resolution
3. **Let reweave discover connections you missed** — run it periodically
4. **Review reweave suggestions** with `dry_run=True` before committing
5. **Garden notes get special treatment** — set maturity when you want body protection
