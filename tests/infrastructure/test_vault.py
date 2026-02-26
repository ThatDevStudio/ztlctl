"""Tests for Vault — ACID transaction coordination across DB, files, graph."""

import json
from pathlib import Path

import pytest
from sqlalchemy import insert, select, text

from ztlctl.config.settings import ZtlSettings
from ztlctl.infrastructure.database.schema import edges, node_tags, nodes, tags_registry
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


# ---------------------------------------------------------------------------
# FTS helpers
# ---------------------------------------------------------------------------


def _insert_node(vault: Vault, node_id: str, title: str = "Test") -> None:
    """Helper: insert a bare node row for tests that need one."""
    with vault.transaction() as txn:
        txn.conn.execute(
            insert(nodes).values(
                id=node_id,
                title=title,
                type="note",
                status="draft",
                path=f"notes/{node_id}.md",
                created="2025-01-15",
                modified="2025-01-15",
            )
        )


class TestFTSHelpers:
    def test_upsert_fts_inserts(self, vault: Vault) -> None:
        _insert_node(vault, "ztl_fts00001")
        with vault.transaction() as txn:
            txn.upsert_fts("ztl_fts00001", "Title", "body text")
        with vault.engine.connect() as conn:
            row = conn.execute(
                text("SELECT title, body FROM nodes_fts WHERE id = :id"),
                {"id": "ztl_fts00001"},
            ).first()
            assert row is not None
            assert row.title == "Title"
            assert row.body == "body text"

    def test_upsert_fts_replaces(self, vault: Vault) -> None:
        _insert_node(vault, "ztl_fts00002")
        with vault.transaction() as txn:
            txn.upsert_fts("ztl_fts00002", "Old", "old body")
        with vault.transaction() as txn:
            txn.upsert_fts("ztl_fts00002", "New", "new body")
        with vault.engine.connect() as conn:
            row = conn.execute(
                text("SELECT title, body FROM nodes_fts WHERE id = :id"),
                {"id": "ztl_fts00002"},
            ).first()
            assert row.title == "New"
            assert row.body == "new body"

    def test_delete_fts(self, vault: Vault) -> None:
        _insert_node(vault, "ztl_fts00003")
        with vault.transaction() as txn:
            txn.upsert_fts("ztl_fts00003", "Title", "body")
        with vault.transaction() as txn:
            txn.delete_fts("ztl_fts00003")
        with vault.engine.connect() as conn:
            row = conn.execute(
                text("SELECT id FROM nodes_fts WHERE id = :id"),
                {"id": "ztl_fts00003"},
            ).first()
            assert row is None

    def test_clear_fts(self, vault: Vault) -> None:
        _insert_node(vault, "ztl_fts00004")
        _insert_node(vault, "ztl_fts00005")
        with vault.transaction() as txn:
            txn.upsert_fts("ztl_fts00004", "A", "body a")
            txn.upsert_fts("ztl_fts00005", "B", "body b")
        with vault.transaction() as txn:
            txn.clear_fts()
        with vault.engine.connect() as conn:
            count = conn.execute(text("SELECT count(*) FROM nodes_fts")).scalar()
            assert count == 0

    def test_delete_fts_nonexistent_is_noop(self, vault: Vault) -> None:
        """Deleting a nonexistent FTS entry should not raise."""
        with vault.transaction() as txn:
            txn.delete_fts("ztl_nope1234")  # no error


# ---------------------------------------------------------------------------
# Tag indexing
# ---------------------------------------------------------------------------


class TestTagIndexing:
    def test_index_new_tags(self, vault: Vault) -> None:
        _insert_node(vault, "ztl_tag00001")
        with vault.transaction() as txn:
            count = txn.index_tags("ztl_tag00001", ["math/algebra", "cs/graphs"], "2025-01-15")
        assert count == 2
        with vault.engine.connect() as conn:
            nt = conn.execute(
                select(node_tags.c.tag).where(node_tags.c.node_id == "ztl_tag00001")
            ).fetchall()
            assert {r.tag for r in nt} == {"math/algebra", "cs/graphs"}

    def test_index_existing_tags(self, vault: Vault) -> None:
        """Tags already in registry should be reused, not duplicated."""
        _insert_node(vault, "ztl_tag00002")
        _insert_node(vault, "ztl_tag00003")
        with vault.transaction() as txn:
            txn.index_tags("ztl_tag00002", ["math/algebra"], "2025-01-15")
        with vault.transaction() as txn:
            txn.index_tags("ztl_tag00003", ["math/algebra"], "2025-01-15")
        with vault.engine.connect() as conn:
            reg = conn.execute(
                select(tags_registry.c.tag).where(tags_registry.c.tag == "math/algebra")
            ).fetchall()
            assert len(reg) == 1  # only one registry entry

    def test_index_unscoped_tags(self, vault: Vault) -> None:
        _insert_node(vault, "ztl_tag00004")
        with vault.transaction() as txn:
            txn.index_tags("ztl_tag00004", ["general"], "2025-01-15")
        with vault.engine.connect() as conn:
            reg = conn.execute(
                select(tags_registry).where(tags_registry.c.tag == "general")
            ).first()
            assert reg.domain == "unscoped"
            assert reg.scope == "general"

    def test_index_empty_tags(self, vault: Vault) -> None:
        _insert_node(vault, "ztl_tag00005")
        with vault.transaction() as txn:
            count = txn.index_tags("ztl_tag00005", [], "2025-01-15")
        assert count == 0


# ---------------------------------------------------------------------------
# Edge insertion
# ---------------------------------------------------------------------------


class TestEdgeInsertion:
    def test_basic_insert(self, vault: Vault) -> None:
        _insert_node(vault, "ztl_edge0001", "Source")
        _insert_node(vault, "ztl_edge0002", "Target")
        with vault.transaction() as txn:
            ok = txn.insert_edge(
                "ztl_edge0001", "ztl_edge0002", "relates", "frontmatter", "2025-01-15"
            )
        assert ok is True
        with vault.engine.connect() as conn:
            e = conn.execute(
                select(edges).where(
                    edges.c.source_id == "ztl_edge0001",
                    edges.c.target_id == "ztl_edge0002",
                )
            ).first()
            assert e is not None
            assert e.edge_type == "relates"

    def test_duplicate_check_skips(self, vault: Vault) -> None:
        _insert_node(vault, "ztl_edge0003", "Source")
        _insert_node(vault, "ztl_edge0004", "Target")
        with vault.transaction() as txn:
            txn.insert_edge("ztl_edge0003", "ztl_edge0004", "relates", "body", "2025-01-15")
        with vault.transaction() as txn:
            ok = txn.insert_edge(
                "ztl_edge0003",
                "ztl_edge0004",
                "relates",
                "body",
                "2025-01-15",
                check_duplicate=True,
            )
        assert ok is False

    def test_target_existence_check_skips(self, vault: Vault) -> None:
        _insert_node(vault, "ztl_edge0005")
        with vault.transaction() as txn:
            ok = txn.insert_edge(
                "ztl_edge0005",
                "ztl_nonexist1",
                "relates",
                "frontmatter",
                "2025-01-15",
                check_target_exists=True,
            )
        assert ok is False

    def test_target_existence_check_passes(self, vault: Vault) -> None:
        _insert_node(vault, "ztl_edge0006")
        _insert_node(vault, "ztl_edge0007")
        with vault.transaction() as txn:
            ok = txn.insert_edge(
                "ztl_edge0006",
                "ztl_edge0007",
                "supports",
                "frontmatter",
                "2025-01-15",
                check_target_exists=True,
            )
        assert ok is True


# ---------------------------------------------------------------------------
# Wikilink resolution
# ---------------------------------------------------------------------------


class TestWikilinkResolution:
    def test_title_match(self, vault: Vault) -> None:
        _insert_node(vault, "ztl_wiki0001", "Quantum Computing")
        with vault.transaction() as txn:
            result = txn.resolve_wikilink("Quantum Computing")
        assert result == "ztl_wiki0001"

    def test_alias_match(self, vault: Vault) -> None:
        with vault.transaction() as txn:
            txn.conn.execute(
                insert(nodes).values(
                    id="ztl_wiki0002",
                    title="Machine Learning",
                    type="note",
                    status="draft",
                    path="notes/ztl_wiki0002.md",
                    aliases=json.dumps(["ML", "Deep Learning"]),
                    created="2025-01-15",
                    modified="2025-01-15",
                )
            )
        with vault.transaction() as txn:
            result = txn.resolve_wikilink("ML")
        assert result == "ztl_wiki0002"

    def test_id_match(self, vault: Vault) -> None:
        _insert_node(vault, "ztl_wiki0003", "Something")
        with vault.transaction() as txn:
            result = txn.resolve_wikilink("ztl_wiki0003")
        assert result == "ztl_wiki0003"

    def test_no_match_returns_none(self, vault: Vault) -> None:
        with vault.transaction() as txn:
            result = txn.resolve_wikilink("Nonexistent Note")
        assert result is None


# ---------------------------------------------------------------------------
# Link indexing
# ---------------------------------------------------------------------------


class TestLinkIndexing:
    def test_frontmatter_links(self, vault: Vault) -> None:
        _insert_node(vault, "ztl_link0001", "Source")
        _insert_node(vault, "ztl_link0002", "Target A")
        _insert_node(vault, "ztl_link0003", "Target B")
        with vault.transaction() as txn:
            count = txn.index_links(
                "ztl_link0001",
                {"relates": ["ztl_link0002"], "supports": ["ztl_link0003"]},
                "No wikilinks here.",
                "2025-01-15",
            )
        assert count == 2

    def test_body_wikilinks(self, vault: Vault) -> None:
        _insert_node(vault, "ztl_link0004", "Source")
        _insert_node(vault, "ztl_link0005", "My Target")
        with vault.transaction() as txn:
            count = txn.index_links(
                "ztl_link0004",
                {},
                "See [[My Target]] for details.",
                "2025-01-15",
            )
        assert count == 1
        with vault.engine.connect() as conn:
            e = conn.execute(select(edges).where(edges.c.source_id == "ztl_link0004")).first()
            assert e.target_id == "ztl_link0005"
            assert e.edge_type == "relates"

    def test_combined_links(self, vault: Vault) -> None:
        """Frontmatter + body wikilinks indexed together."""
        _insert_node(vault, "ztl_link0006", "Source")
        _insert_node(vault, "ztl_link0007", "FM Target")
        _insert_node(vault, "ztl_link0008", "Wiki Target")
        with vault.transaction() as txn:
            count = txn.index_links(
                "ztl_link0006",
                {"relates": ["ztl_link0007"]},
                "Also see [[Wiki Target]].",
                "2025-01-15",
            )
        assert count == 2
