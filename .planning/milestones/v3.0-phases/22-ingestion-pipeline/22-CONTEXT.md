# Phase 22: Ingestion Pipeline - Context

**Gathered:** 2026-03-21
**Status:** Ready for planning

<domain>
## Phase Boundary

Add media file and transcript ingestion to the existing IngestService. Local transcription via faster-whisper (optional dependency). Two-phase workflow: plugin produces `captured` reference with transcription output, agent annotates to `annotated` later. Configurable via `[ingest.media]` config section.

</domain>

<decisions>
## Implementation Decisions

### Transcription Backend
- Use `faster-whisper` — 4x faster than OpenAI whisper, lower memory, same accuracy
- Optional dependency: `uv add --group media faster-whisper` — graceful import error if not installed
- Default model: `base` (~150MB download, good accuracy/speed tradeoff)
- Transcription progress via `@traced` decorator — consistent with existing telemetry patterns

### Ingestion Workflow
- Two-phase: plugin produces `captured` reference with source bundle (`normalized_text`, `capture_agent`, `modalities`), agent annotates later to `annotated`
- Media files NOT copied into vault — path reference stored in source bundle, original stays in place
- Supported formats: Audio (mp3, m4a, wav, ogg, flac), Video (mp4, mkv, webm), Transcript (txt, vtt, srt)

### Config and Integration
- Config section `[ingest.media]` with keys: `whisper_model` (str, default "base"), `language` (str|None, default None for auto-detect), `compute_type` (str, default "int8")
- Extend existing IngestService with `ingest_media` method — same capture pipeline with transcription pre-step
- Transcript files (VTT/SRT) parsed into plain text, create `captured` reference with same source bundle shape as transcribed audio — unified pipeline

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/ztlctl/services/ingest.py` — IngestService with `ingest_text`, `ingest_url`, `list_providers`, `preview`
- `src/ztlctl/controllers/ingest.py` — IngestController with `_run_action` pattern
- `src/ztlctl/services/source_bundles.py` — `normalize_source_bundle`, `persist_source_bundle`, `bundle_artifacts`
- `src/ztlctl/plugins/contracts.py` — `SourceProviderContribution`, `SourceFetchRequest`
- `src/ztlctl/config/models.py` — Pydantic settings models
- `src/ztlctl/domain/lifecycle.py` — `CAPTURED = "captured"`, transition `captured → annotated`
- `src/ztlctl/actions/_ingest.py` — existing ingest action registrations

### Established Patterns
- IngestService extends BaseService, uses CreateService for note creation
- Source bundles: `normalize_source_bundle()` validates, `persist_source_bundle()` writes to vault
- Config via Pydantic nested models in `config/models.py`
- Optional dependencies: guarded imports with `try/except ImportError` (used by MCP, sqlite-vec)

### Integration Points
- `src/ztlctl/services/ingest.py` — add `ingest_media` method
- `src/ztlctl/controllers/ingest.py` — add `ingest_media` controller method
- `src/ztlctl/actions/_ingest.py` — register `ingest_media` action
- `src/ztlctl/config/models.py` — add `MediaIngestConfig` model
- New `src/ztlctl/services/transcription.py` — whisper integration module

</code_context>

<specifics>
## Specific Ideas

- The transcription module should be fully isolated (own file) so the whisper import guard is in one place
- VTT/SRT parsing should be simple regex-based (strip timestamps, join text) — no external parser dependency
- Source bundle for media should include: `normalized_text` (transcription), `capture_agent` ("faster-whisper/{model}"), `modalities` (["audio"] or ["video", "audio"]), `source_path` (original file path)

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>
