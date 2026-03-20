# Pitfalls Research

**Domain:** Documentation restructuring — audience-segmented Jekyll/Just the Docs site, llms.txt, CLI doc search, MCP doc resources for a Python CLI/MCP tool
**Researched:** 2026-03-20
**Confidence:** HIGH (Just the Docs nav mechanics) / MEDIUM (llms.txt spec, MCP resource patterns) / HIGH (package size, redirect constraints)

---

## Critical Pitfalls

### Pitfall 1: `parent:` Field Must Exactly Match the Parent Page's `title:` Value

**What goes wrong:**
When restructuring flat nav into sections, each child page needs `parent: "Section Title"` in its frontmatter. If the parent page's `title:` value ever changes (even capitalization), all child pages under it silently detach from the hierarchy and fall back to the root level. No build error is raised. The navigation tree appears to work but sections are collapsed or missing children.

**Why it happens:**
Just the Docs resolves the parent-child relationship entirely through string matching on `title:` — there is no stable ID. When you rename a section (e.g., "Reference" → "API Reference" for clarity), you must update `parent:` in every child page simultaneously. In a flat-to-hierarchical migration with 16 pages, this is easy to miss for one or two pages.

The ztlctl site has 16 pages all at the root level with `nav_order: 1–12`. Converting to sections means every non-parent page must gain a `parent:` field with a string that exactly matches its new section's `title:`.

**How to avoid:**
1. Rename sections last, after all child pages have been assigned. Never rename a section title mid-migration.
2. Add a build verification step: after the migration, run `grep -r "parent:" docs/` and compare the set of parent values against the set of actual section page titles. Any mismatch is a bug.
3. Use lowercase, simple section titles (e.g., `title: "Reference"`) with no punctuation, making exact-match easier and reducing future rename temptation.

**Warning signs:**
- Top-level nav shows section headings but clicking them reveals no children
- A page appears at the root level when it should be nested
- `nav_order` conflicts in build output (duplicate nav_order values at the root scope appear when children detach)

**Phase to address:**
Navigation Restructuring phase — the frontmatter migration step.

---

### Pitfall 2: GitHub Pages Has No Server-Side Redirects — Client-Side Refresh Is the Only Option

**What goes wrong:**
Moving pages from flat to sectioned navigation typically changes URLs. Just the Docs generates URLs from file paths. If you move `docs/commands.md` to `docs/reference/commands.md`, the URL changes from `/ztlctl/commands` to `/ztlctl/reference/commands`. All external links (README.md, GitHub issues, PyPI page, other tools that link to the docs) break silently. GitHub Pages serves a 404; there is no server-side redirect.

**Why it happens:**
GitHub Pages is a static host. It does not support `.htaccess`, Nginx rewrites, or any server-level redirect mechanism. The only GitHub Pages-approved redirect approach is the `jekyll-redirect-from` gem, which generates stub HTML files containing `<meta http-equiv="refresh">` tags. These are client-side redirects, not HTTP 301s.

For ztlctl, the current flat structure means `/ztlctl/commands`, `/ztlctl/configuration`, `/ztlctl/mcp`, `/ztlctl/installation`, etc. are live public URLs. These are referenced in README.md, CONTRIBUTING.md, and potentially in the Homebrew tap and PyPI description.

**How to avoid:**
1. Decide the new URL structure before moving any files. Once decided, add `redirect_from: ["/ztlctl/old-path/"]` to the new page's frontmatter before renaming or moving the file.
2. Verify `jekyll-redirect-from` is in the `_config.yml` plugins list. For GitHub Pages, it is in the allowlist and does not require custom build steps.
3. Audit all cross-references (README.md, CONTRIBUTING.md, pyproject.toml `[project.urls]`, Homebrew formula description) before any file moves. Update these in the same commit as the move so they never point to a 404.
4. Prefer keeping file paths stable where possible. If a page stays at `docs/commands.md`, its URL `/ztlctl/commands` does not change even if it gains a `parent:` frontmatter field. Hierachical nav in Just the Docs is controlled by frontmatter, not file paths.

**Warning signs:**
- Any file moved to a subdirectory will change its URL (e.g., `docs/reference/commands.md` → `/ztlctl/reference/commands`)
- Internal links using `[text](commands.md)` style resolve correctly in Jekyll but hardcoded links like `[text](/ztlctl/commands)` break if the file moves
- `jekyll-relative-links` plugin (in GitHub Pages allowlist) converts relative markdown links and will update them transparently — use relative links everywhere internally

**Phase to address:**
Infrastructure phase (URL audit before any restructuring) — must happen before any file moves.

---

### Pitfall 3: Just the Docs Navigation Sections Have No URL of Their Own Without an Index Page

**What goes wrong:**
In Just the Docs, a "section" is just a page marked `has_children: true` (legacy) or a page that other pages declare as their `parent:`. The section's own `title:` becomes the nav heading. If the section page is intended to be a landing page for the section (e.g., a "User Guide" overview), it must be a real `.md` file with content. If you only want the visual grouping without a landing page, users clicking the section title get a page that either has no content or shows stale placeholder content.

**Why it happens:**
For audience-segmented docs (User Guide / Developer Guide / Agent Accessibility), the natural instinct is to create section titles as pure nav containers. But Just the Docs does not support folder-only sections — every section header must be a page. If you don't write real content for it, you're shipping an empty placeholder as a public page.

**How to avoid:**
1. Write meaningful section landing pages. A "User Guide" landing page should briefly explain what's in the section and link to the most important child pages. One paragraph + a short table of contents is sufficient.
2. If a section has no meaningful landing content, consider whether it's a real section or just a nav_order grouping. Two to three pages rarely justify a full section.
3. Plan section landing pages as separate deliverables in the phase scope — they are not automatically generated.

**Warning signs:**
- Section page has `title:` and `nav_order:` but no body content below the frontmatter
- The same links appear in both the section landing page and the parent index.md (duplication)

**Phase to address:**
Content authoring phase — section landing pages must be scoped as explicit deliverables.

---

### Pitfall 4: llms.txt Goes Stale Within One Release Cycle

**What goes wrong:**
The `llms.txt` file at the docs root is a manually curated index of important URLs and descriptions. When docs pages are added, renamed, or reorganized, the file is not automatically updated. Within a release cycle, it lists deleted pages, points to stale content, or omits newly important pages. AI agents using it get outdated navigation and may cite pages that no longer exist or miss the most current content.

**Why it happens:**
There is no tooling that generates llms.txt automatically from a Jekyll site. It is always written by hand. Documentation updates happen in PRs focused on content — the llms.txt update is a side task that is easy to forget. The llms.txt specification has no staleness detection mechanism; there is no `last_updated:` field or version identifier in the canonical spec.

For ztlctl, the docs are in a separate `docs/` directory from the Python package. The package release process (`cz bump` → GitHub Release → PyPI) does not touch the docs, so a PyPI release does not trigger a docs review.

**How to avoid:**
1. Add a CI check: run a script in `pr-ci.yml` that verifies every URL listed in `llms.txt` resolves to an actual file in `docs/`. A broken URL means a stale entry. This catches deletions and renames automatically.
2. Write llms.txt in terms of stable, section-level URLs rather than individual deep-link pages. Section entry points change less frequently than individual page content.
3. Add `# Updated: YYYY-MM-DD` as a comment in the first few lines (this is not in the spec but is parseable by agents). Commit to updating this date when any section changes.
4. Treat llms.txt as part of the docs navigation infrastructure, not as content. Put it in the same PR as any structural navigation changes.

**Warning signs:**
- A URL in llms.txt returns a 404 from the deployed site
- A major section added in a release has no entry in llms.txt
- The listed descriptions no longer match what the page actually contains

**Phase to address:**
Agent Accessibility phase (initial creation) and every subsequent docs phase (maintenance automation via CI check).

---

### Pitfall 5: CLI `docs` Command Embeds Stale Documentation in the Package

**What goes wrong:**
Implementing `ztlctl docs <query>` by bundling a snapshot of the docs into the Python package (as package data, a SQLite FTS index, or plain text files) creates a permanent staleness problem. The embedded docs reflect the state at release time. Users on v2.1 who add new notes types via plugins, or who upgrade to v2.2, get `ztlctl docs` results that describe the old behavior. There is no way to update embedded docs without upgrading the package.

**Why it happens:**
Bundling docs as package data is the simplest implementation — copy the markdown files, build a SQLite FTS index at build time, include in `pyproject.toml` `[tool.uv]` package data or `MANIFEST.in`. But ztlctl's docs are in `docs/` (a Jekyll site), not alongside the source. The package build process does not naturally include the docs directory. Someone must manually copy or pre-process the docs into the `src/ztlctl/` tree before each release, creating a high-friction process that will be skipped.

Additionally, the ztlctl package already has sentence-transformers as a dependency (for vector search). Adding a bundled SQLite FTS database for docs search duplicates the search infrastructure and adds binary data to the package.

**How to avoid:**
1. Do not embed a static doc snapshot. Instead, implement `ztlctl docs <query>` as a thin client that fetches from the live docs site or uses the deployed `llms.txt` and individual page URLs. This keeps docs always current.
2. If offline-first is required, implement a `ztlctl docs --sync` command that downloads and caches the current docs locally (in `~/.config/ztlctl/docs_cache/`), rather than bundling at build time. Cache invalidation is version-stamped.
3. For the initial implementation, use the GitHub Pages-deployed docs as the source of truth: the `ztlctl docs <query>` command queries a text index built from the live site, not a build-time snapshot.
4. If a truly offline embedded index is required, use a compressed text file of page titles and anchors only (not full content) — this is kilobytes, not megabytes.

**Warning signs:**
- `pyproject.toml` includes `docs/*.md` or a `.db` file in package data
- The search index file size exceeds 500KB in the installed package
- `pip show -f ztlctl` lists docs markdown files in the package contents

**Phase to address:**
Agent Accessibility phase — scope and design decision must be made explicitly before implementation.

---

### Pitfall 6: MCP Documentation Resources Duplicate Maintenance Burden

**What goes wrong:**
Implementing MCP doc resources by hardcoding resource URI handlers for each documentation page creates a 1:1 mapping between doc pages and resource definitions. When a doc page is added, renamed, or reorganized, both the Jekyll file and the MCP resource definition must be updated. The MCP resource list goes stale independently from the docs site.

**Why it happens:**
The natural first implementation is to write a list of `@server.resource("ztlctl://docs/commands")` handlers in `mcp/resources.py`, each returning the text of the corresponding docs page. ztlctl already has 6 registered MCP resources (per MEMORY.md). Adding per-page doc resources as static registrations means the resource list is frozen at implementation time and requires code changes to update.

MCP's `resources/list` returns all registered resources at call time. If the server has 20 hardcoded doc resource URIs but 8 of those pages have been reorganized or removed, agents calling `resources/list` get 404-equivalent errors when they try to read those resources.

**How to avoid:**
1. Implement doc resources using a single parameterized resource template: `ztlctl://docs/{page}`. The handler dynamically resolves `page` to a docs file path, returning an error for pages that don't exist. This means adding new doc pages requires zero MCP code changes.
2. Use the MCP `listChanged` notification (spec-supported) to signal when the doc resource list changes — trigger this from a CI step or a version bump event.
3. Set `annotations.lastModified` on each resource response to the modification time of the underlying docs file. This lets agents detect stale cached content.
4. Do not register doc resources for internal planning pages (backlog.md, research-mapping.md, roadmap.md) that will be removed in the infrastructure cleanup phase. Register only audience-facing docs.

**Warning signs:**
- MCP resource definitions list individual doc pages by name (not parameterized)
- A doc page is renamed and the corresponding MCP resource still returns the old content
- `resources/list` response includes URIs for pages that return empty or 404 content

**Phase to address:**
Agent Accessibility phase — architecture decision must be made before any MCP resource implementation.

---

## Technical Debt Patterns

Shortcuts that seem reasonable but create long-term problems.

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Copy docs files into `src/ztlctl/data/` for CLI search | Offline search works immediately | Docs go stale in every release; adds binary data to PyPI package | Never — use cache-on-demand approach |
| Hardcode MCP resource URIs for each doc page | Simple implementation, zero abstraction | 1:1 maintenance burden; resource list goes stale independently from docs | Never — use parameterized template |
| Write llms.txt once and never add CI verification | Fast to ship | Stale links within one docs update cycle | Only for initial release, with CI check added immediately |
| Keep internal planning pages (backlog.md, research-mapping.md) in public docs | Avoids deciding what to expose vs. hide | Agents and users get confused by internal planning artifacts in the docs navigation | Never — remove or redirect before launch |
| Use `nav_order: 1–12` flat ordering for all pages during migration | Avoids nav_order conflicts | Pages within sections fight for the same nav_order namespace | Temporary, for one PR only |
| Write section landing pages as stubs ("Content coming soon") | Unblocks navigation structure work | Ships empty pages that degrade user experience and agent context quality | Never — write real content before publishing |

---

## Integration Gotchas

Common mistakes when connecting to external services.

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| GitHub Pages + Jekyll | Moving `docs/page.md` to `docs/section/page.md` without redirects, expecting URLs to be stable | Add `redirect_from: ["/ztlctl/page"]` to the moved page's frontmatter before any file move |
| `jekyll-redirect-from` | Assuming the redirect generates a 301 HTTP redirect | It generates a meta-refresh HTML stub (client-side, not HTTP 301); update canonical links manually |
| Just the Docs `parent:` | Setting `parent: "User Guide"` when the parent page has `title: "User Guides"` (plural) | String comparison is exact and case-sensitive; verify with `grep -r "title:" docs/` |
| llms.txt + GitHub Pages | Placing `llms.txt` in `docs/` expecting it to be served at `/llms.txt` | GitHub Pages serves `docs/` at `/ztlctl/`, so the file lands at `/ztlctl/llms.txt`, not `/llms.txt`; must be in repo root or configured via baseurl |
| MCP `resources/read` | Returning full raw markdown including frontmatter YAML to agents | Strip frontmatter before returning; YAML frontmatter is navigation metadata, not agent-relevant content |
| ztlctl package + docs | Referencing docs URLs in docstrings or CLI help text using hardcoded paths | Use the `NEXT_PUBLIC_VERCEL_PROJECT_PRODUCTION_URL` pattern or a single `DOCS_BASE_URL` constant; never hardcode `/ztlctl/` path prefix in source |

---

## Performance Traps

Patterns that work at small scale but fail as usage grows.

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Build-time SQLite FTS index in package | Package installs slowly; `pip install ztlctl` downloads unexpectedly large wheel | Keep docs index as a separate optional download or cache-on-demand; never include in wheel | Any size — the root issue is staleness, not scale |
| `ztlctl docs <query>` fetches live site on every call | High latency (network round-trip) for every docs lookup from MCP clients | Implement local cache with TTL (7 days), refreshed on `--sync` flag | Network-dependent; breaks in offline environments |
| MCP `resources/list` enumerates all individual doc pages | Response size grows linearly with doc page count; slow for agents to parse 30+ resources | Use single parameterized template `ztlctl://docs/{page}` instead of individual registrations | At ~20 resources, token cost becomes noticeable in context |
| Just the Docs search index | Built-in JS search indexes all page content; with 50+ pages it slows initial page load | Already mitigated by Just the Docs' incremental search; not a real concern at ztlctl's docs size | At 500+ pages (not applicable here) |

---

## UX Pitfalls

Common user experience mistakes in this domain.

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Audience-segmented nav without a clear entry point per audience | Knowledge workers land on "User Guide" and don't know where to start; agents see a flat resource list | Section landing pages must start with "If you are X, start here" guidance |
| Removing docs pages that were in the old flat nav without redirects | Existing bookmarks and links (in GitHub issues, Homebrew docs, PyPI page) return 404 | Redirect every removed page; audit all outbound references before removal |
| llms.txt listing every page equally | Agents prioritize low-value pages (backlog.md, roadmap.md) over core reference docs | Use the Optional section for low-priority content; put the 5 most important pages in the required section |
| `ztlctl docs <query>` returning raw markdown with frontmatter | Agents receive `---\ntitle: Commands\nnav_order: 6\n---` as the first lines of every result | Strip frontmatter before returning; return title from frontmatter as a structured field |
| MCP doc resources returning entire page content | Large pages exceed MCP message size limits; agents receive truncated responses without knowing they are truncated | Chunk large pages by section (H2 headings) and implement pagination or section-level URIs |

---

## "Looks Done But Isn't" Checklist

Things that appear complete but are missing critical pieces.

- [ ] **Navigation restructuring:** Section headings appear in sidebar but `parent:` values on child pages must be verified against actual parent `title:` values — run `grep -r "parent:" docs/` and cross-check
- [ ] **URL redirects:** File moved to new path with `redirect_from:` in frontmatter, but README.md and CONTRIBUTING.md still link to old URL — audit all cross-references in non-docs files
- [ ] **llms.txt deployment:** File written in `docs/llms.txt` but GitHub Pages serves it at `/ztlctl/llms.txt` not `/llms.txt` — verify correct placement relative to `baseurl`
- [ ] **llms.txt content:** File exists but URLs use absolute paths not including the baseurl — test every URL in the file manually against the deployed site
- [ ] **MCP doc resources:** Resource handler implemented but strips frontmatter only partially, returning `---` as first line — write a test that reads a resource and asserts no YAML frontmatter in response
- [ ] **CLI `docs` command:** Command works in development (where `docs/` is on disk) but fails after `pip install` because `docs/` is not in the package — test against an installed wheel, not the source tree
- [ ] **Internal pages removed:** `backlog.md`, `research-mapping.md`, `roadmap.md` are removed from nav but may still be accessible at their URLs if the files remain on disk — verify files are removed or explicitly excluded in `_config.yml`
- [ ] **Section landing pages:** Pages have frontmatter and a title but body content is a placeholder — verify every section landing page has at least one paragraph of real content

---

## Recovery Strategies

When pitfalls occur despite prevention, how to recover.

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Broken `parent:` orphaning child pages | LOW | Find mismatched parent strings with `grep`, fix frontmatter, redeploy (GitHub Pages auto-deploys on push) |
| Broken URLs without redirects after restructure | MEDIUM | Add `redirect_from:` to all moved pages; audit and update all external references; one PR can fix all of them |
| llms.txt deployed at wrong path (wrong baseurl) | LOW | Move file to correct location; update llms.txt URL in any documentation that references it |
| Stale embedded docs in package | HIGH | Must release a new package version; cannot patch installed package; docs cache-on-demand approach sidesteps this |
| MCP resources pointing to removed/renamed pages | LOW | Fix resource template handler to resolve dynamically; parameterized templates prevent recurrence |
| Duplicate nav_order values across root and section pages | LOW | nav_order is scoped per-parent in Just the Docs (same nav_order in different sections does not conflict); only root-level pages need globally unique nav_order |

---

## Pitfall-to-Phase Mapping

How roadmap phases should address these pitfalls.

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| `parent:` title mismatch | Navigation Restructuring | `grep -r "parent:" docs/` output matches exactly the set of section `title:` values |
| Broken URLs from file moves | Infrastructure (URL audit before moves) | All old URLs respond with 200 or 302 after migration; README.md links verified |
| Section pages without real content | Content Authoring | Every section landing page has >50 words of real content; no "coming soon" placeholders |
| llms.txt placed at wrong path | Agent Accessibility | `curl https://thatdevstudio.github.io/ztlctl/llms.txt` returns 200 with expected content |
| llms.txt going stale | Agent Accessibility (CI check on initial setup) | CI script verifies all llms.txt URLs exist as files in `docs/`; runs on every PR |
| CLI docs embedding stale content | Agent Accessibility (architecture decision) | `pip show -f ztlctl` shows no `.db` or `.md` docs files; docs lookup uses cache-on-demand |
| MCP resources with hardcoded page URIs | Agent Accessibility (design review) | `resources/list` response contains parameterized template, not 20+ individual resource URIs |
| Internal planning pages left in public nav | Infrastructure cleanup phase | `docs/backlog.md`, `docs/research-mapping.md`, `docs/roadmap.md` not present in Jekyll build output |

---

## Sources

- [Just the Docs — Page Levels](https://just-the-docs.com/docs/navigation/main/levels/) — `parent:` field mechanics, title exact-match requirement, `has_children` deprecation (HIGH confidence)
- [Just the Docs — Migration and Upgrading](https://just-the-docs.com/migration/) — breaking changes across versions, nav ordering changes (HIGH confidence)
- [jekyll/jekyll-redirect-from](https://github.com/jekyll/jekyll-redirect-from) — GitHub Pages allowlisted redirect plugin, meta-refresh implementation (HIGH confidence)
- [Model Context Protocol — Resources spec 2025-06-18](https://modelcontextprotocol.io/specification/2025-06-18/server/resources) — parameterized resource templates, `lastModified` annotation, `listChanged` notification (HIGH confidence)
- [MCP Servers for Documentation Sites — Fern](https://buildwithfern.com/post/mcp-servers-documentation-sites) — maintenance burden patterns, auto-generation from spec (MEDIUM confidence)
- [llmstxt.org](https://llmstxt.org/) — canonical specification, informal standard status, format rules (MEDIUM confidence — spec is community-driven and evolving)
- [LLMS.txt: Common Mistakes to Avoid — Incremys](https://www.incremys.com/en/resources/blog/llms-txt) — staleness patterns, maintenance cadence recommendations (MEDIUM confidence)
- [Redirects on GitHub Pages — GitHub Docs](https://docs.github.com/en/enterprise/2.13/user/articles/redirects-on-github-pages) — static host limitations, no server-side redirect support (HIGH confidence)
- ztlctl codebase analysis: `docs/_config.yml`, `docs/*.md` frontmatter, `src/ztlctl/mcp/`, `.planning/PROJECT.md`, MEMORY.md project state

---
*Pitfalls research for: documentation restructuring — Jekyll/Just the Docs + llms.txt + CLI doc search + MCP doc resources*
*Researched: 2026-03-20*
