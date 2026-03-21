---
phase: 22-ingestion-pipeline
plan: "01"
subsystem: services
tags: [transcription, faster-whisper, whisper, media, config, pydantic]

requires:
  - phase: 21-contradiction-detection
    provides: services layer patterns, ServiceError/ServiceResult contracts

provides:
  - TranscriptionService with guarded faster-whisper import
  - TranscriptionResult frozen dataclass
  - regex-based VTT/SRT transcript parsing (no external deps)
  - MediaIngestConfig Pydantic model at [ingest.media]
  - IngestConfig.media field wiring for settings access

affects:
  - 22-02 (wires TranscriptionService into IngestService and ActionRegistry)

tech-stack:
  added: []
  patterns:
    - "Stateless utility service pattern — TranscriptionService does not extend BaseService (no Vault needed)"
    - "Guarded optional import — faster_whisper imported inside _transcribe_media() with try/except ImportError"
    - "DEPENDENCY_MISSING error code with uv install hint for optional packages"
    - "Frozen dataclass (dataclass frozen=True) for value-object results alongside Pydantic ServiceResult"

key-files:
  created:
    - src/ztlctl/services/transcription.py
    - tests/services/test_transcription.py
  modified:
    - src/ztlctl/config/models.py

key-decisions:
  - "TranscriptionService is stateless utility (not BaseService subclass) — no Vault access needed for file transcription"
  - "faster-whisper import guarded inside _transcribe_media() — module-level guard would prevent instantiation on import"
  - "TranscriptionResult uses frozen dataclass (not Pydantic) — value-object semantics, no serialization needed at this layer"
  - "VTT/SRT parsing is regex-only — no external parser dependencies per plan constraint"
  - "DEPENDENCY_MISSING code includes uv add --group media faster-whisper install hint"
  - "MediaIngestConfig composes into IngestConfig.media — settings.ingest.media.whisper_model pattern"

patterns-established:
  - "Optional dependency pattern: try import inside method body, return ServiceError(code='DEPENDENCY_MISSING') if ImportError"
  - "Transcript parsing: strip header + timestamp lines via regex, join remaining with space"

requirements-completed: [INGP-01, INGP-02, INGP-05]

duration: 3min
completed: "2026-03-21"
---

# Phase 22 Plan 01: Transcription Service and Media Config Summary

**TranscriptionService with guarded faster-whisper import, regex VTT/SRT parsing, and MediaIngestConfig at settings.ingest.media**

## Performance

- **Duration:** ~3 min
- **Started:** 2026-03-21T20:40:19Z
- **Completed:** 2026-03-21T20:43:52Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments

- `TranscriptionResult` frozen dataclass with text, language, duration_seconds, segments, capture_agent, modalities fields
- `TranscriptionService` stateless utility class with AUDIO/VIDEO/TRANSCRIPT extension sets, @traced decorator, trace_span sub-stages
- Guarded `faster_whisper` import inside `_transcribe_media()` — returns `DEPENDENCY_MISSING` error with `uv add` hint when not installed
- Regex-based `_parse_vtt()` and `_parse_srt()` — strip headers/timestamps/sequence numbers, join remaining content lines
- `MediaIngestConfig` Pydantic model with `whisper_model="base"`, `language=None`, `compute_type="int8"` defaults
- `IngestConfig.media` field wiring — accessible via `settings.ingest.media`
- 31 tests covering all file types, error paths, mocked whisper integration, and config defaults

## Task Commits

1. **Task 1: TranscriptionService with whisper integration and transcript parsing** - `e04a143` (feat)
2. **Task 2: MediaIngestConfig model and settings wiring** - `f6d7dc0` (feat)

## Files Created/Modified

- `src/ztlctl/services/transcription.py` — TranscriptionService, TranscriptionResult
- `tests/services/test_transcription.py` — 31 tests for all code paths
- `src/ztlctl/config/models.py` — Added MediaIngestConfig class and IngestConfig.media field

## Decisions Made

- TranscriptionService does not extend BaseService because it requires no Vault access — pure file I/O utility
- `faster_whisper` import inside `_transcribe_media()` (not module-level) so the class can be instantiated even without the package installed
- `TranscriptionResult` uses `dataclass(frozen=True)` rather than Pydantic since it's a value object that stays within the service layer
- VTT/SRT parsing uses Python stdlib `re` only — no external parser library

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

Pre-commit ruff checks caught line-length violations in the test file (long inline string fixtures, long assertion). Fixed by splitting into multi-line string concatenation and parenthesized assertions. No logic changes required.

## Known Stubs

None — all core behavior is implemented. Plan 02 will wire TranscriptionService into IngestService and register ActionRegistry actions.

## Next Phase Readiness

- `TranscriptionService` and `TranscriptionResult` are fully implemented and ready for Plan 02 wiring
- `settings.ingest.media` config path is available for Plan 02 to pass config values to `TranscriptionService`
- Plan 02 will integrate `transcribe_file()` into `IngestService.ingest_media()` and register `ingest_transcribe` ActionDefinition

---
*Phase: 22-ingestion-pipeline*
*Completed: 2026-03-21*

## Self-Check: PASSED

- FOUND: src/ztlctl/services/transcription.py
- FOUND: tests/services/test_transcription.py
- FOUND: src/ztlctl/config/models.py
- FOUND: .planning/phases/22-ingestion-pipeline/22-01-SUMMARY.md
- FOUND: commit e04a143 (TranscriptionService)
- FOUND: commit f6d7dc0 (MediaIngestConfig)
