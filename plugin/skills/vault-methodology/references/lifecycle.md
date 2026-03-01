# Lifecycle Reference

## Status Transitions by Content Type

### Notes

Status is **machine-computed** from outgoing link count — never set directly.

```
draft (0 links) → linked (1-2 links) → connected (3+ links)
```

Every time links change, the system recalculates status automatically.

### References

```
captured → annotated
```

Simple two-state lifecycle. Moves to `annotated` when annotations are added.

### Tasks

```
inbox → active → done (terminal)
                → dropped (terminal)
       → blocked → active
                  → dropped (terminal)
       → dropped (terminal)
```

Tasks in `inbox`, `active`, or `blocked` appear in the work queue.

### Decisions (note subtype)

```
proposed → accepted → superseded (terminal)
```

**Critical invariant**: After `accepted`, the decision is immutable. Only these fields can change: `status`, `superseded_by`, `modified`, `tags`, `aliases`, `topic`. All other field changes are rejected.

### Sessions (logs)

```
open → closed → open (reopenable)
```

Only one session can be `open` at a time.

## Garden Maturity (Notes Only)

Advisory maturity stages for knowledge garden notes:

```
seed → budding → evergreen
```

| Stage | Description | Advisory thresholds |
|---|---|---|
| `seed` | Raw idea, just captured | Warns if >7 days old |
| `budding` | Developing, being refined | — |
| `evergreen` | Mature, well-connected | >=5 key_points, >=3 bidirectional links |

**Key behavior**: Setting `maturity` on a note marks it as a "garden note." Garden notes have **body protection** — reweave will not inject wikilinks into the body, and `unlink` will not remove body wikilinks. Frontmatter links are still managed normally.

Maturity is human-driven — the system never auto-promotes maturity stages.

## Archive

Archive is a **boolean flag**, not a status. It acts as a soft-delete:

- Preserved: the content item and all its edges
- Hidden from: default list/search results, reweave candidates, graph queries
- Recoverable: visible with `include_archived` flag
- Applied via: `close_content` / `archive()` operation

## Immutable Fields

These fields can never be changed after creation:
- `id` — permanent content identifier
- `type` — content type (note, reference, task, log)
- `created` — creation timestamp
