"""Tests for Vault — ACID transaction coordination across DB, files, graph."""

from pathlib import Path

import pytest
from sqlalchemy import insert, select, text

from ztlctl.config.settings import ZtlSettings
from ztlctl.infrastructure.database.schema import nodes
from ztlctl.infrastructure.vault import Vault

# Uses shared `vault` fixture from tests/conftest.py


# ---------------------------------------------------------------------------
# Vault initialization
# ---------------------------------------------------------------------------


class TestVaultInit:
    def test_creates_database(self, vault: Vault) -> None:
        db_path = vault.root / ".ztlctl" / "ztlctl.db"
        assert db_path.exists()

    def test_creates_directories(self, vault: Vault) -> None:
        assert (vault.root / ".ztlctl").is_dir()
        assert (vault.root / ".ztlctl" / "backups").is_dir()
        assert (vault.root / ".ztlctl" / "plugins").is_dir()

    def test_existing_db_reused(self, tmp_path: Path) -> None:
        """Second Vault construction reuses existing DB without error."""
        settings = ZtlSettings.from_cli(vault_root=tmp_path)
        v1 = Vault(settings)
        v2 = Vault(settings)
        # Both should work — idempotent
        with v1.engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        with v2.engine.connect() as conn:
            conn.execute(text("SELECT 1"))

    def test_vault_root_property(self, vault: Vault, tmp_path: Path) -> None:
        assert vault.root == tmp_path

    def test_settings_property(self, vault: Vault) -> None:
        assert vault.settings.vault.name == "my-vault"


# ---------------------------------------------------------------------------
# Transaction — success path
# ---------------------------------------------------------------------------


class TestTransactionSuccess:
    def test_db_write_commits(self, vault: Vault) -> None:
        with vault.transaction() as txn:
            txn.conn.execute(
                insert(nodes).values(
                    id="ztl_test1234",
                    title="Test",
                    type="note",
                    status="draft",
                    path="notes/ztl_test1234.md",
                    created="2025-01-15",
                    modified="2025-01-15",
                )
            )
        # Verify committed
        with vault.engine.connect() as conn:
            row = conn.execute(select(nodes.c.title).where(nodes.c.id == "ztl_test1234")).one()
            assert row.title == "Test"

    def test_file_write_persists(self, vault: Vault) -> None:
        path = vault.root / "notes" / "test.md"
        with vault.transaction() as txn:
            txn.write_file(path, "hello world")
        assert path.exists()
        assert path.read_text() == "hello world"

    def test_content_write_persists(self, vault: Vault) -> None:
        path = vault.root / "notes" / "note.md"
        fm = {"id": "ztl_test1234", "type": "note", "title": "Test"}
        with vault.transaction() as txn:
            txn.write_content(path, fm, "Body here.")
        content = path.read_text()
        assert "id: ztl_test1234" in content
        assert "Body here." in content

    def test_combined_db_and_file(self, vault: Vault) -> None:
        """Both DB and file writes commit together."""
        path = vault.root / "notes" / "ztl_test1234.md"
        with vault.transaction() as txn:
            txn.conn.execute(
                insert(nodes).values(
                    id="ztl_test1234",
                    title="Combined",
                    type="note",
                    status="draft",
                    path="notes/ztl_test1234.md",
                    created="2025-01-15",
                    modified="2025-01-15",
                )
            )
            txn.write_content(path, {"id": "ztl_test1234"}, "Body")
        assert path.exists()
        with vault.engine.connect() as conn:
            row = conn.execute(select(nodes.c.id).where(nodes.c.id == "ztl_test1234")).one()
            assert row.id == "ztl_test1234"


# ---------------------------------------------------------------------------
# Transaction — rollback path
# ---------------------------------------------------------------------------


class TestTransactionRollback:
    def test_db_rolls_back_on_error(self, vault: Vault) -> None:
        with pytest.raises(RuntimeError):
            with vault.transaction() as txn:
                txn.conn.execute(
                    insert(nodes).values(
                        id="ztl_fail1234",
                        title="Should Not Persist",
                        type="note",
                        status="draft",
                        path="notes/ztl_fail1234.md",
                        created="2025-01-15",
                        modified="2025-01-15",
                    )
                )
                msg = "Simulated failure"
                raise RuntimeError(msg)
        # Verify not committed
        with vault.engine.connect() as conn:
            row = conn.execute(select(nodes.c.id).where(nodes.c.id == "ztl_fail1234")).first()
            assert row is None

    def test_created_file_deleted_on_error(self, vault: Vault) -> None:
        path = vault.root / "notes" / "should_not_exist.md"
        with pytest.raises(RuntimeError):
            with vault.transaction() as txn:
                txn.write_file(path, "temporary content")
                assert path.exists()  # written during transaction
                msg = "Simulated failure"
                raise RuntimeError(msg)
        assert not path.exists()  # compensated

    def test_modified_file_restored_on_error(self, vault: Vault) -> None:
        path = vault.root / "notes" / "existing.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("original content")
        with pytest.raises(RuntimeError):
            with vault.transaction() as txn:
                txn.write_file(path, "modified content")
                assert path.read_text() == "modified content"
                msg = "Simulated failure"
                raise RuntimeError(msg)
        assert path.read_text() == "original content"  # restored

    def test_combined_rollback(self, vault: Vault) -> None:
        """Both DB and file roll back together."""
        path = vault.root / "notes" / "ztl_combo1234.md"
        with pytest.raises(RuntimeError):
            with vault.transaction() as txn:
                txn.conn.execute(
                    insert(nodes).values(
                        id="ztl_combo1234",
                        title="Combo",
                        type="note",
                        status="draft",
                        path="notes/ztl_combo1234.md",
                        created="2025-01-15",
                        modified="2025-01-15",
                    )
                )
                txn.write_file(path, "combo content")
                msg = "Simulated failure"
                raise RuntimeError(msg)
        assert not path.exists()
        with vault.engine.connect() as conn:
            row = conn.execute(select(nodes.c.id).where(nodes.c.id == "ztl_combo1234")).first()
            assert row is None

    def test_multiple_files_all_compensated(self, vault: Vault) -> None:
        paths = [vault.root / "notes" / f"file{i}.md" for i in range(3)]
        with pytest.raises(RuntimeError):
            with vault.transaction() as txn:
                for p in paths:
                    txn.write_file(p, f"content {p.name}")
                msg = "Simulated failure"
                raise RuntimeError(msg)
        for p in paths:
            assert not p.exists()


# ---------------------------------------------------------------------------
# Graph invalidation
# ---------------------------------------------------------------------------


class TestGraphInvalidation:
    def test_graph_invalidated_on_success(self, vault: Vault) -> None:
        _ = vault.graph.graph  # build graph
        assert vault.graph._graph is not None
        with vault.transaction() as _txn:
            pass  # empty transaction
        assert vault.graph._graph is None  # invalidated

    def test_graph_invalidated_on_failure(self, vault: Vault) -> None:
        _ = vault.graph.graph
        assert vault.graph._graph is not None
        with pytest.raises(RuntimeError):
            with vault.transaction() as _txn:
                msg = "fail"
                raise RuntimeError(msg)
        assert vault.graph._graph is None  # still invalidated


# ---------------------------------------------------------------------------
# VaultTransaction helpers
# ---------------------------------------------------------------------------


class TestVaultTransactionHelpers:
    def test_read_file(self, vault: Vault) -> None:
        path = vault.root / "test.txt"
        path.write_text("read me")
        with vault.transaction() as txn:
            content = txn.read_file(path)
        assert content == "read me"

    def test_read_content(self, vault: Vault) -> None:
        path = vault.root / "notes" / "note.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("---\nid: ztl_test\ntitle: Test\n---\nBody here.\n")
        with vault.transaction() as txn:
            fm, body = txn.read_content(path)
        assert fm["id"] == "ztl_test"
        assert "Body here." in body

    def test_resolve_path(self, vault: Vault) -> None:
        with vault.transaction() as txn:
            path = txn.resolve_path("note", "ztl_abc12345")
        assert path == vault.root / "notes" / "ztl_abc12345.md"

    def test_resolve_path_with_topic(self, vault: Vault) -> None:
        with vault.transaction() as txn:
            path = txn.resolve_path("note", "ztl_abc12345", topic="math")
        assert path == vault.root / "notes" / "math" / "ztl_abc12345.md"
