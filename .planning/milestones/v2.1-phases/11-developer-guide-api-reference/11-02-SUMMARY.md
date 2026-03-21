---
phase: 11-developer-guide-api-reference
plan: "02"
subsystem: documentation
tags: [pluggy, plugin-system, hookspecs, NoteTypeDefinition, ActionRejection, PluginMetadata]

requires:
  - phase: 06-extension-plugins-event-bus-mcp
    provides: "pluggy hookspecs, contracts, _version.py, git plugin, reweave plugin, NoteTypeDefinition"
  - phase: 11-developer-guide-api-reference
    provides: "RESEARCH.md and CONTEXT.md with source analysis of plugin system"
provides:
  - "docs/plugin-guide.md: 719-line plugin authoring guide with tutorial + hookspec reference"
  - "8-step tutorial from package creation to entry-point registration and testing"
  - "Complete MyVaultPlugin example with post_action, declare_capabilities, register_note_types, config"
  - "All 16 hookspec signatures from hookspecs.py source of truth"
  - "Deprecated hook migration table with exact parameter signatures"
affects:
  - phase-12
  - phase-13

tech-stack:
  added: []
  patterns:
    - "Plugin tutorial follows real source pattern (git.py hookimpl = pluggy.HookimplMarker('ztlctl'))"
    - "Hookspec reference matches hookspecs.py signatures exactly — read source before writing"
    - "Contribution contract types documented as dataclass signatures for copy-paste correctness"

key-files:
  created:
    - docs/plugin-guide.md
  modified: []

key-decisions:
  - "All 16 hookspecs documented (2 generic action + 2 lifecycle + 11 extension + 1 security) with exact signatures"
  - "Deprecated hook table includes parameter names from hookspecs.py source (not guessed)"
  - "PluginMetadata.capabilities vs declare_capabilities distinction explicitly noted in metadata section"
  - "Compatibility window documented from _version.py: PLUGIN_API_VERSION=1, window=2"

patterns-established:
  - "Plugin guide structure: tutorial first, hookspec reference second — enables both learning and reference modes"
  - "Code examples use exact signatures from source — no paraphrasing of method parameters"

requirements-completed:
  - DVGD-01

duration: 2min
completed: "2026-03-20"
---

# Phase 11 Plan 02: Plugin Authoring Guide Summary

**Single-file plugin guide (719 lines) covering 8-step tutorial + all 16 hookspec signatures from source, enabling plugin authors to go from zero to a working plugin without reading source code.**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-20T19:01:28Z
- **Completed:** 2026-03-20T19:03:30Z
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments

- Created `docs/plugin-guide.md` with tutorial (sections 1-8) and complete working `MyVaultPlugin` example
- Documented all 16 hookspecs with exact signatures from `hookspecs.py` source of truth
- Built deprecated hook migration table with correct parameter names from source (not guessed)
- Documented all contribution contract dataclasses (`CliCommandContribution`, `McpToolContribution`, `VaultInitStepContribution`, etc.) with field types
- Included `NoteTypeDefinition` field table with all 9 fields and types from `domain/registry.py`
- Compatibility window rules from `_version.py` documented with worked example table

## Task Commits

Each task was committed atomically:

1. **Task 1: Create docs/plugin-guide.md with tutorial and hookspec reference** - `e74ad3e` (docs)

## Files Created/Modified

- `docs/plugin-guide.md` - Complete plugin authoring guide: 8-step tutorial, full MyVaultPlugin example, all 16 hookspecs, deprecated hook migration, PluginMetadata, and compatibility rules

## Decisions Made

- Documented `PluginMetadata.capabilities` vs `declare_capabilities()` distinction explicitly — both called "capabilities" but serve different purposes (feature surface vs security declaration)
- Added worked example table in the Compatibility section to make the abstract version rules concrete
- Used `action_name` filter patterns from real GitPlugin and ReweavePlugin source as tutorial guidance

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- `docs/plugin-guide.md` ready for MkDocs navigation inclusion in Phase 12 or 13
- All hookspec signatures are from source — accurate as of PLUGIN_API_VERSION = 1
- Guide references `src/ztlctl/plugins/hookspecs.py` as authoritative — link remains valid

---
*Phase: 11-developer-guide-api-reference*
*Completed: 2026-03-20*
