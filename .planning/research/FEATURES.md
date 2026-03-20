# Feature Research

**Domain:** Documentation and agent accessibility for CLI/MCP developer tools
**Researched:** 2026-03-20
**Confidence:** HIGH (llms.txt spec verified against llmstxt.org; MCP doc patterns verified against official MCP spec and real implementations)

---

## Context

This research covers the v2.1 milestone: adding two-track documentation (user guide + developer guide) with agent accessibility to an existing Python CLI/MCP tool. The tool already has a GitHub Pages / Just-the-Docs site with 16 existing markdown docs, an MCP server with 59 tools and existing resources, and a plugin system.

Four specific questions are answered below:
1. llms.txt and llms-full.txt conventions — format, content, consumers
2. Multi-audience documentation — user guide vs developer guide patterns
3. In-tool documentation search — what CLI tools do beyond --help
4. MCP-served documentation — how MCP servers expose queryable docs as resources

---

## Question 1: llms.txt and llms-full.txt Conventions

### Specification (HIGH confidence — verified against llmstxt.org)

**llms.txt** is placed at `/llms.txt` at the site root. It is a Markdown file with:

1. **H1 heading** (required): Project or site name only
2. **Blockquote** (optional): Short summary with key context for understanding the project
3. **Content paragraphs** (optional): Additional detail, no headings
4. **H2-delimited sections** (optional): Lists of file URLs with descriptions, each entry as `[name](url): description`
5. **"Optional" section** (optional): Secondary URLs agents can skip if context window is short

The file should be under ~10KB. It functions as a navigation index, not content delivery.

**llms-full.txt** is a companion at `/llms-full.txt`. It is NOT part of the official llmstxt.org spec — it is a community convention where the complete content of all documentation pages is concatenated into a single flat markdown file. Typically 50KB–2MB depending on docs volume.

**Difference:**
- `llms.txt` — lightweight index (links + one-line summaries), consumed when the agent needs to navigate or discover what exists
- `llms-full.txt` — all documentation content concatenated, consumed when the agent needs complete knowledge in a single context load

**Who consumes them:**
- MCP clients (Claude Desktop, Cursor, Windsurf) discovering what docs exist before tool use
- AI assistants fetching documentation for a project when answering user questions
- Coding agents that need to orient to a codebase before taking action
- LLM inference pipelines that process documentation at query time

**Current adoption (2025–2026):** 844K+ sites per BuiltWith tracking. Standard for AI-native and open-source companies. Anthropic, Vercel, Cloudflare, and Stripe all implement it.

**Jekyll/GitHub Pages generation:** Straightforward via Liquid templating. A `llms.txt` file in the Jekyll root with `---` frontmatter and Liquid loops over `site.pages` generates the index automatically. Keep it out of Jekyll's page build with proper frontmatter configuration.

### Infrastructure dependency for ztlctl
- Existing: Just-the-Docs on GitHub Pages (Jekyll-based), 16 MDX doc files with YAML frontmatter
- Generation path: Liquid template at `docs/llms.txt` and `docs/llms-full.txt` with Jekyll loops
- No external dependencies beyond existing Jekyll build pipeline

---

## Question 2: Multi-Audience Documentation Patterns

### Established patterns (HIGH confidence — verified against Stripe, Twilio, AWS, Mintlify implementations)

**The two-track pattern** is the dominant approach for tools with both knowledge-worker users and developer/plugin-author audiences:

**Track 1: User Guide** (knowledge worker audience)
- Goal-oriented structure: what can I do? how do I do X?
- Conceptual guides, tutorials, scenario walkthroughs
- Minimal jargon; business/workflow language
- Navigation labels are nouns or outcome phrases: "Research Workflows", "Session Management", "Getting Started"
- Content: quickstart, tutorial, concepts, paradigms, workflow recipes, session guides, Obsidian integration

**Track 2: Developer Reference** (plugin author / integrator audience)
- Task-oriented structure: how do I build X?
- API-first: hook signatures, event types, contracts, examples
- Technical vocabulary expected
- Navigation labels can be API nouns: "Plugin API", "Hookspecs", "ActionRegistry"
- Content: plugin authoring guide, hook reference, event catalog, contributing guide

**Navigation implementation:**
- Top-level sections in the sidebar signal audience. Example: "User Guide" section and "Developer Reference" section as collapsible groups
- Just-the-Docs supports `nav_order`, `parent`, and `has_children` frontmatter — no plugin needed, just frontmatter organization
- An audience landing page (index.md per section) with brief "if you are a knowledge worker..." / "if you are a plugin author..." routing copy is standard practice

**What does NOT work:**
- Flat docs serving both audiences equally — knowledge workers drown in API detail; developers hunt through tutorial prose
- Single long-form "guide" that blends conceptual and reference — hard to navigate, hard to maintain

### Existing ztlctl gap
The 16 current docs are flat. No audience signal. `development.md`, `mcp.md`, and `commands.md` are developer-flavored; `tutorial.md`, `paradigms.md`, `agentic-workflows.md` are user-flavored. They coexist without separation, making navigation ambiguous for either audience.

---

## Question 3: In-Tool Documentation Search — Beyond --help

### What CLI tools actually do (MEDIUM confidence — pattern survey, not single authoritative source)

Most mature CLI tools use one of three approaches beyond `--help`:

**Approach A: External docs only**
- ripgrep, fd — comprehensive `--help` and man pages, but no in-tool doc search
- Users are expected to use the web docs or `man rg`
- Acceptable for tools with simple, stable surfaces; insufficient for tools with 59+ operations

**Approach B: Rich help text with examples**
- kubectl: `kubectl explain <resource>` exposes structured reference per resource type
- git: `git help <command>` opens the man page in the pager (delegates to system)
- Both extend --help with depth but require knowing what to query

**Approach C: In-tool doc/search subcommand** (rare, but emerging for complex tools)
- Tools with large surfaces or AI-centric use cases are adding `docs` subcommands
- The `ztlctl docs <query>` pattern has no dominant CLI precedent — it's a novel but logical pattern
- Typically implemented as: (1) embed markdown files as package data, (2) implement keyword/BM25 search over the embedded docs, (3) render matched content via Rich pager or stdout

**What makes `ztlctl docs <query>` viable:**
- ztlctl already has BM25 search infrastructure (FTS5 in SQLite)
- Docs are already markdown files that could be embedded as package data resources
- Rich output infrastructure already exists for rendering
- The ActionRegistry already knows all command names — autocomplete integration is achievable

**Complexity:** MEDIUM. The hard part is not the search — it's the ingestion pipeline (embed docs at package build time, keep them current with releases). The simplest viable form: ship docs as package_data in `src/ztlctl/docs/`, search with in-memory string matching or SQLite FTS5 over a bundled docs DB.

---

## Question 4: MCP-Served Documentation as Resources

### Established patterns (HIGH confidence — verified against MCP spec, AWS docs MCP, OpenAI docs MCP, Fern docs)

**The standard MCP documentation pattern has two layers:**

**Layer 1: Resource-based doc delivery**
- Each documentation section is a URI-addressable resource
- Pattern: `ztlctl://docs/<section>` returns the section content as markdown text
- Resources are read-only, static or dynamically generated from the doc files
- MCP clients can `read_resource` on demand without burning tool calls

**Layer 2: Tool-based doc search**
- A `search_docs` or `query_docs` tool accepts a query string and returns matching sections
- AWS, OpenAI, and Context7 all implement this pattern
- The tool returns structured results: list of `{section, url, excerpt, relevance}` objects
- This is the primary entry point for agents that don't know what documentation exists

**Real implementations:**
- AWS Documentation MCP Server: `search_documentation(query)` + `read_documentation(url)` tools
- OpenAI Docs MCP: Read-only search over developers.openai.com and platform.openai.com
- Context7: `resolve-library-id` + `query-docs` — resolves library first, then queries into it
- Mintlify's auto-generated servers: search and page-content tools generated from existing docs

**ztlctl existing MCP infrastructure:**
- 6 existing resources including `ztlctl://agent-reference` (onboarding payload)
- 59 tools via ActionRegistry with `discover_tools` / `describe_tool` pattern
- No documentation-specific resources or search tool yet

**What the v2.1 milestone needs:**
- `ztlctl://docs/index` resource — lists all doc sections with summaries (mirrors llms.txt)
- `search_docs` tool — queries documentation by keyword/topic, returns matching sections
- Individual section resources optionally: `ztlctl://docs/<slug>` for direct section access
- These compose with `discover_tools` for the full agent onboarding sequence: docs overview → relevant section → tool discovery → tool use

---

## Table Stakes (Users Expect These)

Features a documentation site for a CLI/MCP developer tool must have. Missing any = feels incomplete.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| llms.txt at site root | Standard for AI-native tools (Anthropic, Vercel, Stripe all have it); agents and MCP clients expect it | LOW | Jekyll Liquid template; no external dependencies; auto-generates from existing doc pages |
| Two-track navigation (user vs developer) | Flat docs fail both audiences; every serious developer tool (kubectl, Stripe, Twilio) separates concerns | LOW | Just-the-Docs frontmatter reorganization; no new tooling; reuse existing 16 docs |
| User guide section with goal-oriented content | Knowledge workers need guides, not API refs; tutorial and walkthrough content they can follow | MEDIUM | Requires writing new content: session lifecycle guides, workflow recipe walkthroughs, plugin usage guides |
| Developer reference section | Plugin authors need hookspec reference, event catalog, and contributing guide; currently missing | MEDIUM | Requires authoring: plugin authoring guide, API reference, contributing architecture walkthrough |
| `--help` depth on all commands | Users assume every command has comprehensive --help with examples; Click docstrings provide this | LOW | Already largely implemented via Click; verify coverage across all 59 actions |
| Clean public docs (no internal artifacts) | `backlog.md`, `roadmap.md`, `research-mapping.md` are internal planning docs exposed publicly; breaks trust | LOW | Exclude from Jekyll build via `_config.yml` exclude list |
| Audience-segmented landing page | Users need routing copy: "if you're a knowledge worker, start here / if you're a developer, start here" | LOW | Single index.md rewrite; no tooling change |

## Differentiators (Competitive Advantage)

Features that distinguish ztlctl's documentation approach. Not universally expected, but create meaningful value.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| `ztlctl docs <query>` in-tool search | Agents and power users can query docs without leaving the tool or opening a browser; novel for Python CLIs | MEDIUM | Requires: embed docs as package data, BM25 or substring search over embedded files, Rich pager output; existing FTS5 and Rich infrastructure reduces cost |
| llms-full.txt (complete docs in one file) | Agents loading the full ztlctl knowledge base in a single context window; especially useful for agents that are bootstrapping a new vault setup | LOW | Liquid template concatenating all doc pages; trivial to add once llms.txt exists |
| MCP `search_docs` tool + doc resources | Agents can query docs through the same MCP connection they use to operate the vault; eliminates the need to open a browser or separate tool call; completes the onboarding loop (docs → tools → use) | MEDIUM | Requires: `search_docs` tool in ActionRegistry (with custom_presentation=True), `ztlctl://docs/index` resource, doc content embedded or read from filesystem; aligns with existing ActionRegistry pattern |
| Agentic workflow recipes as step-by-step walkthroughs | Agents using ztlctl as their note-taking substrate need executable recipes, not just reference; research-capture, review-triage, knowledge-synthesis already have orchestration resource backing | MEDIUM | Requires authoring walkthrough content linking to MCP tool sequences; docs reference the existing orchestration recipe resources |
| Second-brain vs knowledge garden paradigm walkthroughs | Zettelkasten paradigm is non-obvious; helping users understand which paradigm they're operating in reduces support burden and increases tool adoption | LOW | Primarily content work; `paradigms.md` exists but needs deepening with concrete examples |
| Bidirectional doc-tool linking | Each command reference doc links to the MCP tool equivalent; each MCP tool description links to the doc section — agents and humans can navigate between surfaces | LOW | Frontmatter convention + templates; defines where to look for each surface |

## Anti-Features (Commonly Requested, Often Problematic)

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Separate docs site (Mintlify, GitBook, Docusaurus) | Modern docs tooling with versioning, search, AI chat built-in | Adds infrastructure dependency, breaks existing GitHub Pages workflow, requires content migration, ongoing hosting cost; ztlctl's docs are simple markdown — the overhead is not justified at current scale | Jekyll/Just-the-Docs with llms.txt achieves agent accessibility without platform change |
| Auto-generated CLI reference from Click introspection | Seems like single-source-of-truth for commands | Auto-generated reference is brittle: generated text lacks examples, rationale, and usage context; maintaining generated+human content creates two-phase authoring confusion | Hand-authored command reference with examples; mkdocs-click can generate stubs for completion but should not replace authored content |
| Full docs-as-MCP-resources (every page as a resource) | Agents could read any doc page directly | 16+ static resources pollute the MCP tool catalog, slow initialization, and create maintenance burden; agents don't need to read every page — they need to search and get relevant sections | `search_docs` tool + `ztlctl://docs/index` resource covers the use case with one tool and one resource |
| Versioned documentation | Multiple doc versions for different ztlctl releases | Adds significant maintenance burden; ztlctl is pre-1.0 from a public adoption standpoint; multiple versions confuse small audiences; breaking changes tracked in CHANGELOG.md is sufficient | Single docs site tracking latest; note breaking changes clearly in docs with "Changed in v2.x" callouts |
| AI chat widget embedded in docs site | Interactive docs with LLM answering questions | Requires external AI API key, ongoing cost, and the docs site is static Jekyll on GitHub Pages — no server side; adds complexity without meaningful gain given llms.txt + MCP already provide agent accessibility | llms.txt + llms-full.txt + MCP `search_docs` covers the AI accessibility use case without a chat widget |

---

## Feature Dependencies

```
[llms.txt] ──requires──> [Doc frontmatter cleanup]
                             └── (title, description in all pages)

[llms-full.txt] ──requires──> [llms.txt]
                    └── (shares the same generation pipeline)

[ztlctl docs <query>] ──requires──> [Docs embedded as package data]
                            └── (docs/ content bundled into installed package)

[MCP search_docs tool] ──requires──> [ActionRegistry doc action definition]
                              └── (custom_presentation=True, standard registration)

[MCP search_docs tool] ──enhances──> [ztlctl://docs/index resource]
                              └── (index gives overview; search_docs gives lookup)

[Two-track navigation] ──requires──> [Doc frontmatter reorganization]
                              └── (parent/nav_order frontmatter for section grouping)

[Two-track navigation] ──enables──> [User guide content]
                              └── (section structure must exist before content is added)

[Two-track navigation] ──enables──> [Developer reference content]

[Developer reference] ──requires──> [Plugin API already stable]
                            └── (documenting an unstable API is waste; v2.0 stabilized it)

[Agentic recipe walkthroughs] ──requires──> [Orchestration recipe resources (already exist)]
                                  └── (doc references ztlctl://recipes/research-capture etc.)

[Internal artifact removal] ──no dependencies──> [Can be done independently first]
```

### Dependency Notes

- **llms.txt requires doc frontmatter cleanup:** Every page needs `title` and `description` in frontmatter for the Liquid template to generate meaningful index entries. Several existing pages may be missing `description`.
- **MCP search_docs requires ActionRegistry:** ztlctl's architecture mandates all tools go through ActionRegistry — this is a constraint, not a choice. The doc search action needs a definition with `custom_presentation=True` since its output is unstructured search results.
- **Two-track navigation enables content work:** Content authoring for user guides and developer reference should not start until the navigation structure is in place — otherwise content lands in the wrong place.
- **Developer reference requires stable plugin API:** The plugin API was stabilized in v2.0. This is the correct moment to document it. Documenting before stability = documentation rot.

---

## MVP Definition

This is a subsequent milestone (v2.1), not a greenfield MVP. "Launch with" means what the milestone ships.

### Launch With (v2.1 core)

- [ ] Internal artifacts removed from public docs (backlog.md, research-mapping.md, roadmap.md excluded from Jekyll build) — unblocks everything; zero risk
- [ ] Two-track navigation structure (user guide section + developer reference section) via frontmatter reorganization — structural prerequisite for all content work
- [ ] llms.txt at docs root (Liquid template, auto-generated from existing pages) — standard compliance, LOW complexity, HIGH agent value
- [ ] llms-full.txt at docs root (Liquid template, concatenates all pages) — trivial once llms.txt pipeline exists
- [ ] User guide section content: session lifecycle guides, workflow recipe walkthroughs, plugin usage guides (Obsidian, Git, Reweave) — primary value for knowledge-worker audience
- [ ] Developer reference section content: plugin authoring guide, hookspec/event reference, contributing guide — primary value for plugin author audience
- [ ] MCP `ztlctl://docs/index` resource — list of doc sections with summaries; bridges llms.txt and MCP surfaces; LOW complexity given existing resource infrastructure

### Add After Validation (v2.1.x)

- [ ] `ztlctl docs <query>` in-tool CLI search — when user feedback confirms agents/power users want offline doc search; MEDIUM complexity; depends on docs-as-package-data infrastructure
- [ ] MCP `search_docs` tool — when evidence shows agents are loading llms-full.txt and struggling with context size; search tool solves context window pressure; MEDIUM complexity

### Future Consideration (v2.2+)

- [ ] `search_docs` full-text search with BM25 ranking — when `ztlctl docs <query>` is validated and demand exists for MCP-native doc search with ranking
- [ ] Per-page `.md` extension serving (raw markdown at `page.md`) — low value for GitHub Pages static site; llms-full.txt covers the primary use case

---

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Remove internal artifacts | HIGH (trust/professionalism) | LOW | P1 |
| Two-track navigation reorganization | HIGH (both audiences) | LOW | P1 |
| llms.txt | HIGH (agent/MCP clients) | LOW | P1 |
| llms-full.txt | HIGH (full-context agents) | LOW | P1 |
| User guide content (sessions, recipes, plugins) | HIGH (knowledge workers) | MEDIUM | P1 |
| Developer reference content (plugin API, events, contributing) | HIGH (plugin authors) | MEDIUM | P1 |
| MCP `ztlctl://docs/index` resource | MEDIUM (agent onboarding) | LOW | P2 |
| `ztlctl docs <query>` CLI command | MEDIUM (power users / agents) | MEDIUM | P2 |
| MCP `search_docs` tool | MEDIUM (agents with large vaults) | MEDIUM | P2 |
| Agentic recipe walkthroughs (deepened) | MEDIUM (agents) | LOW | P2 |
| Paradigm walkthroughs (deepened) | LOW (casual users) | LOW | P3 |

**Priority key:**
- P1: Must ship in v2.1 milestone
- P2: Ship in v2.1 if scope permits; defer to v2.1.x otherwise
- P3: Nice to have; future milestone

---

## Sources

- [llmstxt.org specification](https://llmstxt.org/) — authoritative llms.txt format (HIGH confidence)
- [Do You Need Both llms.txt and llms-full.txt?](https://llms-txt.io/blog/llms-txt-and-llms-full-txt) — llms-full.txt convention detail (MEDIUM confidence — community, not spec)
- [MCP Servers for Documentation Sites — Fern](https://buildwithfern.com/post/mcp-servers-documentation-sites) — MCP documentation patterns (MEDIUM confidence)
- [AWS Documentation MCP Server](https://awslabs.github.io/mcp/servers/aws-documentation-mcp-server) — real-world MCP docs implementation (HIGH confidence)
- [How to create an llms.txt in Jekyll and GitHub Pages](https://jtemporal.com/how-to-create-llms-txt-in-jekyll/) — Jekyll generation pattern (MEDIUM confidence)
- [8 Best API Documentation Examples — DreamFactory](https://blog.dreamfactory.com/8-api-documentation-examples) — multi-audience navigation patterns (MEDIUM confidence)
- [MCP Resources specification](https://modelcontextprotocol.io/specification/2025-06-18/server/resources) — official MCP resource spec (HIGH confidence)

---
*Feature research for: ztlctl v2.1 Documentation milestone*
*Researched: 2026-03-20*
