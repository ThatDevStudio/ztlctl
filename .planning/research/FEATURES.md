# Feature Research

**Domain:** Professional-grade CLI/MCP developer tool documentation quality
**Researched:** 2026-03-21
**Confidence:** HIGH (Stripe/Docker patterns from primary sources; Diataxis from official site; CLI conventions from CLIG and Google style guide)

---

## Context

This research covers the v3.1 milestone: raising documentation to professional-grade quality (Stripe/Docker/Obsidian-caliber). The docs infrastructure already exists: MkDocs with mkdocs-shadcn theme, two-track navigation (User Guide + Developer Guide), llms.txt, agents.md, API reference. The gap is quality of execution, not presence of structure.

**Existing docs inventory (v2.1 era):**
- User Guide: tutorial, concepts, paradigms, obsidian, plugins, agentic-workflows, commands, configuration, troubleshooting, best-practices
- Developer Guide: contributing, plugin-guide, api-reference, mcp, agents
- Agent accessibility: llms.txt, llms-full.txt, `ztlctl docs` CLI, MCP doc search

**v3.0 features with no documentation yet:** session recall, polaris priorities, contradiction detection, media ingestion, methodology guidance.

---

## Feature Landscape

### Table Stakes (Users Expect These)

Features a professional-grade docs site for a CLI developer tool must have. Missing any = docs feel incomplete or amateur.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Diataxis-aligned page structure (tutorial / how-to / reference / explanation as distinct types) | Every high-quality developer tool docs site separates learning from reference; mixing them makes both worse | HIGH | Structural audit required; most existing pages mix types; Diataxis is the canonical framework (diataxis.fr, adopted by Ubuntu/Canonical, Django, Kubernetes) |
| Quick Start producing a working result in < 5 minutes | Table stakes for every modern dev tool; absence signals the tool is hard to set up | LOW | `quickstart.md` exists but predates v3.0; needs updating |
| Concept page with tool-specific terminology defined before use | "Reweave," "polaris," "WAL," "garden maturity," "session" — users from outside the PKM world need grounding | MEDIUM | `concepts.md` exists; needs v3.0 additions (recall, polaris, contradiction, ingestion) |
| Command reference: option table (flag / default / description) + examples per command | Docker's three-column pattern is the gold standard; users scan this constantly; examples are more important than the table | MEDIUM | `commands.md` exists, source-verified; needs v3.0 command additions |
| Consistent CLI syntax conventions throughout | Google dev style + CLIG + Telerik style guide all converge: `[optional]`, `{required}`, `$` prompts, "The output is similar to the following:" before terminal output | LOW | Convention-only; apply globally across all pages |
| Examples before option tables on every command page | CLIG: "Lead with examples — users gravitate toward them over other documentation forms" | LOW | Commands page starts with glance table; invert: most common invocation first |
| Working copy-pasteable examples | Every example must work against source; not pseudocode; verified against ActionRegistry | LOW | Source-verification discipline established in v2.1; maintain for v3.0 additions |
| Callout admonitions used consistently (Warning / Note / Tip / Danger) | Docker, Stripe, and Obsidian all use visual callouts for critical information; MkDocs admonition extension already enabled | LOW | Extension is enabled; usage is inconsistent; needs standardized taxonomy |
| Cross-linking between related pages | Users land anywhere; they need to find adjacent concepts; Stripe's "fast paths for happy flow" pattern | LOW | Some cross-linking exists; needs systematic coverage |
| "What's next" navigation at end of each page | Guides users through a logical progression; prevents dead-ends | LOW | Currently absent on most pages |
| Troubleshooting that maps errors to diagnosis to fix | Every real tool breaks; users who can't self-diagnose churn | MEDIUM | `troubleshooting.md` exists; verify v3.0 completeness |
| Progressive disclosure: simple usage first, advanced options after | CLIG and Stripe both prioritize happy path before edge cases; don't front-load complexity | MEDIUM | Currently most pages lead with comprehensive tables; restructure to simple → complete |

---

### Differentiators (Competitive Advantage)

Features that set documentation apart from adequate to excellent. These create real quality separation.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Five dedicated v3.0 feature pages (session recall, polaris, contradiction detection, media ingestion, methodology guidance) | Without conceptual grounding, users can't compose these features; they are non-obvious in paradigm and require motivation before mechanics | HIGH | Each page needs: what it is → why it exists → CLI usage → MCP tool surface → agent workflows → examples |
| Three-audience tone model executed consistently | Stripe separates quickstarts (new users) from API ref (experts); ztlctl has user/developer/agent tracks — each track needs a distinct, sustained voice | MEDIUM | Decision already recorded in PROJECT.md; v3.1 applies it consistently: mentor tone for User Guide, peer tone for Developer Guide, structured schema for agents |
| Per-feature MCP tool surface documented alongside CLI surface | ztlctl's MCP tools are the primary interface for agents; every feature page should document both the CLI command and the equivalent MCP tool call | MEDIUM | `agents.md` covers this globally but per-feature MCP coverage is missing in all v3.0 feature pages |
| Glossary page for domain-specific terms | Zettelkasten, polaris, reweave, garden, WAL, session recall, contradiction score — users from outside the PKM world need a reference point | MEDIUM | No glossary exists; build it during feature page writing; each new term links here |
| Error messages as teaching moments in troubleshooting | CLIG: "rewrite expected failures for humans with actionable guidance" — not just what went wrong, but why and what to run instead | MEDIUM | Upgrade troubleshooting.md from symptom lists to diagnostic narratives |
| Methodology guidance section with concrete advice | ztlctl is an opinionated knowledge tool; the "right way to think about notes" is as valuable as command syntax; Obsidian help documents its philosophy | HIGH | `paradigms.md` exists but v3.0 adds prose-as-title convention, garden backlog candidates, title quality checks, polaris alignment — needs dedicated methodology content |
| Documentation-as-code enforcement (CLAUDE.md rule + GSD phase enforcement) | Professional orgs (Stripe) treat docs as part of definition of done; ad-hoc changes accumulate rot; structural enforcement prevents drift | MEDIUM | CLAUDE.md rule needed: no feature phase completes without docs task; GSD phase template to include docs tasks |
| Source-verified examples in CI | Draft.dev: "automate the testing of code examples within your CI/CD pipeline to guarantee they are always up-to-date" | HIGH | v2.1 established manual source-verification; CI automation prevents regression; high value but high cost |

---

### Anti-Features (Commonly Requested, Often Problematic)

Features that seem like improvements but create maintenance debt or harm the reading experience.

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Auto-generated command reference as primary docs | "Always up to date!" | Auto-generated docs have no examples, no rationale, no curation; they become search engine penalties; Draft.dev names this explicitly as an anti-pattern | Use mkdocstrings for API reference only; hand-curate all user-facing command and concept docs |
| Interleaving tutorial content with reference content on the same page | "Less to maintain" | Users in "learning mode" and "looking up a flag" have incompatible reading patterns; mixing both serves neither — Diataxis is definitive; this is the single most common documentation quality failure | Keep tutorial, how-to, reference, and explanation as distinct page types; cross-link between them |
| Fully versioned docs (separate site per release) | "Users on different versions need version-specific docs" | Extreme maintenance burden for a small team; most CLI users upgrade quickly; version sprawl fragments the audience | Version note blocks on changed behavior (e.g., "Added in v3.0"); clear changelog; point to latest |
| Long single-page "everything on one page" design | "Power users want ctrl+F" | Breaks TOC, pagination, and load time; hostile for scan-read patterns | llms-full.txt already serves the "everything on one page" use case for machines; multi-page structure for humans |
| Padded "this page covers…" meta-commentary | "Sets expectations for the reader" | Wastes the user's first sentence; the heading already sets expectations | Start with the answer; context after, not before |
| Exhaustive option tables without examples | "Complete coverage!" | Tables without examples teach what flags exist, not how to use them; users remain confused about actual usage | Every option table must link to or include an example; use progressive disclosure |
| Embedded AI chat widget in the docs site | "Interactive docs!" | Requires external API key, ongoing cost, and MkDocs is a static site — no server side; also redundant with MCP doc search already built | llms.txt + llms-full.txt + MCP `search_docs` covers the AI accessibility use case without a chat widget |

---

## Feature Dependencies

```
Diataxis Content Type Audit
    └──enables──> Consistent progressive disclosure on all pages
    └──enables──> Correct page structure for five new v3.0 feature pages
                      └──requires──> Clear taxonomy: what type is each page?

Three-Audience Tone Model
    └──requires──> Tone guidelines written down and agreed on
    └──enables──> Consistent voice on new v3.0 feature pages

Five New v3.0 Feature Pages
    └──requires──> Diataxis structure pattern established (one reference model page first)
    └──requires──> v3.0 features fully implemented (DONE)
    └──requires──> Source-verified CLI + MCP examples for each feature
    └──enhances──> agents.md, agentic-workflows.md, mcp.md (update cross-references)

Glossary Page
    └──requires──> Feature pages written (terms accumulate during writing)
    └──enhances──> concepts.md, paradigms.md, all feature pages
    └──reduces──> Repetitive inline definitions scattered across pages

"What's Next" Navigation
    └──requires──> Well-defined page ordering (logical learning path established)
    └──enhances──> quickstart → tutorial → concepts → features learning path

Source-Verified Examples (CI)
    └──requires──> v3.0 features fully implemented (DONE)
    └──enhances──> All pages; particularly commands.md and new feature pages

Documentation-as-Code Enforcement
    └──requires──> CLAUDE.md rule written
    └──requires──> GSD phase template updated
    └──prevents──> Future documentation rot
```

### Dependency Notes

- **Diataxis audit is the structural gate.** Before rewriting pages, classify every existing page by content type. Pages mixing tutorial + reference content need to be split or rewritten with a single purpose. This unlocks all other quality improvements.
- **One reference model page before writing the other four.** Session recall should be written first (or whichever is structurally simplest), reviewed, then used as the template pattern for contradiction detection, polaris, media ingestion, and methodology guidance.
- **Source-verification discipline is a gate on accuracy, not structure.** All content changes must verify every example against `src/ztlctl/commands/` and the ActionRegistry before publishing.
- **Glossary is not a blocker but an amplifier.** Build it during feature page writing, not before — terms emerge from the writing process. Link from concepts.md and feature pages as the glossary grows.

---

## MVP Definition

### Launch With (v3.1 documentation overhaul — professional grade)

Minimum set of changes that justify the "professional-grade" claim.

- [ ] Diataxis content type audit — classify every existing page, list mixed-purpose pages for remediation — **foundational gate, unblocks all else**
- [ ] Five new v3.0 feature pages (session recall, polaris, contradiction detection, media ingestion, methodology guidance) — each with: what/why/CLI/MCP/examples structure — **primary coverage gap**
- [ ] Update `concepts.md`, `agentic-workflows.md`, `agents.md`, `mcp.md`, `commands.md` with v3.0 content — **accuracy**
- [ ] Consistent CLI syntax conventions across all pages (brackets, `$` prompts, "similar to the following:" prefix) — **professionalism signal; zero complexity**
- [ ] Callout admonitions applied with a consistent taxonomy (Warning = destructive ops, Note = important context, Tip = best practices) — **scannability**
- [ ] "What's next" links at the end of each page in the User Guide learning path — **retention**
- [ ] Progressive disclosure applied to command pages: simplest useful invocation first, then option table, then advanced examples — **UX**
- [ ] Documentation-as-code CLAUDE.md rule and GSD template update — **prevents future rot**

### Add After Initial Overhaul (v3.1.x)

- [ ] Glossary page — add when feature pages expose enough new terms to justify a standalone reference
- [ ] Methodology guidance deepening — expand `paradigms.md` with specific prose-as-title, garden maturity progression, polaris alignment workflows
- [ ] CI-enforced example validation — add when resources allow; highest protection against regression

### Future Consideration (v4+)

- [ ] Asciinema / terminal recordings — meaningful lift, requires recording infra; defer until core content is excellent
- [ ] Versioned docs — defer until adoption proves version fragmentation is a real support problem
- [ ] i18n — out of scope until adoption requires it

---

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Five new v3.0 feature pages | HIGH | HIGH | P1 |
| Diataxis structural audit + fixes to mixed pages | HIGH | MEDIUM | P1 |
| Update existing pages with v3.0 content | HIGH | MEDIUM | P1 |
| Consistent CLI syntax conventions | HIGH | LOW | P1 |
| Progressive disclosure on command pages | HIGH | LOW | P1 |
| "What's next" page navigation | MEDIUM | LOW | P1 |
| Callout admonition consistency | MEDIUM | LOW | P1 |
| Documentation-as-code enforcement | HIGH | LOW | P1 |
| Per-feature MCP tool surface docs | HIGH | MEDIUM | P2 |
| Glossary page | MEDIUM | MEDIUM | P2 |
| Methodology guidance deepening (paradigms.md) | MEDIUM | MEDIUM | P2 |
| Error messages as teaching moments (troubleshooting.md) | MEDIUM | MEDIUM | P2 |
| CI-enforced example validation | HIGH | HIGH | P3 |
| Asciinema / terminal recordings | LOW | HIGH | P3 |

**Priority key:**
- P1: Required for "professional grade" claim — do in v3.1
- P2: Meaningful quality lift — do when P1 is complete or in parallel if resources allow
- P3: Nice to have — defer

---

## Documentation Patterns from Stripe, Docker, and Obsidian

### Stripe Documentation Patterns (HIGH confidence)

1. **Documentation is part of the definition of done.** Features aren't shipped until documentation is written, reviewed, and published. Documentation contributions count toward performance reviews. This is a cultural decision encoded as process — for ztlctl, the CLAUDE.md enforcement rule and GSD phase template are the equivalent.
2. **Personalization removes friction.** Auto-injecting API keys into examples eliminates copy-paste errors. The ztlctl analog: use realistic, consistent example IDs (`ztl_a1b2c3d4`, `LOG-0042`) throughout all docs, not `<YOUR_ID>` placeholders.
3. **Three-column layout: nav / content / code.** The code column stays visible as users read explanations — they never lose context between prose and example. MkDocs shadcn does not replicate this exactly, but placing code blocks immediately adjacent to their explanatory prose achieves the same effect.
4. **Fast paths for happy flow.** Common use cases appear before edge cases. Error handling, flags, and advanced options are deeper in the page. Implement this on every command page: show the one-line common invocation before the complete flag table.
5. **Explanations are "clear, concise — never too little, never too much."** Stripe's docs are notable for not padding or over-explaining. Every sentence earns its place.

### Docker Documentation Patterns (HIGH confidence — primary source from Docker CLI reference)

1. **Every CLI command page follows the same structure:** Brief description → Detailed description → Options table (flag | default | description) → Examples section → Subcommands table. Predictability reduces cognitive load. Readers know where to find what they need without scanning.
2. **Examples progress from simple to complex.** Don't start with the full flag set — start with the minimal invocation that does the core thing, then build up.
3. **Contextual warnings as callouts.** "Do not use `-t` and `-a stderr` together" appears as a highlighted callout, not buried in prose. Critical gotchas are visually prominent.
4. **Cross-linking subcommands bidirectionally.** Command group pages link to each subcommand; subcommand pages link back to the group. Navigation is bidirectional and consistent.
5. **Environment variables, CLI flags, and config file properties documented in the same section.** All three surfaces (CLI / env / config) for the same setting appear together, grouped by concern. For ztlctl: each configuration option should show the TOML key, the CLI flag equivalent (if any), and the environment variable equivalent.

### Obsidian Help Patterns (MEDIUM confidence — content rendering was limited; patterns inferred from structure)

1. **Concepts are named and defined before they are used.** "Vault," "note," "link" are each defined before being used in how-to pages. For ztlctl: "reweave," "polaris," "WAL," "garden," "session recall," "contradiction score" need the same treatment — define in `concepts.md`, then reference from feature pages.
2. **The tool's philosophy is documented, not just its features.** Obsidian help explains the "why" behind the link-first approach before showing how to create links. `paradigms.md` is the ztlctl analog — it needs to explain why each knowledge paradigm exists and what kind of thinking it enables.
3. **Every feature page answers: what is this, why use it, how to enable it, how to use it.** Not a wall of options — a structured narrative.

### CLIG (Command Line Interface Guidelines — clig.dev) (HIGH confidence)

1. **Lead with examples.** Users look at examples before reading prose. The first code block on any command page should be the simplest useful invocation.
2. **Display frequently-used commands and flags first.** Order by frequency of use, not alphabetically. Git groups "start a working area" before "examine history." In ztlctl: `create note`, `query search`, `session start` are the high-frequency operations and should be prominent.
3. **Include web documentation links in `--help` output.** Bridges terminal ↔ web docs. Users should not have to search for documentation from the terminal.
4. **Error messages are teaching moments.** Rewrite raw errors for humans: what went wrong, why, and what to run instead. This applies to `troubleshooting.md` — each entry should follow: symptom → diagnosis → fix → prevention.
5. **When a command has no required arguments, show concise help automatically.** Don't make users pass `--help` explicitly — running `ztlctl session` with no subcommand should show the session commands, not an error.

### Diataxis Framework (HIGH confidence — canonical source at diataxis.fr)

The single highest-impact structural insight for professional documentation: **four content types serve four different user needs and must be kept separate.**

| Type | User need | Writing approach | ztlctl analog |
|------|-----------|-----------------|---------------|
| **Tutorial** | Learning — take me through it | Hand-holding, step-by-step, guarantee success | `tutorial.md` |
| **How-to guide** | Working — help me accomplish X | Goal-focused, assumes competence, lists steps | New v3.0 feature pages; specific how-to sections |
| **Reference** | Looking up — what are the exact options | Accurate, complete, neutral — no tutorial content | `commands.md`, `configuration.md`, `api-reference.md` |
| **Explanation** | Understanding — why does this work this way | Context, background, rationale | `concepts.md`, `paradigms.md` |

**The single most common documentation quality failure:** mixing tutorial content into reference pages (or vice versa). Reference pages become unscannably long; tutorials lose their narrative structure. Every existing page should be audited against this taxonomy. Pages that mix types should either be split or rewritten with a single purpose.

### Google Developer Style Guide (HIGH confidence — official source)

1. **Optional arguments in brackets, required choices in braces:** `ztlctl create note [--subtype <type>] [--tags <tags>]`
2. **Start multi-line examples with `$` prompt; omit directory paths.** Separate input and output into separate code blocks.
3. **Use "The output is similar to the following:" before terminal output.** This signals the output is example, not literal — important for commands where output varies.
4. **Three dots on a separate line for omitted output.** `...` not `…` (the Unicode ellipsis character).

---

## Sources

- [Stripe API Documentation — apidog.com analysis](https://apidog.com/blog/stripe-docs/)
- [Docker CLI Reference — docs.docker.com](https://docs.docker.com/reference/cli/docker/)
- [Diataxis Documentation Framework — diataxis.fr](https://diataxis.fr/)
- [Command Line Interface Guidelines — clig.dev](https://clig.dev/)
- [Document command-line syntax — Google Developer Style Guide](https://developers.google.com/style/code-syntax)
- [Documenting Command-Line Interfaces — Progress Telerik Style Guide](https://docs.telerik.com/style-guide/document-command-line-tools)
- [Documentation Best Practices for Developer Tools — draft.dev](https://draft.dev/learn/documentation-best-practices-for-developer-tools)
- [12 Documentation Examples Every Dev Tool Can Learn From — draft.dev](https://draft.dev/learn/12-documentation-examples-every-developer-tool-can-learn-from)
- [Building Documentation That Scales — Nerd Level Tech](https://nerdleveltech.com/building-documentation-that-scales-best-practices-for-2025/)
- [Documentation Structure Tips — GitBook](https://gitbook.com/docs/guides/docs-best-practices/documentation-structure-tips)
- [42 Coffee Cups: Technical Documentation Best Practices](https://www.42coffeecups.com/blog/technical-documentation-best-practices)

---

*Feature research for: Professional-grade CLI/MCP developer tool documentation (ztlctl v3.1)*
*Researched: 2026-03-21*
