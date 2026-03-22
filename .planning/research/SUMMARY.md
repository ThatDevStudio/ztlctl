# Project Research Summary

**Project:** ztlctl v3.1 — Documentation Quality Overhaul and Docs-as-Code Enforcement
**Domain:** Professional-grade CLI/MCP developer tool documentation
**Researched:** 2026-03-21
**Confidence:** HIGH

## Executive Summary

ztlctl v3.1 is a documentation quality milestone, not a feature milestone. The product already ships with a working MkDocs site (mkdocs-shadcn theme, two-track nav, GitHub Pages artifact deploy, API reference via mkdocstrings, llms.txt for agent accessibility). What v3.1 must close: five v3.0 features shipped with no documentation, the existing pages mix content types that Diataxis classifies as incompatible, and nothing enforces docs completeness at merge time. The result is a tool with production-grade infrastructure and amateur-grade content.

The research converges on a two-track approach: infrastructure first, then content. The infrastructure track adds a `doc_lint` CI job (mkdocs strict build + Vale + pymarkdownlnt), enforces docs-as-code via a CLAUDE.md rule, and establishes the navigation order that reflects user progression rather than feature ship order. The content track then writes the five missing v3.0 feature pages and updates all stale cross-references — with tone, structure, and source-verification discipline established before the first word is written. Prose linting via Vale with the Google style package enforces active voice, second person, and present tense automatically; pymarkdownlnt catches structural issues; lychee runs on a schedule to catch broken external links.

The primary risks are drift and incompleteness. The historical pattern for ztlctl is that documentation gets written as an afterthought and immediately falls behind: v3.0 shipped five undocumented features, v2.1 found 15+ inaccurate CLI examples during its quality pass. Both risks are structural, not one-time problems. The mitigation is equally structural: CI gates that make broken or missing docs fail the PR, not advisory guidelines that get skipped under time pressure. Every feature phase in every future milestone must embed a mandatory documentation task block — that is the single highest-leverage change this milestone can make.

---

## Key Findings

### Recommended Stack

The existing docs stack (MkDocs 1.6.1, mkdocs-shadcn 0.10.2, mkdocstrings, mkdocs-redirects, GitHub Pages artifact deploy) is solid and must not be replaced. v3.1 adds only four targeted new tools. Vale 3.14.1 is the definitive prose linter for docs-as-code — a Go binary with first-class pre-commit integration, used by Grafana, GitLab, Red Hat. The Google style package (v0.6.3) fits a CLI developer tool: second person, active voice, present tense, sentence-case headings. pymarkdownlnt 0.9.34 is the Python-native Markdown structure linter (the Node.js alternative, markdownlint-cli2, is incompatible with a pure-Python uv project). mkdocs-git-revision-date-localized 1.5.1 adds git-sourced "last updated" timestamps — always accurate, zero author discipline required. lychee runs in scheduled CI only (not per-PR) to avoid network flakiness.

**Core technologies (new additions only):**
- Vale 3.14.1 + Google style 0.6.3: prose linting — enforces consistent, professional writing voice across all doc pages
- pymarkdownlnt 0.9.34: Markdown structure linting — heading hierarchy, list formatting, code fence syntax; Python-native, no Node.js
- mkdocs-git-revision-date-localized 1.5.1: git-sourced "last updated" dates on every page — currency signal for a fast-moving project
- pymdownx.superfences + pymdownx.tabbed: titled code blocks and tabbed CLI/MCP/agent examples — already transitively installed, just needs enabling
- lychee (CI scheduled): external broken link checker; Rust-based, async, runs weekly to avoid PR flakiness

**Critical version requirement:** Never use `mkdocs build -v --strict` — a confirmed MkDocs bug causes `-v --strict` to suppress strict-mode failures. Always `mkdocs build --strict` without `-v`.

### Expected Features

The Diataxis framework is the single most important structural insight: four content types (tutorial, how-to, reference, explanation) serve incompatible user needs and must be kept on separate pages. Mixing them is the most common documentation quality failure and the pattern most visible in the current ztlctl docs. Every existing page must be audited against this taxonomy before new pages are written — this audit is the structural gate that unblocks everything else.

**Must have (table stakes — required for "professional-grade" claim):**
- Diataxis content type audit — classify all existing pages, identify mixed-purpose pages for remediation; this is the foundational gate
- Five new v3.0 feature pages: session recall, polaris priorities, contradiction detection, media ingestion, methodology guidance — each with problem framing, CLI usage, MCP tool surface, and agent workflow examples
- Update `concepts.md`, `agentic-workflows.md`, `agents.md`, `mcp.md`, `commands.md` with v3.0 content — accuracy
- Consistent CLI syntax conventions across all pages (Google style: `[optional]`, `{required}`, `$` prompts, "similar to the following:")
- Callout admonitions with consistent taxonomy (Warning = destructive ops, Note = important context, Tip = best practices)
- "What's next" links at the end of each User Guide page — prevents dead-ends in the learning path
- Progressive disclosure on command pages: simplest useful invocation first, then option table, then advanced examples
- Documentation-as-code CLAUDE.md rule and GSD phase template doc task block — prevents future rot

**Should have (meaningful quality lift — v3.1.x after P1 complete):**
- Glossary page for domain-specific terms (reweave, polaris, WAL, garden, session recall, contradiction score)
- Per-feature MCP tool surface documented alongside CLI surface on every feature page
- Error messages as teaching moments in troubleshooting.md (symptom → diagnosis → fix → prevention)
- Methodology guidance deepening in paradigms.md (prose-as-title, garden maturity progression, polaris alignment workflows)

**Defer (v4+):**
- Asciinema / terminal recordings — meaningful lift, requires recording infrastructure
- Versioned docs — defer until adoption proves version fragmentation is a real support problem
- i18n — out of scope until adoption requires it

### Architecture Approach

The MkDocs system uses artifact-based GitHub Pages deploy (no `gh-pages` branch). All navigation is driven by explicit `nav:` in `mkdocs.yml` — filesystem layout is irrelevant; a file not in `nav:` is unreachable from navigation and excluded from search. The five new v3.0 feature pages go in `docs/` root (consistent with all existing v2.1 pages) and are registered in `mkdocs.yml nav:` under the User Guide section. A new `doc_lint` job runs in `pr-ci.yml` parallel to `validate_pr` — `mkdocs build --strict` plus optional pymarkdownlnt scan — blocking merges with broken or unreachable docs. The deploy workflow (`docs.yml`) is unchanged. `llms.txt` and `llms-full.txt` are hand-maintained and must be updated in the same PR as any new page addition. The CLAUDE.md docs-as-code rule encodes a per-change checklist: feature page, nav registration, llms.txt entry, llms-full.txt append, cross-reference updates, strict build verification.

**Major components:**
1. `mkdocs.yml nav:` — authoritative navigation registry; every new page requires an explicit entry; `mkdocs build --strict` detects missing entries
2. `pr-ci.yml doc_lint job` — new parallel CI job; gates merges; runs `mkdocs build --strict` plus optional link check; must pin identical MkDocs versions to `docs.yml`
3. `.vale.ini` + `.pymarkdown.json` — prose and structure linting config at repo root; `vale sync` downloads Google style on checkout; `.vale/styles/` gitignored
4. `docs/llms.txt` + `docs/llms-full.txt` — hand-maintained agent accessibility files; updated in every docs PR; CI count-check recommended at 30+ pages
5. `CLAUDE.md Documentation Rule` — standing enforcement instruction; defines per-change checklist; makes docs-as-code structural, not advisory

### Critical Pitfalls

1. **Documenting what the tool does instead of what the user needs to accomplish** — Structure pages around user goals, not CLI commands. Every new v3.0 feature page opens with the problem it solves, then shows the solution, then provides the reference table. The existing `agents.md` is the model to follow.

2. **CLI examples that drift from source on the first feature change** — Every CLI example must be verified against `uv run ztlctl <command> --help` at time of writing, flag names copied verbatim. Add CLAUDE.md rule: when writing or updating any CLI example, run the command against source and confirm output matches. CI smoke tests on critical examples (quickstart, agentic-workflows) provide structural protection.

3. **Missing beginner-to-advanced progression** — Map the user journey before adding any new pages: install → daily capture → search/graph → sessions → strategic alignment → ingestion at scale → extensibility. New v3.0 pages must be placed at the correct position in this progression in `mkdocs.yml nav:`, not appended to the bottom.

4. **v3.0 feature pages that don't update existing cross-references** — Every new page PR must touch `concepts.md`, `agentic-workflows.md`, `agents.md`, `mcp.md`, `llms.txt`, and `llms-full.txt`. This is a PR gate, not a follow-up task. Cross-reference updates deferred to a "cleanup pass" reliably never happen.

5. **llms.txt and llms-full.txt going stale** — Five new pages added without updating these files means agents using llms.txt for capability discovery never discover session recall, polaris, contradiction detection, or media ingestion. Update in the same commit as the new page. At 30+ pages, add a generator script and a CI count-check.

---

## Implications for Roadmap

Based on combined research, the build order has a clear dependency chain. Infrastructure must land before content, and a user journey map must be established before the first new feature page is written. All content work can then proceed in parallel across phases.

### Phase 1: Docs-as-Code Infrastructure

**Rationale:** This phase has no content dependencies and enables all subsequent phases. A doc_lint CI gate that doesn't exist means every subsequent docs PR merges without structural validation. The CLAUDE.md rule and GSD phase template update prevent future rot from this milestone forward. These changes take one to two PRs and unblock everything else.

**Delivers:**
- `doc_lint` job in `pr-ci.yml` (`mkdocs build --strict` + pymarkdownlnt scan)
- `.vale.ini` + `.pymarkdown.json` config at repo root with Vale Google style
- CLAUDE.md Documentation Rule section with per-change checklist
- GSD phase template: mandatory Documentation Tasks block in every future feature phase

**Addresses:** Documentation-as-code enforcement (P1), docs CI gate (table stakes)
**Avoids:** Doc PRs separate from feature PRs anti-pattern; `mkdocs build` without `--strict` in CI

### Phase 2: Navigation and Information Architecture

**Rationale:** The user journey map and Diataxis content type audit must be established before new pages are written. Writing five new pages into a navigation that reflects feature ship order (not user progression) amplifies the existing structural problem rather than fixing it. This phase is a short audit PR — classifying pages, not rewriting them.

**Delivers:**
- Diataxis audit: every existing page classified by content type; mixed-purpose pages listed for remediation
- User Guide `nav:` reordered in `mkdocs.yml` to reflect beginner-to-advanced progression
- Confirmed placement for all five v3.0 feature pages in the navigation order
- "What's next" links structure determined for the User Guide learning path

**Addresses:** Diataxis structural audit (P1 gate), progressive disclosure, "What's next" navigation
**Avoids:** Beginner-to-advanced progression pitfall; nav order reflecting feature ship date rather than skill progression

### Phase 3: Five v3.0 Feature Pages

**Rationale:** With CI gating live and nav order established, the five undocumented v3.0 features can be written correctly on the first attempt. Session recall should be written and reviewed first — it is the most structurally straightforward — then used as the template pattern for the remaining four. Each page is delivered as an individual PR to keep review scope manageable.

**Delivers:**
- `docs/session-recall.md` — temporal/topic/topology querying, MCP resource reference, recall vs. session context comparison
- `docs/polaris.md` — init scaffold, MCP resource, check_alignment action, agent alignment workflow; framed as "strategic layer of your vault" not "optional configuration"
- `docs/contradiction-detection.md` — heuristic scoring explanation, CAT_SEMANTIC check, resolution workflow (update / link / mark intentional)
- `docs/media-ingestion.md` — faster-whisper setup with prominent optional dependency callout, VTT/SRT, two-phase workflow
- `docs/methodology-guidance.md` — prose-as-title template, title quality check severity, garden backlog candidates
- For each page: `mkdocs.yml nav:` entry, `llms.txt` entry, `llms-full.txt` append, cross-references in `concepts.md` / `agentic-workflows.md` / `agents.md` / `mcp.md`

**Uses:** Vale + Google style (tone enforcement), pymarkdownlnt (structure), pymdownx.superfences + tabbed (titled code blocks, CLI/MCP/agent tab examples)
**Avoids:** Reference dump anti-pattern; internal architecture leaking into user-facing pages; stale llms.txt; missing cross-references

### Phase 4: Existing Page Updates and Quality Pass

**Rationale:** New pages exist but the existing pages need parallel updates to reflect v3.0 reality and apply quality patterns (progressive disclosure, consistent admonition taxonomy, consistent CLI syntax conventions, "What's next" links). These can proceed in parallel with Phase 3 — there is no blocking dependency between writing new pages and updating existing ones.

**Delivers:**
- `docs/concepts.md`: v3.0 content types added (sessions, contradictions, media)
- `docs/commands.md`: v3.0 commands added; progressive disclosure applied (simplest invocation first)
- `docs/agentic-workflows.md`: v3.0 recipes added (polaris-aligned session, recall-driven context, contradiction review)
- `docs/agents.md`: v3.0 tool inventory rows added; failure mode documentation added for agent error recovery
- `docs/mcp.md`: tool count updated (73+), new resources documented
- `docs/troubleshooting.md`: verified v3.0 completeness; error entries upgraded to symptom → diagnosis → fix → prevention format
- Global: consistent CLI syntax conventions, callout admonition taxonomy, "What's next" links applied across all User Guide pages

**Addresses:** Consistent CLI syntax (P1), progressive disclosure (P1), callout admonitions (P1), cross-reference updates
**Avoids:** Tone inconsistency; mixed tutorial/reference content on same page; examples without workflow narrative

### Phase 5: Internal Documentation Refresh

**Rationale:** CLAUDE.md, DESIGN.md, and README.md reflect pre-v3.0 reality. These are developer-facing documents that do not block user-facing docs from going live. They can run in parallel with Phases 3 and 4 or follow them.

**Delivers:**
- `CLAUDE.md` architecture section: reflects v3.0 6-layer structure, ActionRegistry, plugin API, MCP adapter
- `DESIGN.md`: post-v3.0 architecture decisions captured
- `README.md`: 73+ actions, new v3.0 features, updated command examples

**Addresses:** Internal documentation accuracy
**Avoids:** Developer-voice content leaking into user-facing docs (separate concerns)

### Phase 6: P2 Quality Additions (Glossary, MCP Surface, Methodology Deepening)

**Rationale:** These are meaningful quality lifts but not required for the "professional-grade" claim. The glossary page is written after feature pages because terms emerge during the writing process. Per-feature MCP tool surface documentation and methodology guidance deepening expand on content that Phase 3 establishes.

**Delivers:**
- `docs/glossary.md`: domain-specific terms (reweave, polaris, WAL, garden, session recall, contradiction score) with links from concepts.md and feature pages
- Per-feature MCP tool surface: CLI commands and equivalent MCP tool calls documented side-by-side on every feature page
- `docs/paradigms.md`: methodology guidance deepening — prose-as-title template, garden maturity progression, polaris alignment workflows

**Addresses:** Glossary (P2), per-feature MCP docs (P2), methodology guidance (P2)

### Phase Ordering Rationale

- Phase 1 (infrastructure) has no content dependencies and must land first so subsequent PRs are gated
- Phase 2 (nav/IA) must precede Phase 3 (new pages) to avoid writing content into the wrong structural context
- Phases 3, 4, and 5 are independent and can be parallelized if resources allow; Phase 3 is higher priority because it closes the five-undocumented-features gap
- Phase 6 is deferred until Phase 3 is complete because glossary terms emerge during feature page writing
- The five new feature pages in Phase 3 should be delivered as individual PRs (one per feature), each passing the doc_lint gate before merge, rather than as a single large PR

### Research Flags

Phases with well-documented patterns (skip research-phase):
- **Phase 1:** CI job structure and Vale/pymarkdownlnt configuration are fully specified in STACK.md and ARCHITECTURE.md; implementation is mechanical
- **Phase 2:** Diataxis audit methodology is well-documented at diataxis.fr; nav reordering is a `mkdocs.yml` edit; no external research needed
- **Phase 5:** Internal docs are factual updates derived from codebase reading; no pattern research needed

Phases requiring source verification (codebase reading, not external research):
- **Phase 3:** Each feature page must be verified against the ActionRegistry (`src/ztlctl/actions/`) and the actual CLI (`uv run ztlctl <command> --help`) before the page is considered complete; flag names and MCP tool signatures must come from source, not memory
- **Phase 4:** `agents.md` capability table must be diffed against the ActionRegistry; `mcp.md` tool count must be verified against the auto-generated MCP tool list

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All recommendations sourced from official docs, GitHub releases, and direct codebase inspection. Vale, pymarkdownlnt, lychee, and mkdocs-git-revision-date-localized are current and version-confirmed |
| Features | HIGH | Diataxis, CLIG, Google style guide, and Stripe/Docker patterns are primary sources; Obsidian patterns are MEDIUM (content rendering limited during research; patterns inferred from structure) |
| Architecture | HIGH | Derived from direct codebase reading (`mkdocs.yml`, `pr-ci.yml`, `docs.yml`, all `docs/` pages). No assumptions — live system confirmed |
| Pitfalls | HIGH | Infrastructure and drift pitfalls confirmed against ztlctl source history (v3.0 shipped undocumented features; v2.1 found 15+ inaccurate examples). Agent-specific patterns from blog sources are MEDIUM |

**Overall confidence:** HIGH

### Gaps to Address

- **llms-full.txt generator script existence:** PITFALLS.md references `scripts/gen_llms_txt.py` as existing per v2.1 architecture, but ARCHITECTURE.md notes the v2.1 implementation committed hand-maintained files. Confirm whether the generator script exists in the codebase before Phase 1 begins; if it does not, hand-maintenance is the correct approach until 30+ pages.
- **Vale local development installation path:** Vale is a Go binary and cannot be `uv add`'d. The CI path (errata-ai/vale-action@v2) is clear. The local development path (brew install vale vs. pre-commit hook auto-download) should be decided during Phase 1 implementation and documented in CONTRIBUTING.md.
- **pymarkdownlnt rule overrides for ztlctl docs:** The `.pymarkdown.json` config disables MD033 (inline HTML) because MkDocs admonitions trigger it. Additional rule overrides may be discovered during the first scan of existing docs; expect one tuning iteration before the rules are stable.
- **CI smoke testing of examples (P3):** The highest-protection mechanism against example drift but also the highest implementation cost. If in scope for v3.1, it requires a test vault fixture and should be scoped as a separate sub-phase with its own research.

---

## Sources

### Primary (HIGH confidence)
- Vale GitHub (github.com/vale-cli/vale) — v3.14.1 release confirmed
- Vale Google style GitHub (github.com/errata-ai/Google) — v0.6.3, CC BY 4.0
- pymarkdownlnt PyPI — v0.9.34, Python 3.13 compatible confirmed
- mkdocs-git-revision-date-localized PyPI — v1.5.1, January 2026
- mkdocs-shadcn GitHub — v0.10.2 (2026-03-19), pymdownx confirmed compatible
- Diataxis Documentation Framework (diataxis.fr) — four content type taxonomy
- Command Line Interface Guidelines (clig.dev) — lead with examples, error messages as teaching moments
- Google Developer Documentation Style Guide (developers.google.com/style) — tone, syntax conventions
- Docker CLI Reference (docs.docker.com/reference/cli/docker/) — command page structure pattern
- ztlctl codebase (direct inspection, 2026-03-21) — `mkdocs.yml`, `pr-ci.yml`, `docs.yml`, all `docs/` pages, `.planning/PROJECT.md`

### Secondary (MEDIUM confidence)
- Stripe API Documentation via APIDog analysis (apidog.com/blog/stripe-docs/) — docs as definition of done, fast paths for happy flow
- Obsidian Help — concept definition before use, philosophy before features (content rendering limited)
- Biel.ai — optimizing technical documentation for LLMs and AI agents
- Document360 — common developer documentation mistakes

### Tertiary (LOW confidence)
- WriteAtlas — tone and voice consistency in technical documentation
- 42 Coffee Cups — technical documentation best practices

---
*Research completed: 2026-03-21*
*Ready for roadmap: yes*
