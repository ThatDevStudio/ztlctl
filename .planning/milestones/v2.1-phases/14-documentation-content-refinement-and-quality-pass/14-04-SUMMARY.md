---
phase: 14-documentation-content-refinement-and-quality-pass
plan: 04
subsystem: docs
tags: [mkdocs, documentation, cli, verification, anti-patterns]

requires:
  - phase: 14-01
    provides: quality bar definition and conventions applied across phase

provides:
  - Source-verified tutorial with 4 anti-pattern callouts and corrected CLI examples
  - Enhanced obsidian guide with 2 real-world scenarios and Common Pitfalls section
  - Source-verified commands reference with all commands, flags, types, and defaults
  - Enhanced plugins reference with verified config, anti-patterns, and cross-links
  - Enhanced agentic-workflows with corrected MCP tool names, CLI session commands, and anti-pattern section

affects:
  - docs/tutorial.md
  - docs/obsidian.md
  - docs/commands.md
  - docs/plugins.md
  - docs/agentic-workflows.md

tech-stack:
  added: []
  patterns:
    - "Anti-pattern callout pattern: !!! warning admonition with title explaining the mistake"
    - "CLI example verification: read ActionDefinition cli_name, cli_multiple, cli_flag before writing any flag"
    - "Session command path: session * not agent session * (cli_group=session in ActionDefinition)"
    - "Reweave CLI: reweave run [--content-id] [--dry-run], not reweave --id or reweave --auto-link-related"
    - "Check CLI: check subcommands (check/fix/rebuild/rollback), not flags on root check command"

key-files:
  created: []
  modified:
    - docs/tutorial.md
    - docs/obsidian.md
    - docs/commands.md
    - docs/plugins.md
    - docs/agentic-workflows.md

key-decisions:
  - "tutorial.md: --tags is cli_multiple=True, so examples must use repeatable --tags flag not comma-separated string"
  - "tutorial.md: ztlctl init takes --path flag not positional PATH argument (source-verified from init_cmd.py)"
  - "tutorial.md: query list --maturity choices are seed/sprout/evergreen from ActionDefinition, not seed/budding/evergreen"
  - "agentic-workflows.md: session commands are ztlctl session * not ztlctl agent session * — cli_group=session in ActionDefinition"
  - "agentic-workflows.md: MCP tool names match action.name in ActionDefinition (start, close, context, log_entry, get — not agent_session_start, get_document)"
  - "plugins.md: reweave manual command corrected to ztlctl reweave run --content-id, not ztlctl reweave --id"
  - "commands.md: session commands fully documented as ztlctl session *, upgrade as subcommands, docs search added"

patterns-established:
  - "Anti-pattern: always include at least 3 anti-pattern callouts in user-facing workflow pages"
  - "Cross-linking: every page links to configuration.md, related guides, and best-practices.md"
  - "Command verification: read ActionDefinition cli_name, cli_multiple, cli_flag; read command source for custom_presentation commands"

requirements-completed: []

duration: 45min
completed: 2026-03-20
---

# Phase 14 Plan 04: Workflow and Reference Pages Quality Pass Summary

**Source-verified CLI examples across tutorial, obsidian, commands, plugins, and agentic-workflows — correcting 15+ inaccurate commands and adding anti-pattern guidance to all five pages.**

## Performance

- **Duration:** ~45 min
- **Started:** 2026-03-20T22:15:00Z
- **Completed:** 2026-03-20T23:00:00Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments

- Corrected all CLI examples in tutorial.md against Click source: `ztlctl init --path`, `ztlctl reweave run`, `ztlctl check fix/rebuild/rollback`, and `--tags` as repeatable flags
- Added 4 anti-pattern admonitions to tutorial.md, 4 to agentic-workflows.md, and 4 to plugins.md
- Fixed all session command paths in agentic-workflows.md (`agent session *` → `session *`) and corrected MCP tool names against ActionDefinition registry
- Expanded commands.md from 153 to 366 lines with verified command groups, flags, types, defaults, and `docs search` command
- Added obsidian.md Common Pitfalls section and two real-world scenario walkthroughs (research vault, team wiki)

## Task Commits

1. **Task 1: Enhance tutorial.md, obsidian.md, and commands.md** - `14110e2` (docs)
2. **Task 2: Enhance plugins.md and agentic-workflows.md** - `629e362` (docs)

## Files Created/Modified

- `docs/tutorial.md` (264 → 281 lines) — verified all CLI examples; corrected init, reweave, check, tags; added 4 anti-pattern callouts; updated Next Steps
- `docs/obsidian.md` (155 → 192 lines) — added 2 real-world scenarios; added Common Pitfalls section (4 entries); strengthened cross-links
- `docs/commands.md` (153 → 366 lines) — full command reference with verified flags, types, defaults; corrected session command paths; added docs search, init subcommands, reweave subcommands, check subcommands, upgrade subcommands
- `docs/plugins.md` (244 → 263 lines) — corrected reweave manual CLI; corrected session close command; added 4-entry anti-patterns section; added cross-links to best-practices.md
- `docs/agentic-workflows.md` (485 → 503 lines) — corrected session CLI commands; corrected MCP tool names against source; corrected reweave run calls; corrected check check; added 4-entry anti-patterns section; added cross-links to best-practices.md and agents.md

## Decisions Made

- `agent session start` → `session start`: confirmed via ActionDefinition `cli_group="session"` — no `agent` wrapper group exists in generator.py
- `ztlctl reweave` → `ztlctl reweave run`: confirmed via ActionDefinition `cli_name="run"` in reweave category
- `ztlctl check --fix` → `ztlctl check fix`: confirmed as separate ActionDefinition with `cli_group="check"` and `cli_name="fix"`
- `--tags "a,b"` → `--tags a --tags b`: confirmed via ActionParam `cli_multiple=True` which generates Click `multiple=True` option
- `ztlctl init PATH` → `ztlctl init --path PATH`: confirmed via init_cmd.py `--path` option (not a positional argument)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Corrected --stdin/--as flags in ingest examples**
- **Found during:** Task 1 (commands.md and tutorial.md verification)
- **Issue:** `ztlctl ingest text "Title" --stdin --as reference` — these flags (`--stdin`, `--as`) do not exist in the ActionDefinition for `ingest_text`. The correct flag is `--target-type`
- **Fix:** Updated all ingest examples to use `--target-type reference` or `--target-type note`
- **Files modified:** docs/tutorial.md, docs/commands.md, docs/agentic-workflows.md
- **Committed in:** 14110e2 (Task 1), 629e362 (Task 2)

**2. [Rule 1 - Bug] Corrected get_document MCP tool name in agentic-workflows.md**
- **Found during:** Task 2 (MCP tool name verification)
- **Issue:** Recipe walkthrough used `get_document(content_id=...)` — the actual action name is `get` (confirmed from ActionDefinition name="get")
- **Fix:** Updated to `get(content_id=...)`
- **Files modified:** docs/agentic-workflows.md
- **Committed in:** 629e362 (Task 2)

---

**Total deviations:** 2 auto-fixed (both Rule 1 bugs — incorrect flag/tool names)
**Impact on plan:** Both fixes necessary for correctness. No scope creep.

## Issues Encountered

None — all source verifications were straightforward once the command structure (generator.py + ActionDefinitions) was understood.

## Next Phase Readiness

- All 5 User Guide workflow and reference pages verified and enhanced
- Phase 14 has 1 remaining plan (14-05)

---
*Phase: 14-documentation-content-refinement-and-quality-pass*
*Completed: 2026-03-20*
