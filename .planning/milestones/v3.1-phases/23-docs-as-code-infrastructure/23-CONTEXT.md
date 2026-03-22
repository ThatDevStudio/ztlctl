# Phase 23: Docs-as-Code Infrastructure - Context

**Gathered:** 2026-03-21
**Status:** Ready for planning

<domain>
## Phase Boundary

CI enforcement of documentation quality (build, prose lint, markdown lint), CLAUDE.md documentation rule with per-change checklist, git-sourced page dates, and two small code debt fixes (IngestService post_action dispatch, stale docstrings). Does NOT include writing new feature pages or restructuring navigation — those are Phases 25 and 24 respectively.

</domain>

<decisions>
## Implementation Decisions

### CI Gate Configuration (DINF-01)
- `doc_lint` job runs in parallel with `validate_pr` in `pr-ci.yml` — not sequential
- Three tools: `mkdocs build --strict` (never with -v), Vale prose lint (Google style, Go binary via errata-ai/vale-action@v2), pymarkdownlnt structure lint (Python-native via uv)
- `fetch-depth: 0` required for git-sourced dates to work in CI
- lychee external link checking is NOT in the PR gate — runs on schedule only (network flakiness)
- Vale `.vale/styles/` directory gitignored; `vale sync` runs at CI start to download style packages

### CLAUDE.md Documentation Rule (DINF-02)
- Trigger: any PR that adds/modifies actions, commands, config options, or MCP resources — "If you changed behavior, update the docs"
- 4-item checklist: (1) relevant docs page updated, (2) llms.txt entry current, (3) CLI examples verified against `--help`, (4) MCP tool count accurate
- Location: new `## Documentation Rules` section after `## Git Workflow` in CLAUDE.md
- Enforcement: advisory in CLAUDE.md (checklist reminder), structural in GSD (phase templates include doc tasks) — dual enforcement

### GSD Template Enforcement (DINF-03)
- Note: GSD templates are external to this repo (~/.claude/get-shit-done/) — this SC may need to be addressed as a documentation note rather than a code change, or deferred
- At minimum, document the expectation that feature phases include documentation tasks

### Git-Sourced Dates (DINF-04)
- mkdocs-git-revision-date-localized plugin — always accurate, zero author discipline
- Requires `fetch-depth: 0` in CI checkout (shared with doc_lint job)

### Claude's Discretion
- pymarkdownlnt rule overrides (especially MD033 for admonition HTML) — tune on first scan
- Vale local dev installation path (brew vs pre-commit) — document whichever works
- Exact wording of CLAUDE.md documentation rule checklist items

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `.github/workflows/pr-ci.yml` — existing CI with `validate_pr` job (single job, sequential steps)
- `.github/workflows/docs.yml` — existing docs workflow (likely for docs deployment)
- `mkdocs.yml` — existing MkDocs configuration
- `pyproject.toml` — uv dependency management, dev group for lint tools

### Established Patterns
- CI uses `actions/checkout@v4` with `fetch-depth: 0` already (for commit lint)
- Dev tools installed via `uv sync --group dev`
- MkDocs build uses `--strict` flag (never with `-v`)
- All linting tools are Python-native where possible (ruff, mypy, pymarkdownlnt)

### Integration Points
- `pr-ci.yml` — add parallel `doc_lint` job alongside existing `validate_pr`
- `CLAUDE.md` — add Documentation Rules section
- `mkdocs.yml` — add mkdocs-git-revision-date-localized plugin config
- `pyproject.toml` — add pymarkdownlnt and mkdocs-git-revision-date-localized to dev deps
- `src/ztlctl/services/ingest.py` — add missing `_dispatch_post_action_event` call
- `src/ztlctl/commands/contradiction.py` — fix stale docstring
- `src/ztlctl/commands/generator.py` — fix stale comment

</code_context>

<specifics>
## Specific Ideas

- STATE.md already documents: "NEVER use `mkdocs build -v --strict`" — confirmed MkDocs bug
- Vale + Google style preset decided during research phase
- pymarkdownlnt chosen over markdownlint-cli2 to keep toolchain Python-native (no Node.js)
- DEBT-09 and DEBT-10 bundled with infra work because both are small fixes that unblock clean CI

</specifics>

<deferred>
## Deferred Ideas

- `scripts/gen_llms_txt.py` auto-generation — explicitly out of scope per REQUIREMENTS.md (page count ~25 doesn't justify)
- External link checking — lychee on schedule only, not per-PR

</deferred>
