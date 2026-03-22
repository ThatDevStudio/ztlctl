# Stack Research

**Domain:** Documentation quality tooling for a Python CLI/MCP tool (ztlctl v3.1)
**Researched:** 2026-03-21
**Confidence:** HIGH

> This document covers NEW stack additions for v3.1. The existing stack (Python 3.13, Click,
> pluggy, Pydantic, FastMCP via `mcp` package) is established and unchanged.
> The MkDocs + mkdocs-shadcn docs site is also established (v2.1 shipped) — do not replace
> the theme or the two-track nav structure. See the v2.1 STACK.md (in git history) for that
> prior research. This file focuses exclusively on what v3.1 needs: prose quality enforcement,
> docs-as-code CI, and UX-improving MkDocs plugins.

---

## What Already Exists (Do Not Re-Research)

| Existing Capability | Status |
|---------------------|--------|
| MkDocs + mkdocs-shadcn 0.10.2 | Deployed on GitHub Pages; `mkdocs build --strict` passes |
| mkdocstrings (Python handler, Google docstring style) | In place; API reference auto-generated |
| mkdocs-redirects | In place in `mkdocs.yml` |
| Two-track nav (User Guide + Developer Guide) | In place via `mkdocs.yml` nav |
| llms.txt + llms-full.txt | Committed static files in `docs/` |
| 20 doc pages, agents.md system manual | In place |
| pre-commit with ruff + commitizen | In `.pre-commit-config.yaml` |
| `mkdocs build --strict` passes | Enforced in existing CI |

---

## Recommended Stack — New Additions Only

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Vale | 3.14.1 | Prose linter — enforces writing quality rules on all Markdown docs | The definitive tool for docs-as-code prose linting. Written in Go (fast, zero Python dep). Understands Markdown structure (won't flag code blocks or config examples). Has first-class pre-commit integration. Used by Grafana, GitLab, Red Hat, Google, GitHub. The Google style package provides exactly the tone (active voice, second person, present tense, clear action verbs) that Stripe/Docker-quality docs use. Version 3.14.1 (2025-03-20) is current |
| Vale Google style | 0.6.3 | Style rules derived from Google Developer Documentation Style Guide | The Google style is the right fit for a CLI developer tool: it enforces second person ("you"), active voice, present tense, avoidance of Latin abbreviations (e.g., i.e.), clear heading casing, and avoidance of ambiguous pronouns. Version 0.6.3 (April 2025). Installed via `vale sync` — no vendored files needed. The alternative (Microsoft) is better for enterprise software docs; Google fits CLI/developer tools |
| pymarkdownlnt | 0.9.34 | Markdown structure linter — enforces consistent heading hierarchy, list formatting, code fence syntax | Python-native alternative to markdownlint-cli2 (which requires Node.js). Since ztlctl is a Python project with `uv` as the package manager, adding a Node.js runtime for Markdown linting is a hard no. pymarkdownlnt is GFM-compliant, has 46 rules, supports pre-commit hooks, and is installable via `uv add --group dev`. Token-analyzes docs rather than regex scanning — catches structural issues Vale misses |
| lychee | 0.15.x | External broken link checker — verifies all HTTP(S) links in docs actually resolve | MkDocs `--strict` catches broken *internal* links (missing pages). It does NOT check external URLs. Lychee is a Rust-based async link checker used by large open-source projects (Apache, Mozilla). Run in CI via `lycheeverse/lychee-action`. Use cache + `.lycheeignore` for rate-limit management. Runs independently of MkDocs build — no Python dependency, no theme dependency |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `mkdocs-git-revision-date-localized-plugin` | 1.5.1 | Adds "last updated" date to each doc page from git history | Adds professional signal of currency. Readers see when a page was last touched — critical for a fast-moving project like ztlctl where v3.0 features need visibly fresh docs. Pulls from `git log` at build time. Compatible with mkdocs-shadcn (theme-agnostic via template injection). Use `enable_creation_date: true` to also show when the page was first written |
| `pymdownx.superfences` | bundled in pymdownx | Fenced code blocks with language identifiers and titles | Already pulling pymdownx for admonitions; superfences enables `title="filename.py"` annotations on code blocks — a key Stripe/Docker quality signal. No new `uv add` needed if pymdownx is already installed |
| `pymdownx.tabbed` | bundled in pymdownx | Tabbed code examples (e.g., "Python | Shell | Config") | Useful for the new v3.0 feature pages (session recall, contradiction detection) where the same workflow needs CLI + MCP + agent examples shown side-by-side. mkdocs-shadcn confirms tab support |

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| `vale sync` (one-time setup) | Downloads Google style package into `.vale/styles/Google/` | Run once after checking out repo. `.vale/styles/` should be `.gitignore`d — downloaded on demand, not vendored. The `.vale.ini` at repo root pins the package version |
| `pymarkdown scan docs/` | Scans all Markdown files for structural issues before build | Run in pre-commit and in CI `docs-lint` job. Use `--config .pymarkdown.json` for rule overrides. Key rules to enable: MD001 (heading increment), MD010 (no tabs), MD013 (line length — set to 120 not 80), MD022 (headings surrounded by blank lines), MD032 (lists surrounded by blank lines) |
| `mkdocs build --strict` | MkDocs build that fails on any warning | Already in CI. Catches broken internal links, missing nav entries, malformed YAML front matter. Do NOT add `-v` (verbose) flag — a known MkDocs bug causes `-v --strict` to suppress strict failures |

---

## Installation

```bash
# Prose linting
uv add --group dev vale  # NOTE: vale is a Go binary; install via brew or official installer instead
# Correct install: brew install vale  OR  via GitHub releases
# OR: use the pre-commit hook which downloads vale automatically (recommended)

# Markdown structure linting
uv add --group dev pymarkdownlnt

# "Last updated" dates on doc pages
uv add --group dev mkdocs-git-revision-date-localized-plugin

# pymdownx (for superfences + tabbed) — may already be transitively installed
uv add --group dev pymdown-extensions
```

**Vale installation note:** Vale is a Go binary, not a Python package. Do not `uv add vale`. Install
via `brew install vale` for local development. In CI, use the official GitHub Action
`errata-ai/vale-action@v2` which handles binary installation automatically. The pre-commit hook
approach (using `errata-ai/vale` repo) also works and is self-contained.

---

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| Vale + Google style | Vale + Microsoft style | Microsoft style is better for enterprise software (Windows, Office, Azure docs). Google style fits developer CLIs and open-source tools — matches ztlctl's persona |
| Vale + Google style | write-good Vale package | write-good is a subset (passive voice, weasel words). Use it as a *supplement* to Google, not a replacement. Add both if passive voice is a recurring issue after initial audit |
| pymarkdownlnt | markdownlint-cli2 | If the project uses Node.js already. markdownlint-cli2 is more widely adopted and has a GitHub Action, but requires Node.js runtime. pymarkdownlnt avoids adding a second runtime to a pure-Python project |
| lychee (CI only) | mlc (Markup Link Checker) | mlc is Rust-based and similar. lychee has more active maintenance, better rate-limit handling, and a widely-used GitHub Action (`lycheeverse/lychee-action`) |
| mkdocs-git-revision-date-localized | Manual `last_modified` frontmatter | Manual frontmatter goes stale immediately. Git-based date is always accurate and requires zero author discipline |
| pymdownx.superfences | Standard fenced_code | Standard fenced code works fine for basic examples; superfences adds `title=` and `hl_lines=` annotations needed for Stripe-quality code examples |

---

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| `doc8` | doc8 is an RST (reStructuredText) linter, not Markdown. Wrong tool entirely | `pymarkdownlnt` for Markdown structure |
| `proselint` Vale package | proselint has false-positive rates that frustrate developers; many rules are opinionated about literary prose, not technical writing. Blocks CI noisily on phrases that are completely acceptable in developer docs | Vale + Google style; add write-good selectively for passive voice |
| MkDocs `--verbose` flag in CI | A known bug in MkDocs causes `-v --strict` to suppress strict-mode failures (issue #3991). CI must use `mkdocs build --strict` without `-v` | `mkdocs build --strict` |
| Markdoc (Stripe's framework) | Stripe's MDX-based authoring system. Excellent for interactive API docs with custom React components, but requires a Node.js/Next.js site rebuild. ztlctl's docs are MkDocs-based; Markdoc would replace the entire docs pipeline | Continue with MkDocs + MDX-style features via pymdownx extensions |
| mkdocs-macros-plugin | Jinja2 macros in Markdown seem powerful but create a hybrid authoring model that confuses contributors and breaks when docs are read as raw Markdown (e.g., via llms.txt). ztlctl's agent accessibility depends on clean raw Markdown | Write docs as plain Markdown; use admonitions and tabs for rich content |
| Automated link checking at pre-commit stage | External link checking at commit time is slow (network calls), flaky (rate limits), and blocks local development for no quality gain. External links rarely break between commits | Run lychee only in CI on a scheduled basis (weekly) or on PR to main |
| Vale `MinAlertLevel = suggestion` in CI | Suggestions are not CI-blocking; they add noise. In CI, set `MinAlertLevel = error`. In pre-commit (local), set to `warning` so writers see guidance without being blocked | `MinAlertLevel = error` in CI, `warning` locally |

---

## Stack Patterns by Feature

**Docs-as-code CI enforcement (new `docs-lint` job in `.github/workflows/`):**

```yaml
# .github/workflows/docs-lint.yml
- name: Lint prose (Vale)
  uses: errata-ai/vale-action@v2
  with:
    files: docs/
    version: 3.14.1

- name: Lint Markdown structure (pymarkdownlnt)
  run: uv run pymarkdown scan docs/

- name: Build docs (MkDocs strict)
  run: uv run mkdocs build --strict
```

Run broken-link check separately on schedule (not every PR) to avoid flakiness:
```yaml
# .github/workflows/docs-links.yml  (scheduled weekly)
- uses: lycheeverse/lychee-action@v1
  with:
    args: --verbose --no-progress docs/
```

**Vale configuration (`.vale.ini` at repo root):**

```ini
StylesPath = .vale/styles
MinAlertLevel = warning

Packages = Google

[*.md]
BasedOnStyles = Vale, Google
```

Run `vale sync` once after checkout. Add `.vale/styles/` to `.gitignore`.

**Selective Vale rule overrides for technical docs (`.vale.ini` additions):**

```ini
[*.md]
BasedOnStyles = Vale, Google
# CLI command names are proper nouns — don't flag them for heading case
Google.Headings = NO
# ztlctl uses "e.g." and "i.e." deliberately in some contexts
Google.Latin = suggestion
```

**pymarkdownlnt configuration (`.pymarkdown.json` at repo root):**

```json
{
  "plugins": {
    "md013": {
      "enabled": true,
      "line_length": 120,
      "heading_line_length": 120,
      "code_block_line_length": 160
    },
    "md033": {
      "enabled": false
    }
  }
}
```

Disable MD033 (inline HTML) because MkDocs admonitions use HTML-adjacent syntax that pymarkdownlnt flags.

**Adding "last updated" dates to pages (mkdocs.yml addition):**

```yaml
plugins:
  - search
  - redirects:
      redirect_maps: {}
  - git-revision-date-localized:
      enable_creation_date: true
      type: date
  - mkdocstrings:
      # ... existing config unchanged
```

**pymdownx.superfences for code block titles (mkdocs.yml markdown_extensions):**

```yaml
markdown_extensions:
  - admonition
  - attr_list
  - def_list
  - fenced_code
  - footnotes
  - tables
  - toc:
      permalink: true
  - pymdownx.superfences
  - pymdownx.tabbed:
      alternate_style: true
```

Code blocks in docs then support:
```markdown
```python title="src/ztlctl/services/session.py"
# example code
```
```

**CLAUDE.md docs-as-code enforcement rule (doc-as-code pattern):**

Add to `CLAUDE.md` architecture section: "Every phase plan that adds a user-facing feature MUST include a `docs/` task. Docs are shipped with the feature, not after it. `mkdocs build --strict` must pass before a PR is opened."

---

## Version Compatibility

| Package | Compatible With | Notes |
|---------|-----------------|-------|
| Vale 3.14.1 | Python n/a (Go binary) | No Python version dependency. Works on macOS, Linux, Windows |
| Vale Google style 0.6.3 | Vale 3.x | Compatible. Installed via `vale sync` with `Packages = Google` in `.vale.ini` |
| pymarkdownlnt 0.9.34 | Python 3.10+ | Confirmed Python 3.13 compatible |
| mkdocs-git-revision-date-localized 1.5.1 | MkDocs 1.x, Python 3.8+ | Theme-agnostic; confirmed working January 2026. Requires git history available at build time (use `fetch-depth: 0` in GitHub Actions checkout) |
| mkdocs-shadcn 0.10.2 | MkDocs 1.x, Python 3.8+ | Current; released March 19, 2026. mkdocstrings support is alpha but working |
| pymdownx (superfences, tabbed) | mkdocs-shadcn 0.10.2 | Explicitly confirmed compatible in mkdocs-shadcn docs |
| lychee-action v1 | GitHub Actions | Version-agnostic; binary is downloaded at run time. Use `--cache` flag for rate-limit resilience |

---

## Technical Writing Standards

No tool to install — these are guidelines for the doc quality pass itself.

**Reference:** Google Developer Documentation Style Guide (https://developers.google.com/style)

Key principles that apply directly to ztlctl docs:

| Principle | Application |
|-----------|-------------|
| Second person ("you") | "You can configure ztlctl by..." not "Users can configure..." |
| Active voice | "ztlctl creates a note" not "A note is created by ztlctl" |
| Present tense | "The command returns" not "The command will return" |
| Sentence-case headings | "Session recall" not "Session Recall" |
| Numbered lists for sequences | Procedures (init, configure, run) use numbered steps |
| Bulleted lists for non-ordered | Options, features, caveats use bullets |
| Code formatting for commands | All CLI commands in backticks; full commands in code blocks |
| Concrete task framing | Page titles answer "How do I..."; body opens with what the reader achieves |

**Three-audience tone model (already established in v2.1, reinforce in v3.1):**

| Audience | Tone | Pages |
|----------|------|-------|
| End users (knowledge workers) | Mentor — warm, encouraging, explains why | guide/ pages, tutorial, quickstart |
| Developers/plugin authors | Peer — direct, technical, assumes competence | dev/ pages, plugin-guide, api-reference |
| Agents | Structured — schema-first, deterministic, no narrative | agents.md, llms.txt, mcp.md |

---

## Sources

- [Vale GitHub](https://github.com/vale-cli/vale) — v3.14.1 release (2025-03-20) confirmed (HIGH)
- [Vale docs — pre-commit integration](https://vale.sh/docs/integrations/pre-commit) — two-hook setup (sync + check) confirmed (HIGH)
- [Vale Google style GitHub](https://github.com/errata-ai/Google) — v0.6.3 (April 2025), CC BY 4.0 license (HIGH)
- [Vale packages docs](https://vale.sh/docs/keys/packages) — `Packages = Google`, `vale sync` workflow (HIGH)
- [pymarkdownlnt PyPI](https://pypi.org/project/pymarkdownlnt/) — v0.9.34, Python 3.10+, 46 rules (HIGH)
- [pymarkdownlnt pre-commit docs](https://pymarkdown.readthedocs.io/en/latest/advanced_pre-commit/) — hook configuration (HIGH)
- [lychee-action GitHub](https://github.com/lycheeverse/lychee-action) — async Rust link checker, GitHub Action (HIGH)
- [mkdocs-git-revision-date-localized PyPI](https://pypi.org/project/mkdocs-git-revision-date-localized-plugin/) — v1.5.1, January 2026 (HIGH)
- [mkdocs-shadcn GitHub](https://github.com/asiffer/mkdocs-shadcn) — v0.10.2 (2026-03-19), pymdownx + mkdocstrings confirmed compatible (HIGH)
- [MkDocs strict mode issues](https://github.com/mkdocs/mkdocs/issues/3842) — `-v --strict` bug confirmed (MEDIUM)
- [Google Developer Documentation Style Guide](https://developers.google.com/style) — highlights, word list, tone guidance (HIGH)
- [markdownlint-cli2 GitHub](https://github.com/DavidAnson/markdownlint-cli2) — considered and rejected (requires Node.js) (HIGH)
- Existing `mkdocs.yml` (direct inspection) — current plugins, extensions, theme config (HIGH)
- Existing `.pre-commit-config.yaml` (direct inspection) — current hooks, no Node.js runtime (HIGH)

---
*Stack research for: ztlctl v3.1 — Documentation quality overhaul and docs-as-code enforcement*
*Researched: 2026-03-21*
