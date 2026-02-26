"""Tests for tag domain logic."""

from __future__ import annotations

from ztlctl.domain.tags import parse_tag_parts


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
