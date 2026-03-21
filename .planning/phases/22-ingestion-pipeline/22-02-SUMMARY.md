---
phase: 22-ingestion-pipeline
plan: "02"
subsystem: ingestion
tags: [ingest, media, transcription, action-registry, two-phase-workflow]
dependency_graph:
  requires: ["22-01"]
  provides: ["ingest_media service method", "ingest_media ActionDefinition", "media CLI/MCP surface"]
  affects: ["services/ingest.py", "controllers/ingest.py", "actions/_ingest.py", "services/contracts.py"]
tech_stack:
  added: []
  patterns: ["TranscriptionService composition in service method", "source_bundle extra-field injection post-normalization"]
key_files:
  created:
    - tests/services/test_ingest_media.py
  modified:
    - src/ztlctl/services/ingest.py
    - src/ztlctl/controllers/ingest.py
    - src/ztlctl/actions/_ingest.py
    - src/ztlctl/services/contracts.py
decisions:
  - "source_path stored at top level of bundle JSON via extra-field injection post-normalization (not in Pydantic-validated fields)"
  - "SourceBundleData.input_kind Literal extended to include 'media' (required for validation)"
  - "ingest_media always targets reference type — enforces two-phase captured → annotated workflow"
metrics:
  duration_minutes: 4
  completed_date: "2026-03-21"
  tasks_completed: 2
  files_modified: 4
---

# Phase 22 Plan 02: Media Ingestion Wiring Summary

**One-liner:** `ingest_media` action wired end-to-end: file path in, TranscriptionService transcribes, captured reference with source bundle out, registered in ActionRegistry for auto-CLI/MCP generation.

## Tasks Completed

### Task 1: IngestService.ingest_media and IngestController wiring

**Commits:**
- `61296d2` — test(22-02): add failing tests for ingest_media end-to-end pipeline (TDD RED)
- `d80f1f9` — feat(22-02): implement IngestService.ingest_media and IngestController wiring (TDD GREEN)

**What was built:**
- `IngestService.ingest_media(path, ...)` method with `@traced` decorator
  - Validates path existence (NOT_FOUND) and extension via `TranscriptionService.SUPPORTED_EXTENSIONS` (UNSUPPORTED_INPUT)
  - Creates `TranscriptionService` from `vault.settings.ingest.media` config values
  - Calls `transcribe_file(path)` — propagates `ServiceError` on failure
  - Delegates to `_ingest_normalized` with `input_kind="media"`, `target_type="reference"`, transcription-derived `modalities`, `capture_agent`, and `source_path` via `source_bundle` dict
  - Injects `source_path` into normalized bundle dict post-Pydantic-validation (extra-fields pass in `_create_reference_with_bundle`)
- `IngestController.ingest_media(path: Path | str, ...)` delegating through `_run_action`
- 12 tests in `tests/services/test_ingest_media.py` all pass, TranscriptionService mocked

### Task 2: Register ingest_media ActionDefinition

**Commit:** `b6c75b4` — feat(22-02): register ingest_media ActionDefinition in ActionRegistry

**What was built:**
- `ingest_media` ActionDefinition registered in `_register_ingest_actions()`
- Params: `path` (argument), `title`, `topic`, `tags` (multiple), `summary`, `dry_run` (flag)
- `handler=lambda vault, **kw: IngestController(vault).ingest_media(**kw)`
- `cli_group="ingest"`, `cli_name="media"` → auto-generates `ztlctl ingest media <path>`
- MCP auto-generates `ingest_media` tool with when_to_use/avoid_when/common_errors metadata

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing critical functionality] Extended SourceBundleData.input_kind Literal**
- **Found during:** Task 1 GREEN phase
- **Issue:** `SourceBundleData.input_kind: Literal["text", "file", "url"]` would reject `input_kind="media"` at Pydantic validation time
- **Fix:** Added `"media"` to the Literal in `src/ztlctl/services/contracts.py`
- **Files modified:** `src/ztlctl/services/contracts.py`
- **Commit:** `d80f1f9`

**2. [Rule 1 - Bug] source_path injection post-normalization**
- **Found during:** Task 1 GREEN phase
- **Issue:** `normalize_source_bundle` strips unknown keys (not in Pydantic model) from `source_bundle` dict; `source_path` would be silently dropped
- **Fix:** After `normalize_source_bundle` returns in `_create_reference_with_bundle`, inject extra keys from the original `source_bundle` dict (keys not in the known consumed set) into the normalized bundle dict before `persist_source_bundle`
- **Files modified:** `src/ztlctl/services/ingest.py`
- **Commit:** `d80f1f9`

## Verification Results

- `uv run pytest tests/services/test_ingest_media.py -x -v` — 12/12 passed
- `uv run pytest tests/ -q --ignore=tests/integration/test_verbose_telemetry.py` — 2045 passed, 2 skipped
  - Note: `test_verbose_json_includes_telemetry_in_meta` was pre-existing failure (not caused by this plan)
- `uv run mypy src/ztlctl/services/ingest.py src/ztlctl/services/transcription.py src/ztlctl/controllers/ingest.py src/ztlctl/actions/_ingest.py` — clean
- `uv run ruff check src/ztlctl/services/ src/ztlctl/controllers/ingest.py src/ztlctl/actions/_ingest.py` — clean
- Registry check: `['ingest_media']` in actions where name contains 'media'

## Known Stubs

None — all source bundle fields (normalized_text, capture_agent, modalities, source_path) are fully wired from transcription output.

## Self-Check: PASSED

- tests/services/test_ingest_media.py — FOUND
- src/ztlctl/services/ingest.py — FOUND
- commit 61296d2 — FOUND
- commit d80f1f9 — FOUND
- commit b6c75b4 — FOUND
