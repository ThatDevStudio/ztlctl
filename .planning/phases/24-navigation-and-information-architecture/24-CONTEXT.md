# Phase 24: Navigation and Information Architecture - Context

**Gathered:** 2026-03-21
**Status:** Ready for planning

<domain>
## Phase Boundary

Diataxis audit of all existing docs pages (classify by content type), reorder User Guide nav for beginner-to-advanced progression, confirm placement slots for 5 new v3.0 feature pages, and document quality conventions (CLI syntax, admonitions, cross-referencing) in CLAUDE.md. Does NOT write the new feature pages — that is Phase 25.

</domain>

<decisions>
## Implementation Decisions

### Navigation Reorder (QUAL-01, SC2, SC3)
- User Guide nav order (beginner-to-advanced): install → quickstart → tutorial → concepts → paradigms → commands → config → [session-recall slot] → [polaris slot] → [contradiction-detection slot] → [media-ingestion slot] → [methodology slot] → plugins → obsidian → agentic-workflows → best-practices → troubleshooting
- 5 new v3.0 feature pages slot in after config and before plugins — they are "feature deep-dives" in the learning progression
- Placeholder entries in mkdocs.yml nav using comment markers (e.g., `# session-recall.md — Phase 25`) until files are created in Phase 25
- Developer Guide nav order unchanged (already logical: contributing → plugin authoring → API ref → MCP → agents)

### Diataxis Audit (QUAL-01)
- Create `.planning/phases/24-navigation-and-information-architecture/24-DIATAXIS-AUDIT.md` as a reference artifact (not a published page)
- Classify every existing docs page by Diataxis type: tutorial / how-to / reference / explanation
- Identify mixed-purpose pages and flag for remediation (remediation deferred to Phase 26 if needed)
- Expected classifications:
  - tutorial.md → Tutorial
  - quickstart.md → Tutorial
  - concepts.md → Explanation
  - paradigms.md → Explanation
  - commands.md → Reference
  - configuration.md → Reference
  - api-reference.md → Reference
  - mcp.md → Reference
  - agents.md → Reference
  - plugin-guide.md → How-to
  - plugins.md → Reference
  - obsidian.md → How-to
  - agentic-workflows.md → How-to
  - best-practices.md → How-to / Explanation (mixed?)
  - troubleshooting.md → How-to
  - installation.md → How-to
  - development.md → How-to

### Quality Conventions (QUAL-04)
- Document in CLAUDE.md under `## Documentation Conventions` (new subsection within Documentation Rules area)
- CLI syntax: Google style — `[optional]`, `REQUIRED`, `$` shell prompts, bare `ztlctl` not `$ ztlctl` in examples
- Admonition taxonomy: 3 types only — `!!! warning` (danger/breaking), `!!! note` (context/info), `!!! tip` (recommendations)
- Cross-referencing: every page ends with "What's next" section linking 2-3 related pages
- Sentence-case headings (consistent with Vale Google style)

### Claude's Discretion
- Exact wording of convention documentation in CLAUDE.md
- Whether to add Diataxis type as frontmatter metadata or just document in audit file
- Handling of mixed-purpose pages — flag vs immediate split

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `mkdocs.yml` — current nav structure with User Guide (11 pages) and Developer Guide (5 pages)
- CLAUDE.md — already has `## Documentation Rules` section (added Phase 23)
- Vale + pymarkdownlnt — CI gates enforce quality changes

### Established Patterns
- All docs pages in `docs/` root (not subdirectories except `guide/index.md` and `dev/index.md`)
- Nav entries use explicit titles (e.g., `- Tutorial: tutorial.md`)
- No existing frontmatter on docs pages (MkDocs uses first H1 as title)

### Integration Points
- `mkdocs.yml` nav section — reorder and add placeholder slots
- `CLAUDE.md` — add Documentation Conventions subsection
- `.planning/phases/24-*/24-DIATAXIS-AUDIT.md` — new reference artifact

</code_context>

<specifics>
## Specific Ideas

- The nav order in SC2 is explicit: install → daily capture → search/graph → sessions → strategic alignment → ingestion → extensibility
- New pages go in docs/ root (consistent with all v2.1 pages, per STATE.md decision)
- Five pages: session-recall.md, polaris.md, contradiction-detection.md, media-ingestion.md, methodology.md

</specifics>

<deferred>
## Deferred Ideas

- Writing the actual 5 feature pages — Phase 25
- Remediation of mixed-purpose pages — Phase 26 if flagged
- Updating existing page content for v3.0 — Phase 26

</deferred>
