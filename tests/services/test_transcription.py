"""Tests for TranscriptionService."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ztlctl.services.transcription import TranscriptionResult, TranscriptionService

# ---------------------------------------------------------------------------
# TranscriptionResult dataclass
# ---------------------------------------------------------------------------


class TestTranscriptionResult:
    def test_fields_accessible(self) -> None:
        result = TranscriptionResult(
            text="Hello world",
            language="en",
            duration_seconds=10.5,
            segments=[{"start": 0.0, "end": 1.0, "text": "Hello world"}],
            capture_agent="transcript-parser",
            modalities=["text"],
        )
        assert result.text == "Hello world"
        assert result.language == "en"
        assert result.duration_seconds == 10.5
        assert len(result.segments) == 1
        assert result.capture_agent == "transcript-parser"
        assert result.modalities == ["text"]

    def test_optional_fields_default_to_none(self) -> None:
        result = TranscriptionResult(
            text="Hello",
            language=None,
            duration_seconds=None,
            segments=[],
            capture_agent="whisper",
            modalities=["audio", "text"],
        )
        assert result.language is None
        assert result.duration_seconds is None

    def test_is_frozen(self) -> None:
        result = TranscriptionResult(
            text="Hello",
            language=None,
            duration_seconds=None,
            segments=[],
            capture_agent="whisper",
            modalities=["text"],
        )
        with pytest.raises((AttributeError, TypeError)):
            result.text = "changed"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# _parse_vtt
# ---------------------------------------------------------------------------


class TestParseVtt:
    def setup_method(self) -> None:
        self.svc = TranscriptionService()

    def test_strips_webvtt_header_and_timestamps(self) -> None:
        vtt = (
            "WEBVTT\n\n"
            "00:00:00.000 --> 00:00:02.000\n"
            "Hello world\n\n"
            "00:00:02.000 --> 00:00:04.000\n"
            "How are you\n"
        )
        result = self.svc._parse_vtt(vtt)
        assert "Hello world" in result
        assert "How are you" in result
        assert "WEBVTT" not in result
        assert "-->" not in result
        assert "00:00" not in result

    def test_handles_empty_vtt(self) -> None:
        result = self.svc._parse_vtt("WEBVTT\n\n")
        assert result == ""

    def test_joins_multiple_lines(self) -> None:
        vtt = "WEBVTT\n\n00:00:01.000 --> 00:00:03.000\nLine one\nLine two\n\n"
        result = self.svc._parse_vtt(vtt)
        assert "Line one" in result
        assert "Line two" in result


# ---------------------------------------------------------------------------
# _parse_srt
# ---------------------------------------------------------------------------


class TestParseSrt:
    def setup_method(self) -> None:
        self.svc = TranscriptionService()

    def test_strips_sequence_numbers_and_timestamps(self) -> None:
        srt = (
            "1\n"
            "00:00:00,000 --> 00:00:02,000\n"
            "Hello world\n\n"
            "2\n"
            "00:00:02,000 --> 00:00:04,000\n"
            "How are you\n"
        )
        result = self.svc._parse_srt(srt)
        assert "Hello world" in result
        assert "How are you" in result
        assert "-->" not in result
        assert "00:00" not in result

    def test_handles_empty_srt(self) -> None:
        result = self.svc._parse_srt("\n\n")
        assert result == ""

    def test_strips_standalone_digit_lines(self) -> None:
        srt = (
            "1\n00:00:00,000 --> 00:00:01,000\nText here\n\n"
            "2\n00:00:01,000 --> 00:00:02,000\nMore text\n"
        )
        result = self.svc._parse_srt(srt)
        assert "Text here" in result
        assert "More text" in result
        # Sequence numbers should not appear as standalone lines
        lines = result.split()
        assert "1" not in lines
        assert "2" not in lines


# ---------------------------------------------------------------------------
# _detect_media_type
# ---------------------------------------------------------------------------


class TestDetectMediaType:
    def setup_method(self) -> None:
        self.svc = TranscriptionService()

    @pytest.mark.parametrize("ext", [".mp3", ".m4a", ".wav", ".ogg", ".flac"])
    def test_audio_extensions(self, ext: str) -> None:
        result = self.svc._detect_media_type(Path(f"file{ext}"))
        assert result == "audio"

    @pytest.mark.parametrize("ext", [".mp4", ".mkv", ".webm"])
    def test_video_extensions(self, ext: str) -> None:
        result = self.svc._detect_media_type(Path(f"file{ext}"))
        assert result == "video"

    @pytest.mark.parametrize("ext", [".pdf", ".docx", ".py", ".json"])
    def test_unsupported_extensions_return_none(self, ext: str) -> None:
        result = self.svc._detect_media_type(Path(f"file{ext}"))
        assert result is None

    def test_txt_returns_none(self) -> None:
        # .txt is transcript, not media
        result = self.svc._detect_media_type(Path("file.txt"))
        assert result is None


# ---------------------------------------------------------------------------
# transcribe_file — transcript files
# ---------------------------------------------------------------------------


class TestTranscribeFileTranscripts:
    def setup_method(self) -> None:
        self.svc = TranscriptionService()

    def test_vtt_file_returns_transcription_result(self, tmp_path: Path) -> None:
        vtt = "WEBVTT\n\n00:00:00.000 --> 00:00:02.000\nHello from VTT\n"
        f = tmp_path / "test.vtt"
        f.write_text(vtt, encoding="utf-8")

        result = self.svc.transcribe_file(f)

        assert isinstance(result, TranscriptionResult)
        assert "Hello from VTT" in result.text
        assert result.capture_agent == "transcript-parser"
        assert result.modalities == ["text"]
        assert result.language is None

    def test_srt_file_returns_transcription_result(self, tmp_path: Path) -> None:
        srt = "1\n00:00:00,000 --> 00:00:02,000\nHello from SRT\n"
        f = tmp_path / "test.srt"
        f.write_text(srt, encoding="utf-8")

        result = self.svc.transcribe_file(f)

        assert isinstance(result, TranscriptionResult)
        assert "Hello from SRT" in result.text
        assert result.capture_agent == "transcript-parser"
        assert result.modalities == ["text"]

    def test_txt_file_returns_transcription_result(self, tmp_path: Path) -> None:
        f = tmp_path / "transcript.txt"
        f.write_text("Raw transcript text content", encoding="utf-8")

        result = self.svc.transcribe_file(f)

        assert isinstance(result, TranscriptionResult)
        assert result.text == "Raw transcript text content"
        assert result.capture_agent == "transcript-parser"
        assert result.modalities == ["text"]

    def test_unsupported_extension_returns_error(self, tmp_path: Path) -> None:
        from ztlctl.services.result import ServiceError

        f = tmp_path / "notes.pdf"
        f.write_text("content", encoding="utf-8")

        result = self.svc.transcribe_file(f)

        assert isinstance(result, ServiceError)
        assert result.code == "UNSUPPORTED_INPUT"

    def test_nonexistent_file_returns_error(self, tmp_path: Path) -> None:
        from ztlctl.services.result import ServiceError

        result = self.svc.transcribe_file(tmp_path / "no_such_file.txt")

        assert isinstance(result, ServiceError)
        assert result.code == "NOT_FOUND"


# ---------------------------------------------------------------------------
# transcribe_file — audio/video without faster-whisper installed
# ---------------------------------------------------------------------------


class TestTranscribeFileMissingDependency:
    def test_audio_without_faster_whisper_returns_error(self, tmp_path: Path) -> None:
        from ztlctl.services.result import ServiceError

        f = tmp_path / "recording.mp3"
        f.write_bytes(b"\x00" * 8)  # minimal dummy file

        svc = TranscriptionService()

        # Simulate faster-whisper not being installed by removing from sys.modules
        # and patching the import to raise ImportError
        with patch.dict("sys.modules", {"faster_whisper": None}):
            result = svc.transcribe_file(f)

        assert isinstance(result, ServiceError)
        assert result.code == "DEPENDENCY_MISSING"
        assert (
            "faster-whisper" in result.message.lower() or "faster_whisper" in result.message.lower()
        )
        assert "uv add" in result.message

    def test_video_without_faster_whisper_returns_error(self, tmp_path: Path) -> None:
        from ztlctl.services.result import ServiceError

        f = tmp_path / "lecture.mp4"
        f.write_bytes(b"\x00" * 8)

        svc = TranscriptionService()

        with patch.dict("sys.modules", {"faster_whisper": None}):
            result = svc.transcribe_file(f)

        assert isinstance(result, ServiceError)
        assert result.code == "DEPENDENCY_MISSING"


# ---------------------------------------------------------------------------
# transcribe_file — audio with faster-whisper mocked
# ---------------------------------------------------------------------------


class TestTranscribeFileWithWhisper:
    def test_audio_with_mock_whisper_returns_result(self, tmp_path: Path) -> None:
        f = tmp_path / "recording.wav"
        f.write_bytes(b"\x00" * 16)

        # Mock the faster_whisper module and WhisperModel
        mock_segment = MagicMock()
        mock_segment.text = " Hello from whisper"

        mock_info = MagicMock()
        mock_info.language = "en"
        mock_info.duration = 3.5

        mock_model = MagicMock()
        mock_model.transcribe.return_value = ([mock_segment], mock_info)

        mock_whisper = MagicMock()
        mock_whisper.WhisperModel.return_value = mock_model

        with patch.dict("sys.modules", {"faster_whisper": mock_whisper}):
            svc = TranscriptionService(whisper_model="base", language=None, compute_type="int8")
            result = svc.transcribe_file(f)

        assert isinstance(result, TranscriptionResult)
        assert "Hello from whisper" in result.text
        assert result.language == "en"
        assert result.duration_seconds == 3.5
        assert result.capture_agent == "whisper"
        assert "audio" in result.modalities

    def test_whisper_model_config_passed_correctly(self, tmp_path: Path) -> None:
        f = tmp_path / "audio.flac"
        f.write_bytes(b"\x00" * 16)

        mock_segment = MagicMock()
        mock_segment.text = " Test"

        mock_info = MagicMock()
        mock_info.language = "fr"
        mock_info.duration = 1.0

        mock_model = MagicMock()
        mock_model.transcribe.return_value = ([mock_segment], mock_info)

        mock_whisper = MagicMock()
        mock_whisper.WhisperModel.return_value = mock_model

        with patch.dict("sys.modules", {"faster_whisper": mock_whisper}):
            svc = TranscriptionService(whisper_model="large", language="fr", compute_type="float16")
            result = svc.transcribe_file(f)

        mock_whisper.WhisperModel.assert_called_once_with("large", compute_type="float16")
        mock_model.transcribe.assert_called_once_with(str(f), language="fr")
        assert isinstance(result, TranscriptionResult)
