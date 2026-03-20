"""Tests for DocsController — wraps _docs_search_impl, never touches vault."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ztlctl.controllers.docs import DocsController


@pytest.fixture()
def mock_vault() -> MagicMock:
    """DocsController only accepts vault; never calls any method on it."""
    return MagicMock()


@pytest.fixture()
def fixture_docs_path(tmp_path: Path) -> Path:
    """Minimal docs corpus for deterministic controller testing."""
    docs = tmp_path / "docs"
    docs.mkdir()

    (docs / "session.md").write_text(
        """\
# Session Management

## Starting a Session

Use `ztlctl session start` to begin a session.
The session tracks your workflow.
"""
    )

    (docs / "create.md").write_text(
        """\
# Create Notes

Learn how to create notes in ztlctl.

## Creating a Note

Use `ztlctl create note` to add a new note.
"""
    )

    (docs / "installation.md").write_text(
        """\
# Installation

Install ztlctl via pip or uv.
"""
    )

    (docs / "llms.txt").write_text("# ztlctl\n\n> A local knowledge OS.\n")

    (docs / "guide").mkdir()
    (docs / "dev").mkdir()

    return docs


class TestDocsControllerSearch:
    def test_search_returns_dict_with_results_key(
        self, mock_vault: MagicMock, fixture_docs_path: Path
    ) -> None:
        """DocsController.search() returns a dict with 'results' key."""
        ctrl = DocsController(mock_vault)
        result = ctrl.search(query="session", docs_path=fixture_docs_path)
        assert isinstance(result, dict)
        assert "results" in result

    def test_search_results_is_list(self, mock_vault: MagicMock, fixture_docs_path: Path) -> None:
        """results value is a list."""
        ctrl = DocsController(mock_vault)
        result = ctrl.search(query="session", docs_path=fixture_docs_path)
        assert isinstance(result["results"], list)

    def test_search_finds_relevant_page(
        self, mock_vault: MagicMock, fixture_docs_path: Path
    ) -> None:
        """Searching 'session' returns the session page."""
        ctrl = DocsController(mock_vault)
        result = ctrl.search(query="session", docs_path=fixture_docs_path)
        titles = [r["title"] for r in result["results"]]
        assert any("session" in t.lower() for t in titles)

    def test_search_limit_respected(self, mock_vault: MagicMock, fixture_docs_path: Path) -> None:
        """limit=1 caps results at 1."""
        ctrl = DocsController(mock_vault)
        result = ctrl.search(query="session", limit=1, docs_path=fixture_docs_path)
        assert len(result["results"]) <= 1

    def test_search_and_logic_multi_word(
        self, mock_vault: MagicMock, fixture_docs_path: Path
    ) -> None:
        """Multi-word query uses AND logic — only pages with ALL terms returned."""
        ctrl = DocsController(mock_vault)
        result = ctrl.search(query="create note", docs_path=fixture_docs_path)
        # Only create.md has both "create" and "note"
        assert len(result["results"]) == 1

    def test_search_does_not_access_vault(
        self, mock_vault: MagicMock, fixture_docs_path: Path
    ) -> None:
        """DocsController.search() never accesses vault.engine or vault.db."""
        ctrl = DocsController(mock_vault)
        ctrl.search(query="session", docs_path=fixture_docs_path)
        # vault should not have had engine or db accessed
        mock_vault.engine.assert_not_called()
        mock_vault.db.assert_not_called()

    def test_search_default_limit_is_5(
        self, mock_vault: MagicMock, fixture_docs_path: Path
    ) -> None:
        """Default limit is 5 — with 1 matching page, returns at most 5 results."""
        ctrl = DocsController(mock_vault)
        result = ctrl.search(query="session", docs_path=fixture_docs_path)
        assert len(result["results"]) <= 5

    def test_search_no_results_for_missing_term(
        self, mock_vault: MagicMock, fixture_docs_path: Path
    ) -> None:
        """Query for a term not in any doc returns empty results list."""
        ctrl = DocsController(mock_vault)
        result = ctrl.search(query="xyzzy_nonexistent_9876", docs_path=fixture_docs_path)
        assert result["results"] == []

    def test_search_uses_resolve_docs_path_by_default(
        self, mock_vault: MagicMock, fixture_docs_path: Path
    ) -> None:
        """When docs_path not given, controller delegates to _resolve_docs_path."""
        ctrl = DocsController(mock_vault)
        with patch("ztlctl.services.docs._resolve_docs_path", return_value=fixture_docs_path):
            result = ctrl.search(query="session")
        assert isinstance(result, dict)
        assert "results" in result
