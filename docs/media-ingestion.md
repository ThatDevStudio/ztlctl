---
title: Media ingestion
---

# Media ingestion

Media ingestion turns audio, video, and transcript files into structured vault references. ztlctl transcribes audio and video locally using faster-whisper (no data leaves your machine), and parses pre-existing transcript files without any external dependency. Every ingest operation creates a `captured` reference — the first phase of a two-phase workflow that ends when an agent or user annotates and promotes the reference to `annotated` status.

## Prerequisites

!!! warning
    Audio and video transcription requires **faster-whisper**, which is an optional dependency not installed by default. Transcript files (`.txt`, `.vtt`, `.srt`) do **not** require faster-whisper — they are parsed locally with no extra dependencies.

    Install faster-whisper before ingesting audio or video:

    ```bash
    uv add --group media faster-whisper
    ```

    If faster-whisper is not installed and you attempt to ingest an audio or video file, the command returns a `DEPENDENCY_MISSING` error with the install hint above.

## Supported formats

| Format | Type | Requires faster-whisper | Notes |
|--------|------|------------------------|-------|
| `.mp3` | Audio | Yes | Common podcast and voice recording format |
| `.m4a` | Audio | Yes | Apple audio; common for voice memos |
| `.wav` | Audio | Yes | Uncompressed audio; large files |
| `.ogg` | Audio | Yes | Open audio format |
| `.flac` | Audio | Yes | Lossless audio format |
| `.mp4` | Video | Yes | Common video format; audio track is transcribed |
| `.mkv` | Video | Yes | Matroska container; audio track is transcribed |
| `.webm` | Video | Yes | Web video format; audio track is transcribed |
| `.txt` | Transcript | No | Plain text transcript; ingested as-is |
| `.vtt` | Transcript | No | WebVTT subtitle/caption format; timestamps stripped |
| `.srt` | Transcript | No | SubRip subtitle format; sequence numbers and timestamps stripped |

## Ingesting media files

Use `ztlctl ingest media` to ingest an audio or video file. ztlctl loads the whisper model, transcribes the file locally, and creates a captured reference in your vault.

```bash
$ ztlctl ingest media PATH [OPTIONS]
```

**Arguments and options:**

| Argument / Flag | Required | Description |
|-----------------|----------|-------------|
| `PATH` | Yes | Filesystem path to the media or transcript file |
| `--title TEXT` | No | Title override for the captured reference (defaults to the file stem) |
| `--topic TEXT` | No | Topic directory under `notes/` for routing |
| `--tags TEXT` | No | Tags applied to the captured reference (repeatable) |
| `--summary TEXT` | No | Capture summary hint written into the reference frontmatter |
| `--dry-run` | No | Preview ingestion without creating any files |

**Example — ingest a podcast recording:**

```bash
$ ztlctl ingest media recordings/interview-2026-03-21.mp3 \
    --title "Interview: distributed systems patterns" \
    --topic ml/research \
    --tags podcast --tags distributed-systems
```

**Example — preview before writing:**

```bash
$ ztlctl ingest media lecture.mp4 --dry-run
```

The `--dry-run` flag returns a preview with the first 280 characters of the normalized transcript, the resolved title, and the ingest metadata — no files are written.

!!! note
    Transcription runs entirely on your local machine. The audio or video file is never sent to an external service. The whisper model is downloaded once to a local cache on first use. See [Configuration](#configuration) to choose a different model size.

## Ingesting transcripts

If you already have a transcript file — from an external transcription service, a video platform, or a manual capture — use `ztlctl ingest media` with the transcript file directly. No faster-whisper installation is required.

**WebVTT file:**

```bash
$ ztlctl ingest media captions.vtt --title "Conference talk: CRDT internals"
```

**SRT file:**

```bash
$ ztlctl ingest media subtitles.srt --title "Lecture 4 — consensus protocols"
```

**Plain text transcript:**

```bash
$ ztlctl ingest media transcript.txt --title "Team meeting notes 2026-03-21"
```

VTT and SRT files are automatically stripped of timestamps, sequence numbers, and header lines before ingestion. The resulting plain text is stored in the reference body and the normalized text bundle.

## The two-phase workflow

Every `ztlctl ingest media` call creates a `captured` reference — not a finished note. This is intentional: the transcription is raw material that needs human or agent review before it becomes a durable knowledge artifact.

**Phase 1: Captured** — `ztlctl ingest media` produces a reference with:

- `status: captured` in the frontmatter
- The normalized transcript text in the reference body
- A source bundle (written to `.ztlctl/bundles/`) containing: `normalized_text`, `capture_agent` (`whisper` for audio/video, `transcript-parser` for transcript files), `modalities` (e.g. `["audio", "text"]`), and the original `source_path`.

**Phase 2: Annotated** — An agent or user reviews the captured reference, adds `key_points`, a `summary`, and relevant `tags`, then updates the status to `annotated`:

```bash
$ ztlctl update ZTL-0123 \
    --summary "Key insights from the distributed systems interview" \
    --tags podcast distributed-systems \
    --status annotated
```

!!! tip
    Use `ztlctl query work-queue` to find all `captured` references waiting for annotation. The work queue scores items by age and status — newly captured media references appear near the top.

Once annotated, the reference is indexed, tagged, and eligible for reweave link discovery like any other vault content.

## Configuration

The `[ingest.media]` section in `ztlctl.toml` controls the whisper model and transcription behavior:

```toml
[ingest.media]
whisper_model = "base"   # model size: tiny, base, small, medium, large-v2
language = null          # ISO language code (e.g. "en", "de"); null = auto-detect
compute_type = "int8"    # quantization: int8 (CPU), float16 (GPU), float32
```

**All config fields** (sourced from `MediaIngestConfig` in `config/models.py`):

| Field | Default | Description |
|-------|---------|-------------|
| `whisper_model` | `"base"` | Whisper model size. Larger models are more accurate but slower and require more memory. |
| `language` | `null` | ISO language code hint. `null` enables automatic language detection. |
| `compute_type` | `"int8"` | Quantization type. Use `int8` on CPU (default), `float16` on CUDA GPU for faster transcription. |

**Model size trade-offs:**

| Model | Relative speed | Accuracy | Memory |
|-------|---------------|----------|--------|
| `tiny` | Fastest | Lower | ~40 MB |
| `base` | Fast (default) | Good | ~75 MB |
| `small` | Moderate | Better | ~240 MB |
| `medium` | Slow | High | ~770 MB |
| `large-v2` | Slowest | Highest | ~1550 MB |

!!! tip
    For voice memos and short recordings, `base` (the default) provides good accuracy with fast turnaround. For long lectures or interviews where accuracy matters, switch to `small` or `medium`.

## MCP tool

The `ingest_media` MCP tool mirrors the CLI. Agents use it to ingest media files already accessible on the local filesystem.

**Tool name:** `ingest_media`

**Side effect:** write

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `path` | string | Yes | Filesystem path to the media or transcript file |
| `title` | string | No | Title override for the captured reference |
| `topic` | string | No | Topic directory under `notes/` |
| `tags` | list[string] | No | Tags applied to the captured reference |
| `summary` | string | No | Capture summary hint |
| `dry_run` | bool | No | Preview ingestion without creating files |

**Return format:**

```json
{
  "id": "REF-0042",
  "path": "references/REF-0042.md",
  "title": "Interview: distributed systems patterns",
  "type": "reference",
  "input_kind": "media",
  "source_kind": "media",
  "modalities": ["audio", "text"],
  "capture_agent": "whisper",
  "source_bundle_version": 1,
  "source_bundle_path": ".ztlctl/bundles/REF-0042/bundle.json"
}
```

**Common errors:**

| Error code | Cause |
|------------|-------|
| `NOT_FOUND` | The file path does not exist |
| `UNSUPPORTED_INPUT` | File extension is not in the supported set |
| `DEPENDENCY_MISSING` | faster-whisper not installed (audio/video only) |

## What's next

- [Concepts](concepts.md) — understand references, lifecycle statuses, and source bundles
- [Configuration](configuration.md) — full `ztlctl.toml` reference including `[ingest.media]`
- [Agentic workflows](agentic-workflows.md) — orchestration recipes for capture-and-annotate pipelines
