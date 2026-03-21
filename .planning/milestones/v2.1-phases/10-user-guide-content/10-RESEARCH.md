# Phase 10: User Guide Content - Research

**Researched:** 2026-03-20
**Domain:** Technical documentation writing — content expansion, plugin behavior documentation, agentic workflow walkthroughs
**Confidence:** HIGH (all findings derived from direct source code inspection and existing docs)

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Writing depth and tone:**
- Expand existing terse docs with examples, scenarios, and expected CLI output
- Keep existing content as foundation — enhance, don't rewrite from scratch
- Show expected terminal output for key commands so readers can verify progress
- Explanatory tone: guide the reader through "why" not just "what"
- Each guide should be self-contained — a reader can follow it without reading other guides first

**Paradigm guide (docs/paradigms.md) — UGDE-02:**
- Restructure from current 72-line overview into a comprehensive comparison guide
- Comparison table: second-brain vs knowledge garden approaches (capture style, organization, enrichment, tools)
- "Choose your path" guidance: scenario-based recommendations (e.g., "If you're researching a new technology → second-brain capture-first approach", "If you're tending long-term knowledge → garden enrichment-first approach")
- 2-3 concrete scenarios per paradigm with full command sequences
- Explain how ztlctl supports both paradigms simultaneously (they're not exclusive)

**Built-in plugin guides — UGDE-03:**
- Obsidian (docs/obsidian.md): Enhance existing 71-line doc — add setup walkthrough with screenshots/output, vault structure explanation, garden/ directory usage, community plugin recommendations
- Git plugin: New section or page — setup, what it auto-commits, when it fires (post_action), how to configure, ztlctl.toml `[plugins.git]` example
- Reweave plugin: New section or page — what it does (auto-reweave after create), when it fires, scoring signals, how to tune via config, practical examples of reweave improving connections
- Each plugin guide includes: what it does, how to enable/configure, ztlctl.toml config example, common scenarios

**Agentic workflow recipes — UGDE-04:**
- Full terminal session walkthroughs for all 3 MCP recipe resources:
  1. Research-capture: Agent-driven research session → ingest → note creation → reweave
  2. Review-triage: Agent reviews work queue → prioritizes → processes actionable items
  3. Knowledge-synthesis: Agent analyzes graph → identifies themes → generates synthesis notes
- Each recipe: introduction (what it accomplishes), prerequisites, step-by-step commands with expected output, what to expect after completion
- Include both human-driven and agent-driven variants where applicable

**Session lifecycle guides — UGDE-05:**
- Expand session content (currently in agentic-workflows.md at 192 lines)
- Human-driven session: start → work → log entries → close with enrichment pipeline
- Agent-driven session: MCP tool calls → structured context → automated enrichment
- Include concrete examples: "A 30-minute research session", "An agent-driven literature review"
- Show the enrichment pipeline (reweave + orphan sweep + integrity check) that runs on session close

### Claude's Discretion
- Exact page structure and heading hierarchy within each guide
- Whether Git and Reweave plugin content is new pages or sections within existing pages
- Markdown formatting choices (admonitions, code blocks, tables, etc. within mkdocs-shadcn capabilities)
- Order of scenarios within each guide

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope

</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| UGDE-02 | Second-brain vs knowledge garden paradigm walkthroughs with examples and common scenarios | Current paradigms.md analyzed (72 lines, terse overview); source code command sequences verified; comparison table structure identified |
| UGDE-03 | Built-in plugin guides — Obsidian setup and integration, Git plugin usage, Reweave plugin behavior | All three plugins inspected at source level; exact trigger conditions, config fields, and behavior documented below |
| UGDE-04 | Agentic workflow recipe walkthroughs — research-capture, review-triage, knowledge-synthesis with step-by-step examples | All three `_impl` functions in resources.py read directly; exact step sequences extracted |
| UGDE-05 | Session lifecycle guides for both human-driven and agent-driven usage with concrete examples | session.py `close()` pipeline read; enrichment steps (with config guards) documented verbatim |

</phase_requirements>

---

## Summary

Phase 10 is a pure documentation phase — no code changes, no new features. The work is expanding four existing under-developed docs and adding plugin-specific content that does not yet exist anywhere. All research was done by reading source code directly, so confidence is HIGH throughout.

The biggest content gap is plugins: there is currently **no documentation at all** for the Git plugin or the Reweave plugin. Both are built-in and enabled by default. Users running `ztlctl create note ...` silently get auto-reweave and auto-git-commit behavior with no explanation. This is the primary new content to produce.

The secondary gap is depth: paradigms.md (72 lines) and obsidian.md (71 lines) are correct but terse reference stubs. They need to become walkthrough-style guides with command examples and expected output. agentic-workflows.md (192 lines) is better but still describes features without telling a narrative story about how to use them together.

**Primary recommendation:** Write plugin guides first (Git and Reweave are net-new content), then expand existing docs using tutorial.md's tone as the template — it achieves the right balance of explanation + commands + expected outcome.

---

## What Each Existing Doc Covers vs. What Is Missing

### docs/paradigms.md (72 lines) — Foundation for UGDE-02

**Currently covers:**
- Two-layer model named "Capture and Synthesis" and "Enrichment"
- Short command list for each layer
- A 3-row paradigm mapping table (Zettelkasten / Second-brain / Knowledge-garden)
- 4-step "intended flow" at the end

**Missing for UGDE-02:**
- No comparison table (second-brain vs knowledge-garden as decision frameworks)
- No "choose your path" scenario guidance
- No concrete 2-3 scenario walkthroughs with full command sequences and expected output
- No explanation of how the paradigms are non-exclusive / can coexist
- No anchoring to real user situations ("I want to capture a research paper" → which approach?)

### docs/obsidian.md (71 lines) — Foundation for UGDE-03 (Obsidian portion)

**Currently covers:**
- What the obsidian profile scaffolds (file list)
- Community plugin preset (5 plugins listed)
- Ownership model (core vs. profile vs. human-managed paths)
- 4-step "first open in Obsidian" checklist
- Dashboard export relationship note

**Missing for UGDE-03:**
- No setup walkthrough with expected terminal output
- No explanation of WHY each community plugin matters for the workflow
- No vault structure diagram showing garden/ coexistence with notes/
- No examples of using garden/ for enrichment alongside ztlctl queries
- No guidance on the Dataview or Templater use cases for ztlctl content

### docs/agentic-workflows.md (192 lines) — Foundation for UGDE-04 and UGDE-05

**Currently covers:**
- Capture and synthesis workflow (command block, no narrative)
- Ingestion types (text, file, URL with bundle model)
- Context assembly 5-layer system (table + commands)
- Topic packets (3 modes: learn, review, decision)
- Session close enrichment pipeline (4 steps with config toggles)
- Decision extraction
- MCP server integration (discovery flow, key resources)
- Batch operations
- Scripting with `--json`

**Missing for UGDE-04 (Recipes):**
- The 3 MCP recipe resources (`ztlctl://recipes/*`) are not mentioned at all
- No terminal walkthrough of what a recipe-driven session looks like end-to-end
- No expected output shown

**Missing for UGDE-05 (Session lifecycle):**
- Session commands are scattered across the file, not presented as a narrative lifecycle
- No "human-driven session" walkthrough (start → log → close pattern)
- No "agent-driven session" walkthrough (MCP tool sequence)
- No concrete example scenarios (e.g., "30-minute research session")
- Session close enrichment pipeline exists (lines 111-126) but has no explanation of what each step does

---

## Git Plugin — Exact Behavior (Source: git.py)

**Confidence: HIGH** — read directly from `src/ztlctl/plugins/builtins/git.py`

### What It Does

The Git plugin provides automatic version control for vault operations via the `post_action` hookspec. It stages and commits vault files as knowledge operations happen.

### Two Modes

| Mode | Behavior | Config |
|------|----------|--------|
| **Batch (default)** | Stages files on each operation; commits once at session close | `batch_commits = true` |
| **Immediate** | Stages AND commits after every individual operation | `batch_commits = false` |

### Which Actions Trigger Git Operations

| Action | What happens | Commit message format |
|--------|-------------|----------------------|
| `create_note` | Stage file; commit if immediate mode | `feat: create note {id} — {title}` |
| `create_reference` | Stage file; commit if immediate mode | `feat: create reference {id} — {title}` |
| `create_task` | Stage file; commit if immediate mode | `feat: create task {id} — {title}` |
| `update` | Stage file; commit if immediate mode | `docs: update {id} ({fields_changed})` |
| `close` | Stage file; commit if immediate mode | `docs: close {id} — {summary}` |
| `archive` | Stage file; commit if immediate mode | `docs: close {id} — {summary}` |
| `session_close` | Commit all staged (batch mode) + optional push | `docs: session {id} — N created, N updated` |
| `init` | `git init` + write .gitignore + initial commit | `feat: initialize vault '{name}'` |

### Actions That Are No-ops

`reweave`, `session_start`, `check`, `check_rebuild` — explicitly listed as no-ops in the plugin source.

### Failure Model

All git subprocess calls are wrapped in try/except. A missing `git` binary, a non-repo directory, or a failed `git commit` logs a DEBUG message and continues silently. Vault operations never fail due to git errors.

### Config Fields (`GitConfig` model)

| Field | Default | Meaning |
|-------|---------|---------|
| `enabled` | `true` | Enable/disable the entire plugin |
| `branch` | `"develop"` | Target branch (informational, not enforced by plugin) |
| `auto_push` | `true` | Push to remote on session close |
| `commit_style` | `"conventional"` | Commit message style |
| `batch_commits` | `true` | Batch vs. immediate commit mode |
| `auto_ignore` | `true` | Write .gitignore on vault init |

### ztlctl.toml Configuration Example

```toml
[plugins.git]
enabled = true
batch_commits = true      # commit all changes at session close
auto_push = false         # don't push automatically
auto_ignore = true        # write .gitignore during init
```

### .gitignore Content (Auto-Generated)

```
# ztlctl vault gitignore
.ztlctl/backups/
*.db-journal
```

---

## Reweave Plugin — Exact Behavior (Source: reweave_plugin.py)

**Confidence: HIGH** — read directly from `src/ztlctl/plugins/builtins/reweave_plugin.py`

### What It Does

The Reweave plugin runs the reweave pipeline automatically after notes and references are created, connecting them to existing content via the 4-signal scoring algorithm.

### Trigger Conditions

**Fires when:** `action_name` is `"create_note"` or `"create_reference"`

**Does NOT fire for:** `create_task`, `update`, `close`, `archive`, `session_close`, or any other action.

### Skip Conditions (checked in order)

1. Result indicates failure (`result.ok == False`) — skip
2. `content_id` not present in kwargs — skip
3. `subtype == "decision"` — skip (decision notes have strict lifecycle, must not be auto-mutated)
4. `settings.no_reweave` is True (--no-reweave CLI flag) — skip
5. `settings.reweave.enabled` is False — skip

### What It Does When It Runs

Calls `ReweaveService(vault).reweave(content_id=content_id)` — runs the full 4-signal scoring algorithm on the new item against all existing content, creates edges for items above threshold.

### Config Fields (ReweaveConfig model)

| Field | Default | Meaning |
|-------|---------|---------|
| `enabled` | `true` | Global enable/disable |
| `min_score_threshold` | `0.6` | Minimum score (0.0–1.0) to create a link |
| `max_links_per_note` | `5` | Maximum links added per reweave run |
| `lexical_weight` | `0.35` | BM25 lexical similarity weight |
| `tag_weight` | `0.25` | Jaccard tag overlap weight |
| `graph_weight` | `0.25` | Existing graph proximity weight |
| `topic_weight` | `0.15` | Shared topic directory weight |

### ztlctl.toml Configuration Example

```toml
[reweave]
enabled = true
min_score_threshold = 0.6   # raise to 0.75 for fewer, higher-quality links
max_links_per_note = 5      # raise for denser graphs
lexical_weight = 0.35
tag_weight = 0.25
graph_weight = 0.25
topic_weight = 0.15
```

### Disabling Per-Command

```bash
ztlctl create note "Quick capture" --no-reweave
```

---

## Session Lifecycle — Exact Enrichment Pipeline (Source: session.py)

**Confidence: HIGH** — read directly from `src/ztlctl/services/session.py`

### Session Start

```python
SessionService(vault).start(topic="my topic")
```
- Creates a `LOG-NNNN` node with `type="log"`, `status="open"`
- Only one session can be open at a time — returns error if active session exists
- Dispatches `post_session_start` event (GitPlugin is a no-op for session_start)

### Session Close Pipeline (in exact order)

```
LOG CLOSE → CROSS-SESSION REWEAVE → ORPHAN SWEEP → INTEGRITY CHECK → GRAPH MATERIALIZATION → EVENT DISPATCH
```

**Step 1 — LOG CLOSE:** Updates session node `status="closed"`, inserts a `session_close` log entry. All in one transaction.

**Step 2 — CROSS-SESSION REWEAVE** (guarded by `cfg.close_reweave`):
- Queries all notes/references with `session == session_id` and `archived == 0`
- Runs `ReweaveService.reweave()` on each
- Returns total links created across all notes

**Step 3 — ORPHAN SWEEP** (guarded by `cfg.close_orphan_sweep`):
- Finds ALL notes/references with zero outgoing edges (not just session notes)
- Runs reweave with `min_score_override = settings.session.orphan_reweave_threshold` (default `0.2`)
- Lower threshold means orphans get links they wouldn't normally qualify for

**Step 4 — INTEGRITY CHECK** (guarded by `cfg.close_integrity_check`):
- Runs `CheckService(vault).check()`
- Counts error-severity issues; appends warning if any found
- Does NOT auto-fix — only reports

**Step 5 — GRAPH MATERIALIZATION** (always runs, no guard):
- Calls `GraphService(vault).materialize_metrics()`
- Updates PageRank, degree, and betweenness centrality for all nodes

**Step 6 — EVENT DISPATCH:**
- Fires `post_session_close` event with stats payload
- Drains event bus (sync barrier) before returning

### Session Config Fields (SessionConfig model)

| Field | Default | Meaning |
|-------|---------|---------|
| `close_reweave` | `true` | Run cross-session reweave on close |
| `close_orphan_sweep` | `true` | Attempt to connect orphan notes on close |
| `close_integrity_check` | `true` | Run integrity check on close |
| `orphan_reweave_threshold` | `0.2` | Min score for orphan reweave (lower = more connections) |

### Session Reopen

`session.reopen(session_id)` — reopens a closed session. Errors if no session found or another session is already open.

### Close Result Data

```json
{
  "session_id": "LOG-0001",
  "status": "closed",
  "reweave_count": 7,
  "orphan_count": 2,
  "integrity_issues": 0
}
```

---

## MCP Recipe Resources — Exact Step Sequences (Source: resources.py)

**Confidence: HIGH** — read directly from `src/ztlctl/mcp/resources.py`

### Recipe Discovery

Three recipe URIs exist under the MCP server:
- `ztlctl://recipes` — index of all recipes
- `ztlctl://recipes/research-capture`
- `ztlctl://recipes/review-triage`
- `ztlctl://recipes/knowledge-synthesis`

### Recipe 1: research-capture

**Description:** Capture research findings — search existing content, create synthesis notes, link evidence.

| Step | Action | Params | Condition |
|------|--------|--------|-----------|
| 1 | `search` | `query: {topic}, limit: 10` | Always |
| 2 | `create_note` | `title: {synthesis_title}, maturity: seed` | Skip if step 1 returns note with identical title |
| 3 | `reweave` | `content_id: {step_2.content_id}` | Always |

**Human CLI equivalent:**
```bash
ztlctl query search "oauth security" --limit 10
ztlctl create note "OAuth Security Patterns" --maturity seed
ztlctl reweave --id ztl_<new_id>
```

### Recipe 2: review-triage

**Description:** Triage the work queue — inspect items, update stale notes, archive completed or obsolete ones.

| Step | Action | Params | Condition |
|------|--------|--------|-----------|
| 1 | `work_queue` | (none) | Always |
| 2 | `get_document` | `content_id: {step_1.items[0].id}` | Repeat for each item in work queue |
| 3 | `update` | `content_id: {step_2.id}, changes: {}` | Skip if item needs no changes |
| 4 | `archive` | `content_id: {step_2.id}` | Only if item is complete or stale beyond recovery |

**Human CLI equivalent:**
```bash
ztlctl query work-queue
ztlctl query get TASK-0001
ztlctl update TASK-0001 --maturity budding
ztlctl archive TASK-0001
```

### Recipe 3: knowledge-synthesis

**Description:** Synthesize knowledge from existing content — search, find gaps, draft a synthesis note, reweave connections.

| Step | Action | Params | Condition |
|------|--------|--------|-----------|
| 1 | `search` | `query: {topic}, limit: 20` | Always |
| 2 | `gaps` | `top: 10` | Always |
| 3 | `draft_from_topic` | `topic: {topic}, target: note` | Skip if step 1 already returned a mature synthesis note |
| 4 | `reweave` | `content_id: {step_3.content_id}` | Always |

**Human CLI equivalent:**
```bash
ztlctl query search "distributed systems" --limit 20
ztlctl graph gaps --top 10
ztlctl query draft --topic "distributed-systems" --target note
ztlctl reweave --id ztl_<draft_id>
```

---

## Nav and Infrastructure Impact

### Current Nav (mkdocs.yml)

The nav has 8 User Guide pages:
```
- Tutorial: tutorial.md
- Core Concepts: concepts.md
- Knowledge Paradigms: paradigms.md
- Obsidian Starter Kit: obsidian.md
- Agentic Workflows: agentic-workflows.md
- Command Reference: commands.md
- Configuration: configuration.md
- Troubleshooting: troubleshooting.md
```

### If New Pages Are Added (Git plugin, Reweave plugin)

Two options exist per CONTEXT.md (Claude's discretion):
1. **Sections within existing pages** — Add `## Git Plugin` and `## Reweave Plugin` sections to obsidian.md or agentic-workflows.md. No nav changes needed.
2. **New standalone pages** — e.g., `docs/plugins.md` or `docs/git-plugin.md`. Requires:
   - Adding to `mkdocs.yml` nav
   - Adding to `scripts/gen_llms_full_txt.py` NAV_ORDER constant
   - Adding to `docs/llms.txt`

**Recommendation:** Add a new `docs/plugins.md` page covering all built-in plugins (Git + Reweave) as one cohesive guide, placed between `obsidian.md` and `agentic-workflows.md` in nav. This avoids bloating obsidian.md with unrelated content, keeps session/recipe content in agentic-workflows.md, and groups all plugin behavior in one discoverable location.

### gen_llms_full_txt.py NAV_ORDER

If a new page is added, the `NAV_ORDER` list in `scripts/gen_llms_full_txt.py` must be updated to include it in the same position as mkdocs.yml. The list is a Python constant — it maps section names to file lists.

---

## Architecture Patterns

### Writing Pattern: Tutorial.md as the Gold Standard

`tutorial.md` (264 lines) demonstrates the target pattern:
1. Short sentence explaining what the step accomplishes
2. Code block with exact commands
3. Brief note on what was created and what to expect
4. Options listed as bullets where relevant

Apply this exact structure to all new and expanded content.

### admonitions Available in mkdocs-shadcn

`mkdocs.yml` includes `admonition` markdown extension. This enables:
```markdown
!!! note
    Content here

!!! tip
    Content here

!!! warning
    Content here
```

Use these for:
- "tip" — shortcuts and best practices
- "note" — important caveats (e.g., "Git plugin requires git to be installed")
- "warning" — behavior users might not expect (e.g., "reweave skips decision notes")

### Self-Contained Guide Pattern

Each guide must stand alone per user decision. This means:
- Begin with a 1-paragraph "what this page covers" intro
- Don't assume the reader has read paradigms.md before reading obsidian.md
- Define terms on first use or link to concepts.md
- End with "next steps" linking to related guides

---

## Common Pitfalls to Document

### Pitfall 1: Reweave Silently Skips Decision Notes

**What goes wrong:** User creates a `subtype=decision` note and expects it to get auto-linked. It won't.
**Why it happens:** Decision notes have a strict lifecycle and should not be auto-mutated by async post-create reweave (see reweave_plugin.py line 84-98).
**How to document:** Callout in the Reweave plugin guide explaining the exception.

### Pitfall 2: Git Plugin Requires Git Binary

**What goes wrong:** Vault init runs on a machine without git installed. No error is raised but no git repo is created.
**Why it happens:** All subprocess calls are wrapped in try/except with DEBUG logging only.
**How to document:** Note at the top of the Git plugin guide: "Requires git to be installed and available on PATH."

### Pitfall 3: Batch Mode Means No Commit Until Session Close

**What goes wrong:** User enables git plugin, creates many notes outside a session, and never sees commits. Files are staged but not committed.
**Why it happens:** In batch mode, `session_close` triggers the commit. If no session is active, the staged changes accumulate but never commit.
**How to document:** Explain batch vs. immediate mode explicitly; show what `git status` would look like in each mode.

### Pitfall 4: Session Close Enrichment Is Silent

**What goes wrong:** User closes a session and doesn't realize reweave/orphan-sweep/integrity-check ran.
**Why it happens:** The close result data shows counts (`reweave_count`, `orphan_count`, `integrity_issues`) but these aren't prominently surfaced in the CLI output unless `--json` is used.
**How to document:** Show `--json` output of a session close so users can see what happened.

### Pitfall 5: `--no-reweave` Is Per-Command, Not Persistent

**What goes wrong:** User wants to disable reweave globally and uses `--no-reweave` on one command, not realizing it only applies to that invocation.
**Why it happens:** `--no-reweave` is a CLI flag, not a config toggle. The config toggle is `[reweave] enabled = false` in ztlctl.toml.
**How to document:** Show both options in the Reweave plugin guide.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest |
| Config file | `pyproject.toml` (pytest section) |
| Quick run command | `uv run pytest tests/ -x -q` |
| Full suite command | `uv run pytest` |

### Phase Requirements → Test Map

Documentation phases have no automated unit tests — the "tests" are:

| Req ID | Behavior | Test Type | Automated Command |
|--------|----------|-----------|-------------------|
| UGDE-02 | paradigms.md expanded with comparison table + scenarios | manual | `mkdocs build --strict` (validates markdown) |
| UGDE-03 | Plugin guides accurate to source code behavior | manual | `mkdocs build --strict` |
| UGDE-04 | Recipe walkthroughs match resources.py step sequences | manual | `mkdocs build --strict` |
| UGDE-05 | Session lifecycle matches session.py close pipeline | manual | `mkdocs build --strict` |

**Build validation command:**
```bash
mkdocs build --strict
```
This validates all markdown, nav references, and internal links. It is the gating check for documentation phases.

### Wave 0 Gaps

None for documentation phases — no test files needed. The `mkdocs build --strict` command validates doc structure.

---

## Open Questions

1. **Git plugin guide location — new page vs. section**
   - What we know: CONTEXT.md leaves this to Claude's discretion
   - What's unclear: Whether users expect to find plugin docs under "Obsidian Starter Kit" or a separate "Built-in Plugins" page
   - Recommendation: New `docs/plugins.md` page covering both Git and Reweave, added to nav between obsidian.md and agentic-workflows.md

2. **Session guide location — expand agentic-workflows.md vs. new page**
   - What we know: CONTEXT.md says "expand session content (currently in agentic-workflows.md)" — implies in-place expansion
   - What's unclear: Whether the recipes content (UGDE-04) should be a new page or an expanded section
   - Recommendation: Keep all session/recipe/agentic content in agentic-workflows.md (it will grow from 192 to ~500 lines, which is fine). The page already has the right conceptual scope.

3. **llms.txt update trigger**
   - What we know: llms.txt is hand-authored; llms-full.txt is generated from NAV_ORDER
   - What's unclear: Whether the planner should include updating llms.txt and NAV_ORDER as explicit tasks when a new plugins.md page is added
   - Recommendation: Yes — include as explicit tasks so they don't get missed

---

## Sources

### Primary (HIGH confidence)
- `src/ztlctl/plugins/builtins/git.py` — Git plugin behavior, trigger conditions, config fields, commit message formats
- `src/ztlctl/plugins/builtins/reweave_plugin.py` — Reweave plugin trigger conditions, skip logic, config integration
- `src/ztlctl/services/session.py` — Session lifecycle, close pipeline steps, enrichment config fields
- `src/ztlctl/mcp/resources.py` — Recipe step sequences (research-capture, review-triage, knowledge-synthesis)
- `src/ztlctl/config/models.py` — GitConfig, ReweaveConfig, SessionConfig field defaults and documentation
- `docs/tutorial.md` — Tone and depth reference
- `docs/paradigms.md`, `docs/obsidian.md`, `docs/agentic-workflows.md` — Existing content baseline
- `mkdocs.yml` — Nav structure
- `scripts/gen_llms_full_txt.py` — NAV_ORDER constant, llms-full.txt generation pattern

### Secondary (MEDIUM confidence)
- `docs/concepts.md` — Terminology reference used to understand content type/subtype system
- `.planning/phases/09-navigation-structure/09-CONTEXT.md` — Nav structure decisions, page assignment rationale

---

## Metadata

**Confidence breakdown:**
- Standard stack: N/A (documentation phase — no library selection)
- Architecture: HIGH — direct source code inspection; all plugin, session, and recipe behavior confirmed
- Pitfalls: HIGH — derived from source code logic (not speculation); each pitfall has a specific code path explaining it
- Content gaps: HIGH — line counts and content survey directly measured

**Research date:** 2026-03-20
**Valid until:** Stable until source code changes in git.py, reweave_plugin.py, session.py, or resources.py. These are feature-complete modules with no planned changes in this milestone.
