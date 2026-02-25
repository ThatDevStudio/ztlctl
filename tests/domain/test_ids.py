"""Tests for ID patterns, validation, and content-hash generation."""

import pytest

from ztlctl.domain.ids import (
    ID_PATTERNS,
    TYPE_PREFIXES,
    generate_content_hash,
    normalize_title,
    validate_id,
)


class TestNormalizeTitle:
    def test_lowercases(self) -> None:
        assert normalize_title("Hello World") == "hello world"

    def test_strips_punctuation(self) -> None:
        assert normalize_title("What's Up?") == "whats up"

    def test_collapses_whitespace(self) -> None:
        assert normalize_title("  lots   of   space  ") == "lots of space"

    def test_nfkc_normalization(self) -> None:
        """NFKC normalizes compatibility characters."""
        assert normalize_title("\ufb01le") == "file"  # fi ligature -> fi

    def test_empty_string(self) -> None:
        assert normalize_title("") == ""


class TestGenerateContentHash:
    def test_deterministic(self) -> None:
        """Same title always produces the same hash."""
        h1 = generate_content_hash("Test Title", "ztl_")
        h2 = generate_content_hash("Test Title", "ztl_")
        assert h1 == h2

    def test_correct_prefix(self) -> None:
        result = generate_content_hash("Test", "ztl_")
        assert result.startswith("ztl_")

    def test_reference_prefix(self) -> None:
        result = generate_content_hash("Test", "ref_")
        assert result.startswith("ref_")

    def test_correct_length(self) -> None:
        """Prefix + 8 hex chars."""
        result = generate_content_hash("Test", "ztl_")
        assert len(result) == 12  # "ztl_" (4) + 8 hex chars

    def test_different_titles_produce_different_hashes(self) -> None:
        h1 = generate_content_hash("First Title", "ztl_")
        h2 = generate_content_hash("Second Title", "ztl_")
        assert h1 != h2

    def test_case_insensitive(self) -> None:
        """Title normalization makes hashing case-insensitive."""
        h1 = generate_content_hash("Database Architecture", "ztl_")
        h2 = generate_content_hash("database architecture", "ztl_")
        assert h1 == h2


class TestValidateId:
    @pytest.mark.parametrize(
        "content_id,content_type",
        [
            ("ztl_abcd1234", "note"),
            ("ref_00ff99aa", "reference"),
            ("LOG-0001", "log"),
            ("LOG-12345", "log"),
            ("TASK-0001", "task"),
            ("TASK-99999", "task"),
        ],
    )
    def test_valid_ids(self, content_id: str, content_type: str) -> None:
        assert validate_id(content_id, content_type)

    @pytest.mark.parametrize(
        "content_id,content_type",
        [
            ("ztl_ABCD1234", "note"),  # uppercase hex
            ("ztl_abc", "note"),  # too short
            ("ref_abcd12345", "reference"),  # too long
            ("LOG-001", "log"),  # only 3 digits
            ("TASK-abc", "task"),  # non-numeric
            ("unknown_123", "note"),  # wrong prefix
        ],
    )
    def test_invalid_ids(self, content_id: str, content_type: str) -> None:
        assert not validate_id(content_id, content_type)

    def test_unknown_type_returns_false(self) -> None:
        assert not validate_id("abc-123", "unknown")


class TestPatternConstants:
    def test_id_patterns_cover_all_types(self) -> None:
        assert set(ID_PATTERNS.keys()) == {"note", "reference", "log", "task"}

    def test_type_prefixes_cover_all_types(self) -> None:
        assert set(TYPE_PREFIXES.keys()) == {"note", "reference", "log", "task"}
