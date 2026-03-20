# Phase 14: Documentation Content Refinement and Quality Pass - Context

**Gathered:** 2026-03-20
**Status:** Ready for planning

<domain>
## Phase Boundary

Apply a comprehensive quality pass across all 18 existing documentation pages and agent artifacts. Enhance in-place to meet the "ThatDev Quality Bar" — sharp, decisive, no fluff. Add new pages where they provide genuine value (best-practices.md, agents.md). Verify every CLI example, hookspec signature, and config option against source code. Fix all known gaps from the milestone audit. No new features or code changes — documentation content only.

</domain>

<decisions>
## Implementation Decisions

### Scope and approach
- Enhance existing 18 pages in-place — no structural reorganization of nav or file locations
- Add new pages when they add genuine value (not for the sake of having more pages)
- Three audiences served: End Users (mentor tone), Developers (peer tone), Agentic Systems (structured/deterministic)
- Existing two-track nav (User Guide + Developer Guide) is preserved

### Quality bar — "ThatDev Quality Bar"
- **Full editorial + source verification**: the highest standard
- Every CLI command and example verified by reading Click command source code
- Every hookspec signature verified against `hookspecs.py`
- Every config option verified against `models.py`
- Consistent heading hierarchy across all pages
- Tone alignment: mentor/teacher for User Guide, senior-to-senior for Developer Guide
- Eliminate hedging language — be decisive and opinionated
- Add cross-links between related pages
- Every page must have at least 2 concrete, real-world examples (not toy examples)
- Outdated content flagged and fixed

### Anti-patterns and best practices — BOTH inline and standalone
- Add anti-pattern and best practice sections inline in relevant pages (paradigms.md, tutorial.md, agentic-workflows.md, etc.)
- Create standalone `docs/best-practices.md` that aggregates all best practices and anti-patterns in one reference destination
- Cross-link from context pages to the consolidated page
- Add to User Guide nav section

### Agent documentation hardening
- Harden existing artifacts: improve llms.txt, llms-full.txt, and mcp.md with stricter structure, explicit schemas, and interaction flow examples
- Create new `docs/agents.md` — dedicated machine-readable system manual for LLM consumers
  - System capabilities as structured data
  - Entity schemas (content types, lifecycle states, relationships)
  - Constraint rules (what's allowed, what's not)
  - Deterministic interaction flows (step-by-step, no ambiguity)
  - Input/output schemas for key operations
- Add agents.md to Developer Guide nav section
- Existing `agentic-workflows.md` stays human-focused (User Guide)

### Decisions & tradeoffs / Evolution path content
- Claude's discretion on whether these become standalone pages or inline sections
- Candidates for inline: "Design Decisions" section in concepts.md, "Growing Your Practice" in paradigms.md
- If standalone pages add enough value, create decisions.md and/or evolution.md

### Known gaps to fix (from milestone audit)
- `docs/guide/index.md` — add missing Built-in Plugins row to the "In This Guide" table (INT-01)
- Document `ZTLCTL_DOCS_PATH` env var requirement for `ztlctl docs search` in user-facing docs
- Note GitHub Pages source setting manual step in troubleshooting or configuration docs (FLOW-01)

### Content guidelines from user's prompt
- Be highly structured: prefer sections, lists, tables over long paragraphs
- Be deeply informative without being verbose
- Strongly opinionated — make decisions and justify them
- Emphasize real-world usability, not theory
- Avoid generic explanations — teach through concrete examples and patterns
- Teach the "why" before the "what"
- No fluff, no filler, no vague statements
- Prefer decisive language over hedging

### llms.txt and llms-full.txt
- Regenerate after content changes (existing gen_llms_full_txt.py script)
- Update llms.txt if new pages are added (best-practices.md, agents.md)
- Update NAV_ORDER in gen_llms_full_txt.py for new pages

### Claude's Discretion
- Exact page structure and heading hierarchy within each enhanced page
- Whether Decisions & Tradeoffs and Evolution Path warrant standalone pages or inline sections
- Order of anti-patterns within best-practices.md
- Depth of agent schema documentation in agents.md
- Whether to add mkdocs admonitions (tips, warnings) for anti-pattern callouts
- Prioritization order of which pages to refine first

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Source code for verification (CRITICAL for this phase)
- `src/ztlctl/commands/` — All Click command definitions (verify CLI examples)
- `src/ztlctl/plugins/hookspecs.py` — All hookspec signatures (verify plugin API docs)
- `src/ztlctl/config/models.py` — All config models (verify configuration docs)
- `src/ztlctl/actions/definitions.py` — ActionDefinition, ActionParam (verify action model docs)
- `src/ztlctl/actions/registry.py` — ActionRegistry (verify architecture docs)
- `src/ztlctl/services/` — All service implementations (verify workflow descriptions)
- `src/ztlctl/mcp/resources.py` — MCP resource implementations (verify MCP docs)
- `src/ztlctl/mcp/tools.py` — MCP tool implementations (verify MCP docs)

### Existing docs to enhance
- `docs/*.md` — All 18 pages (line counts: index 35, quickstart 50, tutorial 264, concepts 91, paradigms 192, obsidian 155, plugins 244, agentic-workflows 485, commands 153, configuration 96, troubleshooting 107, installation 69, development 154, plugin-guide 719, api-reference 69, mcp 105)
- `docs/guide/index.md` — User Guide landing (18 lines, missing Built-in Plugins row)
- `docs/dev/index.md` — Developer Guide landing (12 lines)

### Agent artifacts to harden
- `docs/llms.txt` — 31-line agent discovery file
- `docs/llms-full.txt` — 3039-line concatenated corpus
- `scripts/gen_llms_full_txt.py` — Generation script (NAV_ORDER needs updating for new pages)

### Milestone audit findings
- `.planning/v2.1-MILESTONE-AUDIT.md` — Known gaps: INT-01 (guide/index.md table), FLOW-01 (Pages source setting), doc search env var docs

### Prior phase context (tone and depth precedents)
- `.planning/phases/10-user-guide-content/10-CONTEXT.md` — Writing depth and tone decisions
- `.planning/phases/11-developer-guide-api-reference/11-CONTEXT.md` — Developer docs decisions

### MkDocs configuration
- `mkdocs.yml` — Nav structure, theme, plugins (needs updating for new pages)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- 18 existing docs with substantial content (3018 lines total) — enhance, don't rewrite
- `scripts/gen_llms_full_txt.py` — regeneration script for llms-full.txt
- mkdocs-shadcn theme with admonitions, code blocks, tables — use for structured callouts
- mkdocstrings already configured for API reference generation

### Established Patterns
- Tutorial.md (264 lines) and agentic-workflows.md (485 lines) set the depth precedent
- MkDocs nav is config-driven — new pages added via mkdocs.yml
- llms.txt hand-authored, llms-full.txt script-generated
- `exclude_docs: plans/` already excludes internal artifacts

### Integration Points
- `mkdocs.yml` nav — needs entries for new pages (best-practices.md, agents.md)
- `docs/llms.txt` — needs new page entries
- `scripts/gen_llms_full_txt.py` NAV_ORDER — needs new pages
- `docs/guide/index.md` — needs Built-in Plugins table row fix
- All existing pages — cross-link additions

</code_context>

<specifics>
## Specific Ideas

- User provided a detailed prompt defining the "ThatDev Quality Bar": "Write like a high-performing engineer building a killer product. Prioritize sharp thinking, clarity, and practical usefulness."
- Three audience framework: End Users (mentor tone, teach the "why"), Developers (peer tone, enable builders), Agentic Systems (structured, deterministic, machine-parseable)
- Anti-patterns are first-class content — not afterthoughts. "Common mistakes and what to avoid" with strong opinions
- Agent hardening is explicit: "All agent-facing content MUST be deterministic and unambiguous. Avoid natural language vagueness where structured data is possible."
- User explicitly wants "real workflows, not toy examples" and "start → build → scale your knowledge system" progression
- Evolution path concept: Beginner → Advanced user, Simple plugin → Complex ecosystem, Manual workflows → Agentic automation

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 14-documentation-content-refinement-and-quality-pass*
*Context gathered: 2026-03-20*
