# Phase 8: MkDocs Infrastructure - Research

**Researched:** 2026-03-20
**Domain:** MkDocs + mkdocs-shadcn theme, GitHub Actions docs deploy, URL redirect handling, internal artifact exclusion
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Replace Jekyll in-place — remove `docs/_config.yml` and add `mkdocs.yml` at project root
- Migrate all 16 existing markdown files to MkDocs-compatible format (update front matter from Jekyll `nav_order`/`title` to MkDocs `nav:` config)
- Delete internal planning artifacts from docs/: `backlog.md`, `research-mapping.md`, `roadmap.md`
- Exclude `docs/plans/` from the built site via mkdocs.yml (don't delete the directory, just exclude from build)
- Keep docs content in `docs/` directory (MkDocs `docs_dir: docs`)
- Use mkdocs-shadcn theme (`pip install mkdocs-shadcn`, `theme: name: shadcn`)
- Dark mode as default with toggle available for light mode
- Use `mkdocs-redirects` plugin to create redirect stubs for any URLs that change during migration
- All 16 current docs pages must have working redirects if their paths change
- External links from README.md, PyPI, GitHub issues must continue to work
- New GitHub Actions workflow: `.github/workflows/docs.yml`
- Trigger: push to `develop` branch (matches existing release pipeline pattern)
- Build: `mkdocs build` then deploy to `gh-pages` branch via `mkdocs gh-deploy`
- Remove Jekyll-specific files: `_config.yml`, `Gemfile`, `Gemfile.lock` (if present)

### Claude's Discretion
- Exact mkdocs.yml plugin configuration beyond shadcn + redirects
- Whether to add `mkdocs-minify-plugin` or other build optimizations
- Footer content and layout details
- Search configuration tuning

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| INFR-01 | Migrate from Jekyll + Just the Docs to MkDocs + mkdocs-shadcn theme with dark mode, modern shadcn/ui aesthetic | mkdocs-shadcn 0.10.2 installation, theme config, pygments_style dark/light dict |
| INFR-02 | Remove internal planning artifacts from public docs site (backlog.md, research-mapping.md, internal roadmap.md) | Physical deletion from docs/ root; these are loose .md files, not in plans/ |
| INFR-03 | Exclude docs/plans/ directory from published site via mkdocs.yml config | `exclude_docs` gitignore pattern: `plans/` covers the entire subdirectory |
| INFR-04 | Set up GitHub Actions workflow for MkDocs gh-deploy to GitHub Pages | `contents: write` permission + `mkdocs gh-deploy --force` to gh-pages branch |
| INFR-05 | Add redirect handling for changed URLs to preserve existing links | mkdocs-redirects 1.2.2 `redirect_maps` config; all 16 pages stay at root so NO URL changes occur if files remain at docs/*.md |
</phase_requirements>

---

## Summary

This phase replaces the Jekyll + Just the Docs pipeline with MkDocs + mkdocs-shadcn. The existing Jekyll site auto-builds from `docs/` via GitHub's built-in Pages integration; after migration, a new `.github/workflows/docs.yml` takes over using `mkdocs gh-deploy --force` to push the built site to a `gh-pages` branch.

The critical insight that simplifies this phase: **all 16 existing docs pages live at `docs/*.md` and can remain there**. MkDocs builds them at the same URL paths (`/ztlctl/commands`, `/ztlctl/installation`, etc.) as long as `docs_dir: docs` and `use_directory_urls: true` (MkDocs default). This means most pages need **zero redirect stubs** — the URL structure is preserved by keeping files in place. Only files that are moved or renamed need `redirect_maps` entries.

The three internal artifacts (`backlog.md`, `research-mapping.md`, `roadmap.md`) must be physically deleted from `docs/` — they are not in `docs/plans/`. The `docs/plans/` directory is excluded from the build via `exclude_docs`, but the directory is not deleted (it holds `.md` planning files).

**Primary recommendation:** Keep all 16 docs files at `docs/*.md` (no subdirectory move), configure `nav:` explicitly in `mkdocs.yml` to control ordering, delete the three internal artifacts, add `exclude_docs: plans/`, set up GitHub Actions workflow with `contents: write` permission, and install mkdocs + mkdocs-shadcn + mkdocs-redirects as dev dependencies.

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| mkdocs | 1.6.1 | Static site generator for docs | Industry standard Python docs builder; powers the entire build pipeline |
| mkdocs-shadcn | 0.10.2 | Shadcn/ui-styled theme for MkDocs | Decided by user; modern aesthetic; v0.10.2 released 2026-03-19 (current) |
| mkdocs-redirects | 1.2.2 | HTML redirect stub generation | Official mkdocs plugin; handles URL preservation; released 2024-11-07 |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| actions/checkout | v4 | GitHub Actions repo checkout | Standard in all existing workflows |
| actions/setup-python | v5 | Python setup in GitHub Actions | Standard for pip-based installations in CI |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| mkdocs-shadcn | Material for MkDocs | Material is more mature but user specifically wants shadcn/ui aesthetic |
| mkdocs-redirects | meta-refresh in HTML | mkdocs-redirects automates this; same underlying mechanism (no server-side redirects on GitHub Pages) |
| `mkdocs gh-deploy` | `actions/deploy-pages` | `gh-deploy` is simpler, writes to gh-pages branch directly; deploy-pages requires separate build/upload steps |

**Installation (dev dependencies only — not shipped in ztlctl package):**
```bash
uv add --group dev mkdocs mkdocs-shadcn mkdocs-redirects
```

**Version verification (confirmed 2026-03-20):**
- mkdocs: 1.6.1 (PyPI confirmed)
- mkdocs-shadcn: 0.10.2 (PyPI confirmed, released 2026-03-19)
- mkdocs-redirects: 1.2.2 (PyPI confirmed, released 2024-11-07)

---

## Architecture Patterns

### Recommended Project Structure

The critical decision: **do not move the 16 existing doc files into subdirectories during Phase 8**. Navigation restructuring into two-track User Guide / Developer Guide sections is Phase 9. This phase is infrastructure only. Keep all docs at `docs/*.md`.

```
docs/
├── index.md                         # Landing page — keep, update front matter
├── installation.md                  # Keep at root — URL preserved
├── quickstart.md                    # Keep at root — URL preserved
├── tutorial.md                      # Keep at root — URL preserved
├── concepts.md                      # Keep at root — URL preserved
├── paradigms.md                     # Keep at root — URL preserved
├── obsidian.md                      # Keep at root — URL preserved
├── commands.md                      # Keep at root — URL preserved
├── configuration.md                 # Keep at root — URL preserved
├── mcp.md                           # Keep at root — URL preserved
├── agentic-workflows.md             # Keep at root — URL preserved
├── troubleshooting.md               # Keep at root — URL preserved
├── development.md                   # Keep at root — URL preserved
├── backlog.md                       # DELETE — internal artifact
├── research-mapping.md              # DELETE — internal artifact
├── roadmap.md                       # DELETE — internal artifact
└── plans/                           # Keep directory, exclude from build
    └── *.md

mkdocs.yml                           # NEW: at project root (replaces docs/_config.yml)
.github/workflows/docs.yml           # NEW: MkDocs deploy workflow
```

**Files removed:** `docs/_config.yml` (Jekyll config, no longer needed)
**Files to delete:** `docs/backlog.md`, `docs/research-mapping.md`, `docs/roadmap.md`
**Note:** No `Gemfile` or `Gemfile.lock` were found in the repo — nothing to remove there.

### Pattern 1: mkdocs.yml Configuration

**What:** Single config file at project root. Uses `docs_dir: docs` to point to existing docs directory. Explicit `nav:` controls page ordering (replaces Jekyll's `nav_order:` front matter). `exclude_docs` pattern removes `plans/` from the build. Theme config sets shadcn with dark/light pygments styles.

**Example mkdocs.yml:**
```yaml
# Source: https://www.mkdocs.org/user-guide/configuration/ + https://asiffer.github.io/mkdocs-shadcn/get_started/
site_name: ZettelControl
site_description: CLI utility and agentic note-taking ecosystem for knowledge graph management.
site_url: https://thatdevstudio.github.io/ztlctl/
repo_url: https://github.com/ThatDevStudio/ztlctl
repo_name: ThatDevStudio/ztlctl

docs_dir: docs

theme:
  name: shadcn
  show_title: true
  show_stargazers: true
  show_datetime: false
  pygments_style:
    light: shadcn-light
    dark: github-dark

exclude_docs: |
  plans/

nav:
  - Home: index.md
  - Installation: installation.md
  - Quick Start: quickstart.md
  - Tutorial: tutorial.md
  - Core Concepts: concepts.md
  - Knowledge Paradigms: paradigms.md
  - Obsidian Starter Kit: obsidian.md
  - Command Reference: commands.md
  - Configuration: configuration.md
  - MCP Server: mcp.md
  - Agentic Workflows: agentic-workflows.md
  - Troubleshooting: troubleshooting.md
  - Development: development.md

plugins:
  - search
  - redirects:
      redirect_maps: {}

markdown_extensions:
  - admonition
  - attr_list
  - def_list
  - fenced_code
  - footnotes
  - tables
  - toc:
      permalink: true

copyright: >-
  MIT License. Distributed under the
  <a href="https://github.com/ThatDevStudio/ztlctl/blob/develop/LICENSE">MIT License</a>.
```

**Key notes:**
- `exclude_docs: plans/` uses gitignore-pattern syntax (introduced MkDocs 1.5, stable in 1.6.1)
- `plugins: - search` must be explicitly listed when using any other plugins (MkDocs default search is overridden otherwise)
- `redirect_maps: {}` is initially empty — populated only if URLs actually change
- `pygments_style` dict enables separate light/dark code themes without extra configuration

### Pattern 2: Front Matter Migration

**What:** Jekyll front matter uses `nav_order:` and `title:` for navigation ordering. MkDocs ignores these fields entirely — page ordering and titles come from `nav:` in `mkdocs.yml` (when explicitly configured). The existing front matter is harmless but redundant.

**Jekyll format (current):**
```yaml
---
title: Command Reference
nav_order: 6
---
```

**MkDocs format (after migration):**
```yaml
---
title: Command Reference
---
```

**Action:** Remove `nav_order:` from all 16 files' front matter. The `title:` field is still respected by MkDocs for the page's `<title>` tag and breadcrumbs. Navigation ordering is controlled entirely by `nav:` in `mkdocs.yml`.

**Important:** `index.md` has `title: Home` and `nav_order: 1`. After migration, the `nav:` in mkdocs.yml controls order, so `nav_order: 1` is removed. But keep `title: Home` — it controls the browser tab title.

### Pattern 3: GitHub Actions Docs Workflow

**What:** New `.github/workflows/docs.yml` triggering on push to `develop`, installing Python + MkDocs stack, running `mkdocs gh-deploy --force`.

**When to use:** Fires on every push to develop, same trigger as release-pipeline.yml.

**Key permissions:** `contents: write` is required for `mkdocs gh-deploy` to push to the `gh-pages` branch.

```yaml
# Source: https://squidfunk.github.io/mkdocs-material/publishing-your-site/
# (standard pattern, verified for mkdocs gh-deploy)
name: Deploy Docs

on:
  push:
    branches: [develop]
  workflow_dispatch:

permissions:
  contents: write

jobs:
  deploy:
    name: Deploy to GitHub Pages
    runs-on: ubuntu-latest
    steps:
      - name: Check out repository
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.x'

      - name: Install MkDocs dependencies
        run: pip install mkdocs mkdocs-shadcn mkdocs-redirects

      - name: Configure git identity
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "41898282+github-actions[bot]@users.noreply.github.com"

      - name: Deploy docs
        run: mkdocs gh-deploy --force
```

**Notes:**
- Uses `pip install` directly (not `uv`) because the CI environment only needs docs tools, not the full project dev environment
- `fetch-depth: 0` is needed by `mkdocs gh-deploy` to access `gh-pages` branch history
- `--force` overwrites the gh-pages branch on every deploy
- `workflow_dispatch:` allows manual triggering during migration testing

### Pattern 4: URL Preservation Analysis

**What:** Current Jekyll site serves pages at `/ztlctl/<filename>` (e.g., `/ztlctl/commands`). MkDocs with `use_directory_urls: true` (default) serves them at `/ztlctl/commands/` (trailing slash, `index.html` inside directory). Browsers and most link resolvers handle the redirect from `/ztlctl/commands` to `/ztlctl/commands/` automatically (GitHub Pages handles this).

**Analysis of all 16 pages:**

| Current URL | File Location | Post-Migration URL | Redirect Needed? |
|---|---|---|---|
| `/ztlctl/` | docs/index.md | `/ztlctl/` | No |
| `/ztlctl/installation` | docs/installation.md | `/ztlctl/installation/` | No (trailing slash handled by host) |
| `/ztlctl/quickstart` | docs/quickstart.md | `/ztlctl/quickstart/` | No |
| `/ztlctl/tutorial` | docs/tutorial.md | `/ztlctl/tutorial/` | No |
| `/ztlctl/concepts` | docs/concepts.md | `/ztlctl/concepts/` | No |
| `/ztlctl/paradigms` | docs/paradigms.md | `/ztlctl/paradigms/` | No |
| `/ztlctl/obsidian` | docs/obsidian.md | `/ztlctl/obsidian/` | No |
| `/ztlctl/commands` | docs/commands.md | `/ztlctl/commands/` | No |
| `/ztlctl/configuration` | docs/configuration.md | `/ztlctl/configuration/` | No |
| `/ztlctl/mcp` | docs/mcp.md | `/ztlctl/mcp/` | No |
| `/ztlctl/agentic-workflows` | docs/agentic-workflows.md | `/ztlctl/agentic-workflows/` | No |
| `/ztlctl/troubleshooting` | docs/troubleshooting.md | `/ztlctl/troubleshooting/` | No |
| `/ztlctl/development` | docs/development.md | `/ztlctl/development/` | No |
| `/ztlctl/backlog` | docs/backlog.md | DELETED | Add redirect if needed |
| `/ztlctl/research-mapping` | docs/research-mapping.md | DELETED | Add redirect if needed |
| `/ztlctl/roadmap` | docs/roadmap.md | DELETED | Add redirect if needed |

**Conclusion:** Zero redirect stubs needed for the 13 public pages — URLs are preserved (trailing slash difference is handled by host). The three deleted internal pages (`backlog.md`, `research-mapping.md`, `roadmap.md`) could redirect to `index.md` if desired, but since these are internal artifacts, 404 is acceptable. README.md links to these must be removed regardless.

**`redirect_maps` in mkdocs.yml can start empty:**
```yaml
plugins:
  - redirects:
      redirect_maps: {}
```

### Pattern 5: GitHub Pages Source Migration

**What:** The current setup has GitHub Pages serving from the `docs/` folder of the `develop` branch (Jekyll auto-build mode). After migration, GitHub Pages source must be changed to the `gh-pages` branch (where `mkdocs gh-deploy` pushes the built site).

**Action required:** After the first successful `mkdocs gh-deploy` run, change the repository's Pages settings:
- Repository Settings → Pages → Source: change from "Deploy from branch: develop / docs" to "Deploy from branch: gh-pages / root"

**This is a one-time manual step** in the GitHub repository settings UI. It cannot be automated via GitHub Actions.

### Anti-Patterns to Avoid

- **Moving all 16 docs files into subdirectories in Phase 8:** Navigation restructuring is Phase 9. Moving files in Phase 8 would require redirect stubs and interleave two concerns. Keep files at `docs/*.md` for Phase 8.
- **Omitting `- search` from plugins list:** When `plugins:` is defined in mkdocs.yml, it overrides MkDocs defaults. The built-in search plugin is no longer auto-included — it must be listed explicitly.
- **Using `uv run mkdocs gh-deploy` in CI:** The CI workflow doesn't need the full uv project environment. Use `pip install` for simplicity — the docs build doesn't need the ztlctl package installed.
- **Setting `use_directory_urls: false`:** This would change URL structure to `/ztlctl/commands.html` — worse for SEO and breaks the trailing-slash pattern browsers expect. Use the default `true`.
- **Forgetting `fetch-depth: 0`:** `mkdocs gh-deploy` pushes to the `gh-pages` branch; without full git history, it may fail to find the remote ref.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| HTML redirect stubs | Custom Python script generating meta-refresh HTML | mkdocs-redirects plugin | Plugin handles `use_directory_urls` correctly, integrates with `mkdocs build`, creates proper stub pages |
| Dark/light code themes | Custom CSS overrides | `pygments_style: light/dark dict` in mkdocs-shadcn | Built-in theme support handles both modes automatically |
| Docs directory exclusion | Custom plugin or pre-build script | `exclude_docs: plans/` in mkdocs.yml | Native MkDocs 1.5+ feature; gitignore-pattern syntax handles glob exclusions |

**Key insight:** MkDocs 1.5+ covers the file exclusion requirement natively. No custom plugins are needed for this phase.

---

## Common Pitfalls

### Pitfall 1: Jekyll Pages Source Not Switched to gh-pages Branch
**What goes wrong:** New `docs.yml` workflow runs successfully and pushes to `gh-pages`, but the live site still shows the old Jekyll content because GitHub Pages is still serving from `develop/docs/`.
**Why it happens:** GitHub Pages source is a repository setting, not controlled by the workflow. The workflow and the Pages setting are independent.
**How to avoid:** Immediately after the first successful `mkdocs gh-deploy` run, update the Pages source in repo settings. Sequence: workflow runs → Pages source updated → verify deployed site.
**Warning signs:** Workflow shows green but the live site looks unchanged (still Jekyll-styled).

### Pitfall 2: search Plugin Silently Dropped
**What goes wrong:** Site builds without errors but the search bar is missing on the deployed site.
**Why it happens:** Specifying `plugins:` in mkdocs.yml overrides the default plugin list. MkDocs no longer auto-includes the built-in search plugin.
**How to avoid:** Always include `- search` as the first entry under `plugins:` when defining any plugins.
**Warning signs:** `mkdocs build` succeeds but no search bar in `site/` output.

### Pitfall 3: Dark Mode Has No Configuration Switch to Force Default
**What goes wrong:** The user wants dark mode as the default. The mkdocs-shadcn theme uses system preferences + localStorage for dark/light mode — there is no `default_theme: dark` configuration option.
**Why it happens:** The theme follows the shadcn/ui pattern: detect system preference, save to localStorage. The `pygments_style` dict only controls code block colors, not the UI theme default.
**How to avoid:** The theme auto-respects system dark mode preference. For users whose systems are set to light mode, the site shows light mode. This is the expected behavior — not a bug. The "dark mode as default" decision is best interpreted as "dark mode supported and code blocks styled for dark". No additional config is needed.
**Warning signs:** Trying to add a non-existent `default_color_scheme: dark` or `color_mode: dark` config key (these don't exist in mkdocs-shadcn; they're Material for MkDocs options).

### Pitfall 4: README.md Links to Deleted Internal Artifacts
**What goes wrong:** `backlog.md`, `research-mapping.md`, and `roadmap.md` are deleted, but `docs/index.md` and `README.md` still link to them.
**Why it happens:** The current `docs/index.md` "For Developers and Agents" section links to `roadmap.md`, `research-mapping.md`, and `backlog.md`. These links become 404s after deletion.
**How to avoid:** Update `docs/index.md` and `README.md` in the same task that deletes the three files. The "For Developers and Agents" section in `index.md` should be simplified to only link to `development.md`, `agentic-workflows.md`, and `troubleshooting.md`.
**Warning signs:** `mkdocs build --strict` reports warnings about missing reference targets.

### Pitfall 5: mkdocs.yml `nav:` Omits a File That Still Exists
**What goes wrong:** A file in `docs/*.md` is not listed in the `nav:` config and is not in `exclude_docs`. MkDocs warns "Doc file 'X' is not included in the nav." In strict mode this becomes an error.
**Why it happens:** After deleting the 3 internal artifacts, exactly 13 public pages remain. If the `nav:` list has 12 entries (missed one), MkDocs warns for the unlisted file.
**How to avoid:** After deletion, the final docs root contains exactly: `index.md`, `installation.md`, `quickstart.md`, `tutorial.md`, `concepts.md`, `paradigms.md`, `obsidian.md`, `commands.md`, `configuration.md`, `mcp.md`, `agentic-workflows.md`, `troubleshooting.md`, `development.md`, and `plans/` (excluded). That's 13 files. The `nav:` config must list all 13.

### Pitfall 6: `exclude_docs` Pattern Syntax Error
**What goes wrong:** Writing `exclude_docs: plans/` as a scalar string instead of the multi-line string format causes a YAML parse error or unexpected behavior.
**Why it happens:** The MkDocs docs show `exclude_docs` as a YAML block scalar (using `|`). A bare scalar works for a single pattern, but the `|` block scalar format is the documented and safe approach.
**How to avoid:** Use the block scalar format:
```yaml
exclude_docs: |
  plans/
```
**Warning signs:** `mkdocs build` raises a YAML parse error or the `plans/` directory content appears in the built site.

---

## Code Examples

Verified patterns from official sources:

### Complete mkdocs.yml for Phase 8
```yaml
# mkdocs.yml — project root
# Source: https://www.mkdocs.org/user-guide/configuration/ + https://asiffer.github.io/mkdocs-shadcn/get_started/
site_name: ZettelControl
site_description: CLI utility and agentic note-taking ecosystem for knowledge graph management.
site_url: https://thatdevstudio.github.io/ztlctl/
repo_url: https://github.com/ThatDevStudio/ztlctl
repo_name: ThatDevStudio/ztlctl

docs_dir: docs

theme:
  name: shadcn
  show_title: true
  show_stargazers: true
  show_datetime: false
  pygments_style:
    light: shadcn-light
    dark: github-dark

exclude_docs: |
  plans/

nav:
  - Home: index.md
  - Installation: installation.md
  - Quick Start: quickstart.md
  - Tutorial: tutorial.md
  - Core Concepts: concepts.md
  - Knowledge Paradigms: paradigms.md
  - Obsidian Starter Kit: obsidian.md
  - Command Reference: commands.md
  - Configuration: configuration.md
  - MCP Server: mcp.md
  - Agentic Workflows: agentic-workflows.md
  - Troubleshooting: troubleshooting.md
  - Development: development.md

plugins:
  - search
  - redirects:
      redirect_maps: {}

markdown_extensions:
  - admonition
  - attr_list
  - def_list
  - fenced_code
  - footnotes
  - tables
  - toc:
      permalink: true

copyright: >-
  MIT License. Distributed under the
  <a href="https://github.com/ThatDevStudio/ztlctl/blob/develop/LICENSE">MIT License</a>.
```

### GitHub Actions Docs Workflow
```yaml
# .github/workflows/docs.yml
# Source: https://squidfunk.github.io/mkdocs-material/publishing-your-site/ (standard pattern)
name: Deploy Docs

on:
  push:
    branches: [develop]
  workflow_dispatch:

permissions:
  contents: write

jobs:
  deploy:
    name: Deploy to GitHub Pages
    runs-on: ubuntu-latest
    steps:
      - name: Check out repository
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.x'

      - name: Install MkDocs dependencies
        run: pip install mkdocs==1.6.1 mkdocs-shadcn==0.10.2 mkdocs-redirects==1.2.2

      - name: Configure git identity
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "41898282+github-actions[bot]@users.noreply.github.com"

      - name: Deploy docs
        run: mkdocs gh-deploy --force
```

### Front Matter Migration Example
```yaml
# BEFORE (Jekyll format — current state)
---
title: Command Reference
nav_order: 6
---

# AFTER (MkDocs format — nav_order removed, title kept)
---
title: Command Reference
---
```

### pyproject.toml Dev Dependency Addition
```toml
# Run: uv add --group dev mkdocs mkdocs-shadcn mkdocs-redirects
# This adds to [dependency-groups] dev in pyproject.toml
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Jekyll + remote_theme | MkDocs + mkdocs-shadcn | This phase | No more Ruby dependency; Python-native build pipeline |
| GitHub Pages auto-build from docs/ | mkdocs gh-deploy to gh-pages branch | This phase | Full control over build process; requires Pages source setting change |
| `nav_order:` front matter (Just the Docs) | `nav:` in mkdocs.yml | This phase | Centralized navigation config instead of distributed front matter |
| `exclude:` in _config.yml (Jekyll) | `exclude_docs:` in mkdocs.yml (MkDocs) | This phase | Gitignore-pattern syntax; cleaner exclusion mechanism |

**Deprecated/removed:**
- `docs/_config.yml`: Jekyll config — deleted as part of this phase
- Jekyll `nav_order:` front matter: Replaced by `nav:` in mkdocs.yml — stripped from all 16 files
- GitHub Pages "Deploy from branch: develop/docs": Replaced by gh-pages branch deployment

---

## Open Questions

1. **Dark mode as explicit default vs. system preference**
   - What we know: mkdocs-shadcn has no `default_color_scheme` config option; it uses system preference detection via CSS `prefers-color-scheme` and localStorage
   - What's unclear: Whether the user expected a "force dark" behavior or "support dark mode" behavior
   - Recommendation: Implement with system preference detection (shadcn default). If the user explicitly wants dark as forced default regardless of system preference, a custom `docs/overrides/` partial would be needed — but this is out of scope and undocumented for mkdocs-shadcn. Treat "dark mode as default" as "dark mode supported with system preference detection."

2. **`mkdocs-minify-plugin` inclusion**
   - What we know: Claude's discretion. The plugin (`mkdocs-minify-plugin`) minifies HTML/CSS/JS output. For a GitHub Pages site with ~13 pages, the benefit is marginal.
   - Recommendation: Skip for Phase 8 — adds a dependency with minimal benefit at this scale. Phase 9+ can add it if desired.

3. **Pinned vs. latest versions in the docs.yml workflow**
   - What we know: Pinning exact versions in `pip install` ensures reproducible builds; using unpinned versions risks unexpected breakage on new releases
   - Recommendation: Pin exact versions in the workflow (`mkdocs==1.6.1 mkdocs-shadcn==0.10.2 mkdocs-redirects==1.2.2`) — matches the approach used in the existing release-pipeline.yml which pins tool invocations explicitly.

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (already in project dev dependencies) |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` |
| Quick run command | `uv run pytest tests/ -q` |
| Full suite command | `uv run pytest --cov --cov-report=term-missing` |

### Phase Requirements → Test Map

This phase is infrastructure/configuration — no Python source code changes occur. The validation approach is build-verification rather than unit tests.

| Req ID | Behavior | Test Type | Automated Command | Notes |
|--------|----------|-----------|-------------------|-------|
| INFR-01 | `mkdocs build` completes with shadcn theme | smoke | `mkdocs build --strict 2>&1` | Manual verification of site/ output; no pytest test |
| INFR-02 | backlog.md, research-mapping.md, roadmap.md absent from docs/ | file-system | `ls docs/ \| grep -E 'backlog\|research-mapping\|roadmap'` returns nothing | Can be a CI check |
| INFR-03 | docs/plans/ excluded from built site | smoke | `mkdocs build && ls site/ \| grep plans` returns nothing | Verified by inspecting site/ output |
| INFR-04 | GitHub Actions workflow deploys on develop push | integration | Manual: push to develop, verify gh-pages branch updated | No automated local test |
| INFR-05 | Redirect stubs present for changed URLs | smoke | `mkdocs build --strict` with no redirect warnings | N/A if no URLs change (Phase 8 keeps files at root) |

**Note:** INFR-01, INFR-03, and INFR-05 are verified by running `mkdocs build --strict` locally before pushing. INFR-02 is verified by `ls docs/`. INFR-04 is verified by observing the GitHub Actions run after merge.

### Sampling Rate
- **Per task commit:** `mkdocs build --strict` (verify build is clean)
- **Per wave merge:** `mkdocs build --strict && ls site/` (verify no plans/ in output, no missing pages)
- **Phase gate:** `mkdocs build --strict` green + docs.yml workflow green on develop + live site renders correctly at `https://thatdevstudio.github.io/ztlctl/`

### Wave 0 Gaps
None — no new Python test files are required. This phase adds no Python source code. The existing 1095+ tests are unaffected. Validation is build-level (`mkdocs build --strict`), not pytest-level.

---

## Sources

### Primary (HIGH confidence)
- [MkDocs Configuration](https://www.mkdocs.org/user-guide/configuration/) — `exclude_docs`, `not_in_nav`, `docs_dir`, `nav`, `use_directory_urls`, plugins override behavior
- [mkdocs-shadcn Get Started](https://asiffer.github.io/mkdocs-shadcn/get_started/) — all 8 theme config options verified, `pygments_style` light/dark dict
- [mkdocs-redirects GitHub](https://github.com/mkdocs/mkdocs-redirects) — `redirect_maps` syntax, version 1.2.2
- PyPI mkdocs: 1.6.1 (confirmed 2026-03-20)
- PyPI mkdocs-shadcn: 0.10.2 (confirmed 2026-03-20, released 2026-03-19)
- PyPI mkdocs-redirects: 1.2.2 (confirmed 2026-03-20)
- Existing codebase: `docs/_config.yml`, `docs/*.md` front matter, `.github/workflows/release-pipeline.yml`

### Secondary (MEDIUM confidence)
- [Material for MkDocs — Publishing Your Site](https://squidfunk.github.io/mkdocs-material/publishing-your-site/) — GitHub Actions workflow pattern with `contents: write` permission; standard pattern applicable to any mkdocs theme
- [MkDocs Deploying Your Docs](https://www.mkdocs.org/user-guide/deploying-your-docs/) — `mkdocs gh-deploy --force` semantics, gh-pages branch behavior

### Tertiary (LOW confidence — for awareness only)
- WebSearch results on mkdocs-shadcn dark mode: consistent finding that no `default_color_scheme` option exists; theme uses system preference detection

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all three package versions verified against PyPI (2026-03-20)
- Architecture: HIGH — URL analysis based on direct file inspection + MkDocs configuration docs
- Pitfalls: HIGH (build tool behavior) / MEDIUM (dark mode expectations — depends on user interpretation)
- GitHub Actions workflow: MEDIUM — pattern verified against Material for MkDocs docs (standard mkdocs pattern, minor variations possible)

**Research date:** 2026-03-20
**Valid until:** 2026-06-20 (stable ecosystem — mkdocs and mkdocs-shadcn change infrequently at patch level)
