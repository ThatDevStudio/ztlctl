# Pitfalls Research

**Domain:** Documentation quality overhaul — adding professional-grade docs to an existing Python CLI/MCP tool (ztlctl v3.1)
**Researched:** 2026-03-21
**Confidence:** HIGH (infrastructure, drift, tone) / MEDIUM (agent-specific docs patterns) / HIGH (ztlctl-specific analysis from source)

---

## Critical Pitfalls

### Pitfall 1: Documenting What the Tool Does Instead of What the User Needs to Accomplish

**What goes wrong:**
Pages become feature inventories: "The `create note` command accepts the following flags: `--title`, `--tags`, `--topic`, `--links`..." Users arrive with a goal — "I want to capture a research finding" — not with a desire to enumerate flags. The docs are technically complete but practically useless because they describe the tool from the inside out rather than the user's task from the outside in.

ztlctl has 73+ actions, 15 services, and 5 command groups. A reference-first organization makes every feature discoverable but makes every workflow invisible.

**Why it happens:**
The people writing the docs know the codebase. They reach for the structure they already understand: commands, flags, services. Writing from a user's mental model requires deliberately stepping outside the implementation.

**How to avoid:**
Structure pages around user goals, not CLI commands. Each major page should open with "When you want to X, you..." not "The X command provides...". The reference table (flags, options, types) belongs after the narrative explanation, not before it.

For ztlctl specifically: every new v3.0 feature page (session recall, polaris, contradiction detection, media ingestion) should open with the *problem it solves*, then show the solution, then provide the reference. The `agents.md` page already does this correctly and is the model to follow.

**Warning signs:**
- A page's first heading is a command name
- Flags and options appear before any explanation of why you'd use them
- The page has no examples showing an end-to-end workflow

**Phase to address:**
Documentation quality overhaul phase — apply to all new and updated pages before publishing.

---

### Pitfall 2: CLI Examples That Drift from Source on the First Feature Change

**What goes wrong:**
Every example in the docs claims `ztlctl session recall --topic python --limit 10`. Three weeks later, a flag is renamed, a default changes, or the command gains a required positional argument. The example still "works" syntactically but produces wrong output or fails silently. Users copy-paste it and get a confusing result.

For ztlctl v3.1, all five new v3.0 feature pages need fresh examples. These pages will be written exactly once during the milestone and never reviewed against source again unless there is a structural enforcement mechanism.

**Why it happens:**
Documentation is written in a sprint, then falls into maintenance limbo. There is no CI step that runs docs examples against the actual CLI. Documentation PRs don't require a source-verified badge. The ztlctl v2.1 docs already found 15+ inaccurate commands during its quality pass — that correction happened once, manually.

**How to avoid:**
1. Every CLI example in docs must be verified against the actual CLI output at time of writing. Use `uv run ztlctl <command> --help` as ground truth — copy flag names verbatim.
2. Add a CLAUDE.md rule: "When writing or updating any CLI example, run the command against the source and confirm output matches before committing."
3. For the most critical examples (quickstart, agentic-workflows, agents.md), add a CI smoke test that runs the example commands against a real vault and asserts non-zero success.
4. When an action is renamed or a flag changes, add a docs update task to the PR that made the change.

**Warning signs:**
- A docs PR is merged without any `uv run ztlctl` verification step
- An example uses a flag name that differs by even one character from `--help` output
- Examples for v3.0 features were written before the feature was finalized

**Phase to address:**
Documentation-as-code enforcement phase — establish the rule before writing new pages. Apply retroactively to all existing examples in the quality pass phase.

---

### Pitfall 3: Over-Documenting Internal Architecture That Users Don't Need

**What goes wrong:**
The architecture is genuinely interesting: 6-layer package structure, ActionRegistry define-once pattern, WAL-backed event bus, 4-layer action model. But writing extensive docs about `domain/` vs `infrastructure/` separation, or how `_dispatch_post_action_event` works internally, creates noise in the wrong place. Users following the user guide encounter architecture diagrams meant for plugin authors. Plugin authors encounter user-guide workflows when they need hookspec signatures.

This is already partially solved by the two-track navigation (User Guide + Developer Guide), but the risk is that new pages for v3.0 features blur the line — "session recall" belongs in User Guide, "how session recall stores temporal edges in SQLite" belongs nowhere unless it's in DESIGN.md.

**Why it happens:**
The author knows the implementation and finds it interesting. The impulse is to share internal knowledge because it feels like it adds depth. But architectural detail in user-facing docs adds cognitive overhead without helping the user accomplish anything.

**How to avoid:**
Apply the test: "Does knowing this help a user accomplish their goal?" If yes, include it. If it only satisfies curiosity or explains implementation choices, it belongs in DESIGN.md or a Developer Guide architecture page — not in user-facing docs.

For v3.1: new pages for session recall, polaris, contradiction detection, media ingestion, and methodology guidance should be tested against this filter before publishing. Internal details about the WAL drain, the cosine similarity threshold, or the faster-whisper frame size don't belong in user-facing pages.

**Warning signs:**
- A user-facing page contains class names, method names, or module paths
- A page explains *why* a technical decision was made rather than *what to do*
- The page references `infrastructure/`, `domain/`, or layer names by name

**Phase to address:**
Documentation quality overhaul phase — apply the "Does this help the user accomplish their goal?" filter during writing and review.

---

### Pitfall 4: Missing the Beginner-to-Advanced Progression

**What goes wrong:**
A new user reads the quickstart, installs the tool, creates their first note — and then has no path forward. The docs jump from "here's how to create a note" directly to "here's the advanced reweave algorithm configuration" with nothing in between. The intermediate user — who has a vault, understands the basic workflow, and wants to integrate sessions or polaris priorities — has no guide that meets them where they are.

ztlctl's feature set now spans: basic CRUD (create/update/close), search and graph, session lifecycle, reweave and enrichment, semantic search, polaris priorities, contradiction detection, and media ingestion. Each of these represents a step up in conceptual complexity. If docs don't sequence them, users get overwhelmed or miss capabilities entirely.

**Why it happens:**
Docs are added feature-by-feature as features ship. Each new page explains its feature in isolation. No one steps back to ask "what is the progression from a new user to a power user, and does each page in the navigation correspond to a step in that progression?"

**How to avoid:**
Map the intended user journey before writing any new pages:
1. Install + first vault (quickstart)
2. Daily capture workflow (create, update, close, best-practices)
3. Finding and connecting knowledge (search, graph, reweave)
4. Working in sessions (session lifecycle, session recall)
5. Strategic alignment (polaris priorities, contradiction detection)
6. Ingestion at scale (media ingestion, methodology guidance)
7. Extensibility (plugins, agentic workflows)

Each new v3.0 page should be placed explicitly on this journey. The User Guide navigation order should reflect progression from simple to complex.

**Warning signs:**
- User Guide navigation order is roughly chronological by feature ship date, not by user progression
- An intermediate feature (sessions) appears before a foundational one (search)
- New feature pages are added to the bottom of the nav without considering where they fall in the user journey

**Phase to address:**
Navigation and information architecture phase — establish the progression map before writing new feature pages.

---

### Pitfall 5: Inconsistent Tone Across the Three-Audience Model

**What goes wrong:**
ztlctl already established a three-audience model: end users (mentor tone), developers (peer tone), agents (structured schemas). But when five new pages are added by one author in a sprint, all five may sound like the same voice — regardless of which track they're in. Alternatively, pages updated across multiple PRs by different contributors develop a patchwork of styles: some pages say "you can use," others say "the tool supports," others say "execute the following command."

Tone inconsistency is subtle but erodes the sense that the docs are a coherent product rather than a collection of notes.

**Why it happens:**
No style guide exists to constrain contributors. The three-audience model is documented as a decision in PROJECT.md but not as an actionable writing guide. When the same person writes user-facing and developer-facing pages in the same session, the mental context switch doesn't happen automatically.

**How to avoid:**
1. Write a one-page style guide as a CLAUDE.md appendix or a `docs/CONTRIBUTING.md`. Define:
   - User Guide tone: second person ("you"), present tense, active voice, no jargon without definition, goal-first
   - Developer Guide tone: first-person plural optional ("we"), technical terms assumed, rationale welcome
   - Agent docs tone: third-person declarative, schema-first, no narrative
2. Add a checklist to the docs PR template: "Which audience is this page for? Does the tone match?"
3. When adding v3.0 feature pages, assign each page to exactly one audience track and write it entirely in that voice.

**Warning signs:**
- A user-guide page says "the ActionRegistry dispatches..." (developer voice)
- An agent-facing page says "you might want to consider..." (user voice)
- Two pages in the same section use different verb forms for the same concept

**Phase to address:**
Style guide establishment phase (early) — define tone before writing new pages. Quality pass phase — audit existing pages for tone consistency.

---

### Pitfall 6: Technically Correct But Not Helpful — The "Reference Dump" Anti-Pattern

**What goes wrong:**
Pages contain every fact about a feature but answer no questions. A contradiction detection page that lists all the fields returned by `get_contradictions`, explains the heuristic scoring algorithm, describes every filter flag, and shows the TOML config options — but never shows a user how to act on a contradiction finding — is technically complete and practically useless.

The test: can a user who reads the page accomplish something they couldn't accomplish before? If yes, the page is helpful. If the page only tells them what exists, it fails.

**Why it happens:**
Reference-style writing is easier to produce. It maps directly from source code: list the flags, list the return fields, list the config keys. Explaining what to *do* with those capabilities requires understanding the user's workflow, which takes more thought.

**How to avoid:**
Every feature page must include at least one end-to-end "doing" example — not just command syntax, but a narrative that shows what the user starts with, what they run, and what they do next. For contradiction detection: "You've been capturing notes on a research topic for two weeks. Run `ztlctl check contradictions` to find where your thinking has evolved or diverged. Here's what the output looks like, and here's how to resolve a contradiction by updating a note."

For v3.1 specifically: session recall, polaris priorities, contradiction detection, media ingestion, and methodology guidance pages should each pass the "can a user accomplish something after reading this?" test before merging.

**Warning signs:**
- Page has complete flag reference but no workflow narrative
- Examples show command invocation but not what to do with the output
- No "typical usage" or "when to use this" section

**Phase to address:**
Documentation quality overhaul phase — apply the "accomplish something" test to every new and updated page.

---

### Pitfall 7: v3.0 Feature Pages That Don't Update Existing Cross-References

**What goes wrong:**
Five new feature pages are added. They're well-written, well-placed in the navigation, and source-verified. But `concepts.md` still doesn't mention contradiction detection. `agentic-workflows.md` still describes the session workflow without mentioning polaris priorities alignment. `agents.md` system capability table is missing `check_alignment`, `recall_sessions`, and `ingest_source`. The new pages exist but the existing docs don't point to them, so users following the established paths never discover the new capabilities.

**Why it happens:**
New pages are scoped as "add this page." Cross-reference updates feel like separate work and get deferred. There is no checklist that asks "which existing pages need to link to this new page?"

**How to avoid:**
For each new v3.0 feature page, identify every existing page where a cross-reference belongs:
- `concepts.md` → add new content types or mechanics
- `agentic-workflows.md` → add new workflow patterns
- `agents.md` → update system capabilities table and MCP tool list
- `mcp.md` → update tool reference if new MCP tools are added
- `llms.txt` and `llms-full.txt` → add new page entries

Make this identification explicit in the PR checklist for every docs PR that adds a new page.

**Warning signs:**
- `agents.md` capability table has fewer rows than the ActionRegistry has registered actions
- `concepts.md` doesn't mention a feature that has been shipped for two releases
- `llms.txt` doesn't include a page that was added in the same milestone

**Phase to address:**
New page authoring phase — require cross-reference audit as a PR gate. Also addressed in llms.txt/llms-full.txt update phase.

---

### Pitfall 8: llms.txt and llms-full.txt Going Stale After v3.0 Addition

**What goes wrong:**
`llms.txt` was built during v2.1 for the documentation site as it existed then. After v3.1 adds five new pages, the file still reflects the v2.1 page set. Agents using `llms.txt` for navigation don't know about session recall, polaris priorities, contradiction detection, or media ingestion. `llms-full.txt` concatenates page content and also becomes stale.

This is a v3.1-specific instance of the general staleness pitfall documented in v2.1 research. The risk is identical but the trigger is different: the staleness here comes from adding pages, not restructuring them.

**Why it happens:**
`llms.txt` is treated as a finished artifact, not a living index. PRs that add new docs pages don't include an `llms.txt` update in their scope.

**How to avoid:**
1. Regenerate `llms-full.txt` as a build step (`scripts/gen_llms_txt.py` already exists per v2.1 architecture). Run it as part of the docs build.
2. Add a CI check: count the pages in `docs/` (excluding internal/plans), count the entries in `llms.txt`, and fail if they differ.
3. Include `llms.txt` and `llms-full.txt` updates explicitly in the scope of every milestone docs phase.

**Warning signs:**
- `llms.txt` entry count is lower than the docs page count
- A new feature page exists under `docs/` but has no entry in `llms.txt`
- `llms-full.txt` file size hasn't grown after adding multiple new pages

**Phase to address:**
Agent accessibility update phase — scope as an explicit deliverable, not an afterthought.

---

## Technical Debt Patterns

Shortcuts that seem reasonable but create long-term problems.

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Write feature pages without source-verifying examples | Faster to write | Examples drift within one release; users copy broken commands | Never — always verify against `--help` output |
| Update `agents.md` capability table by memory | Avoids reading source | Table omits new actions; agents get incomplete tool inventory | Never — diff against ActionRegistry |
| Add new pages to bottom of nav by default | Zero nav redesign effort | Navigation reflects feature ship order, not user journey | Only if page genuinely belongs at the end of the user journey |
| Write user-facing pages with developer-voice explanations | Author writes what they know | Tone patchwork erodes docs coherence; users get confused by jargon | Never in User Guide track |
| Defer cross-reference updates to a "cleanup pass" | Unblocks page authoring | New pages are invisible to users following existing navigation paths | Never — do cross-references in the same PR as the page |
| Use placeholder/stub content for sections not yet written | Unblocks page structure | Ships empty sections; degrades trust; agents get empty context | Never — write real content or don't create the section |
| Skip `llms-full.txt` regeneration after adding pages | Saves one build step | Agent tools that rely on full-text context get incomplete knowledge base | Never in a docs milestone |

---

## Integration Gotchas

Common mistakes when connecting documentation to the tool's surfaces.

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| `agents.md` + ActionRegistry | Writing capability table from memory | Diff against `src/ztlctl/actions/` registered definitions; every action that has an MCP tool should have a row |
| `mcp.md` + auto-generated tools | Documenting tool signatures by hand | Auto-generated tools from ActionRegistry may have parameter names that differ from CLI flags; read `src/ztlctl/mcp/` as source of truth |
| `llms.txt` + docs site | Pointing to relative paths | All `llms.txt` URLs must be absolute (full domain); test each URL against the deployed site |
| `ztlctl docs` CLI command + page content | Returning raw markdown with frontmatter | The `---` YAML block is navigation metadata; strip before returning to any consumer |
| MkDocs `--strict` flag + new pages | Adding pages without nav entries | `mkdocs build --strict` fails on pages not listed in `nav:` in `mkdocs.yml`; add nav entry in same commit as page |
| CLAUDE.md enforcement rule + PR workflow | Writing the rule but not auditing existing pages | New rule prevents future drift but existing pages already have stale examples; schedule a retroactive audit as a milestone task |

---

## UX Pitfalls

Common user experience mistakes for a CLI/MCP tool with three audiences.

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| No "when to use this" section on feature pages | Users don't know if they need the feature; advanced users skip pages that would help them | Every feature page starts with a 1–2 sentence "When this matters" framing |
| Session recall page with no comparison to existing `session context` command | Users don't know the difference; may use the wrong tool | Explicit comparison: "Use session recall when... use session context when..." |
| Polaris priorities page framed as a configuration guide | Users see it as optional setup, not as a core alignment practice | Frame polaris as "the strategic layer of your vault" — define its purpose before its mechanics |
| Contradiction detection page with only automated detection | Users don't know how to act on a detected contradiction | Include a resolution workflow: "Found a contradiction? Here's how to decide whether to update, link, or mark it as intentional" |
| Media ingestion page without noting the optional dependency | Users install ztlctl and `ztlctl ingest file audio.mp3` fails with an opaque error | Prominently note at top of page: "Requires `uv add ztlctl[faster-whisper]` — see Installation" |
| Agent docs missing failure mode documentation | Agents encounter undocumented errors and either retry blindly or fail silently | `agents.md` should document every `ServiceResult` error category with a structured recovery action |

---

## "Looks Done But Isn't" Checklist

Things that appear complete in docs PRs but are missing critical pieces.

- [ ] **New feature page authored:** Cross-references added in `concepts.md`, `agentic-workflows.md`, `agents.md`, and `mcp.md` — verify each file was touched in the same PR
- [ ] **CLI examples written:** Every example verified with `uv run ztlctl <command> --help` or actual execution — flag names copied verbatim from output, not from memory
- [ ] **`agents.md` updated:** Capability table row count matches registered action count in `src/ztlctl/actions/` — run `grep -r "ActionDefinition" src/ztlctl/actions/ | wc -l` as a proxy check
- [ ] **`llms.txt` updated:** Entry count matches deployable docs page count — run `ls docs/*.md docs/**/*.md | grep -v plans | wc -l` as proxy check
- [ ] **`llms-full.txt` regenerated:** File modification timestamp is newer than any new doc page timestamp
- [ ] **MkDocs nav updated:** New page appears in `nav:` section of `mkdocs.yml` — `mkdocs build --strict` passes with zero warnings
- [ ] **Optional dependency callout present:** Any page for a feature with an optional dep (faster-whisper, sentence-transformers) has an explicit install note at the top
- [ ] **Tone verified:** Page re-read from top to bottom asking "which audience is this for?" — no user-guide pages with developer voice, no agent pages with narrative voice
- [ ] **Internal/implementation details removed:** Page passes the "does knowing this help the user accomplish their goal?" filter — no class names, layer names, or architectural rationale in user-facing pages
- [ ] **Progression placement confirmed:** Page placed in nav at the correct position in the beginner-to-advanced journey, not appended to the bottom by default

---

## Recovery Strategies

When pitfalls occur despite prevention, how to recover.

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| CLI examples found to be wrong after publish | LOW | Source-verify all examples on the affected pages; submit a fix PR; add the CLAUDE.md verification rule to prevent recurrence |
| `agents.md` capability table is stale | LOW | Diff against ActionRegistry registrations; add missing rows; this is a one-time audit per release |
| Tone patchwork across pages | MEDIUM | Establish style guide first; then audit pages one by one — user guide pages identified by track in nav; one edit pass per page |
| Missing beginner-to-advanced progression | MEDIUM | Reorder nav in `mkdocs.yml` (nav order is config-controlled, no file moves needed); add progression framing to section landing pages |
| New pages invisible because no cross-references | LOW | Audit existing pages for natural mention points; add cross-reference links in a single pass PR |
| `llms.txt` stale after page additions | LOW | Regenerate with `scripts/gen_llms_txt.py` or add entries manually; add CI check to prevent recurrence |
| Feature pages are reference dumps with no workflow narrative | HIGH | Requires rewriting the narrative framing of affected pages; cannot be patched with cross-references alone; plan as a dedicated task in the quality pass phase |

---

## Pitfall-to-Phase Mapping

How roadmap phases should address these pitfalls.

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Documenting tool internals instead of user goals | Pre-writing: establish "user goal" frame before authoring | Each new page opens with "When you want to..." not "The X command..." |
| CLI examples drifting from source | Enforcement: add CLAUDE.md rule + PR checklist before authoring | CI smoke test on critical examples; PR author attestation on flag names |
| Over-documenting internal architecture | Writing + review: apply "Does this help the user accomplish their goal?" filter | User Guide pages contain zero class names or layer references |
| Missing beginner-to-advanced progression | Navigation phase: map user journey before adding pages | Nav order reflects skill progression; no feature appears before its prerequisites |
| Inconsistent tone across audiences | Style guide: define tone rules before authoring phase | Each page re-read from the audience's perspective before merging |
| Reference dumps with no workflow narrative | Writing phase: require "doing" example before page is considered complete | Every page passes "can a user accomplish something after reading this?" test |
| v3.0 pages not cross-referenced from existing docs | Authoring phase: cross-reference audit is a PR gate | `concepts.md`, `agentic-workflows.md`, `agents.md` all touch same PR as new page |
| `llms.txt`/`llms-full.txt` stale | Agent accessibility phase: regeneration is a build step | CI page-count check; `llms-full.txt` size grows monotonically across releases |

---

## Sources

- [10 Common Developer Documentation Mistakes — Document360](https://document360.com/blog/developer-documentation-mistakes/) — structure, outdated content, missing setup, error scenarios (MEDIUM confidence — paywalled content accessed via search summary)
- [Why Stripe's API Docs Are the Benchmark — APIDog](https://apidog.com/blog/stripe-docs/) — progressive layers, interactive examples, features-not-shipped-until-docs-written cultural practice (HIGH confidence)
- [Optimizing Technical Documentation for LLMs and AI Agents — Biel.ai](https://biel.ai/blog/optimizing-docs-for-ai-agents-complete-guide) — standalone pages, single-question sections, consistent terminology, complete examples (MEDIUM confidence — blog post, verified against multiple sources)
- [Docs Linting Guide — Fern](https://buildwithfern.com/post/docs-linting-guide) — Vale linter, CI enforcement, link checking (MEDIUM confidence)
- [Avoiding the Silent Stale Doc Problem — Daryl J. White](https://djw.fyi/portfolio/preventing-drift/) — docs drift root causes, automation approaches (MEDIUM confidence)
- [Voice and Tone — Google Developer Documentation Style Guide](https://developers.google.com/style/tone) — tone consistency rules, second-person preference, active voice (HIGH confidence — official Google guide)
- [Top 10 Information Architecture Mistakes — Nielsen Norman Group](https://www.nngroup.com/articles/top-10-ia-mistakes/) — navigation invisibility, organizational principles, findability (HIGH confidence — NNGroup primary research)
- [How to Develop a Consistent Tone in Technical Documentation — WriteAtlas](https://writeatlas.com/how-to-develop-a-consistent-tone-and-voice-in-technical-documentation/) — style guide as linguistic constitution, reviewer role (MEDIUM confidence)
- ztlctl source analysis: `docs/` page inventory, `docs/agents.md` capability table, `docs/best-practices.md` pattern reference, `docs/agentic-workflows.md`, `.planning/PROJECT.md` v3.0 feature list, MEMORY.md project state

---
*Pitfalls research for: documentation quality overhaul — adding professional-grade docs to an existing Python CLI/MCP tool*
*Researched: 2026-03-21*
