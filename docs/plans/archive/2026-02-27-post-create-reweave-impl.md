# Post-Create Automatic Reweave — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Automatically run reweave after content creation (notes and references) unless `--no-reweave` is passed, surfacing link suggestions inline in the create output.

**Architecture:** Add a REWEAVE stage to `CreateService._create_content()` between EVENT DISPATCH and RESPOND. Gates on `settings.no_reweave` (CLI flag) and content type (notes/references only). Follows the established service-to-service call pattern from `SessionService._cross_session_reweave()`.

**Tech Stack:** Python, SQLAlchemy, pytest, existing ReweaveService

---

## Task 1: Test — `--no-reweave` gate skips reweave

**Files:**
- Modify: `tests/services/test_create.py` (append new test class)

**Step 1: Write the failing test**

Add to the end of `tests/services/test_create.py`:

```python
# ---------------------------------------------------------------------------
# Post-create automatic reweave (T-001)
# ---------------------------------------------------------------------------


class TestPostCreateReweave:
    def test_no_reweave_flag_skips_reweave(self, vault_root: Path) -> None:
        """When no_reweave=True, reweave does not run after create."""
        from unittest.mock import patch

        settings = ZtlSettings.from_cli(vault_root=vault_root, no_reweave=True)
        v = Vault(settings)
        svc = CreateService(v)

        with patch("ztlctl.services.create.ReweaveService") as mock_cls:
            result = svc.create_note("Skip Reweave Note")

        assert result.ok
        mock_cls.assert_not_called()
```

Requires adding these imports at the top of the file (if not already present):

```python
from pathlib import Path
from ztlctl.config.settings import ZtlSettings
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/services/test_create.py::TestPostCreateReweave::test_no_reweave_flag_skips_reweave -v`
Expected: FAIL — `ReweaveService` is not imported in `create.py` yet, or the mock isn't triggered because the code path doesn't exist.

---

## Task 2: Test — task creation skips reweave

**Files:**
- Modify: `tests/services/test_create.py`

**Step 1: Write the failing test**

Add to `TestPostCreateReweave`:

```python
    def test_task_creation_skips_reweave(self, vault: Vault) -> None:
        """Tasks don't participate in the knowledge graph — no reweave."""
        from unittest.mock import patch

        with patch("ztlctl.services.create.ReweaveService") as mock_cls:
            result = vault_create_task(vault)

        assert result.ok
        mock_cls.assert_not_called()
```

Note: this test needs a helper. Use the `CreateService` directly instead:

```python
    def test_task_creation_skips_reweave(self, vault: Vault) -> None:
        """Tasks don't participate in the knowledge graph — no reweave."""
        from unittest.mock import patch

        svc = CreateService(vault)
        with patch("ztlctl.services.create.ReweaveService") as mock_cls:
            result = svc.create_task("Some Task")

        assert result.ok
        mock_cls.assert_not_called()
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/services/test_create.py::TestPostCreateReweave::test_task_creation_skips_reweave -v`
Expected: FAIL — same reason (code path doesn't exist, but once it does, tasks should be filtered out).

---

## Task 3: Test — reweave runs on note creation (happy path)

**Files:**
- Modify: `tests/services/test_create.py`

**Step 1: Write the failing test**

Add to `TestPostCreateReweave`:

```python
    def test_reweave_runs_on_note_creation(self, vault: Vault) -> None:
        """Reweave is called with the new content_id after note creation."""
        from unittest.mock import patch

        mock_result = ServiceResult(
            ok=True, op="reweave", data={"count": 2, "suggestions": []}
        )
        svc = CreateService(vault)

        with patch("ztlctl.services.create.ReweaveService") as mock_cls:
            mock_cls.return_value.reweave.return_value = mock_result
            result = svc.create_note("Reweave Me")

        assert result.ok
        mock_cls.assert_called_once_with(vault)
        mock_cls.return_value.reweave.assert_called_once()
        call_kwargs = mock_cls.return_value.reweave.call_args.kwargs
        assert call_kwargs["content_id"] == result.data["id"]
```

Also add `ServiceResult` to the imports at top if not present:

```python
from ztlctl.services.result import ServiceResult
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/services/test_create.py::TestPostCreateReweave::test_reweave_runs_on_note_creation -v`
Expected: FAIL — `ReweaveService` not called in create pipeline.

---

## Task 4: Test — reweave warning surfaces in create result

**Files:**
- Modify: `tests/services/test_create.py`

**Step 1: Write the failing test**

Add to `TestPostCreateReweave`:

```python
    def test_reweave_count_in_warnings(self, vault: Vault) -> None:
        """When reweave adds links, a warning is included in the result."""
        from unittest.mock import patch

        mock_result = ServiceResult(
            ok=True, op="reweave", data={"count": 3, "suggestions": []}
        )
        svc = CreateService(vault)

        with patch("ztlctl.services.create.ReweaveService") as mock_cls:
            mock_cls.return_value.reweave.return_value = mock_result
            result = svc.create_note("Links Added")

        assert result.ok
        assert any("Auto-reweave: 3 link(s) added" in w for w in result.warnings)
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/services/test_create.py::TestPostCreateReweave::test_reweave_count_in_warnings -v`
Expected: FAIL — no reweave warning in result.

---

## Task 5: Test — reweave failure doesn't break create

**Files:**
- Modify: `tests/services/test_create.py`

**Step 1: Write the failing test**

Add to `TestPostCreateReweave`:

```python
    def test_reweave_failure_still_creates(self, vault: Vault) -> None:
        """If reweave fails, create still succeeds with a warning."""
        from unittest.mock import patch

        from ztlctl.services.result import ServiceError

        mock_result = ServiceResult(
            ok=False,
            op="reweave",
            error=ServiceError(code="NOT_FOUND", message="No candidates"),
        )
        svc = CreateService(vault)

        with patch("ztlctl.services.create.ReweaveService") as mock_cls:
            mock_cls.return_value.reweave.return_value = mock_result
            result = svc.create_note("Reweave Fails")

        assert result.ok  # create still succeeds
        assert any("Auto-reweave skipped" in w for w in result.warnings)
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/services/test_create.py::TestPostCreateReweave::test_reweave_failure_still_creates -v`
Expected: FAIL — no reweave failure handling in create.

---

## Task 6: Implement the REWEAVE stage

**Files:**
- Modify: `src/ztlctl/services/create.py:1` (docstring), `src/ztlctl/services/create.py:291-316` (insert REWEAVE stage)

**Step 1: Update the module docstring**

Change line 1-4 from:
```python
"""CreateService — five-stage content creation pipeline.

Pipeline: VALIDATE → GENERATE → PERSIST → INDEX → RESPOND
(DESIGN.md Section 4)
"""
```

To:
```python
"""CreateService — six-stage content creation pipeline.

Pipeline: VALIDATE → GENERATE → PERSIST → INDEX → REWEAVE → RESPOND
(DESIGN.md Section 4)
"""
```

**Step 2: Update `_create_content` docstring**

Change line 158 from:
```python
        """Shared pipeline: VALIDATE → GENERATE → PERSIST → INDEX → RESPOND."""
```

To:
```python
        """Shared pipeline: VALIDATE → GENERATE → PERSIST → INDEX → REWEAVE → RESPOND."""
```

**Step 3: Insert the REWEAVE stage**

After the EVENT block (after line 303), insert before the RESPOND block:

```python
        # ── REWEAVE ──────────────────────────────────────────────
        if (
            not self._vault.settings.no_reweave
            and content_type in ("note", "reference")
        ):
            with trace_span("post_create_reweave"):
                from ztlctl.services.reweave import ReweaveService

                rw = ReweaveService(self._vault).reweave(content_id=content_id)
                if rw.ok:
                    count = rw.data.get("count", 0)
                    if count > 0:
                        warnings.append(f"Auto-reweave: {count} link(s) added")
                else:
                    msg = rw.error.message if rw.error else "unknown"
                    warnings.append(f"Auto-reweave skipped: {msg}")

```

**Step 4: Run all tests to verify they pass**

Run: `uv run pytest tests/services/test_create.py -v`
Expected: ALL PASS (including the 5 new tests from Tasks 1-5)

**Step 5: Commit**

```bash
git add src/ztlctl/services/create.py tests/services/test_create.py
git commit -m "feat(create): add post-create automatic reweave stage (T-001)

Adds a REWEAVE stage to the content creation pipeline that runs
after INDEX and before RESPOND. Gates on --no-reweave CLI flag
and content type (notes/references only, tasks skipped).

Reweave results surface as warnings in the ServiceResult, visible
inline in the create output."
```

---

## Task 7: Full validation

**Step 1: Run the full test suite**

Run: `uv run pytest`
Expected: ALL PASS

**Step 2: Run linting and type checking**

Run: `uv run ruff check . && uv run ruff format --check . && uv run mypy src/`
Expected: No errors

**Step 3: Fix any issues and commit fixes**

If any linting/typing issues, fix and commit separately:
```bash
git commit -m "style: fix lint/type issues from post-create reweave"
```
