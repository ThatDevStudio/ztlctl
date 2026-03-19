"""Tests for MCP _impl functions — importable without the mcp package.

Each _impl function accepts a Vault directly and returns a plain dict.
These tests verify the _impl layer is independently testable.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ztlctl.config.settings import ZtlSettings
from ztlctl.infrastructure.vault import Vault
from ztlctl.mcp.tools import (
    create_note_impl,
    get_document_impl,
    search_impl,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def vault_root(tmp_path: Path) -> Path:
    (tmp_path / "notes").mkdir()
    (tmp_path / "ops" / "logs").mkdir(parents=True)
    (tmp_path / "ops" / "tasks").mkdir(parents=True)
    return tmp_path


@pytest.fixture
def vault(vault_root: Path) -> Vault:
    settings = ZtlSettings.from_cli(vault_root=vault_root)
    return Vault(settings)


# ---------------------------------------------------------------------------
# Tests — _impl functions (no mcp package required)
# ---------------------------------------------------------------------------


def test_create_note_impl(vault: Vault) -> None:
    """create_note_impl returns a dict with expected keys and ok=True."""
    resp = create_note_impl(vault, "Test Note From Impl")
    assert resp["ok"] is True
    assert resp["op"] == "create_note"
    data = resp["data"]
    assert "id" in data
    assert data["id"]
    assert data["title"] == "Test Note From Impl"
    assert data["type"] == "note"


def test_create_note_impl_with_tags_and_topic(vault: Vault) -> None:
    """create_note_impl accepts optional tags and topic."""
    resp = create_note_impl(
        vault,
        "Tagged Impl Note",
        tags=["test/impl"],
        topic="testing",
    )
    assert resp["ok"] is True
    assert "id" in resp["data"]


def test_search_impl(vault: Vault) -> None:
    """search_impl returns a dict with results for a matching query."""
    create_note_impl(vault, "Searchable Impl Note")
    resp = search_impl(vault, "Searchable")
    assert resp["ok"] is True
    assert resp["op"] == "search"
    assert "items" in resp["data"]


def test_search_impl_no_results(vault: Vault) -> None:
    """search_impl returns ok=True with empty items when nothing matches."""
    resp = search_impl(vault, "xyzzy_nonexistent_term_123")
    assert resp["ok"] is True
    assert resp["data"]["count"] == 0


def test_get_note_impl(vault: Vault) -> None:
    """get_document_impl returns the created note's data by ID."""
    create_resp = create_note_impl(vault, "Fetched By Impl")
    note_id = create_resp["data"]["id"]

    resp = get_document_impl(vault, note_id)
    assert resp["ok"] is True
    assert resp["data"]["id"] == note_id
    assert resp["data"]["title"] == "Fetched By Impl"


def test_get_note_impl_not_found(vault: Vault) -> None:
    """get_document_impl returns ok=False when the ID does not exist."""
    resp = get_document_impl(vault, "N-9999")
    assert resp["ok"] is False
    assert resp["error"]["code"] == "NOT_FOUND"
