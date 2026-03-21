---
phase: 11-developer-guide-api-reference
plan: "01"
subsystem: infra
tags: [mkdocstrings, mkdocs, docs, ci, griffe, python-handler]

# Dependency graph
requires: []
provides:
  - mkdocstrings[python]>=1.0.3 installed as dev dependency
  - mkdocs.yml plugin block with python handler (paths: [src], allow_inspection: false, google docstring style)
  - CI docs.yml pip install updated to include mkdocstrings
  - mkdocs build verified clean with plugin loaded
affects:
  - 11-02 (API reference nav additions depend on mkdocstrings being wired)
  - 11-03 (api-reference.md ::: directives require mkdocstrings plugin)
  - 11-04 (any further developer guide content that uses autodoc)

# Tech tracking
tech-stack:
  added:
    - mkdocstrings==1.0.3
    - mkdocstrings-python==2.0.3
    - griffelib==2.0.0
    - mkdocs-autorefs==1.4.4
  patterns:
    - "Static AST mode via allow_inspection: false — griffe reads source without importing runtime deps"
    - "paths: [src] forces griffe to locate ztlctl package via filesystem, not sys.path"

key-files:
  created: []
  modified:
    - pyproject.toml
    - uv.lock
    - mkdocs.yml
    - .github/workflows/docs.yml

key-decisions:
  - "allow_inspection: false mandated — CI docs env has no runtime deps (SQLAlchemy, pluggy, etc.) so dynamic import would fail"
  - "paths: [src] mandated — CI uses bare pip install, not uv; griffe must resolve via AST not sys.path"
  - "docstring_style: google chosen to match existing ztlctl docstring conventions"
  - "No show_inheritance_diagram — mkdocs-shadcn has alpha-status mkdocstrings support; mermaid diagrams risk breakage"

patterns-established:
  - "mkdocstrings python handler: always configure paths: [src] + allow_inspection: false for projects with runtime-heavy deps in CI"

requirements-completed: [DVGD-02]

# Metrics
duration: 1min
completed: "2026-03-20"
---

# Phase 11 Plan 01: mkdocstrings Tooling Installation and Wiring Summary

**mkdocstrings[python]>=1.0.3 installed and wired into mkdocs.yml (paths: [src], allow_inspection: false, google docstring style) with CI pip install updated — mkdocs build verified clean**

## Performance

- **Duration:** 1 min
- **Started:** 2026-03-20T19:01:18Z
- **Completed:** 2026-03-20T19:02:18Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- Installed mkdocstrings[python]>=1.0.3 and transitive deps (mkdocstrings-python 2.0.3, griffelib 2.0.0, mkdocs-autorefs 1.4.4) into dev dependency group via `uv add`
- Added mkdocstrings plugin block to mkdocs.yml with python handler configured for static AST mode (allow_inspection: false, paths: [src], google docstring style, source display, member filters excluding private symbols)
- Updated .github/workflows/docs.yml pip install line to include mkdocstrings[python]>=1.0.3
- Confirmed `mkdocs build` completes cleanly in 0.71 seconds with the new plugin loaded

## Task Commits

Each task was committed atomically:

1. **Task 1: Install mkdocstrings dev dependency** - `4ad0005` (build)
2. **Task 2: Wire mkdocstrings plugin into mkdocs.yml and update CI workflow** - `47e918a` (feat)

**Plan metadata:** (docs commit to follow)

## Files Created/Modified
- `pyproject.toml` - Added `mkdocstrings[python]>=1.0.3` to dev dependency group
- `uv.lock` - Updated with resolved mkdocstrings transitive deps
- `mkdocs.yml` - Added mkdocstrings plugin block after redirects entry with full python handler config
- `.github/workflows/docs.yml` - Updated pip install step to include mkdocstrings[python]>=1.0.3

## Decisions Made
- `allow_inspection: false` forces griffe into static AST analysis mode — CI docs environment only installs mkdocs tools (not the full ztlctl runtime), so dynamic import would fail on SQLAlchemy/pluggy/etc.
- `paths: [src]` is mandatory so griffe resolves ztlctl via filesystem path rather than sys.path (CI uses bare pip, not uv project install)
- `docstring_style: google` matches existing codebase docstring conventions
- No `show_inheritance_diagram` — mkdocs-shadcn has alpha-status mkdocstrings support; mermaid diagram rendering is not guaranteed

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- mkdocstrings fully wired and verified — Plan 02 (nav additions) and Plan 03 (api-reference.md with ::: directives) can proceed
- No blockers

---
*Phase: 11-developer-guide-api-reference*
*Completed: 2026-03-20*
