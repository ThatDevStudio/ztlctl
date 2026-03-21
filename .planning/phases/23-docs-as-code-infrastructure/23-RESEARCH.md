# Phase 23: Docs-as-Code Infrastructure - Research

**Researched:** 2026-03-21
**Domain:** CI/CD documentation quality gates, Vale prose linting, pymarkdownlnt, mkdocs-git-revision-date-localized, IngestService post_action dispatch
**Confidence:** HIGH

## Summary

Phase 23 is an infrastructure phase: CI enforcement of documentation quality, authoring rule documentation, git-sourced page dates, and two small code fixes. All technical decisions were locked in CONTEXT.md during the discuss phase — this research validates those decisions against current package versions and surfaces the exact implementation details the planner needs.

The three CI lint tools are all confirmed ready: Vale (via `vale-cli/vale-action@v2.1.1`) requires a `.vale.ini` with `Packages = Google` and a gitignored `StylesPath`, pymarkdownlnt (0.9.36) uses JSON config with `--disable-rules` or config file rule overrides, and mkdocs-git-revision-date-localized-plugin (1.5.1) requires only a plugin stanza addition to `mkdocs.yml` plus `fetch-depth: 0` in the `doc_lint` CI job (already present in `docs.yml`).

The DEBT-09 fix is precisely scoped: `IngestService._ingest_normalized` and `_create_reference_with_bundle` call `create._dispatch_event("post_create", ...)` but never call `self._dispatch_post_action_event("ingest_*", ...)`. The test `test_post_action_dispatch.py` also omits `ingest.py` from its AST scan. Both the service code and the test need updating. The DEBT-10 fix is purely textual: one stale docstring in `ContradictionController.confirm_contradiction` (says "stub — wired in Plan 02") and one stale comment in `commands/generator.py` line 196 (the `# noqa: F401 — triggers _register_core_actions()` comment is accurate but the surrounding import comment may need review).

**Primary recommendation:** Implement in two plans — Plan A: CI infrastructure (doc_lint job, .vale.ini, pymarkdown config, mkdocs plugin, CLAUDE.md rule, DINF-03 note) and Plan B: code debt (DEBT-09 IngestService dispatch + test, DEBT-10 stale strings).

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**CI Gate Configuration (DINF-01)**
- `doc_lint` job runs in parallel with `validate_pr` in `pr-ci.yml` — not sequential
- Three tools: `mkdocs build --strict` (never with -v), Vale prose lint (Google style, Go binary via errata-ai/vale-action@v2), pymarkdownlnt structure lint (Python-native via uv)
- `fetch-depth: 0` required for git-sourced dates to work in CI
- lychee external link checking is NOT in the PR gate — runs on schedule only (network flakiness)
- Vale `.vale/styles/` directory gitignored; `vale sync` runs at CI start to download style packages

**CLAUDE.md Documentation Rule (DINF-02)**
- Trigger: any PR that adds/modifies actions, commands, config options, or MCP resources — "If you changed behavior, update the docs"
- 4-item checklist: (1) relevant docs page updated, (2) llms.txt entry current, (3) CLI examples verified against `--help`, (4) MCP tool count accurate
- Location: new `## Documentation Rules` section after `## Git Workflow` in CLAUDE.md
- Enforcement: advisory in CLAUDE.md (checklist reminder), structural in GSD (phase templates include doc tasks) — dual enforcement

**GSD Template Enforcement (DINF-03)**
- Note: GSD templates are external to this repo (~/.claude/get-shit-done/) — this SC may need to be addressed as a documentation note rather than a code change, or deferred
- At minimum, document the expectation that feature phases include documentation tasks

**Git-Sourced Dates (DINF-04)**
- mkdocs-git-revision-date-localized plugin — always accurate, zero author discipline
- Requires `fetch-depth: 0` in CI checkout (shared with doc_lint job)

### Claude's Discretion
- pymarkdownlnt rule overrides (especially MD033 for admonition HTML) — tune on first scan
- Vale local dev installation path (brew vs pre-commit) — document whichever works
- Exact wording of CLAUDE.md documentation rule checklist items

### Deferred Ideas (OUT OF SCOPE)
- `scripts/gen_llms_txt.py` auto-generation — explicitly out of scope per REQUIREMENTS.md
- External link checking in CI — lychee on schedule only, not per-PR
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| DINF-01 | Doc lint CI gate in pr-ci.yml: `mkdocs build --strict` + Vale prose lint + pymarkdownlnt structure lint | New `doc_lint` job added parallel to `validate_pr`; all three tools confirmed and configured |
| DINF-02 | CLAUDE.md enforceable rule for docs updates with feature changes | New `## Documentation Rules` section with 4-item checklist; location after `## Git Workflow` |
| DINF-03 | GSD workflow templates include documentation tasks structurally | GSD templates are external (~/.claude/get-shit-done/); addressed as documentation note in CLAUDE.md per CONTEXT.md decision |
| DINF-04 | mkdocs-git-revision-date-localized shows "last updated" dates from git history | Plugin 1.5.1, `fetch-depth: 0` already in docs.yml; doc_lint job must also set it |
| DEBT-09 | IngestService calls `_dispatch_post_action_event` for ingest_* actions; `test_post_action_dispatch.py` includes `ingest.py` | Missing call in `_ingest_normalized`; test currently omits ingest.py from AST scan |
| DEBT-10 | Stale docstrings/comments fixed in ContradictionController and commands/generator.py | Line 39 of contradiction.py ("stub — wired in Plan 02"); line 196 of generator.py (`_register_core_actions` comment context) |
</phase_requirements>

---

## Standard Stack

### Core Tools
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pymarkdownlnt | 0.9.36 | Markdown structure linting (MD rules) | Python-native, no Node.js, uv-compatible |
| mkdocs-git-revision-date-localized-plugin | 1.5.1 | Git-sourced "last updated" dates on every page | Zero author discipline, reads git history |
| vale-cli/vale-action | v2.1.1 | Prose lint GitHub Action (active voice, sentence case, etc.) | Go binary, Google style package, CI-native |
| Vale Google style | (via `vale sync`) | Google Developer Documentation Style Guide rules | Active voice, second person, present tense, sentence-case headings |

### Package Name Note
The PyPI package is `mkdocs-git-revision-date-localized-plugin` but the MkDocs plugin name (in `mkdocs.yml`) is `git-revision-date-localized`. Install with the full PyPI name.

**Installation (dev deps):**
```bash
uv add --group dev pymarkdownlnt
uv add --group dev mkdocs-git-revision-date-localized-plugin
```

Vale is a Go binary installed by the GitHub Action — no Python package needed in `pyproject.toml`. For local dev: `brew install vale`.

**Version verification (confirmed 2026-03-21):**
- pymarkdownlnt 0.9.36 released 2026-03-16
- mkdocs-git-revision-date-localized-plugin 1.5.1 released 2026-01-26
- vale-action v2.1.1 released 2024-10-15 (stable)

## Architecture Patterns

### CI Job Structure

The `doc_lint` job runs **in parallel** with `validate_pr` — both triggered on PR to develop. They share no steps; `doc_lint` is entirely self-contained.

```yaml
# .github/workflows/pr-ci.yml — add alongside existing validate_pr job
jobs:
  validate_pr:
    # ... existing job unchanged ...

  doc_lint:
    name: Doc Lint
    runs-on: ubuntu-latest
    permissions:
      contents: read
    steps:
      - name: Check out repository
        uses: actions/checkout@v4
        with:
          fetch-depth: 0          # required for git-revision-date-localized

      - name: Set up uv
        uses: astral-sh/setup-uv@v3
        with:
          enable-cache: true

      - name: Sync dev dependencies
        run: uv sync --group dev

      - name: MkDocs build (strict)
        run: uv run mkdocs build --strict

      - name: Vale sync
        uses: vale-cli/vale-action@v2.1.1
        with:
          vale_flags: "--glob=*.md"
          fail_on_error: true
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}

      - name: pymarkdownlnt
        run: uv run pymarkdown --config .pymarkdown.json scan --recurse docs
```

**Note on action namespace:** errata-ai organization migrated to `vale-cli` on GitHub. Use `vale-cli/vale-action@v2.1.1` (not `errata-ai/vale-action@v2`). Verify the action marketplace listing before writing the workflow.

### Vale Configuration

Vale requires a `.vale.ini` at the repo root and a `StylesPath` directory that is **gitignored** (downloaded at CI start via `vale sync`).

```ini
# .vale.ini
StylesPath = .vale/styles
MinAlertLevel = suggestion
Packages = Google

[*.md]
BasedOnStyles = Vale, Google
```

```
# .gitignore additions:
.vale/styles/
```

Vale sync downloads Google style into `StylesPath` at CI start. The `vale-action` handles the sync step automatically when `Packages` is declared in `.vale.ini`.

### pymarkdownlnt Configuration

pymarkdownlnt uses a JSON config file (conventionally `.pymarkdown.json` at repo root).

```json
{
  "plugins": {
    "md033": {
      "enabled": false
    }
  }
}
```

Run command:
```bash
uv run pymarkdown --config .pymarkdown.json scan --recurse docs
```

Command-line alternative for ad-hoc disable:
```bash
uv run pymarkdown --disable-rules MD033 scan --recurse docs
```

**MD033 override is expected on first scan** due to MkDocs admonition HTML syntax. Tune by running locally and examining what fires, then add overrides to `.pymarkdown.json`. Scan before committing config — start minimal (MD033 only) and add others only if they are false positives for this codebase.

### mkdocs-git-revision-date-localized Plugin

Add to `mkdocs.yml` plugins list:

```yaml
plugins:
  - search
  - git-revision-date-localized:
      type: date
      enable_creation_date: false
      fallback_to_build_date: false
  - redirects:
      redirect_maps: {}
  - mkdocstrings:
      # ... existing config ...
```

The `type: date` renders as "November 28, 2019" format — readable and unambiguous. `fallback_to_build_date: false` ensures stale dates surface as errors rather than silently showing build time. `enable_creation_date: false` unless creation date display is also desired (it is not required by DINF-04).

The `docs.yml` deploy workflow already has `fetch-depth: 0`. The new `doc_lint` job must also have `fetch-depth: 0` (shown in CI pattern above).

**Also update `docs.yml`:** The deploy workflow installs MkDocs dependencies via raw `pip install` with pinned versions. Add `mkdocs-git-revision-date-localized-plugin` to that install command.

### CLAUDE.md Documentation Rules Section

New section placed after `## Git Workflow` and before the next major section:

```markdown
## Documentation Rules

**Rule:** If a PR adds or modifies actions, commands, config options, or MCP resources, the same PR MUST update the relevant docs.

### Docs Update Checklist

Before marking a PR ready for review, verify all that apply:

- [ ] Relevant docs page updated (new feature, changed behavior, new config option)
- [ ] `docs/llms.txt` entry current (new page added, stale description corrected)
- [ ] CLI examples verified against `uv run ztlctl <command> --help` (flag names from source)
- [ ] MCP tool count accurate in `docs/mcp.md` if tools were added or removed

**Where to find things:**
- User-facing docs: `docs/` directory, registered in `mkdocs.yml` nav
- LLM index: `docs/llms.txt` and `docs/llms-full.txt` (hand-maintained)
- Command reference: `docs/commands.md`
- MCP reference: `docs/mcp.md`

**DINF-03 note:** GSD feature phase plans must include a Documentation Tasks block.
Every Phase 25+ plan template includes a "Documentation Tasks" wave that is structural,
not optional.
```

### DEBT-09: IngestService post_action Dispatch

**Current state:** `_ingest_normalized` (and `_create_reference_with_bundle`) call `create._dispatch_event("post_create", ...)` which fires the post_create hook, but no `_dispatch_post_action_event` call fires for the `ingest_*` action itself. Plugin hooks listening on `post_action` for ingest actions receive nothing.

**Fix:** Add `self._dispatch_post_action_event(...)` call at the end of `_ingest_normalized` after the successful path (for both note and reference branches). The call should use the operation name (e.g., `f"ingest_{input_kind}"`) and pass the result payload and warnings.

Pattern from `create.py` (post-transaction call at line ~368):
```python
self._dispatch_post_action_event(
    action_name=f"ingest_{input_kind}",
    payload=payload,
    warnings=list(warnings),
    result=result,
)
return result
```

**Note on `_create_reference_with_bundle`:** This private method is called by `_ingest_normalized` and returns a `ServiceResult`. The dispatch should happen in `_ingest_normalized` after `_create_reference_with_bundle` returns (so it wraps both note and reference paths). Alternatively, add it at the end of `_create_reference_with_bundle` for the reference path, and in `_ingest_normalized` for the note path. Either approach works; the latter keeps symmetry with how `_create_reference_with_bundle` is a complete operation.

**Test fix:** `test_post_action_dispatch.py` must add `"ingest.py"` to the `service_files` list at line 63-70. Two exempt methods need adding to `EXEMPT_METHODS`: `_ingest_normalized` (private helper called by the public methods) and `_create_reference_with_bundle` (private helper). The public methods `ingest_text`, `ingest_file`, `ingest_media`, `ingest_url` do not directly call `transaction()` — they delegate to `_ingest_normalized` — so the AST scan will need to handle this correctly. The simplest fix: add `_ingest_normalized` to `EXEMPT_METHODS` (it's private) and ensure `_create_reference_with_bundle` has the dispatch call (since it does the actual `transaction()` call for references), OR add a second AST check for the private internal method. Check what the AST scan would find before deciding approach.

### DEBT-10: Stale Docstrings and Comments

**File 1:** `src/ztlctl/controllers/contradiction.py`, line 39:
```python
def confirm_contradiction(self, *, note_a: str, note_b: str) -> ServiceResult:
    """Confirm a contradiction between two notes (stub — wired in Plan 02)."""
```
The "(stub — wired in Plan 02)" parenthetical is stale — `confirm_contradiction` is fully implemented in `ContradictionService`. Replace with an accurate description matching the actual behavior.

**File 2:** `src/ztlctl/commands/generator.py`, line 196:
```python
import ztlctl.actions  # noqa: F401 — triggers _register_core_actions()
```
The `_register_core_actions()` function was the old registration mechanism in earlier architecture. With v2.0's ActionRegistry and feature-local registration, this comment is misleading. The import still triggers module-level registration (via `@action_registry.register` decorators in submodules), but the comment should accurately describe what importing `ztlctl.actions` actually does now.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Markdown rule linting | Custom regex checks | pymarkdownlnt | 44 built-in GFM rules, AST-based, configurable |
| Prose style enforcement | Grep for passive voice | Vale + Google style | Hundreds of prose rules, sentence-case, active voice, etc. |
| Git-sourced page dates | Manual frontmatter dates | mkdocs-git-revision-date-localized | Always accurate, reads `git log` for every file |
| CI prose/doc gate | Shell scripts | GitHub Actions jobs | Parallel execution, artifact integration, proper failure reporting |

## Common Pitfalls

### Pitfall 1: `mkdocs build -v --strict` breaks strict mode
**What goes wrong:** Adding the verbose flag `-v` to `mkdocs build --strict` silently suppresses strict-mode errors. The build appears to succeed with warnings that should be failures.
**Why it happens:** Confirmed MkDocs bug documented in STATE.md.
**How to avoid:** ALWAYS use `mkdocs build --strict` without `-v`. Never add `-v`.
**Warning signs:** CI passes on a PR that has broken doc links.

### Pitfall 2: Vale StylesPath committed to git
**What goes wrong:** If `.vale/styles/` is not gitignored, the downloaded Google style package (hundreds of YAML files) gets committed. PRs become noisy and the repo balloons.
**Why it happens:** `vale sync` downloads style packages into `StylesPath`. If `StylesPath` is tracked by git, they get staged.
**How to avoid:** Add `.vale/styles/` to `.gitignore` before running `vale sync` locally. Vale action runs sync at CI start.
**Warning signs:** `git status` shows hundreds of new YAML files under `.vale/styles/`.

### Pitfall 3: Shallow clone strips git dates
**What goes wrong:** If the `doc_lint` job uses `fetch-depth: 1` (default), `mkdocs-git-revision-date-localized` cannot read git history and either errors out or falls back to build date.
**Why it happens:** Default `actions/checkout@v4` does a shallow clone (depth 1) for speed.
**How to avoid:** Set `fetch-depth: 0` in the `doc_lint` job's checkout step. The existing `validate_pr` job already does this — replicate the pattern.
**Warning signs:** All pages show the same "last updated" date (the build date).

### Pitfall 4: pymarkdownlnt MD033 false positives on admonitions
**What goes wrong:** MkDocs admonitions use inline HTML comment-style markers. MD033 (no-inline-html) fires on every admonition block.
**Why it happens:** pymarkdownlnt's MD033 rule flags any raw HTML in Markdown, including the `!!! note` syntax which renders to HTML.
**How to avoid:** Disable MD033 in `.pymarkdown.json`. Run `uv run pymarkdown scan --recurse docs` locally first, collect all rule IDs that fire, and add only legitimate false-positives to the disable list.
**Warning signs:** CI fails with `MD033` on every file that has an admonition.

### Pitfall 5: docs.yml deploy workflow missing new plugin
**What goes wrong:** The deploy workflow (`docs.yml`) installs MkDocs dependencies via a raw `pip install` command with explicit package names/versions. If `mkdocs-git-revision-date-localized-plugin` is not added to that install command, the deploy build fails even though the PR CI build passed (which uses `uv sync --group dev`).
**Why it happens:** `docs.yml` does not use `uv` — it installs packages directly. Any new MkDocs plugin added to `pyproject.toml` dev deps must also be added to the `docs.yml` pip install command.
**How to avoid:** When adding a new plugin to `pyproject.toml`, always update `docs.yml` in the same commit.
**Warning signs:** `docs.yml` deploy job fails with `ModuleNotFoundError` for `mkdocs_git_revision_date_localized`.

### Pitfall 6: vale-action organization name change
**What goes wrong:** Documentation and older examples reference `errata-ai/vale-action@v2`. The errata-ai GitHub organization migrated to `vale-cli`. Using the old org name may work via redirect today but is fragile.
**Why it happens:** GitHub org migration.
**How to avoid:** Use `vale-cli/vale-action@v2.1.1` (confirmed current name from research).

### Pitfall 7: DEBT-09 dispatch in wrong layer
**What goes wrong:** Adding `_dispatch_post_action_event` inside the private `_ingest_normalized` method before the early-return on `dry_run` would fire the event for dry runs.
**Why it happens:** `_ingest_normalized` returns early for `dry_run=True` without creating content. Post-action events must only fire after successful writes.
**How to avoid:** The dispatch call must be placed AFTER the dry-run early-return block, only on the success path.

## Code Examples

### doc_lint Job (CI)
```yaml
# Source: pattern from existing validate_pr job in pr-ci.yml
doc_lint:
  name: Doc Lint
  runs-on: ubuntu-latest
  permissions:
    contents: read
  steps:
    - name: Check out repository
      uses: actions/checkout@v4
      with:
        fetch-depth: 0

    - name: Set up uv
      uses: astral-sh/setup-uv@v3
      with:
        enable-cache: true

    - name: Sync dev dependencies
      run: uv sync --group dev

    - name: MkDocs build (strict)
      id: mkdocs_build
      run: uv run mkdocs build --strict

    - name: Vale prose lint
      id: vale
      uses: vale-cli/vale-action@v2.1.1
      with:
        fail_on_error: true
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}

    - name: pymarkdownlnt
      id: pymarkdown
      run: uv run pymarkdown --config .pymarkdown.json scan --recurse docs
```

### .vale.ini
```ini
# Source: vale.sh/docs + vale-action README
StylesPath = .vale/styles
MinAlertLevel = suggestion
Packages = Google

[*.md]
BasedOnStyles = Vale, Google
```

### .pymarkdown.json (initial — tune after first scan)
```json
{
  "plugins": {
    "md033": {
      "enabled": false
    }
  }
}
```

### mkdocs.yml plugin stanza
```yaml
# Source: timvink.github.io/mkdocs-git-revision-date-localized-plugin/options/
plugins:
  - search
  - git-revision-date-localized:
      type: date
      enable_creation_date: false
      fallback_to_build_date: false
  - redirects:
      redirect_maps: {}
  - mkdocstrings:
      # ... existing config unchanged ...
```

### IngestService post_action dispatch pattern
```python
# Source: existing pattern in src/ztlctl/services/create.py ~line 368
# Add at success path in _ingest_normalized (after dry_run early return)
self._dispatch_post_action_event(
    action_name=f"ingest_{input_kind}",
    payload=payload,
    warnings=list(warnings),
    result=result,
)
return result
```

### test_post_action_dispatch.py addition
```python
# Add "ingest.py" to service_files list
# Add to EXEMPT_METHODS set:
"_ingest_normalized",       # private helper, called by public methods
"_create_reference_with_bundle",  # private helper
"_source_bundle_requested",       # staticmethod, no writes
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| errata-ai/vale-action | vale-cli/vale-action | 2024 org migration | Update action reference |
| Vale StylesPath checked into git | GitIgnored + vale sync at CI | Recommended pattern | Keeps repo clean |
| Manual "last updated" frontmatter | mkdocs-git-revision-date-localized | Plugin available since ~2020, adopted here in v3.1 | Zero maintenance, always accurate |

## Open Questions

1. **vale-action organization name**
   - What we know: Research found that `errata-ai` migrated to `vale-cli`. The vale-action README on GitHub confirms `vale-cli/vale-action@v2.1.1`.
   - What's unclear: Whether `errata-ai/vale-action@v2` still resolves or redirects on GitHub Marketplace.
   - Recommendation: Use `vale-cli/vale-action@v2.1.1` (specific version). Verify against GitHub Marketplace at implementation time.

2. **DINF-03 GSD template enforcement**
   - What we know: GSD templates live in `~/.claude/get-shit-done/` which is external to this repo. Per CONTEXT.md, this is addressed as a documentation note.
   - What's unclear: Whether a Documentation Tasks block convention should be documented in CONTRIBUTING.md, CLAUDE.md, or a separate planning note.
   - Recommendation: Add the expectation to the CLAUDE.md `## Documentation Rules` section. No code change needed. Mark DINF-03 satisfied by the CLAUDE.md addition.

3. **DEBT-09 dispatch placement: `_ingest_normalized` vs `_create_reference_with_bundle`**
   - What we know: The note path and reference path both pass through `_ingest_normalized`. The reference path delegates to `_create_reference_with_bundle`.
   - What's unclear: Whether dispatch should be added once in `_ingest_normalized` (after both branches return) or separately in `_create_reference_with_bundle` (for the reference path) and inline for the note path.
   - Recommendation: Add dispatch in `_ingest_normalized` after each successful branch returns (note branch and reference branch) — this keeps the dispatch co-located with the op name construction (`f"ingest_{input_kind}"`).

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.3 |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` |
| Quick run command | `uv run pytest tests/services/test_post_action_dispatch.py -x` |
| Full suite command | `uv run pytest --cov --cov-report=term-missing` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| DINF-01 | `mkdocs build --strict` passes on docs/ | smoke | `uv run mkdocs build --strict` | N/A (CI gate) |
| DINF-01 | pymarkdownlnt passes on docs/ | smoke | `uv run pymarkdown --config .pymarkdown.json scan --recurse docs` | N/A (CI gate) |
| DINF-04 | Plugin installed and mkdocs.yml updated | smoke | `uv run mkdocs build --strict` | N/A (build test) |
| DEBT-09 | IngestService calls `_dispatch_post_action_event` | structural/AST | `uv run pytest tests/services/test_post_action_dispatch.py -x` | ✅ (needs update) |
| DEBT-10 | Stale strings removed | N/A | Manual inspection | N/A |

### Sampling Rate
- **Per task commit:** `uv run pytest tests/services/test_post_action_dispatch.py -x`
- **Per wave merge:** `uv run pytest --cov --cov-report=term-missing`
- **Phase gate:** Full suite green + `uv run mkdocs build --strict` passes before `/gsd:verify-work`

### Wave 0 Gaps
- None — existing test infrastructure covers all phase requirements. `test_post_action_dispatch.py` exists and needs a targeted update, not creation.

## Sources

### Primary (HIGH confidence)
- PyPI pymarkdownlnt — version 0.9.36 confirmed, released 2026-03-16
- PyPI mkdocs-git-revision-date-localized-plugin — version 1.5.1 confirmed, released 2026-01-26
- timvink.github.io/mkdocs-git-revision-date-localized-plugin/options/ — complete options reference
- pymarkdown.readthedocs.io — CLI reference, config format, rule disable syntax
- github.com/errata-ai/vale-action (now vale-cli) — v2.1.1 current, workflow YAML pattern
- Direct code inspection: `src/ztlctl/services/ingest.py`, `src/ztlctl/controllers/contradiction.py`, `src/ztlctl/commands/generator.py`, `.github/workflows/pr-ci.yml`, `mkdocs.yml`, `pyproject.toml`

### Secondary (MEDIUM confidence)
- WebSearch results for Vale Google style + `.vale.ini` configuration — multiple sources agree on `Packages = Google`, `BasedOnStyles = Vale, Google` pattern
- WebSearch results confirming vale-cli org migration from errata-ai

### Tertiary (LOW confidence)
- None

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — versions confirmed from PyPI and official docs
- Architecture: HIGH — patterns from official docs and direct code inspection of existing project
- Pitfalls: HIGH — most derive from direct code inspection or documented known issues (STATE.md MkDocs -v bug)
- DEBT fixes: HIGH — direct code inspection of ingest.py, contradiction.py, generator.py

**Research date:** 2026-03-21
**Valid until:** 2026-04-21 (pymarkdownlnt and mkdocs-git-revision-date-localized release frequently; vale-action is stable)
