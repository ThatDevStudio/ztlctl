# Trunk-Based Migration Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Migrate from two-branch (main + develop) to trunk-based development on `develop` with auto-release on version-bumping merges.

**Architecture:** All release automation moves from `main` to `develop`. The `main` branch and stale branches are deleted. Documentation updated to reflect the simplified model.

**Tech Stack:** GitHub Actions, Commitizen, Click (Python CLI), Pydantic config

---

### Task 1: Merge main into develop

**Context:** `main` is at version 1.1.1 with 6 release commits not on `develop` (which is at 1.0.0). Merging brings develop up to the published version state. Conflicts expected in version files.

**Step 1: Fetch latest remote state**

```bash
git fetch origin
```

**Step 2: Merge main into develop**

```bash
git merge origin/main --no-edit
```

Expected: Merge conflicts in `pyproject.toml`, `src/ztlctl/__init__.py`, and/or `CHANGELOG.md`.

**Step 3: Resolve conflicts favoring main's versions**

For each conflicted file, resolve to use main's version numbers (1.1.1 is the published state). For `CHANGELOG.md`, keep both histories — main's release entries plus develop's full history.

```bash
git add <resolved files>
git commit --no-edit
```

**Step 4: Verify the merge**

```bash
uv run python -c "from ztlctl import __version__; print(__version__)"
# Expected: 1.1.1

uv run pytest -x -q
# Expected: all pass

uv run ruff check .
uv run mypy src/
# Expected: clean
```

**Step 5: Push**

```bash
git push origin develop
```

---

### Task 2: Update release.yml for trunk-based auto-release

**Files:**
- Modify: `.github/workflows/release.yml`

**Step 1: Change branch trigger from main to develop**

In `.github/workflows/release.yml`, line 5:

```yaml
# Before:
    branches: [main]

# After:
    branches: [develop]
```

**Step 2: Change push target from main to develop**

Line 52:

```yaml
# Before:
        run: git push origin main --follow-tags

# After:
        run: git push origin develop --follow-tags
```

**Step 3: Change release target from main to develop**

Line 62:

```yaml
# Before:
            --target main

# After:
            --target develop
```

**Step 4: Commit**

```bash
git add .github/workflows/release.yml
git commit -m "ci(release): move release trigger from main to develop"
```

---

### Task 3: Update ci.yml to remove main branch triggers

**Files:**
- Modify: `.github/workflows/ci.yml`

**Step 1: Remove main from push and pull_request triggers**

Lines 5 and 7:

```yaml
# Before:
  push:
    branches: [develop, main]
  pull_request:
    branches: [develop, main]

# After:
  push:
    branches: [develop]
  pull_request:
    branches: [develop]
```

**Step 2: Commit**

```bash
git add .github/workflows/ci.yml
git commit -m "ci: remove main branch from CI triggers"
```

---

### Task 4: Update GitConfig default branch

**Files:**
- Modify: `src/ztlctl/config/models.py:127`

**Step 1: Change the default from "main" to "develop"**

```python
# Before (line 127):
    branch: str = "main"

# After:
    branch: str = "develop"
```

**Step 2: Check for tests that assert the old default**

```bash
grep -r '"main"' tests/ --include='*.py' | grep -i git
grep -r 'branch.*main' tests/ --include='*.py'
```

Update any test assertions that check the default branch value.

**Step 3: Run tests**

```bash
uv run pytest tests/config/ -v
uv run pytest -x -q
```

Expected: all pass.

**Step 4: Commit**

```bash
git add src/ztlctl/config/models.py
git commit -m "fix(config): change default git branch from main to develop"
```

---

### Task 5: Update CLAUDE.md for trunk-based model

**Files:**
- Modify: `CLAUDE.md`

**Changes (6 edits):**

1. **Line 10** — already says `develop`, no change needed.

2. **Lines 47–49 (User role)** — Remove release-to-main responsibilities:

```markdown
# Before:
**User (human):**
- Reviews PRs, approves, and merges (squash-merge)
- Creates PRs from `develop` to `main` when ready to release
- Merges release PRs to `main`

# After:
**User (human):**
- Reviews PRs, approves, and merges (squash-merge)
```

3. **Lines 51–54 (Automation role)** — Update release trigger:

```markdown
# Before:
**Automation (CI/CD):**
- Runs lint, test, typecheck, security, commit-lint on every PR
- On merge to `main`: bumps version, updates changelog, creates tag + GitHub Release
- On GitHub Release: builds and publishes to PyPI

# After:
**Automation (CI/CD):**
- Runs lint, test, typecheck, security, commit-lint on every PR
- On merge to `develop`: if version-bumping commits exist, bumps version, updates changelog, creates tag + GitHub Release
- On GitHub Release: builds and publishes to PyPI (manual approval)
```

4. **Lines 56–64 (Branching Model)** — Replace with trunk-based:

```markdown
# After:
### Branching Model

| Branch | Purpose | Merges to |
|---|---|---|
| `develop` | Trunk — all development and releases | — |
| `feature/<name>` | New features | `develop` |
| `fix/<name>` | Bug fixes | `develop` |
```

5. **Lines 122–140 (Post-Release Sync + Hotfix Workflow)** — Delete both sections entirely. Replace with a note:

```markdown
### Post-Release

After a version-bumping merge, the release workflow pushes a version bump commit directly to `develop`. Pull before starting new work:

\```bash
git checkout develop && git pull origin develop
\```
```

6. **Lines 144–153 (What NOT to Do)** — Update to remove main references:

```markdown
- **Don't commit directly to `develop`** — always use feature/fix branches with PRs
- **Don't use non-conventional commit messages** — pre-commit hook and CI will reject them
- **Don't use non-conventional PR titles** — squash-merge uses the PR title as the commit message
- **Don't manually edit version numbers** — `cz bump` manages `pyproject.toml` and `src/ztlctl/__init__.py`
- **Don't manually edit CHANGELOG.md** — `cz bump --changelog` generates it
- **Don't create git tags manually** — the release workflow creates annotated tags
- **Don't merge PRs** — the user reviews and merges; Claude only creates PRs and addresses feedback
- **Don't use git worktrees** — work directly on feature/fix branches
- **Don't use `uv pip install`** — always use `uv add` (or `uv add --group <group>` for dev deps)
```

7. **Lines 157–161 (CI/CD Pipeline table)** — Update:

```markdown
| Workflow | Trigger | Purpose |
|---|---|---|
| `ci.yml` | PR/push to `develop` | Lint, test, typecheck, security audit, commit lint |
| `release.yml` | Push to `develop` | Auto version bump, changelog, tag, GitHub Release (if version-bumping commits) |
| `publish.yml` | GitHub Release published | Build and publish to PyPI via OIDC (manual approval) |
```

**Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: update CLAUDE.md for trunk-based development model"
```

---

### Task 6: Update CONTRIBUTING.md

**Files:**
- Modify: `CONTRIBUTING.md`

**Changes:**

1. **Lines 64–72 (Branching Model)** — Replace with:

```markdown
## Branching Model

| Branch | Purpose | Merges to |
|--------|---------|-----------|
| `develop` | Trunk — all development and releases | — |
| `feature/<name>` | New features | `develop` |
| `fix/<name>` | Bug fixes | `develop` |

**Important:**
- Never commit directly to `develop`
- Always work on feature/fix branches created from `develop`
- PRs always target `develop`
```

2. **Line 163 (PR Requirements)** — Remove "(unless hotfix)":

```markdown
# Before:
- **Target**: `develop` branch (unless hotfix)

# After:
- **Target**: `develop` branch
```

**Step 2: Commit**

```bash
git add CONTRIBUTING.md
git commit -m "docs: update CONTRIBUTING.md for trunk-based development model"
```

---

### Task 7: Update README.md

**Files:**
- Modify: `README.md`

**Changes:**

Line 117 — Update release description:

```markdown
# Before:
4. Releases are automated when `develop` is merged to `main`

# After:
4. Releases are automated when version-bumping commits (`feat:`, `fix:`) merge to `develop`
```

**Step 2: Commit**

```bash
git add README.md
git commit -m "docs: update README.md for trunk-based release model"
```

---

### Task 8: Update memory files

**Files:**
- Modify: `.claude/projects/-Users-shparki-Documents-Workspace-thatdev-ztlctl/memory/workflow.md`
- Modify: `.claude/projects/-Users-shparki-Documents-Workspace-thatdev-ztlctl/memory/MEMORY.md`

**Changes to workflow.md:**

Replace the full Rules section:

```markdown
## Rules

- **No worktrees** — work directly on feature/fix branches in the main repo
- **Never commit to `develop` directly**
- **Never merge PRs** — user reviews and merges
- **PR titles must use conventional commit format** (squash-merge uses title as commit message)
- **Trunk-based model** — `develop` is the only long-lived branch; no `main` branch
- **Auto-release** — version-bumping merges to develop trigger release pipeline automatically
```

**Changes to MEMORY.md:**

Add under Git Workflow section:

```markdown
- **Trunk-based model** — `develop` is the single trunk; `main` was removed (2026-02-28)
- **Auto-release** — version-bumping commits merged to develop trigger: cz bump → tag → GitHub Release → PyPI (manual approval)
```

---

### Task 9: Delete stale branches (local + remote)

**Step 1: Delete remote stale branches**

```bash
git push origin --delete docs/documentation-upgrade
git push origin --delete fix/sync-version-from-release
git push origin --delete hotfix/fix-wheel-duplicates
git push origin --delete release/v1.1.0
```

Some may already be gone — ignore errors.

**Step 2: Delete local stale branches**

```bash
git branch -D docs/documentation-upgrade 2>/dev/null
git branch -D fix/sync-version-from-release 2>/dev/null
git branch -D hotfix/fix-wheel-duplicates 2>/dev/null
git branch -D release/v1.1.0 2>/dev/null
```

---

### Task 10: Push all changes and delete main

**Step 1: Push develop with all commits**

```bash
git push origin develop
```

**Step 2: Remind user of manual GitHub steps**

Print a checklist for the user:
- [ ] Change GitHub default branch to `develop` (Settings → General → Default branch) — likely already done
- [ ] Delete `main` branch on GitHub (or `git push origin --delete main` after default is changed)
- [ ] Verify branch protection rules apply to `develop`
- [ ] Verify the `pypi` environment protection (manual approval) is still configured

---

### Task 11: Final validation

**Step 1: Run full validation suite**

```bash
uv run ruff check .
uv run ruff format --check .
uv run pytest -x -q
uv run mypy src/
```

All must pass.

**Step 2: Verify no remaining references to old model**

```bash
grep -rn '"main"' .github/workflows/
grep -rn 'hotfix' CLAUDE.md CONTRIBUTING.md README.md
grep -rn 'merge.*main' CLAUDE.md CONTRIBUTING.md README.md
```

Expected: no matches (or only in design doc / historical context).
