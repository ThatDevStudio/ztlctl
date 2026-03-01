---
name: vault-methodology
description: >
  Use when working in a ztlctl vault — creating notes, organizing knowledge,
  tagging, linking, or making decisions about content types and structure.
  Activates for any knowledge management task.
version: 1.0.0
---

# Zettelkasten Methodology for ztlctl Vaults

You are working in a ztlctl knowledge vault — an agentic note-taking system built on zettelkasten, second-brain, and knowledge-garden paradigms.

## Core Principle: Atomic, Connected Knowledge

Every piece of knowledge should be:
1. **Atomic** — one idea per note, self-contained
2. **Connected** — linked to related ideas via wikilinks and tags
3. **Evolving** — progressing through maturity stages over time

## Content Type Decision Tree

Before creating content, choose the right type:

- **Is it an idea, concept, or insight?** → `note`
  - Is it a decision with alternatives? → `note` with subtype `decision`
  - Does it capture key points from learning? → `note` with subtype `knowledge`
- **Is it an external source (article, paper, tool, spec)?** → `reference`
  - Classify with subtype: `article`, `tool`, or `spec`
- **Is it something to do?** → `task`
  - Set priority/impact/effort for scoring
- **Starting a research session?** → `log` (via session start)

## Quick-Capture vs. Full Notes

Use `garden_seed` (or `/ztlctl:seed`) to capture ideas quickly with `maturity=seed`. Seeds are:
- Low-ceremony: just a title and optional tags
- Time-tracked: vault warns if seeds go unattended for >7 days
- Body-protected: reweave won't modify their content

Progress seeds → `budding` → `evergreen` as you develop them.

## Tags

Use hierarchical `domain/scope` format:
- `math/algebra`, `python/stdlib`, `research/methodology`
- Single-segment tags (e.g., `important`) are valid but get classified as `unscoped`

Tags enable filtered search and cross-cutting discovery.

## Linking

Use `[[wikilinks]]` in note bodies to connect ideas. Links can reference:
- Titles: `[[Machine Learning Fundamentals]]`
- Aliases: `[[ML Basics]]`
- IDs: `[[ztl_a1b2c3d4]]`

The reweave system automatically suggests and creates links based on 4 signals:
lexical similarity, tag overlap, graph proximity, and topic match.

## Key Invariants

1. **Note status is automatic** — computed from outgoing link count (draft→linked→connected)
2. **Accepted decisions are immutable** — only metadata can change after acceptance
3. **Garden notes (maturity set) have body protection** — automated tools won't modify their body
4. **Archive is soft-delete** — preserves edges, hides from default queries

For detailed reference, see:
- `references/content-types.md` — full content type specifications
- `references/linking-patterns.md` — wikilink resolution and reweave mechanics
- `references/lifecycle.md` — status transitions, maturity stages, archive behavior
