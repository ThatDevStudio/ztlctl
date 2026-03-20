# Research Summary — v2.1 Documentation

**Researched:** 2026-03-20
**Confidence:** HIGH

## Key Findings

### Stack Additions
- **Zero new runtime dependencies** — Just the Docs front matter (`parent:`, `nav_order:`) handles multi-audience navigation natively
- **griffe2md 1.4.0** (dev dependency only) — AST-based Python API reference generation to Markdown, no runtime import needed
- **`llms.txt`** — hand-authored static Markdown file per llmstxt.org spec; no build tooling required
- **`ztlctl docs <query>`** — stdlib `pathlib` + `re` for ~20-page corpus; follows existing `_impl` pattern
- **MCP doc resource** — `ztlctl://docs/search` follows established `_RESOURCE_CATALOG` pattern in resources.py

### Feature Landscape
**Table stakes:** llms.txt at docs root, two-track navigation (user guide / developer guide), remove internal artifacts from public site
**Differentiators:** llms-full.txt (concatenated docs), `ztlctl docs <query>` CLI search, MCP `ztlctl://docs/search` resource, auto-generated API reference
**Anti-features to avoid:** Migrating away from Jekyll, auto-generated CLI reference replacing hand-authored content, per-page MCP resources, versioned documentation

### Architecture
- **Two parent pages** (`docs/guide.md`, `docs/dev.md`) as section roots — Just the Docs builds nav from `parent:` front matter strings
- **`scripts/gen_llms_txt.py`** walks docs/ tree, writes `docs/llms.txt` (pre-commit or CI step)
- **`scripts/build_docs_index.py`** writes `src/ztlctl/data/docs_index.json` for CLI/MCP search (pre-package-build)
- **Shared `_impl` function** for `ztlctl docs` CLI and `ztlctl://docs/search` MCP resource
- **docs/plans/ must be excluded** in `_config.yml` — currently publicly served

### Critical Pitfalls
1. **`parent:` string matching is exact** — a single-char mismatch silently orphans child pages with no build error; need automated verification
2. **GitHub Pages has no server-side redirects** — `jekyll-redirect-from` generates meta-refresh HTML stubs (not 301s); plan all URL changes before moving files
3. **llms.txt at `/ztlctl/llms.txt`** not `/llms.txt` due to `baseurl: /ztlctl` — verify serving path
4. **Embedded docs in package creates staleness** — prefer runtime path resolution or cache-on-demand over baked-in content
5. **MCP resources should use parameterized template** (`ztlctl://docs/{page}`) not individual hardcoded URIs

## Build Order (Dependency Chain)

1. **Infrastructure cleanup** — remove internal artifacts, exclude docs/plans/, audit links (unblocks everything)
2. **Navigation restructure** — create section parent pages, update all front matter, verify nav (must precede content)
3. **Agent accessibility** — llms.txt + llms-full.txt (low cost, high value, can ship early)
4. **Content tracks** — user guide + developer guide content (primary value, can parallelize)
5. **Doc search integration** — `ztlctl docs` CLI + MCP resource + build scripts (depends on restructure)
6. **API reference** — griffe2md generation (depends on dev guide structure)

## Open Questions

- Does `docs/llms.txt` with no YAML front matter get served correctly by Jekyll, or does it need processing?
- Should `ztlctl docs <query>` work fully offline (bundled fallback) or require access to docs directory?
- How should `agentic-workflows.md` be split between user guide (session workflows) and agent recipes?
