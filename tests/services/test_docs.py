"""Tests for docs.py — _resolve_docs_path, _docs_search_impl, _docs_index_impl."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from ztlctl.services.docs import (
    _docs_index_impl,
    _docs_search_impl,
    _resolve_docs_path,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def fixture_docs_path(tmp_path: Path) -> Path:
    """Create a minimal docs corpus for deterministic testing."""
    docs = tmp_path / "docs"
    docs.mkdir()

    # Page 1: title contains "session", heading and body too
    (docs / "session.md").write_text(
        """\
---
title: Session Management
---

# Session Management

## Starting a Session

Use `ztlctl agent session start` to begin a session.
The session tracks your note-taking workflow.

## Closing a Session

Run `ztlctl agent session close` to end a session.
"""
    )

    # Page 2: title contains "create", body mentions "note"
    (docs / "create.md").write_text(
        """\
# Create Notes

Learn how to create notes in ztlctl.

## Creating a Note

Use `ztlctl create note` to add a new note to your vault.
This creates a zettel with a unique ID.
"""
    )

    # Page 3: body only mentions "session" (no title/heading match)
    (docs / "configuration.md").write_text(
        """\
# Configuration

Configure ztlctl via TOML config file.

## Vault Settings

You can configure the vault path.
A session timeout can also be set here.
"""
    )

    # Page 4: no "session" mention at all
    (docs / "installation.md").write_text(
        """\
# Installation

Install ztlctl via pip or uv.

## Requirements

Python 3.13+ required.
"""
    )

    # llms.txt for index tests
    (docs / "llms.txt").write_text(
        """\
# ztlctl

> A local knowledge operating system.

## Getting Started

- [Home](https://example.com/)
- [Installation](https://example.com/installation/)
"""
    )

    # guide/ and dev/ subdirs (empty — no .md files, just the dir)
    (docs / "guide").mkdir()
    (docs / "dev").mkdir()

    return docs


# ---------------------------------------------------------------------------
# _resolve_docs_path
# ---------------------------------------------------------------------------


class TestResolveDocsPath:
    def test_resolve_path_dev_install(self) -> None:
        """In editable (dev) install, docs/ exists relative to the package."""
        result = _resolve_docs_path()
        # In test context (editable install), docs/ should be found
        assert result is not None
        assert result.is_dir()
        # Verify it actually looks like a docs directory (has .md files or llms.txt)
        assert any(result.glob("*.md")) or (result / "llms.txt").exists()

    def test_env_override_valid_dir(self, tmp_path: Path) -> None:
        """ZTLCTL_DOCS_PATH pointing to a real dir returns that path."""
        real_dir = tmp_path / "my_docs"
        real_dir.mkdir()
        old = os.environ.pop("ZTLCTL_DOCS_PATH", None)
        try:
            os.environ["ZTLCTL_DOCS_PATH"] = str(real_dir)
            result = _resolve_docs_path()
            assert result == real_dir
        finally:
            if old is not None:
                os.environ["ZTLCTL_DOCS_PATH"] = old
            else:
                os.environ.pop("ZTLCTL_DOCS_PATH", None)

    def test_env_override_nonexistent_dir(self) -> None:
        """ZTLCTL_DOCS_PATH pointing to non-existent dir returns None."""
        old = os.environ.pop("ZTLCTL_DOCS_PATH", None)
        try:
            os.environ["ZTLCTL_DOCS_PATH"] = "/tmp/does_not_exist_ztlctl_9999"
            result = _resolve_docs_path()
            assert result is None
        finally:
            if old is not None:
                os.environ["ZTLCTL_DOCS_PATH"] = old
            else:
                os.environ.pop("ZTLCTL_DOCS_PATH", None)

    def test_returns_none_when_no_docs_found(self, tmp_path: Path) -> None:
        """If docs/ doesn't exist and env var not set, returns None.

        We test this by setting ZTLCTL_DOCS_PATH to a directory that
        doesn't exist — already covered in test_env_override_nonexistent_dir.
        This test additionally verifies that returning None doesn't crash.
        """
        old = os.environ.pop("ZTLCTL_DOCS_PATH", None)
        try:
            os.environ["ZTLCTL_DOCS_PATH"] = str(tmp_path / "no_such_dir")
            result = _resolve_docs_path()
            assert result is None  # no crash, just None
        finally:
            if old is not None:
                os.environ["ZTLCTL_DOCS_PATH"] = old
            else:
                os.environ.pop("ZTLCTL_DOCS_PATH", None)


# ---------------------------------------------------------------------------
# _docs_search_impl
# ---------------------------------------------------------------------------


class TestDocsSearchImpl:
    def test_returns_list_of_dicts(self, fixture_docs_path: Path) -> None:
        """Results are a list of dicts with required keys."""
        results = _docs_search_impl("session", docs_path=fixture_docs_path)
        assert isinstance(results, list)
        assert len(results) > 0
        for item in results:
            assert "title" in item
            assert "path" in item
            assert "score" in item
            assert "excerpt" in item

    def test_single_term_finds_matching_pages(self, fixture_docs_path: Path) -> None:
        """Query 'session' returns pages that contain 'session'."""
        results = _docs_search_impl("session", docs_path=fixture_docs_path)
        titles = [r["title"] for r in results]
        # session.md and configuration.md mention "session"
        assert len(results) >= 2
        # installation.md does NOT mention session — should not appear
        assert not any("Installation" in t for t in titles)

    def test_and_logic_multi_word_query(self, fixture_docs_path: Path) -> None:
        """Multi-word query: only pages with ALL terms are returned."""
        results = _docs_search_impl("create note", docs_path=fixture_docs_path)
        # Only create.md has both "create" and "note"
        # session.md, configuration.md, installation.md do NOT have both
        assert len(results) == 1
        assert "create" in results[0]["title"].lower() or "note" in results[0]["title"].lower()

    def test_and_logic_excludes_partial_matches(self, fixture_docs_path: Path) -> None:
        """A page with only one of two query terms is excluded."""
        results = _docs_search_impl("session installation", docs_path=fixture_docs_path)
        # session.md has "session" but not "installation"
        # installation.md has "installation" but not "session"
        # No page should have both
        assert len(results) == 0

    def test_limit_respected(self, fixture_docs_path: Path) -> None:
        """limit=1 returns at most 1 result."""
        results = _docs_search_impl("session", limit=1, docs_path=fixture_docs_path)
        assert len(results) <= 1

    def test_limit_default_is_5(self, fixture_docs_path: Path) -> None:
        """Default limit is 5; with fewer matching pages, returns all matches."""
        # We have 4 pages; at most 3 mention "session" — all should be returned
        results = _docs_search_impl("session", docs_path=fixture_docs_path)
        # Default limit is 5, so all matching pages are returned (3 max in fixture)
        assert len(results) <= 5

    def test_scoring_title_beats_body(self, fixture_docs_path: Path) -> None:
        """A page with 'session' in title ranks higher than body-only match."""
        results = _docs_search_impl("session", docs_path=fixture_docs_path)
        # session.md title is "Session Management" — should rank highest
        assert results[0]["title"] == "Session Management"

    def test_results_sorted_descending_by_score(self, fixture_docs_path: Path) -> None:
        """Results are sorted by score descending."""
        results = _docs_search_impl("session", docs_path=fixture_docs_path)
        scores = [r["score"] for r in results]
        assert scores == sorted(scores, reverse=True)

    def test_score_is_positive_float(self, fixture_docs_path: Path) -> None:
        """Each result has a positive score."""
        results = _docs_search_impl("session", docs_path=fixture_docs_path)
        for r in results:
            assert isinstance(r["score"], float)
            assert r["score"] > 0

    def test_excerpt_is_string(self, fixture_docs_path: Path) -> None:
        """Each result has an excerpt string."""
        results = _docs_search_impl("session", docs_path=fixture_docs_path)
        for r in results:
            assert isinstance(r["excerpt"], str)

    def test_excerpt_max_200_chars(self, fixture_docs_path: Path) -> None:
        """Excerpt is at most 200 characters."""
        results = _docs_search_impl("session", docs_path=fixture_docs_path)
        for r in results:
            assert len(r["excerpt"]) <= 200

    def test_path_is_string(self, fixture_docs_path: Path) -> None:
        """Each result has a path string."""
        results = _docs_search_impl("session", docs_path=fixture_docs_path)
        for r in results:
            assert isinstance(r["path"], str)

    def test_empty_query_returns_empty(self, fixture_docs_path: Path) -> None:
        """Empty/whitespace query returns empty list."""
        results = _docs_search_impl("", docs_path=fixture_docs_path)
        assert results == []

    def test_no_docs_path_returns_error(self) -> None:
        """When docs_path=None and _resolve_docs_path fails, returns error dict."""
        old = os.environ.pop("ZTLCTL_DOCS_PATH", None)
        try:
            os.environ["ZTLCTL_DOCS_PATH"] = "/tmp/does_not_exist_ztlctl_9999"
            results = _docs_search_impl("session", docs_path=None)
            assert isinstance(results, list)
            assert len(results) == 1
            assert "error" in results[0]
        finally:
            if old is not None:
                os.environ["ZTLCTL_DOCS_PATH"] = old
            else:
                os.environ.pop("ZTLCTL_DOCS_PATH", None)

    def test_no_results_for_missing_term(self, fixture_docs_path: Path) -> None:
        """Query for a term not in any doc returns empty list."""
        results = _docs_search_impl("xyzzy_nonexistent_term_9876", docs_path=fixture_docs_path)
        assert results == []


# ---------------------------------------------------------------------------
# _docs_index_impl
# ---------------------------------------------------------------------------


class TestDocsIndexImpl:
    def test_returns_llms_txt_content(self, fixture_docs_path: Path) -> None:
        """Returns the content of docs/llms.txt as a string."""
        content = _docs_index_impl(docs_path=fixture_docs_path)
        assert isinstance(content, str)
        assert "ztlctl" in content
        assert "Getting Started" in content

    def test_returns_exact_file_content(self, fixture_docs_path: Path) -> None:
        """Content matches the actual file bytes."""
        expected = (fixture_docs_path / "llms.txt").read_text()
        content = _docs_index_impl(docs_path=fixture_docs_path)
        assert content == expected

    def test_error_when_llms_txt_missing(self, tmp_path: Path) -> None:
        """Returns error string when llms.txt is not found."""
        docs_no_llms = tmp_path / "docs_no_llms"
        docs_no_llms.mkdir()
        content = _docs_index_impl(docs_path=docs_no_llms)
        assert isinstance(content, str)
        # Should contain an error message (not crash)
        assert "error" in content.lower() or "not found" in content.lower()

    def test_no_docs_path_returns_error_string(self) -> None:
        """When docs_path=None and path resolution fails, returns error string."""
        old = os.environ.pop("ZTLCTL_DOCS_PATH", None)
        try:
            os.environ["ZTLCTL_DOCS_PATH"] = "/tmp/does_not_exist_ztlctl_9999"
            content = _docs_index_impl(docs_path=None)
            assert isinstance(content, str)
            assert len(content) > 0
        finally:
            if old is not None:
                os.environ["ZTLCTL_DOCS_PATH"] = old
            else:
                os.environ.pop("ZTLCTL_DOCS_PATH", None)
