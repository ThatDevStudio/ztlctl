---
phase: 32-validation-and-hardening
plan: 01
subsystem: plugin
tags: [testing, distribution, plugin, skills, changelog]
dependency_graph:
  requires: []
  provides:
    - test_plugin_structure_extended
    - plugin_changelog
    - plugin_readme_accurate
  affects:
    - plugin/CHANGELOG.md
    - plugin/README.md
    - tests/plugin/test_plugin_structure.py
    - plugin/skills/align/SKILL.md
tech_stack:
  added: []
  patterns:
    - ruamel.yaml for SKILL.md frontmatter parsing in tests
    - Jaccard coefficient for skill description overlap detection
    - Function-call syntax detection (tool_name() not prose) to avoid false positives
key_files:
  created:
    - plugin/CHANGELOG.md
  modified:
    - tests/plugin/test_plugin_structure.py
    - plugin/README.md
    - plugin/skills/align/SKILL.md
decisions:
  - "Write-tool detection uses function-call syntax (tool_name() pattern) not plain word search — avoids false positives from prose mentions like 'the reweave system'"
  - "align skill is read-only per STATE.md decision; removed create_note() call template from body (preserved guidance in prose) rather than adding disable-model-invocation: true"
  - "session-workflow skill references tool names as documentation bullets not invocations — correctly passes side-effect test after function-call detection refinement"
metrics:
  duration: ~6 minutes
  completed: "2026-03-22"
  tasks_completed: 2
  files_modified: 4
---

# Phase 32 Plan 01: Distribution Checklist Validation Summary

Extended the plugin test suite from 11 tests to 58 tests covering all automatable PITFALLS.md distribution checklist items, created the missing CHANGELOG.md, and fixed README component count inaccuracies found by the new tests.

## What Was Built

### Task 1: Extend test suite with distribution checklist validations

Added 10 new test functions to `tests/plugin/test_plugin_structure.py` (total: 58 collected, 57 passing, 1 skipped):

| Test | Pitfall Covered | What it validates |
|------|-----------------|-------------------|
| `test_plugin_json_version_semver` | #3 (Version Bump) | semver format + >= 1.0.0 |
| `test_plugin_changelog_exists` | #3 (Version Bump) | CHANGELOG.md present, contains version |
| `test_skill_line_counts_under_limit` [×13] | #7 (Context Bloat) | all SKILL.md < 500 lines |
| `test_all_skills_have_name_field` [×13] | structural | name: field in frontmatter |
| `test_skill_descriptions_no_overlap` | #6 (Activation Failure) | Jaccard < 0.5 on significant words |
| `test_side_effect_skills_have_disable_model_invocation` [×13] | #20 (Auto-invocation) | write-op tool call templates require flag |
| `test_agent_frontmatter_no_unsupported_fields` [×2] | #19 (Unsupported Fields) | no hooks/mcpServers/permissionMode |
| `test_mcp_json_no_path_traversals` | #12 (Path Traversal) | no ../ in .mcp.json |
| `test_readme_component_counts_accurate` | distribution | README table matches filesystem |
| `test_hook_exit_codes_documented` | #9 (Exit Codes) | exit 0 and exit 2 both present |

Key implementation decision: `test_side_effect_skills_have_disable_model_invocation` uses function-call syntax detection (`tool_name(` pattern) rather than plain word search. This correctly distinguishes:
- `create_note(title="...")` in `align/SKILL.md` — detected as a call template (genuine write op)
- `` `create_note` `` in `session-workflow/SKILL.md` — prose bullet reference, correctly ignored
- `reweave won't modify their content` in `vault-methodology/SKILL.md` — prose explanation, correctly ignored

### Task 2: Fix issues found by the tests

**CHANGELOG.md created** at `plugin/CHANGELOG.md` with v1.0.0 entry documenting all 13 skills, 5 commands, 2 agents, vault gate hook, and MCP stdio transport config.

**README.md fixed** at `plugin/README.md`:
- Intro line: "10 deep skills" → "13 deep skills"
- Component table Skills row: `10` → `13` with all 13 skill names enumerated

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed align/SKILL.md create_note() call template**
- **Found during:** Task 1 — test_side_effect_skills_have_disable_model_invocation flagged align
- **Issue:** `align/SKILL.md` had a `create_note(title="Decision: <title>", ...)` function-call template in step 4. The skill is designated read-only per STATE.md decision "[Phase 29-mvp-skills]: orient and align are read-only skills". A function-call template in the body contradicts this designation and would confuse the side-effect detector.
- **Fix:** Replaced the function-call template with prose guidance: "suggest creating an audit trail note with `subtype="decision"` ... wait for the user to confirm before using any create tool"
- **Files modified:** `plugin/skills/align/SKILL.md`
- **Commit:** `d3c6a7f`

**2. [Rule 1 - Bug] Refined write-tool detection to avoid false positives**
- **Found during:** Task 1 test execution — vault-methodology and session-workflow were incorrectly flagged
- **Issue:** Initial implementation used word-matching (`tool_name in body`) which flagged prose mentions like "reweave won't modify content" and `` `session_close` `` as documentation bullets
- **Fix:** Changed to function-call syntax detection (`tool_name(` regex) — only actual call templates trigger the check; prose references and backtick documentation mentions are correctly ignored
- **Files modified:** `tests/plugin/test_plugin_structure.py`
- **Commit:** `d3c6a7f`

## Skill Description Overlap Analysis

All 13 skill descriptions were reviewed as a set. The Jaccard overlap test at threshold 0.5 passes — no two descriptions share more than 50% of significant words. Closest pairs observed during testing: `review-triage` and `review-contradictions` share "review" domain language but have distinct action verbs and contexts (work queue triage vs. contradiction pair evaluation). No blocking overlap found.

## Known Stubs

None — all tests exercise real plugin filesystem content with no mocked/placeholder data.

## Self-Check: PASSED

- plugin/CHANGELOG.md: FOUND
- plugin/README.md: FOUND
- tests/plugin/test_plugin_structure.py: FOUND
- Commit d3c6a7f: FOUND
- Commit 8ba22e7: FOUND
- 58 tests collected, 57 passing, 1 skipped (mcp integration — correct)
