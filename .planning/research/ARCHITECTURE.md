# Architecture Research

**Domain:** Docs-as-code enforcement and MkDocs site integration for a Python CLI/MCP tool (v3.1 Documentation & Hardening milestone)
**Researched:** 2026-03-21
**Confidence:** HIGH

> This document supersedes the v2.1 ARCHITECTURE.md (which described a Jekyll/Just-the-Docs system that was never implemented). The live system is MkDocs + mkdocs-shadcn with GitHub Pages artifact deploy. All findings are derived from reading the actual codebase.

---

## Standard Architecture

### System Overview

```
┌──────────────────────────────────────────────────────────────────────┐
│                          Authoring Layer                              │
│                                                                       │
│  docs/                          docs/guide/      docs/dev/            │
│  ├── index.md (landing)         (flat pages,     (flat pages,         │
│  ├── installation.md            referenced by    referenced by        │
│  ├── quickstart.md              mkdocs.yml nav)  mkdocs.yml nav)      │
│  ├── [v3.0 feature pages]  <-- NEW: 5 pages                          │
│  ├── llms.txt (maintained)                                            │
│  └── llms-full.txt (maintained)                                       │
│                                                                       │
│  Internal (excluded from build via mkdocs.yml exclude_docs)          │
│  └── docs/plans/               <- already excluded                   │
└──────────────────────────────────────────────────────────────────────┘
                          │
┌─────────────────────────┴────────────────────────────────────────────┐
│                           Build Layer                                 │
│                                                                       │
│  mkdocs.yml — explicit nav: tree drives all navigation               │
│  mkdocs build --strict  — fatal on warnings (broken refs, bad links) │
│  mkdocs-shadcn theme                                                  │
│  mkdocstrings[python] — auto-generates api-reference.md content      │
│  mkdocs-redirects — handles any URL changes without breaking links   │
│                                                                       │
│  NEW: docs linting step (pre-CI or new CI step)                      │
│  ├── mkdocs build --strict  (already done in docs.yml deploy)        │
│  ├── linkcheck (markdown-link-check or lychee)                       │
│  └── example verification (grep or ast-based spot check)             │
└──────────────────────────────────────────────────────────────────────┘
                          │
┌─────────────────────────┴────────────────────────────────────────────┐
│                           Deploy Layer                                │
│                                                                       │
│  docs.yml (GitHub Actions):                                           │
│  push to develop → mkdocs build → upload Pages artifact              │
│  → deploy-pages action → https://thatdevstudio.github.io/ztlctl/    │
│                                                                       │
│  No gh-pages branch. Artifact-based deploy (v2.1 decision).         │
└──────────────────────────────────────────────────────────────────────┘
                          │
┌─────────────────────────┴────────────────────────────────────────────┐
│                         Consumer Layer                                │
│                                                                       │
│  Human users (browser) │ AI agents (llms.txt, llms-full.txt,        │
│                         │  ztlctl docs <query> CLI, MCP doc search)  │
└──────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Notes |
|-----------|----------------|-------|
| `mkdocs.yml nav:` | Single source of truth for site navigation | Must be updated when any page is added or renamed |
| `docs/` root files | User Guide pages — flat, referenced directly in nav | No `parent:` front matter (MkDocs does not use it) |
| `docs/guide/index.md` | User Guide section landing page | Modified to link new v3.0 feature pages |
| `docs/dev/index.md` | Developer Guide section landing page | Unchanged for v3.1 |
| `docs/llms.txt` | Machine-readable index of doc pages for agent discovery | Hand-maintained; must be updated when pages are added |
| `docs/llms-full.txt` | Full documentation corpus concatenated for LLM ingestion | Hand-maintained; must be updated when pages change |
| `docs.yml` | Build and deploy to GitHub Pages on push to develop | Only runs on develop; no PR doc check currently |
| `pr-ci.yml` | PR gate: lint, format, mypy, pytest, build, pip-audit | No doc checks currently — gap to address in v3.1 |
| `CLAUDE.md` | Standing instructions for Claude Code | Needs explicit docs-as-code rule |

---

## Recommended Project Structure

```
docs/
├── index.md                         # Modified: add v3.0 features to overview table
├── concepts.md                      # Modified: add v3.0 types (sessions, contradictions, media)
├── agentic-workflows.md             # Modified: add v3.0 recipes (recall, polaris, contradiction)
├── agents.md                        # Modified: add v3.0 tool inventory entries
├── mcp.md                           # Modified: update tool count (73+), add new resources
│
├── session-recall.md                # NEW: session recall — temporal/topic/topology querying
├── polaris.md                       # NEW: polaris priorities layer — init, MCP resource, check_alignment
├── contradiction-detection.md       # NEW: heuristic contradiction scoring, CAT_SEMANTIC, review workflow
├── media-ingestion.md               # NEW: faster-whisper pipeline, VTT/SRT, two-phase workflow
├── methodology-guidance.md          # NEW: prose-as-title, title quality check, garden backlog candidates
│
├── llms.txt                         # Modified: add 5 new page entries
├── llms-full.txt                    # Modified: append 5 new pages' full content
│
├── guide/
│   └── index.md                     # Modified: link new feature pages in User Guide table
├── dev/
│   └── index.md                     # Unchanged
└── plans/                           # Excluded from build (mkdocs.yml exclude_docs)
    └── *.md

.github/workflows/
├── pr-ci.yml                        # Modified: add doc-lint job (mkdocs build --strict + link check)
└── docs.yml                         # Unchanged (already builds + deploys)

mkdocs.yml                           # Modified: add 5 new pages to nav: User Guide section

CLAUDE.md                            # Modified: add docs-as-code rule (architecture section)

.planning/milestones/v3.1-phases/
└── [phase files]                    # GSD phases — each feature phase includes doc tasks
```

### Structure Rationale

- **New pages in `docs/` root, not `docs/guide/`:** Existing v2.1 pages (concepts, commands, etc.) live at `docs/` root. The five new v3.0 feature pages follow the same convention. Moving them into `docs/guide/` would require updating all cross-links — no benefit for v3.1.
- **No subdirectory for v3.0 features:** Five pages do not warrant a new section. They slot into the User Guide nav section alongside existing pages via `mkdocs.yml nav:`.
- **`mkdocs.yml nav:` is the authoritative navigation registry:** MkDocs with `nav:` defined ignores filesystem layout for navigation. A file that exists in `docs/` but is not in `nav:` is built (if referenced by a page) but not reachable from any navigation. New pages must be added explicitly.
- **llms.txt and llms-full.txt are hand-maintained:** The v2.1 research proposed a generator script; the actual v2.1 implementation committed hand-maintained files (confirmed by reading the live files). For v3.1, maintain the same approach — add entries when pages are added. The CLAUDE.md rule enforces this.

---

## Architectural Patterns

### Pattern 1: MkDocs nav Registration

**What:** Every new doc page must be registered in `mkdocs.yml` under the appropriate section of the `nav:` tree. Without this entry, MkDocs builds the HTML but the page is unreachable from navigation.

**When to use:** Always — every new `.md` file in `docs/`.

**Trade-offs:** Explicit nav requires a mechanical `mkdocs.yml` edit per page. The benefit is that a missing nav entry is detectable: `mkdocs build --strict` emits a warning for docs files not reachable from nav (with `not_in_nav` plugin or by observing "documentation file not found" warnings). Use this as a lint signal.

**Example — adding the 5 v3.0 pages to nav:**

```yaml
nav:
  - Home: index.md
  - Installation: installation.md
  - Quick Start: quickstart.md
  - User Guide:
    - guide/index.md
    - Tutorial: tutorial.md
    - Core Concepts: concepts.md
    - Knowledge Paradigms: paradigms.md
    - Obsidian Starter Kit: obsidian.md
    - Built-in Plugins: plugins.md
    - Session Recall: session-recall.md           # NEW
    - Polaris Priorities: polaris.md              # NEW
    - Contradiction Detection: contradiction-detection.md  # NEW
    - Media Ingestion: media-ingestion.md         # NEW
    - Methodology Guidance: methodology-guidance.md        # NEW
    - Agentic Workflows: agentic-workflows.md
    - Command Reference: commands.md
    - Configuration: configuration.md
    - Troubleshooting: troubleshooting.md
    - Best Practices: best-practices.md
  - Developer Guide:
    - dev/index.md
    - Contributing: development.md
    - Plugin Authoring: plugin-guide.md
    - API Reference: api-reference.md
    - MCP Server: mcp.md
    - Agent System Manual: agents.md
```

### Pattern 2: Strict Build as Doc Lint Gate

**What:** `mkdocs build --strict` converts all MkDocs warnings into errors. This catches: broken internal links, pages in `docs/` not referenced by `nav:`, malformed front matter. Run in PR CI to block merges with broken docs.

**When to use:** In a new `doc-lint` job in `pr-ci.yml`, separate from the main `validate_pr` job so it can be clearly identified in the CI summary.

**Trade-offs:** Adds ~30 seconds to PR CI (MkDocs build on a 20-page site is fast). Worth it — catches broken links before merge, not after deploy.

**Implementation in `pr-ci.yml`:**

```yaml
doc_lint:
  name: Doc Lint
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
      with:
        fetch-depth: 0
    - uses: actions/setup-python@v5
      with:
        python-version: '3.x'
    - name: Install MkDocs dependencies
      run: pip install mkdocs==1.6.1 mkdocs-shadcn==0.10.2 mkdocs-redirects==1.2.2 "mkdocstrings[python]>=1.0.3"
    - name: Doc lint (strict build)
      run: mkdocs build --strict
    - name: Link check
      run: |
        pip install linkchecker
        linkchecker site/ --check-extern --ignore-url "^https://github.com" --ignore-url "^https://pypi.org"
```

Note: External link checking is optional and can be scoped to only internal links (`--no-warnings --check-extern` can be omitted) to avoid flakiness from transient network failures in CI.

### Pattern 3: CLAUDE.md Docs-as-Code Rule

**What:** A standing rule in CLAUDE.md that fires whenever code changes touch a feature. The rule is explicit and checkable, not vague ("keep docs current").

**When to use:** Every time a feature is added, modified, or removed.

**Recommended rule text for CLAUDE.md:**

```markdown
## Documentation Rule

Every PR that adds, modifies, or removes a user-visible feature MUST include documentation changes in the same PR. "Same PR" is enforced — do not open a follow-up doc PR.

**What counts as user-visible:** New CLI commands or flags, new MCP tools/resources/prompts,
new configuration keys, changed behavior of existing commands, new content types or lifecycle states.

**Required updates per change:**
1. The feature's dedicated page in `docs/` — write or update it
2. `mkdocs.yml nav:` — add the page if it is new
3. `docs/llms.txt` — add a line for the new page (title + URL)
4. `docs/llms-full.txt` — append the page's full content
5. `docs/index.md` quick links table — if the feature warrants a top-level entry
6. Cross-reference pages — concepts.md, agents.md, agentic-workflows.md, mcp.md as relevant

**Verification:** Run `mkdocs build --strict` locally before pushing. A clean build means no broken links and no unreachable pages.
```

### Pattern 4: GSD Phase Doc Task Injection

**What:** Every GSD phase plan for a feature includes a mandatory doc task block. This is a structural convention in the phase template — not advisory but required to close the phase.

**When to use:** Every feature phase in every future milestone.

**Standard doc task block to include in each phase plan:**

```markdown
### Documentation Tasks

These tasks close in the same phase as the feature — not deferred.

- [ ] Write or update `docs/<feature-page>.md` with CLI usage, MCP tool reference, examples, and agent workflow
- [ ] Update `mkdocs.yml nav:` to include the new page
- [ ] Update `docs/llms.txt` with the new page entry
- [ ] Update `docs/llms-full.txt` with the page's full content
- [ ] Update cross-reference pages: concepts.md (if new type), agents.md (tool inventory), mcp.md (tool count), agentic-workflows.md (if new recipe)
- [ ] Verify: `mkdocs build --strict` passes locally
```

### Pattern 5: Redirect Registration for URL Changes

**What:** When a doc page is renamed or moved, the old URL must redirect to the new URL via `mkdocs.yml redirects:`. Without this, any external link (blog posts, agent memory, search engine results) hard-breaks.

**When to use:** Whenever a doc file is renamed or moved.

**Trade-offs:** Requires remembering to add the redirect alongside the file change. The `mkdocs-redirects` plugin is already installed (in both `pyproject.toml` dev deps and `docs.yml` CI). The cost is one YAML line.

```yaml
# mkdocs.yml
plugins:
  - redirects:
      redirect_maps:
        old-page-name.md: new-page-name.md
```

---

## Data Flow

### New Page Integration Flow

```
Author writes docs/session-recall.md
    |
    v
mkdocs.yml nav: — add "Session Recall: session-recall.md" under User Guide
    |
    v
docs/llms.txt — add line: "- [Session Recall](https://...): ..."
    |
    v
docs/llms-full.txt — append page's full content
    |
    v (PR CI: new doc-lint job)
mkdocs build --strict
    | Checks: broken internal links, unreachable pages, bad front matter
    | Fails PR if any warning/error
    v
PR merges to develop
    |
    v (docs.yml triggered by develop push)
mkdocs build → upload Pages artifact → deploy-pages
    |
    v
https://thatdevstudio.github.io/ztlctl/session-recall/ live
```

### Existing CI Integration Points

```
pr-ci.yml (current)                     pr-ci.yml (v3.1)
──────────────────────────────────      ──────────────────────────────────────
validate_pr job:                        validate_pr job (unchanged):
  - ruff check                            - ruff check
  - ruff format                           - ruff format
  - mypy                                  - mypy
  - pytest                                - pytest
  - uv build                              - uv build
  - pip-audit                             - pip-audit
  - mcp extra tests                       - mcp extra tests
  - commit lint                           - commit lint

                                        doc_lint job (NEW, parallel):
                                          - mkdocs build --strict
                                          - (optional) link check
```

The two jobs run in parallel — `doc_lint` does not need `validate_pr` to complete first and vice versa. PR is blocked if either fails.

### llms.txt and llms-full.txt Update Flow

```
New page added (e.g., docs/session-recall.md)
    |
    v
docs/llms.txt — manual update (CLAUDE.md rule requires this)
  Add: "- [Session Recall](https://thatdevstudio.github.io/ztlctl/session-recall/): Description"
    |
    v
docs/llms-full.txt — manual update
  Append: "## Session Recall\n\n[full page content]"
    |
    v (committed in same PR as the new page)
GitHub Pages serves updated llms.txt and llms-full.txt after docs.yml runs
```

---

## Integration Points

### New vs Modified Files for v3.1

**New files (docs):**

| File | Section | Notes |
|------|---------|-------|
| `docs/session-recall.md` | User Guide | CLI usage, MCP resource ref, temporal/topic/topology query examples |
| `docs/polaris.md` | User Guide | Init scaffold, MCP resource, check_alignment action, agent alignment workflow |
| `docs/contradiction-detection.md` | User Guide | Heuristic scoring explanation, CAT_SEMANTIC check, contradicts edges, MCP review |
| `docs/media-ingestion.md` | User Guide | faster-whisper setup, VTT/SRT, two-phase captured→annotated, optional dep install |
| `docs/methodology-guidance.md` | User Guide | Prose-as-title template, title quality check severity, garden backlog candidates |

**Modified files (docs):**

| File | What Changes |
|------|-------------|
| `docs/concepts.md` | Add v3.0 content types: media/ingested references, session recall entries, contradiction edges |
| `docs/agentic-workflows.md` | Add recipes: polaris-aligned session, recall-driven context, contradiction review workflow |
| `docs/agents.md` | Add v3.0 tool inventory rows: recall_*, check_alignment, detect_contradictions, ingest_* |
| `docs/mcp.md` | Update tool count (73+), add new resources (sessions/recent, polaris/priorities, contradictions/review) |
| `docs/llms.txt` | Add 5 new page entries |
| `docs/llms-full.txt` | Append 5 new pages' full content; update modified pages |
| `docs/index.md` | Add v3.0 features to "What Makes ztlctl Different" section |
| `docs/guide/index.md` | Add new pages to User Guide navigation table |
| `mkdocs.yml` | Add 5 new pages to `nav:` User Guide section |

**New files (CI):**

No new workflow files — the doc lint job is added as a second job inside the existing `pr-ci.yml`.

**Modified files (CI):**

| File | What Changes |
|------|-------------|
| `.github/workflows/pr-ci.yml` | Add `doc_lint` job: `mkdocs build --strict` + optional link check |

**Modified files (project):**

| File | What Changes |
|------|-------------|
| `CLAUDE.md` | Add explicit docs-as-code rule in a new "Documentation Rule" section |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| `mkdocs.yml nav:` ↔ `docs/*.md` | MkDocs resolves nav entries as relative paths from docs_dir | Every new page requires both a file and a nav entry |
| `docs/llms.txt` ↔ GitHub Pages | Static file served as-is | MkDocs does not process it — served at `/llms.txt` relative to site root |
| `docs/llms-full.txt` ↔ GitHub Pages | Static file served as-is | Same as llms.txt |
| `mkdocstrings[python]` ↔ `src/ztlctl/` | Auto-generates API reference from docstrings at build time | Requires `allow_inspection: false` in CI (no optional deps installed) |
| `pr-ci.yml doc_lint` ↔ `mkdocs.yml` | Installs same pinned MkDocs versions as `docs.yml` | Pin versions identically to avoid "passes CI, breaks deploy" |
| `docs/plans/` ↔ build | `exclude_docs: |` in `mkdocs.yml` already excludes `plans/` | Confirmed — no action needed |

---

## Build Order

The v3.1 work has a clear dependency chain:

```
Step 1: doc-lint CI job (pr-ci.yml)
        Add doc_lint job to pr-ci.yml.
        No content dependency — can be done first as infrastructure.
        Unblocks: all subsequent doc PRs are gated before merge.
        |
        v
Step 2: CLAUDE.md rule
        Add Documentation Rule section.
        No content dependency — standing instruction.
        |
        v
Step 3: 5 new v3.0 feature pages (can be written in any order)
        session-recall.md, polaris.md, contradiction-detection.md,
        media-ingestion.md, methodology-guidance.md
        Each PR: new page + mkdocs.yml nav entry + llms.txt entry +
                 llms-full.txt append + relevant cross-reference updates
        Each PR: must pass new doc_lint gate before merge
        |
        +──────────────────────────────────────────────┐
        v                                              v
Step 4a: Update existing docs                   Step 4b: Quality pass
         concepts.md, agentic-workflows.md,           Tone/depth/examples audit
         agents.md, mcp.md, index.md                  across all pages
         (can be one PR or split by file)              (independent of step 4a)
        |
        v
Step 5: internal doc refresh
        CLAUDE.md architecture section (reflects v3.0 layer structure),
        DESIGN.md (post v3.0 architecture decisions),
        README.md feature list (73+ actions, new features)
        (independent of steps 3-4; can be done concurrently)
```

Steps 3, 4a, 4b, and 5 are independent and can be phased or parallelized. Step 1 (CI gate) and Step 2 (CLAUDE.md rule) should land first so subsequent PRs are covered.

---

## Anti-Patterns

### Anti-Pattern 1: Doc PRs Separate from Feature PRs

**What people do:** Write the feature code in one PR, open a follow-up "docs: ..." PR after merge.

**Why it is wrong:** The follow-up PR gets deprioritized under time pressure and quietly never merges. v3.0 shipped with 5 undocumented features because of exactly this pattern (per PROJECT.md). The CI gate and CLAUDE.md rule exist to close this gap — but only if enforced at the PR that introduces the feature, not after.

**Do this instead:** Every feature PR includes the doc page, nav registration, llms.txt update, and cross-reference edits. The doc_lint CI gate makes it a hard requirement, not a soft expectation.

### Anti-Pattern 2: `mkdocs build` Without `--strict` in CI

**What people do:** Run `mkdocs build` without `--strict` in PR CI, assuming the deploy job will catch issues.

**Why it is wrong:** `mkdocs build` without `--strict` succeeds with warnings for broken internal links and unreachable pages. These become live 404s on the deployed site. The deploy job runs only on develop (post-merge), so broken docs pass the PR gate and land in production.

**Do this instead:** Always use `mkdocs build --strict` in both PR CI and the deploy job. One line change.

### Anti-Pattern 3: Updating llms.txt and llms-full.txt in a Separate Pass

**What people do:** Write the new doc page and register it in `mkdocs.yml`, then update llms.txt in a subsequent commit or PR.

**Why it is wrong:** After the page deploys, `llms.txt` serves an index without the new page entry for days or weeks. Agents consuming llms.txt for capability discovery miss the new feature entirely. llms-full.txt used for LLM context ingestion is similarly stale.

**Do this instead:** Every PR that adds a new doc page includes the llms.txt and llms-full.txt updates in the same commit. The CLAUDE.md rule lists this as a mandatory item in the per-change checklist.

### Anti-Pattern 4: Pinning Different MkDocs Versions in CI vs Deploy

**What people do:** Update the version in `docs.yml` (the deploy workflow) but not in `pr-ci.yml` (the lint job), or vice versa.

**Why it is wrong:** A warning that `--strict` would catch in the deploy job but not the lint job means broken docs pass the PR gate. Or a warning caught only in the lint job means the PR is blocked for something the deploy accepts — confusing and noisy.

**Do this instead:** The `doc_lint` job in `pr-ci.yml` installs identical versions: `mkdocs==1.6.1 mkdocs-shadcn==0.10.2 mkdocs-redirects==1.2.2 "mkdocstrings[python]>=1.0.3"`. When versions are bumped, update both files in the same PR.

### Anti-Pattern 5: Adding Pages to `docs/guide/` Without Updating Nav

**What people do:** Add `docs/guide/session-recall.md` thinking the subdirectory structure implies the nav section.

**Why it is wrong:** MkDocs with an explicit `nav:` block ignores filesystem hierarchy entirely. A page in `docs/guide/` that is not in `nav:` is reachable only by direct URL — it appears in no navigation panel and does not appear in search results (MkDocs search indexes only nav-registered pages when `nav:` is defined).

**Do this instead:** New pages go in `docs/` root (consistent with existing pages). Register them in `mkdocs.yml` `nav:` under the correct section. The guide/index.md section landing page links to them via relative path.

---

## Scaling Considerations

This is a local CLI tool docs site. Delivery scaling is not a concern — GitHub Pages handles all traffic. The relevant dimension is content maintenance overhead as the site grows.

| Content Scale | Architecture Adjustments |
|---------------|--------------------------|
| 20 pages (current) | Hand-maintained llms.txt and llms-full.txt are viable. One CLAUDE.md rule is enough enforcement. |
| 35-50 pages (v3.1 + next 2 milestones) | Add a `scripts/gen_llms_txt.py` generator (proposed in v2.1 research). Hand-maintenance becomes error-prone past ~30 pages. |
| 100+ pages | Consider sectioned llms.txt with `## Optional` block per spec. Split llms-full.txt by section to avoid token limits. |

The doc_lint CI job scales to any page count — `mkdocs build --strict` runs the same regardless of site size.

---

## Sources

- Existing codebase read directly: `mkdocs.yml`, `.github/workflows/docs.yml`, `.github/workflows/pr-ci.yml`, `docs/index.md`, `docs/guide/index.md`, `docs/dev/index.md`, `docs/llms.txt`, `docs/agents.md`, `docs/mcp.md`, `docs/agentic-workflows.md`, `pyproject.toml` — 2026-03-21 (HIGH)
- `.planning/PROJECT.md` — v3.1 milestone scope and feature list — 2026-03-21 (HIGH)
- Previous `.planning/research/ARCHITECTURE.md` (v2.1) — provides history context; not the live system — 2026-03-20 (reference only)
- MkDocs docs: `--strict` flag converts warnings to errors, `exclude_docs` excludes files from build, explicit `nav:` overrides filesystem discovery — training data confirmed against project's live mkdocs.yml (HIGH)

---

*Architecture research for: ztlctl v3.1 documentation site integration and docs-as-code enforcement*
*Researched: 2026-03-21*
