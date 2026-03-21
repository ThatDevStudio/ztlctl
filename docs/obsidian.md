---
title: Obsidian Starter Kit
---

# Obsidian Starter Kit

This guide walks through setting up the first-party Obsidian integration from vault init through community plugin activation. The obsidian workspace profile scaffolds a curated starter kit optimized for hybrid human-agent knowledge work. You don't need Obsidian to use ztlctl — this guide is for users who want to pair the two.

The first-party `obsidian` workspace profile scaffolds a curated Obsidian starter kit for hybrid knowledge work.

It creates:

- `.obsidian/` starter configuration scaffolded during init
- `garden/` directories and templates owned by the human after scaffold
- install and verification guidance shown during `ztlctl init --profile obsidian`

It does **not**:

- download community plugin binaries
- enable plugins automatically inside Obsidian
- index `garden/` through the ztlctl core

## Setup Walkthrough

### Scenario 1: Research Vault

Initialize a research vault with the Obsidian profile — the most common setup for academics and knowledge workers tracking literature and concepts:

```bash
ztlctl init --path research-vault --profile obsidian --name "Research Vault" --topics "ml,systems"
cd research-vault
```

Expected output:

```
✓ Vault initialized: research-vault/
✓ Obsidian starter kit scaffolded (.obsidian/, garden/)
✓ Community plugin configs written

Next steps for Obsidian:
1. Open research-vault/ in Obsidian and trust it
2. Settings → Community plugins → Browse → install: dataview, templater-obsidian,
   folder-notes, omnisearch, obsidian-book-search-plugin
3. Enable all five plugins
4. Verify settings in .obsidian/ took effect (graph view, templates path)
```

!!! note
    ztlctl writes the .obsidian/ starter files during init, then leaves them for you to customize. After the first open, .obsidian/ is yours — ztlctl won't overwrite your changes.

### Scenario 2: Team Wiki Vault

A team wiki benefits from the same profile, with topics aligned to project areas and the git plugin enabled so edits are tracked automatically:

```bash
ztlctl init --path team-wiki --profile obsidian --name "Team Wiki" --topics "architecture,ops,decisions"
cd team-wiki
```

Configure the git plugin for team use in `ztlctl.toml`:

```toml
[plugins.git]
enabled = true
batch_commits = false    # commit immediately so teammates see changes faster
auto_push = true         # push to shared remote on every operation
```

Each teammate's Obsidian instance opens the same vault directory. ztlctl's database (`/.ztlctl/`) is not shared via git — only the markdown files and `.obsidian/` config are committed. Run `ztlctl check rebuild` to re-derive the local database from the shared files when conflicts arise.

## What Gets Scaffolded

The Obsidian starter kit writes:

- `.obsidian/app.json`
- `.obsidian/appearance.json`
- `.obsidian/core-plugins.json`
- `.obsidian/community-plugins.json`
- `.obsidian/templates.json`
- `.obsidian/graph.json`
- `.obsidian/snippets/ztlctl.css`
- `.obsidian/snippets/garden-layers.css`
- plugin config files for `folder-notes`, `omnisearch`, and `obsidian-book-search-plugin`
- `garden/README.md`
- `garden/notes/`, `garden/groves/`, `garden/library/`, `garden/canvases/`, `garden/attachments/`
- `garden/templates/note.md`, `grove.md`, and `book.md`

## Curated Community Plugin Preset

The generated `.obsidian/community-plugins.json` expects you to install:

- `dataview`
- `templater-obsidian`
- `folder-notes`
- `omnisearch`
- `obsidian-book-search-plugin`

ztlctl writes config and guidance for those plugins, but it does not ship the plugin binaries.

## Why Each Community Plugin

| Plugin | Purpose in this workflow |
|--------|--------------------------|
| `dataview` | Query your ztlctl-exported dashboard as a live Obsidian database — surfaces stale notes, seed candidates, and decision queue without leaving Obsidian |
| `templater-obsidian` | Apply garden templates (note.md, grove.md, book.md) scaffolded by ztlctl init — keeps garden entries consistent |
| `folder-notes` | Makes garden/ subdirectory structure navigable in Obsidian's file explorer — groves and canvases get clickable folder notes |
| `omnisearch` | Full-text search across both ztlctl notes AND garden/ content in one Obsidian search bar |
| `obsidian-book-search-plugin` | Fetch metadata for books added to the library/ garden layer — configured to match the book.md template |

## Vault Structure

The vault contains both machine-managed paths (owned by ztlctl) and human-managed paths (owned by you):

```
research-vault/
├── ztlctl.toml          # Core config — managed by ztlctl
├── .ztlctl/             # Internal state (DB, backups) — managed by ztlctl
├── self/                # Identity and methodology files — managed by ztlctl
├── notes/               # Atomic knowledge notes — managed by ztlctl
├── ops/                 # Tasks and session logs — managed by ztlctl
├── sources/             # Ingested source bundles — managed by ztlctl
├── .obsidian/           # Obsidian workspace config — scaffolded by ztlctl, then yours
└── garden/              # Human-managed knowledge garden — never touched by ztlctl
    ├── README.md
    ├── notes/           # Garden notes (seed → sprout → evergreen)
    ├── groves/          # Topic clusters
    ├── library/         # Books and long-form sources
    ├── canvases/        # Visual mind maps
    ├── attachments/     # Images and files
    └── templates/       # note.md, grove.md, book.md
```

!!! tip
    garden/ is intentionally outside ztlctl's indexing. You can freely restructure, rename, and reorganize garden/ content without affecting ztlctl's graph or database.

## Ownership

- Core-managed paths: `ztlctl.toml`, `.ztlctl/`, `self/`, `notes/`, `ops/`
- Profile-associated scaffold surface: `.obsidian/`
- Human-managed paths: `garden/`

`ztlctl` writes the `.obsidian/` starter files during init, then leaves them for you to customize in Obsidian or by editing the files directly. `garden/` is intentionally outside default indexing and mutation. The core vault model still indexes only `notes/` and `ops/`.

## First Open in Obsidian

After `ztlctl init --profile obsidian`:

1. Open the vault in Obsidian and trust it.
2. Install the curated community plugins from Settings -> Community plugins.
3. Enable those plugins so the scaffolded config in `.obsidian/` takes effect.
4. Verify that new notes target `garden/notes`, attachments target `garden/attachments`, templates point at `garden/templates`, and both CSS snippets are enabled.

The same checklist is printed during init and stored in `garden/README.md`. `ztlctl` does not later validate or rewrite your `.obsidian/` changes.

## Using garden/ for Enrichment

After a ztlctl session, export a review dashboard and open it in Obsidian to guide garden work:

```bash
# After closing a session, generate a review workbench
ztlctl export dashboard ./dashboard/ --viewer obsidian

# Then open dashboard/ in Obsidian alongside your vault
# The dashboard shows: stale notes, orphan candidates, topic dossiers
```

The exported dashboard is a machine-layer review workbench — not a mirror of garden/. Use it to decide what to tend next, then do the tending in Obsidian's garden/ directly.

## Relationship to Export

`ztlctl export dashboard ./output/ --viewer obsidian` is an external review workbench, not part of the starter kit itself. It gives you portable markdown and JSON review artifacts for triage and topic review, but it does not export the literal `garden/` directory and it does not mirror `.obsidian/` workspace state.

## Common Pitfalls

**Sync conflicts from `.ztlctl/` in git:**
The `.ztlctl/` directory contains the SQLite database and binary backup files. Never commit it — it is written to `.gitignore` automatically during `ztlctl init`. If it ends up in git, binary merge conflicts will corrupt the database. Remove it from git tracking with `git rm -r --cached .ztlctl/`.

**Manually editing the SQLite database:**
The `.ztlctl/ztlctl.db` file is managed exclusively by ztlctl. Editing it directly with a SQLite browser bypasses frontmatter sync and breaks the filesystem-as-source-of-truth contract. If you need to correct a record, update the corresponding `.md` file and run `ztlctl check rebuild` to re-derive the database.

**Ignoring the `.ztlctl/` directory in Obsidian:**
Obsidian's file indexer will try to open `.ztlctl/` contents if not excluded. Add `.ztlctl` to Obsidian's excluded file paths in Settings → Files & Links → Excluded files to keep binary files out of Obsidian search and graph.

**Modifying `.obsidian/` config and expecting ztlctl to re-read it:**
ztlctl reads vault config from `ztlctl.toml` only. Changes to `.obsidian/app.json` or similar files are not read by ztlctl. The relationship is one-directional: ztlctl writes `.obsidian/` once at init, then Obsidian and you own it.

## Next Steps

- See [Built-in Plugins](plugins.md) for Git and Reweave plugin configuration, including git plugin setup for team vaults
- See [Agentic Workflows](agentic-workflows.md) for session lifecycle and recipe walkthroughs
- See [Configuration](configuration.md) for the full ztlctl.toml reference
