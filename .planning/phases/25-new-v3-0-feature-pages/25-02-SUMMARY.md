---
phase: 25-new-v3-0-feature-pages
plan: "02"
subsystem: docs
tags: [documentation, contradiction-detection, media-ingestion, how-to, mcp]
dependency_graph:
  requires: [25-01]
  provides: [contradiction-detection.md, media-ingestion.md]
  affects: [docs/llms.txt, docs/llms-full.txt, mkdocs.yml nav]
tech_stack:
  added: []
  patterns: [diataxis-how-to, source-verified-docs, three-audience-model]
key_files:
  created:
    - docs/contradiction-detection.md
    - docs/media-ingestion.md
  modified: []
decisions:
  - "Contradiction detection page uses check/contradictions and check/confirm-contradiction CLI paths (not a standalone contradiction subcommand)"
  - "Media ingestion page documents ogg/flac/mkv/webm formats from TranscriptionService.SUPPORTED_EXTENSIONS (broader than originally scoped mp4/mp3/m4a/wav)"
metrics:
  duration_seconds: 117
  completed_date: "2026-03-21"
  tasks_completed: 2
  files_created: 2
  files_modified: 0
---

# Phase 25 Plan 02: Feature Pages (Contradiction Detection + Media Ingestion) Summary

Two standalone v3.0 How-to documentation pages covering contradiction detection (semantic integrity via heuristic scoring and graph edges) and media ingestion (faster-whisper transcription pipeline with two-phase captured-to-annotated workflow).

## What Was Built

### Task 1: docs/contradiction-detection.md (NDOC-03)

Complete How-to guide for contradiction detection. Covers:

- **How it works**: three-signal heuristic (cosine similarity 40%, negation density 30%, key-points divergence 30%) and two-phase discovery (vector similarity threshold + shared tag filter)
- **CLI usage**: `ztlctl check contradictions [--similarity-threshold FLOAT] [--max-pairs INTEGER]` and `ztlctl check confirm-contradiction NOTE_A NOTE_B` — flags verified against `--help` output
- **CAT_SEMANTIC**: explained as the `semantic_analysis` category in the general `ztlctl check check` scanner
- **Graph edges**: bidirectional `contradicts` edges with `source_layer=user`; warns that edges are not auto-removed on content update
- **MCP tools table**: `check_contradictions` (read) and `confirm_contradiction` (write) with full parameter tables
- **MCP resource**: `ztlctl://review/contradictions` with example JSON payload showing `candidates`, `score`, `signals`
- **Agent workflow**: concrete 5-step loop (read resource → inspect docs → evaluate → confirm or skip → re-scan)

### Task 2: docs/media-ingestion.md (NDOC-04)

Complete How-to guide for media ingestion. Covers:

- **Prominent `!!! warning`** for faster-whisper optional dependency at top of Prerequisites section, with install command
- **Supported formats**: full table of 11 formats (mp3, m4a, wav, ogg, flac, mp4, mkv, webm, txt, vtt, srt) with faster-whisper requirement column
- **CLI usage**: `ztlctl ingest media PATH [--title] [--topic] [--tags] [--summary] [--dry-run]` — flags verified against `--help` output
- **Two-phase workflow**: captured → annotated explained with concrete before/after examples and `ztlctl update` annotation command
- **Configuration**: `[ingest.media]` TOML section with `whisper_model`, `language`, `compute_type` from `MediaIngestConfig`; model size trade-offs table
- **MCP tool**: `ingest_media` parameters, return format (with `source_bundle_path`, `capture_agent`, `modalities`), and common errors table

## Deviations from Plan

### Auto-expanded Issues

**1. [Rule 2 - Scope Expansion] Documented ogg/flac/mkv/webm formats**
- **Found during**: Task 2, reading `TranscriptionService.SUPPORTED_EXTENSIONS`
- **Issue**: Plan scope listed mp4, mp3, m4a, wav as "supported formats" but the source also supports ogg, flac, mkv, webm
- **Fix**: Included all 8 audio/video formats from `AUDIO_EXTENSIONS | VIDEO_EXTENSIONS` in the formats table
- **Files modified**: docs/media-ingestion.md

**2. [Rule 1 - Accuracy] CLI paths use check group, not standalone subcommand**
- **Found during**: Task 1, running `ztlctl check --help`
- **Issue**: Plan description implied a possible `ztlctl contradiction` top-level subcommand; source routes through `ztlctl check contradictions` and `ztlctl check confirm-contradiction`
- **Fix**: All CLI examples use the correct `ztlctl check <subcommand>` path
- **Files modified**: docs/contradiction-detection.md

## Known Stubs

None — both pages have complete content. No placeholder text, no TODO items, no hardcoded empty sections.

## Self-Check: PASSED

- `docs/contradiction-detection.md` exists and contains: check_contradictions, confirm_contradiction, ztlctl://review/contradictions, CAT_SEMANTIC/semantic, What's next
- `docs/media-ingestion.md` exists and contains: faster-whisper warning, ingest_media, captured, annotated, !!! warning, What's next
- Commit `fc4aba9`: contradiction-detection.md
- Commit `d9a3286`: media-ingestion.md
