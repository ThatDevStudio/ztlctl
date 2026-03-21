# Phase 8: MkDocs Infrastructure - Context

**Gathered:** 2026-03-20
**Status:** Ready for planning

<domain>
## Phase Boundary

Migrate the docs site from Jekyll + Just the Docs to MkDocs + mkdocs-shadcn. Remove internal planning artifacts from the public docs. Set up GitHub Actions workflow for automated deployment to GitHub Pages. Preserve existing URLs via redirects. Content reorganization into two-track navigation is Phase 9.

</domain>

<decisions>
## Implementation Decisions

### Migration strategy
- Replace Jekyll in-place — remove `docs/_config.yml` and add `mkdocs.yml` at project root
- Migrate all 16 existing markdown files to MkDocs-compatible format (update front matter from Jekyll `nav_order`/`title` to MkDocs `nav:` config)
- Delete internal planning artifacts from docs/: `backlog.md`, `research-mapping.md`, `roadmap.md`
- Exclude `docs/plans/` from the built site via mkdocs.yml (don't delete the directory, just exclude from build)
- Keep docs content in `docs/` directory (MkDocs `docs_dir: docs`)

### Theme configuration
- Use mkdocs-shadcn theme (`pip install mkdocs-shadcn`, `theme: name: shadcn`)
- Dark mode as default with toggle available for light mode
- Color accent and typography: Claude's discretion within shadcn defaults

### URL preservation
- Use `mkdocs-redirects` plugin to create redirect stubs for any URLs that change during migration
- All 16 current docs pages must have working redirects if their paths change
- External links from README.md, PyPI, GitHub issues must continue to work

### Deploy pipeline
- New GitHub Actions workflow: `.github/workflows/docs.yml`
- Trigger: push to `develop` branch (matches existing release pipeline pattern)
- Build: `mkdocs build` → deploy to `gh-pages` branch via `mkdocs gh-deploy`
- Remove Jekyll-specific files: `_config.yml`, `Gemfile`, `Gemfile.lock` (if present)

### Claude's Discretion
- Exact mkdocs.yml plugin configuration beyond shadcn + redirects
- Whether to add `mkdocs-minify-plugin` or other build optimizations
- Footer content and layout details
- Search configuration tuning

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### MkDocs + mkdocs-shadcn
- `docs/_config.yml` — Current Jekyll config to replace (baseurl, theme, search, aux_links)
- https://github.com/asiffer/mkdocs-shadcn — Theme installation, configuration, supported features

### Current docs structure
- `docs/index.md` — Current landing page (needs migration to MkDocs format)
- All 16 files in `docs/*.md` — Content to migrate (front matter update needed)

### CI/CD
- `.github/workflows/release-pipeline.yml` — Existing CI pattern (trigger on develop push)
- `.github/workflows/pr-ci.yml` — Existing PR validation workflow

### Research findings
- `.planning/research/STACK.md` — Stack recommendations including mkdocs-shadcn details
- `.planning/research/ARCHITECTURE.md` — Directory structure and build pipeline architecture
- `.planning/research/PITFALLS.md` — URL redirect pitfalls, Jekyll removal gotchas

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- 16 markdown docs with substantial content — migrate, don't rewrite
- `docs/_config.yml` — reference for site metadata (title, description, URL, baseurl)
- README.md documentation table — links to current docs URLs (must be updated if paths change)

### Established Patterns
- GitHub Pages serves from `docs/` on develop branch (current Jekyll auto-build)
- CI workflows trigger on push to develop (`.github/workflows/release-pipeline.yml`)
- No `Gemfile` or `Gemfile.lock` found (remote theme only)

### Integration Points
- `README.md` links to docs site — URL updates needed if paths change
- `pyproject.toml` may need mkdocs as dev dependency (`uv add --group dev mkdocs mkdocs-shadcn mkdocs-redirects`)
- GitHub repository settings may need Pages source changed from "Deploy from branch" (docs/) to "GitHub Actions"

</code_context>

<specifics>
## Specific Ideas

- User wants modern, clean shadcn/ui aesthetic — not the dated Just the Docs look
- Dark mode as default reflects the tool's positioning as a modern agentic platform
- mkdocs-shadcn chosen specifically for its shadcn/ui port aesthetic (v0.10.2, actively maintained)

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 08-mkdocs-infrastructure*
*Context gathered: 2026-03-20*
