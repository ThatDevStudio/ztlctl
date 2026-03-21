"""TranscriptionService — media and transcript file ingestion.

Handles audio/video transcription via faster-whisper (optional dependency)
and plain transcript parsing (.vtt, .srt, .txt) using regex-only parsing.

faster-whisper is an optional dependency. When not installed, audio/video
transcription returns a ServiceError with installation instructions.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ztlctl.services.result import ServiceError
from ztlctl.services.telemetry import trace_span, traced


@dataclass(frozen=True)
class TranscriptionResult:
    """Structured output from transcription of a media or transcript file."""

    text: str
    language: str | None
    duration_seconds: float | None
    segments: list[dict[str, Any]]
    capture_agent: str
    modalities: list[str]


class TranscriptionService:
    """Transcribe audio/video files and parse transcript files.

    This is a stateless utility service — it does NOT extend BaseService
    because it requires no Vault access. It can be instantiated standalone
    from config values::

        cfg = settings.ingest.media
        svc = TranscriptionService(
            whisper_model=cfg.whisper_model,
            language=cfg.language,
            compute_type=cfg.compute_type,
        )
        result = svc.transcribe_file(Path("recording.mp3"))

    Returns :class:`TranscriptionResult` on success, :class:`ServiceError` on failure.
    """

    AUDIO_EXTENSIONS: frozenset[str] = frozenset({".mp3", ".m4a", ".wav", ".ogg", ".flac"})
    VIDEO_EXTENSIONS: frozenset[str] = frozenset({".mp4", ".mkv", ".webm"})
    TRANSCRIPT_EXTENSIONS: frozenset[str] = frozenset({".txt", ".vtt", ".srt"})
    SUPPORTED_EXTENSIONS: frozenset[str] = (
        AUDIO_EXTENSIONS | VIDEO_EXTENSIONS | TRANSCRIPT_EXTENSIONS
    )

    def __init__(
        self,
        *,
        whisper_model: str = "base",
        language: str | None = None,
        compute_type: str = "int8",
    ) -> None:
        self._whisper_model = whisper_model
        self._language = language
        self._compute_type = compute_type

    @traced
    def transcribe_file(self, path: Path) -> TranscriptionResult | ServiceError:
        """Transcribe or parse *path* and return a TranscriptionResult.

        Dispatches to:
        - ``_transcribe_media()`` for audio (.mp3, .m4a, .wav, .ogg, .flac)
          and video (.mp4, .mkv, .webm) files.
        - ``_parse_transcript()`` for transcript files (.txt, .vtt, .srt).

        Returns ``ServiceError`` for unsupported extensions or missing files.
        """
        resolved = path.resolve() if path.is_absolute() else path
        if not resolved.exists():
            return ServiceError(
                code="NOT_FOUND",
                message=f"File not found: {path}",
            )

        suffix = path.suffix.lower()
        if suffix not in self.SUPPORTED_EXTENSIONS:
            return ServiceError(
                code="UNSUPPORTED_INPUT",
                message=f"Unsupported file extension: {suffix or '<none>'}",
                detail={"supported": sorted(self.SUPPORTED_EXTENSIONS)},
            )

        media_type = self._detect_media_type(path)
        if media_type is not None:
            return self._transcribe_media(path, media_type)
        return self._parse_transcript(path)

    def _transcribe_media(self, path: Path, media_type: str) -> TranscriptionResult | ServiceError:
        """Transcribe audio or video using faster-whisper.

        The import is guarded so that TranscriptionService can be instantiated
        without faster-whisper installed — the error only surfaces when this
        method is actually called.
        """
        try:
            from faster_whisper import WhisperModel  # type: ignore[import-not-found]
        except ImportError:
            return ServiceError(
                code="DEPENDENCY_MISSING",
                message=(
                    "faster-whisper is not installed. "
                    "Install it with: uv add --group media faster-whisper"
                ),
                detail={"install": "uv add --group media faster-whisper"},
            )

        with trace_span("whisper.load_model"):
            model = WhisperModel(self._whisper_model, compute_type=self._compute_type)

        with trace_span("whisper.transcribe"):
            raw_segments, info = model.transcribe(str(path), language=self._language)
            segments: list[dict[str, Any]] = []
            text_parts: list[str] = []
            for seg in raw_segments:
                seg_text = seg.text.strip()
                text_parts.append(seg_text)
                segments.append(
                    {
                        "start": getattr(seg, "start", None),
                        "end": getattr(seg, "end", None),
                        "text": seg_text,
                    }
                )

        return TranscriptionResult(
            text=" ".join(text_parts),
            language=getattr(info, "language", None),
            duration_seconds=getattr(info, "duration", None),
            segments=segments,
            capture_agent="whisper",
            modalities=[media_type, "text"],
        )

    def _parse_transcript(self, path: Path) -> TranscriptionResult | ServiceError:
        """Parse a .txt, .vtt, or .srt transcript file into plain text."""
        try:
            raw = path.read_text(encoding="utf-8")
        except OSError as exc:
            return ServiceError(
                code="READ_ERROR",
                message=f"Could not read file: {exc}",
            )

        suffix = path.suffix.lower()
        if suffix == ".vtt":
            text = self._parse_vtt(raw)
        elif suffix == ".srt":
            text = self._parse_srt(raw)
        else:
            text = raw

        return TranscriptionResult(
            text=text,
            language=None,
            duration_seconds=None,
            segments=[],
            capture_agent="transcript-parser",
            modalities=["text"],
        )

    def _parse_vtt(self, text: str) -> str:
        """Strip WebVTT headers and timestamps, return joined text lines.

        Removes:
        - The ``WEBVTT`` header line
        - Timestamp lines matching ``HH:MM:SS.mmm --> HH:MM:SS.mmm``
        - Blank lines
        Joins remaining content lines with a space.
        """
        lines = text.splitlines()
        result: list[str] = []
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            if stripped == "WEBVTT":
                continue
            # Timestamp line: contains digits, colons and -->
            if re.match(r"^\d{2}:\d{2}", stripped):
                continue
            result.append(stripped)
        return " ".join(result)

    def _parse_srt(self, text: str) -> str:
        """Strip SRT sequence numbers and timestamps, return joined text lines.

        Removes:
        - Lines that are purely digits (sequence numbers)
        - Timestamp lines matching ``HH:MM:SS,mmm --> HH:MM:SS,mmm``
        - Blank lines
        Joins remaining content lines with a space.
        """
        lines = text.splitlines()
        result: list[str] = []
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            # Sequence number lines: only digits
            if re.match(r"^\d+$", stripped):
                continue
            # Timestamp line: starts with HH:MM
            if re.match(r"^\d{2}:\d{2}", stripped):
                continue
            result.append(stripped)
        return " ".join(result)

    def _detect_media_type(self, path: Path) -> str | None:
        """Return "audio", "video", or None based on file extension."""
        suffix = path.suffix.lower()
        if suffix in self.AUDIO_EXTENSIONS:
            return "audio"
        if suffix in self.VIDEO_EXTENSIONS:
            return "video"
        return None
