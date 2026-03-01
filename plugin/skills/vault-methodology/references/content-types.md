# Content Types Reference

## Note (`note`)

Primary knowledge unit. One idea per note, atomically self-contained.

| Field | Details |
|---|---|
| **ID format** | `ztl_[0-9a-f]{8}` (SHA-256 of normalized title) |
| **Status** | Machine-computed: `draft` (<1 link) → `linked` (1-2 links) → `connected` (3+ links) |
| **Maturity** | Optional garden stage: `seed` → `budding` → `evergreen` |
| **Subtypes** | `decision`, `knowledge`, or plain |

### Decision Subtype

Strict lifecycle for architectural/strategic decisions.

- **Required body sections**: Context, Choice, Rationale, Alternatives, Consequences
- **Must be created with** `status="proposed"`
- **Transitions**: `proposed` → `accepted` → `superseded`
- **Immutability**: After acceptance, only metadata fields can change (`status`, `superseded_by`, `modified`, `tags`, `aliases`, `topic`)
- **Extra frontmatter**: `supersedes`, `superseded_by`

### Knowledge Subtype

Advisory structure for learning capture.

- **Advisory field**: `key_points` list in frontmatter
- **Soft validation**: Warns if no key_points on creation
- **Same lifecycle as plain notes**

## Reference (`reference`)

External source capture — articles, tools, specifications.

| Field | Details |
|---|---|
| **ID format** | `ref_[0-9a-f]{8}` (SHA-256 of normalized title) |
| **Status** | `captured` → `annotated` |
| **Subtypes** | `article`, `tool`, `spec` |
| **Extra fields** | `url` for source location |

## Task (`task`)

Actionable items with priority scoring.

| Field | Details |
|---|---|
| **ID format** | `TASK-NNNN` (sequential) |
| **Status** | `inbox` → `active` → `blocked` / `done` / `dropped` |
| **Scoring** | `priority*2 + impact*1.5 + (4 - effort)` |
| **Priority levels** | `critical`, `high`, `medium`, `low` |
| **Impact/Effort** | `high`, `medium`, `low` |

Work queue returns tasks in actionable statuses (`inbox`, `active`, `blocked`), sorted by score descending.

## Log (`log`)

Session records — created automatically by session start.

| Field | Details |
|---|---|
| **ID format** | `LOG-NNNN` (sequential) |
| **Status** | `open` → `closed` (reopenable) |
| **Storage** | DB-only (no physical file) |
| **Tracks** | All content created during the session via `session` field |

## Custom Subtypes

Plugins can register additional subtypes via `register_content_model()`. Built-in names (`note`, `knowledge`, `decision`, `reference`, `task`) are reserved.
