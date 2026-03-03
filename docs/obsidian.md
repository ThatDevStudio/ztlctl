---
title: Obsidian Starter Kit
nav_order: 8
---

# Obsidian Starter Kit

The first-party `obsidian` workspace profile scaffolds a curated Obsidian starter kit for hybrid knowledge work.

It creates:

- `.obsidian/` starter configuration scaffolded during init
- `garden/` directories and templates owned by the human after scaffold
- install and verification guidance shown during `ztlctl init --profile obsidian`

It does **not**:

- download community plugin binaries
- enable plugins automatically inside Obsidian
- index `garden/` through the ztlctl core

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
