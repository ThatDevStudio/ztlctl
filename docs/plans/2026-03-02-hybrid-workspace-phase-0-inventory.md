# Hybrid Workspace Phase 0 Inventory

**Date:** 2026-03-02
**Status:** Recorded

## Purpose

Inventory the current hardcoded workspace/client/viewer assumptions that Phase 0 must reconcile.

## Findings

| Surface | Current behavior | Classification | Phase 0 action |
|--------|------------------|----------------|----------------|
| `src/ztlctl/config/models.py` | `vault.client` defaults to `obsidian`; `[plugins]` declares `git` and `obsidian` | Keep `client`, remove stale plugin claim | Normalize `client`; remove canonical `plugins.obsidian` |
| `src/ztlctl/config/settings.py` | TOML/settings composition accepts unknown nested plugin keys | Keep in core | Rely on this for backward compatibility |
| `src/ztlctl/commands/init_cmd.py` | `--client` hardcoded as `obsidian|vanilla` | Rename in Phase 0 | Canonicalize to `obsidian|none`; accept alias |
| `src/ztlctl/services/init.py` | writes `client` to TOML; scaffolds `.obsidian/snippets/ztlctl.css`; maps non-obsidian workflow viewer to `vanilla` | Keep direct Obsidian scaffolding for now; rename non-Obsidian mode | Normalize to `none`; keep init-side Obsidian scaffold |
| `src/ztlctl/commands/workflow.py` | `--viewer` hardcoded as `obsidian|vanilla` | Rename in Phase 0 | Canonicalize to `obsidian|none`; accept alias |
| `src/ztlctl/services/workflow.py` | `Viewer = Literal["obsidian", "vanilla"]`; answers parsing rejects anything else | Rename in Phase 0 | Normalize legacy answers and rewrite canonical `none` |
| `src/ztlctl/commands/export.py` | dashboard export exposes `obsidian|vanilla` | Rename in Phase 0 | Canonicalize to `obsidian|none`; accept alias |
| `src/ztlctl/services/export.py` | viewer drives wikilink vs portable markdown rendering | Keep in core for now | Rename portable mode to `none` |
| `src/ztlctl/templates/workflow/copier.yml` | viewer choices include `vanilla` | Rename in Phase 0 | Replace with `none` |
| `src/ztlctl/templates/workflow/layers/viewer/vanilla.md.jinja` | portable viewer layer uses `vanilla` filename | Rename in Phase 0 | Rename layer file to `none.md.jinja` |
| `src/ztlctl/templates/self/*.md.j2` | stale IDs, stale `sapling`, stale task lifecycle | Remove stale semantics | Rewrite to actual domain truth |
| `DESIGN.md` / docs | docs claim `obsidian|vanilla`, `[plugins].obsidian`, and broader Obsidian behavior than exists | Remove stale claims | Reconcile to current implementation |
| `tests/...` | tests mix canonical `vanilla` with one internal `none` case | Rename plus compatibility coverage | Update most tests to `none`; keep alias tests |
| `src/ztlctl/infrastructure/filesystem.py` | discovery walks only `notes/` and `ops/`; skips `.obsidian/` | Keep in core for now | Record as current indexing truth |

## Key Conclusions

- `client` is still the current vault-facing abstraction.
- `viewer` is still the current workflow/export abstraction.
- `vanilla` is the main naming drift and should be normalized to `none`.
- `.obsidian` integration is still a direct init concern, not a plugin-owned workspace profile.
- the config model overstated built-in Obsidian integration through `[plugins].obsidian`.
- `garden/` is not currently a core-owned indexed path because discovery only traverses `notes/` and `ops/`.
