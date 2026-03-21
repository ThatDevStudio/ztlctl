---
phase: 22-ingestion-pipeline
verified: 2026-03-21T21:00:00Z
status: passed
score: 8/8 must-haves verified
re_verification: false
---

# Phase 22: Ingestion Pipeline Verification Report

**Phase Goal:** Media files and transcripts can be ingested into the vault as structured captured references, ready for agent annotation
**Verified:** 2026-03-21T21:00:00Z
**Status:** passed
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | TranscriptionService accepts audio/video/transcript file paths and returns structured transcription output | VERIFIED | `src/ztlctl/services/transcription.py` — `transcribe_file()` dispatches audio/video to `_transcribe_media()` and transcript files to `_parse_transcript()`, returns `TranscriptionResult` or `ServiceError` |
| 2 | faster-whisper is an optional dependency with graceful ImportError handling | VERIFIED | `_transcribe_media()` wraps `from faster_whisper import WhisperModel` in `try/except ImportError`, returning `ServiceError(code="DEPENDENCY_MISSING")` with `uv add --group media faster-whisper` hint |
| 3 | VTT and SRT transcript files are parsed into plain text without external parser dependencies | VERIFIED | `_parse_vtt()` and `_parse_srt()` use stdlib `re` only — strip headers/timestamps/sequence numbers, join remaining lines |
| 4 | MediaIngestConfig exposes whisper_model, language, and compute_type with sensible defaults | VERIFIED | `src/ztlctl/config/models.py` line 111 — `class MediaIngestConfig` with `whisper_model="base"`, `language=None`, `compute_type="int8"`; composed into `IngestConfig.media` at line 130 |
| 5 | User can pass a media or transcript file path to ingest_media and receive a captured reference note in the vault | VERIFIED | `IngestService.ingest_media()` at line 181 in `ingest.py` resolves path, transcribes, delegates to `_ingest_normalized` with `target_type="reference"`; 12 tests confirm captured reference creation |
| 6 | The captured reference source bundle contains normalized_text, capture_agent, modalities, and source_path from transcription output | VERIFIED | `ingest_media` passes `modalities`, `capture_agent`, and `source_bundle={"source_path": str(source_path)}`; post-Pydantic injection at lines 623–648 in `ingest.py` ensures `source_path` survives normalization |
| 7 | ingest_media is a registered action in ActionRegistry with MCP tool auto-generated | VERIFIED | `src/ztlctl/actions/_ingest.py` registers `ActionDefinition(name="ingest_media", cli_group="ingest", cli_name="media")`; live check confirms `get_action_registry().get("ingest_media")` returns the definition |
| 8 | The two-phase workflow produces a captured reference ready for agent annotation to annotated status | VERIFIED | `ingest_media` hardcodes `target_type="reference"` (enforcing two-phase); `_create_reference_with_bundle` creates a reference content node with source bundle stored; status transitions captured→annotated remain available via UpdateService |

**Score:** 8/8 truths verified

---

## Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/ztlctl/services/transcription.py` | TranscriptionService, TranscriptionResult | VERIFIED | 228 lines; exports both symbols; `@traced` on `transcribe_file`; `trace_span` for whisper sub-stages |
| `src/ztlctl/config/models.py` | MediaIngestConfig Pydantic model | VERIFIED | `class MediaIngestConfig` at line 111; `IngestConfig.media` field at line 130 |
| `tests/services/test_transcription.py` | Tests for transcription service, min 80 lines | VERIFIED | 330 lines; 31 tests covering all file types, error paths, mocked whisper, VTT/SRT fixtures |
| `src/ztlctl/services/ingest.py` | ingest_media method | VERIFIED | `def ingest_media` at line 181; full validation, transcription, and bundle creation |
| `src/ztlctl/controllers/ingest.py` | ingest_media controller method | VERIFIED | `def ingest_media` at line 168; delegates through `_run_action` with `IngestService(self._vault).ingest_media(...)` |
| `src/ztlctl/actions/_ingest.py` | ingest_media ActionDefinition | VERIFIED | Full `ActionDefinition` at line 168–232 with 6 params, handler lambda, MCP metadata, cli_group/cli_name |
| `tests/services/test_ingest_media.py` | End-to-end media ingestion tests, min 60 lines | VERIFIED | 260 lines; 12 tests covering vtt/srt/txt, not-found, unsupported extension, dry_run, source_path storage, controller delegation |

---

## Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `src/ztlctl/services/transcription.py` | faster-whisper | guarded import with `try/except ImportError` | VERIFIED | `try: from faster_whisper import WhisperModel` inside `_transcribe_media()` body at line 107–117 |
| `src/ztlctl/config/models.py` | `src/ztlctl/config/settings.py` | `MediaIngestConfig` composed into `IngestConfig` | VERIFIED | `IngestConfig.media: MediaIngestConfig = Field(default_factory=MediaIngestConfig)` at line 130 — accessible as `settings.ingest.media` |
| `src/ztlctl/services/ingest.py` | `src/ztlctl/services/transcription.py` | `TranscriptionService` instantiation with config values | VERIFIED | `from ztlctl.services.transcription import TranscriptionService` at line 31; instantiated with `cfg.whisper_model`, `cfg.language`, `cfg.compute_type` at lines 224–228 |
| `src/ztlctl/services/ingest.py` | `src/ztlctl/services/source_bundles.py` | `normalize_source_bundle` with transcription output | VERIFIED | `from ztlctl.services.source_bundles import normalize_source_bundle` at line 27; called at line 600 passing `modalities`, `capture_agent`; `source_path` injected post-normalization at line 648 |
| `src/ztlctl/actions/_ingest.py` | `src/ztlctl/controllers/ingest.py` | `ActionDefinition` handler lambda | VERIFIED | `handler=lambda vault, **kw: IngestController(vault).ingest_media(**kw)` at line 219 |

---

## Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| INGP-01 | 22-01 | Source provider accepts mp4, mp3, m4a, wav, and transcript files (txt, vtt, srt) | SATISFIED | `AUDIO_EXTENSIONS`, `VIDEO_EXTENSIONS`, `TRANSCRIPT_EXTENSIONS` frozensets in `TranscriptionService`; plus `.ogg`, `.flac`, `.mkv`, `.webm` |
| INGP-02 | 22-01 | Local transcription via whisper/faster-whisper (no data leaves the machine) | SATISFIED | `_transcribe_media()` calls `WhisperModel` locally; guarded import; no network calls |
| INGP-03 | 22-02 | Two-phase workflow: plugin produces `captured` reference, agent annotates to `annotated` | SATISFIED | `ingest_media` hardcodes `target_type="reference"`; references stored with `captured_at`; `UpdateService` handles captured→annotated transitions |
| INGP-04 | 22-02 | `ingest_media` action registered in ActionRegistry with MCP tool auto-generated | SATISFIED | Confirmed live via `get_action_registry().get("ingest_media")`; `cli_name="media"` auto-generates `ztlctl ingest media` |
| INGP-05 | 22-01 | Config section `[ingest.media]` for whisper model selection, language hints, output preferences | SATISFIED | `MediaIngestConfig` with `whisper_model`, `language`, `compute_type`; accessible via `settings.ingest.media` |
| INGP-06 | 22-02 | Source bundle populated with transcription output (normalized_text, capture_agent, modalities) | SATISFIED | `normalized_text` stored via `persist_source_bundle`; `capture_agent` and `modalities` passed through `_ingest_normalized`; `source_path` injected post-normalization |

All 6 requirements satisfied. No orphaned requirements detected.

---

## Anti-Patterns Found

No blockers or warnings found. Scan of key phase files:

- No `TODO/FIXME/PLACEHOLDER` comments in new files
- No stub implementations (`return null`, `return {}`, `return []`, empty handlers)
- No hardcoded empty data flowing to rendering
- `source_bundle={"source_path": str(source_path)}` in `ingest_media` is not a stub — it carries real data from the resolved file path

---

## Human Verification Required

### 1. Real faster-whisper transcription on audio file

**Test:** Install faster-whisper (`uv add --group media faster-whisper`) and run `ztlctl ingest media path/to/audio.mp3`
**Expected:** A captured reference is created with transcribed text in source bundle, `capture_agent="whisper"`, `modalities=["audio","text"]`
**Why human:** Tests mock `TranscriptionService`; actual faster-whisper model loading and GPU/CPU compute cannot be verified programmatically without the optional package installed

### 2. MCP tool auto-generation for ingest_media

**Test:** Start the MCP server (`ztlctl serve`) and inspect available tools
**Expected:** `ingest_media` tool appears with correct `when_to_use`, `avoid_when`, and `common_errors` metadata
**Why human:** ActionRegistry-to-MCP tool generation is verified by integration test infrastructure; direct MCP server tool list cannot be confirmed without a running server

---

## Gaps Summary

No gaps. All 8 observable truths are verified, all 7 artifacts pass all three levels (exists, substantive, wired), all 5 key links are wired, and all 6 INGP requirements are satisfied.

The one notable implementation decision — `source_path` injection after `normalize_source_bundle` via the `_known_bundle_keys` exclusion pattern — is documented in the SUMMARY and confirmed working by test `test_ingest_media_stores_source_path_in_bundle` (line 172 in `test_ingest_media.py`).

---

_Verified: 2026-03-21T21:00:00Z_
_Verifier: Claude (gsd-verifier)_
