"""Tests for shared service-layer helper functions."""

from __future__ import annotations

import re

from ztlctl.services._helpers import now_compact, now_iso, parse_tag_parts, today_iso


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


class TestParseTagParts:
    def test_scoped_tag(self) -> None:
        assert parse_tag_parts("domain/scope") == ("domain", "scope")

    def test_unscoped_tag(self) -> None:
        assert parse_tag_parts("general") == ("unscoped", "general")

    def test_multi_slash(self) -> None:
        """Only the first slash is used as separator."""
        assert parse_tag_parts("a/b/c") == ("a", "b/c")

    def test_empty_domain(self) -> None:
        """Edge case: tag starts with slash."""
        assert parse_tag_parts("/scope") == ("", "scope")

    def test_trailing_slash(self) -> None:
        """Edge case: tag ends with slash."""
        assert parse_tag_parts("domain/") == ("domain", "")
