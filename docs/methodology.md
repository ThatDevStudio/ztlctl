---
title: Methodology guidance
---

# Methodology guidance

ztlctl encodes Zettelkasten methodology conventions that the integrity scanner enforces and the init templates teach. Writing descriptive, prose-style titles is the single highest-leverage habit in a knowledge graph — it determines how well you and your agents can find ideas without opening files.

## Prose-as-title convention

A prose-as-title is a complete thought, not a label. Instead of naming a note after its topic, name it after the insight, decision, or claim the note makes. The title becomes a one-sentence summary that works as a search result, a graph node label, and a cross-reference anchor all at once.

| Instead of | Write |
|---|---|
| `Authentication` | `JWT authentication with refresh token rotation` |
| `Meeting Notes` | `Q1 planning alignment on data pipeline priorities` |
| `Bug Fix` | `Fix race condition in session close during concurrent reweave` |
| `Ideas` | `Potential approaches to cross-vault knowledge federation` |
| `Notes on caching` | `Redis eviction policy tradeoffs for session-heavy workloads` |

A good title lets you find the note without opening it. Aim for four or more words that capture the specific insight, decision, or topic — not the category it belongs to.

!!! tip
    Run `ztlctl query search "keyword"` on your own vault. If the search results look like file-cabinet labels instead of ideas, your titles need prose treatment.

## Title quality checks

`ztlctl check` includes a title quality advisory under the `structural_validation` category at `info` severity. The scanner flags notes whose titles are considered short or generic.

A title is flagged when it meets either condition:

- **Short**: three words or fewer (word count ≤ 3)
- **Generic**: exactly matches one of the reserved patterns — `untitled`, `new note`, `note`, `notes`, `draft`, `temp`, `test` — or begins with `notes on `

The flag is advisory (`info` severity), not a blocking error. It never prevents saves or transitions. The message reads:

```
Title quality: '<title>' is short or generic — consider a prose title
that captures the specific insight (see methodology.md for examples)
```

To see title quality advisories, run check with `--min-severity info`:

```bash
ztlctl check check --min-severity info
```

Without `--min-severity info`, check defaults to `warning` severity and title advisories are suppressed. This keeps routine health checks focused on actionable problems.

!!! note
    Title quality is checked at `info` severity so it never blocks your workflow. The intent is to surface improvement opportunities during dedicated vault-maintenance sessions, not to interrupt capture.

## Garden backlog candidates

The `ztlctl://garden/backlog` MCP resource aggregates three categories of notes that benefit from attention:

- **Stale seeds** — notes in `seed` maturity that have not been updated recently
- **Orphan notes** — notes with no graph connections
- **Title improvement candidates** — notes flagged by the title quality check

The title improvement candidates in the garden backlog come directly from a `check --min-severity info` scan filtered to `Title quality` messages. Each entry carries the note ID and the advisory message so agents can prioritize which titles to rewrite.

Agents can use the garden backlog as a systematic improvement queue:

```
Read ztlctl://garden/backlog
→ for each title_improvement_candidate: rewrite the title as prose
→ update the note: ztlctl update <id> --title "New prose title"
```

Users can inspect the same data via the CLI:

```bash
ztlctl check check --min-severity info
```

Filter the output for `Title quality` lines to find the same candidates.

!!! tip
    Run a garden backlog session periodically — once a month is enough for most vaults. Improving ten titles in a session meaningfully improves search quality and graph readability.

## Init template

When you run `ztlctl init`, the initialization pipeline renders a `methodology.md` file into your vault's `self/` directory. This file is your operational reference — a vault-specific guide customized to the tone, profile, and topics you chose during init.

The template lives at `src/ztlctl/templates/self/methodology.md.j2` in the ztlctl source. It contains:

- Core principles (atomic notes, progressive formalization, bidirectional linking, tag taxonomy)
- Content type reference table (ID patterns, status flows)
- Workflow guidance keyed to your vault tone (`research-partner`, `assistant`, or `minimal`)
- The prose-as-title convention table, when tone is `research-partner`
- Graph maintenance commands
- Obsidian integration notes (when profile is `obsidian`)
- Tool reference table

To regenerate `self/methodology.md` after changing your vault settings:

```bash
ztlctl agent regenerate
```

This re-renders both `identity.md` and `methodology.md` from current vault config without affecting any notes. It detects staleness automatically — if settings have not changed since the last render, regenerate reports that no update is needed.

To customize the methodology further, edit `self/methodology.md` directly in your vault. The file is plain markdown — no special syntax required.

!!! warning
    `ztlctl agent regenerate` overwrites `self/methodology.md`. Save local customizations outside `self/` or in a separate note before regenerating.

## What's next

- [Core Concepts](concepts.md) — content types, lifecycle states, and the vault structure underlying all methodology conventions
- [Best Practices](best-practices.md) — opinionated patterns and anti-patterns for notes, tags, sessions, and agent workflows
- [Tutorial](tutorial.md) — hands-on walkthrough that applies these conventions in a real vault
