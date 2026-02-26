"""Tests for shared service-layer helper functions."""

from __future__ import annotations

import re

from ztlctl.services._helpers import (
    estimate_tokens,
    now_compact,
    now_iso,
    today_iso,
)


class TestEstimateTokens:
    def test_empty_string(self) -> None:
        assert estimate_tokens("") == 1

    def test_short_string(self) -> None:
        # "hello" = 5 chars -> 5//4 = 1
        assert estimate_tokens("hello") == 1

    def test_longer_string(self) -> None:
        # 100 chars -> 25 tokens
        assert estimate_tokens("a" * 100) == 25

    def test_realistic_text(self) -> None:
        text = "This is a realistic paragraph of text that might appear in a note."
        result = estimate_tokens(text)
        assert result > 0
        assert result == len(text) // 4


class TestTodayIso:
    def test_format(self) -> None:
        result = today_iso()
        assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", result)

    def test_returns_string(self) -> None:
        assert isinstance(today_iso(), str)


class TestNowIso:
    def test_format(self) -> None:
        result = now_iso()
        # Standard ISO 8601 contains 'T' separator and '+' or timezone info
        assert "T" in result
        assert isinstance(result, str)

    def test_contains_colons(self) -> None:
        """Standard ISO timestamps have colons in the time portion."""
        assert ":" in now_iso()


class TestNowCompact:
    def test_format(self) -> None:
        result = now_compact()
        assert re.fullmatch(r"\d{8}T\d{6}", result)

    def test_no_colons(self) -> None:
        """Compact format must be filename-safe (no colons)."""
        assert ":" not in now_compact()

    def test_no_dashes(self) -> None:
        """Compact format omits dashes for brevity."""
        assert "-" not in now_compact()
