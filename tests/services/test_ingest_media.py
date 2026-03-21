"""Tests for IngestService.ingest_media and IngestController.ingest_media."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from ztlctl.controllers.ingest import IngestController
from ztlctl.services.ingest import IngestService
from ztlctl.services.transcription import TranscriptionResult

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_transcription_result(
    text: str = "Transcribed content here.",
    capture_agent: str = "transcript-parser",
    modalities: list[str] | None = None,
) -> TranscriptionResult:
    return TranscriptionResult(
        text=text,
        language=None,
        duration_seconds=None,
        segments=[],
        capture_agent=capture_agent,
        modalities=modalities or ["text"],
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def vtt_file(tmp_path: Path) -> Path:
    """Create a minimal WebVTT transcript file."""
    p = tmp_path / "lecture.vtt"
    p.write_text(
        "WEBVTT\n\n00:00:01.000 --> 00:00:05.000\nHello world.\n\n"
        "00:00:06.000 --> 00:00:10.000\nThis is a test.\n",
        encoding="utf-8",
    )
    return p


@pytest.fixture
def srt_file(tmp_path: Path) -> Path:
    """Create a minimal SRT transcript file."""
    p = tmp_path / "meeting.srt"
    p.write_text(
        "1\n00:00:01,000 --> 00:00:05,000\nHello world.\n\n"
        "2\n00:00:06,000 --> 00:00:10,000\nThis is a test.\n",
        encoding="utf-8",
    )
    return p


@pytest.fixture
def txt_file(tmp_path: Path) -> Path:
    """Create a plain text transcript file."""
    p = tmp_path / "transcript.txt"
    p.write_text("This is a plain text transcript.\n", encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# IngestService.ingest_media tests
# ---------------------------------------------------------------------------


class TestIngestMediaService:
    def test_ingest_vtt_creates_captured_reference(self, vault, vtt_file: Path) -> None:
        """VTT transcript ingestion creates a reference with correct source bundle fields."""
        mock_result = _make_transcription_result(
            text="Hello world. This is a test.",
            capture_agent="transcript-parser",
            modalities=["text"],
        )
        with patch(
            "ztlctl.services.ingest.TranscriptionService.transcribe_file",
            return_value=mock_result,
        ):
            result = IngestService(vault).ingest_media(vtt_file)

        assert result.ok, f"Expected ok=True, got error: {result.error}"
        assert result.data["type"] == "reference"

        # Check source bundle is written with correct fields
        bundle_path = vault.root / result.data["source_bundle_path"]
        assert bundle_path.is_file()
        bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
        # normalized text content is in the separate normalized.md file, not the bundle JSON
        normalized_text_path = vault.root / bundle["normalized_text"]["path"]
        assert normalized_text_path.is_file()
        assert "Hello world." in normalized_text_path.read_text(encoding="utf-8")
        assert bundle["capture_agent"] == "transcript-parser"
        assert "text" in bundle["modalities"]

    def test_ingest_srt_creates_captured_reference(self, vault, srt_file: Path) -> None:
        """SRT transcript ingestion creates a captured reference."""
        mock_result = _make_transcription_result(
            text="Hello world. This is a test.",
            capture_agent="transcript-parser",
            modalities=["text"],
        )
        with patch(
            "ztlctl.services.ingest.TranscriptionService.transcribe_file",
            return_value=mock_result,
        ):
            result = IngestService(vault).ingest_media(srt_file)

        assert result.ok, f"Expected ok=True, got error: {result.error}"
        assert result.data["type"] == "reference"

    def test_ingest_txt_creates_captured_reference(self, vault, txt_file: Path) -> None:
        """Plain text transcript ingestion creates a captured reference."""
        mock_result = _make_transcription_result(
            text="This is a plain text transcript.",
            capture_agent="transcript-parser",
            modalities=["text"],
        )
        with patch(
            "ztlctl.services.ingest.TranscriptionService.transcribe_file",
            return_value=mock_result,
        ):
            result = IngestService(vault).ingest_media(txt_file)

        assert result.ok, f"Expected ok=True, got error: {result.error}"
        assert result.data["type"] == "reference"

    def test_ingest_nonexistent_file_returns_not_found(self, vault, tmp_path: Path) -> None:
        """Non-existent file path returns NOT_FOUND error."""
        missing = tmp_path / "no_such_file.vtt"
        result = IngestService(vault).ingest_media(missing)

        assert not result.ok
        assert result.error is not None
        assert result.error.code == "NOT_FOUND"

    def test_ingest_unsupported_extension_returns_error(self, vault, tmp_path: Path) -> None:
        """Unsupported file extension returns UNSUPPORTED_INPUT error."""
        bad_file = tmp_path / "document.pdf"
        bad_file.write_text("content", encoding="utf-8")

        result = IngestService(vault).ingest_media(bad_file)

        assert not result.ok
        assert result.error is not None
        assert result.error.code == "UNSUPPORTED_INPUT"

    def test_ingest_media_dry_run_returns_preview(self, vault, vtt_file: Path) -> None:
        """dry_run=True returns a preview without writing files."""
        notes_before = list((vault.root / "notes").rglob("*.md"))
        mock_result = _make_transcription_result(text="Preview content.")

        with patch(
            "ztlctl.services.ingest.TranscriptionService.transcribe_file",
            return_value=mock_result,
        ):
            result = IngestService(vault).ingest_media(vtt_file, dry_run=True)

        assert result.ok
        notes_after = list((vault.root / "notes").rglob("*.md"))
        assert len(notes_before) == len(notes_after), "dry_run must not create notes"

    def test_ingest_media_stores_source_path_in_bundle(self, vault, vtt_file: Path) -> None:
        """source_path in the source bundle is the original file path (not copied)."""
        mock_result = _make_transcription_result(text="Content.")

        with patch(
            "ztlctl.services.ingest.TranscriptionService.transcribe_file",
            return_value=mock_result,
        ):
            result = IngestService(vault).ingest_media(vtt_file)

        assert result.ok
        bundle_path = vault.root / result.data["source_bundle_path"]
        bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
        # source_path is stored at the top level of the bundle JSON
        assert "source_path" in bundle
        assert str(vtt_file.resolve()) == bundle["source_path"]

    def test_ingest_media_uses_stem_as_default_title(self, vault, vtt_file: Path) -> None:
        """When no title is provided, the file stem is used as the title."""
        mock_result = _make_transcription_result(text="Content.")

        with patch(
            "ztlctl.services.ingest.TranscriptionService.transcribe_file",
            return_value=mock_result,
        ):
            result = IngestService(vault).ingest_media(vtt_file)

        assert result.ok
        assert result.data["title"] == "lecture"

    def test_ingest_media_with_explicit_title(self, vault, vtt_file: Path) -> None:
        """When title is provided explicitly, it overrides the file stem."""
        mock_result = _make_transcription_result(text="Content.")

        with patch(
            "ztlctl.services.ingest.TranscriptionService.transcribe_file",
            return_value=mock_result,
        ):
            result = IngestService(vault).ingest_media(vtt_file, title="My Lecture Notes")

        assert result.ok
        assert result.data["title"] == "My Lecture Notes"

    def test_ingest_media_transcription_error_propagates(self, vault, vtt_file: Path) -> None:
        """When TranscriptionService returns a ServiceError, ingest_media propagates it."""
        from ztlctl.services.result import ServiceError

        transcription_error = ServiceError(
            code="DEPENDENCY_MISSING",
            message="faster-whisper is not installed.",
        )
        with patch(
            "ztlctl.services.ingest.TranscriptionService.transcribe_file",
            return_value=transcription_error,
        ):
            result = IngestService(vault).ingest_media(vtt_file)

        assert not result.ok
        assert result.error is not None
        assert result.error.code == "DEPENDENCY_MISSING"


# ---------------------------------------------------------------------------
# IngestController.ingest_media tests
# ---------------------------------------------------------------------------


class TestIngestMediaController:
    def test_controller_delegates_through_run_action(self, vault, vtt_file: Path) -> None:
        """IngestController.ingest_media delegates through _run_action."""
        mock_result = _make_transcription_result(text="Controller test content.")

        with patch(
            "ztlctl.services.ingest.TranscriptionService.transcribe_file",
            return_value=mock_result,
        ):
            result = IngestController(vault).ingest_media(str(vtt_file))

        assert result.ok, f"Expected ok=True, got error: {result.error}"
        assert result.data["type"] == "reference"

    def test_controller_ingest_media_not_found(self, vault, tmp_path: Path) -> None:
        """Controller returns NOT_FOUND for missing file."""
        missing = tmp_path / "ghost.vtt"
        result = IngestController(vault).ingest_media(str(missing))

        assert not result.ok
        assert result.error is not None
        assert result.error.code == "NOT_FOUND"
