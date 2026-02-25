"""Tests for CheckService — integrity checking, fix, rebuild, rollback."""

from __future__ import annotations

from sqlalchemy import delete, insert, select, text

from tests.conftest import create_note, create_reference
from ztlctl.domain.content import parse_frontmatter, render_frontmatter
from ztlctl.infrastructure.database.schema import edges, node_tags, nodes, tags_registry
from ztlctl.infrastructure.vault import Vault
from ztlctl.services.check import CheckService

# ---------------------------------------------------------------------------
# check() — read-only integrity reporting
# ---------------------------------------------------------------------------


class TestCheckCleanVault:
    def test_empty_vault_zero_issues(self, vault: Vault) -> None:
        """A fresh vault with no content should report zero issues."""
        svc = CheckService(vault)
        result = svc.check()
        assert result.ok
        assert result.data["count"] == 0
        assert result.data["issues"] == []

    def test_clean_vault_after_create(self, vault: Vault) -> None:
        """Vault with properly created content should have no errors.

        Isolated node warnings are expected for unlinked notes.
        """
        create_note(vault, "Note A", tags=["domain/scope"])
        create_note(vault, "Note B", tags=["area/test"])
        svc = CheckService(vault)
        result = svc.check()
        assert result.ok
        errors = [i for i in result.data["issues"] if i["severity"] == "error"]
        assert len(errors) == 0


class TestCheckDbFileConsistency:
    def test_orphan_db_row_detected(self, vault: Vault) -> None:
        """DB row with no corresponding file → detected as error."""
        data = create_note(vault, "Ghost Note")
        # Delete the file
        (vault.root / data["path"]).unlink()

        result = CheckService(vault).check()
        assert result.data["count"] >= 1
        issues = result.data["issues"]
        orphan = [i for i in issues if i["node_id"] == data["id"] and "missing" in i["message"]]
        assert len(orphan) == 1
        assert orphan[0]["category"] == "db_file_consistency"
        assert orphan[0]["severity"] == "error"

    def test_orphan_file_detected(self, vault: Vault) -> None:
        """File on disk with no DB row → detected as error."""
        # Write a file directly (bypassing CreateService)
        orphan_path = vault.root / "notes" / "ztl_orphan00.md"
        fm = {"id": "ztl_orphan00", "type": "note", "status": "draft", "title": "Orphan"}
        orphan_path.write_text(render_frontmatter(fm, "body text"), encoding="utf-8")

        result = CheckService(vault).check()
        issues = result.data["issues"]
        orphan = [i for i in issues if "no DB row" in i["message"]]
        assert len(orphan) == 1
        assert orphan[0]["category"] == "db_file_consistency"

    def test_title_mismatch_detected(self, vault: Vault) -> None:
        """Title mismatch between DB and file → warning."""
        data = create_note(vault, "Original Title")
        # Modify file title directly
        file_path = vault.root / data["path"]
        fm, body = parse_frontmatter(file_path.read_text(encoding="utf-8"))
        fm["title"] = "Changed Title"
        file_path.write_text(render_frontmatter(fm, body), encoding="utf-8")

        result = CheckService(vault).check()
        issues = result.data["issues"]
        mismatch = [i for i in issues if "Title mismatch" in i["message"]]
        assert len(mismatch) == 1
        assert mismatch[0]["severity"] == "warning"

    def test_status_mismatch_detected(self, vault: Vault) -> None:
        """Status mismatch between DB and file → warning."""
        data = create_note(vault, "Status Note")
        file_path = vault.root / data["path"]
        fm, body = parse_frontmatter(file_path.read_text(encoding="utf-8"))
        fm["status"] = "linked"
        file_path.write_text(render_frontmatter(fm, body), encoding="utf-8")

        result = CheckService(vault).check()
        issues = result.data["issues"]
        mismatch = [i for i in issues if "Status mismatch" in i["message"]]
        assert len(mismatch) == 1


class TestCheckSchemaIntegrity:
    def test_dangling_edge_detected(self, vault: Vault) -> None:
        """Edge referencing nonexistent node → error."""
        data = create_note(vault, "Source Node")
        # Temporarily disable FK checks to insert corrupted data
        with vault.engine.begin() as conn:
            conn.execute(text("PRAGMA foreign_keys=OFF"))
            conn.execute(
                text(
                    "INSERT INTO edges (source_id, target_id, edge_type, "
                    "source_layer, weight, created) "
                    "VALUES (:src, :tgt, :etype, :layer, :w, :c)"
                ),
                {
                    "src": data["id"],
                    "tgt": "ztl_nonexist",
                    "etype": "relates",
                    "layer": "body",
                    "w": 1.0,
                    "c": "2025-01-01",
                },
            )
            conn.execute(text("PRAGMA foreign_keys=ON"))

        result = CheckService(vault).check()
        issues = result.data["issues"]
        dangling = [
            i for i in issues if i["category"] == "schema_integrity" and "target" in i["message"]
        ]
        assert len(dangling) >= 1

    def test_fts_desync_detected(self, vault: Vault) -> None:
        """Node missing from FTS5 → error."""
        data = create_note(vault, "FTS Note")
        # Delete FTS row directly
        with vault.engine.begin() as conn:
            conn.execute(
                text("DELETE FROM nodes_fts WHERE id = :id"),
                {"id": data["id"]},
            )

        result = CheckService(vault).check()
        issues = result.data["issues"]
        fts = [i for i in issues if "FTS5" in i["message"]]
        assert len(fts) == 1
        assert fts[0]["category"] == "schema_integrity"

    def test_orphan_node_tag_detected(self, vault: Vault) -> None:
        """node_tags entry referencing nonexistent node → error."""
        with vault.engine.begin() as conn:
            conn.execute(text("PRAGMA foreign_keys=OFF"))
            conn.execute(
                insert(tags_registry).values(
                    tag="test/orphan", domain="test", scope="orphan", created="2025-01-01"
                )
            )
            conn.execute(insert(node_tags).values(node_id="ztl_noexist", tag="test/orphan"))
            conn.execute(text("PRAGMA foreign_keys=ON"))

        result = CheckService(vault).check()
        issues = result.data["issues"]
        orphan_tag = [
            i for i in issues if i["category"] == "schema_integrity" and "node_tags" in i["message"]
        ]
        assert len(orphan_tag) >= 1


class TestCheckGraphHealth:
    def test_self_referencing_edge_detected(self, vault: Vault) -> None:
        """Self-loop edge → error."""
        data = create_note(vault, "Self Linker")
        with vault.engine.begin() as conn:
            conn.execute(
                insert(edges).values(
                    source_id=data["id"],
                    target_id=data["id"],
                    edge_type="relates",
                    source_layer="body",
                    weight=1.0,
                    created="2025-01-01",
                )
            )

        result = CheckService(vault).check()
        issues = result.data["issues"]
        self_ref = [i for i in issues if "Self-referencing" in i["message"]]
        assert len(self_ref) == 1
        assert self_ref[0]["category"] == "graph_health"

    def test_isolated_node_warning(self, vault: Vault) -> None:
        """Node with zero connections → warning."""
        create_note(vault, "Lonely Node")

        result = CheckService(vault).check()
        issues = result.data["issues"]
        isolated = [i for i in issues if "Isolated" in i["message"]]
        assert len(isolated) >= 1
        assert isolated[0]["severity"] == "warning"


class TestCheckStructuralValidation:
    def test_invalid_id_pattern_detected(self, vault: Vault) -> None:
        """ID that doesn't match expected pattern → error."""
        # Insert a node with a bad ID directly
        with vault.engine.begin() as conn:
            conn.execute(
                insert(nodes).values(
                    id="bad_id",
                    title="Bad ID Node",
                    type="note",
                    status="draft",
                    path="notes/bad_id.md",
                    created="2025-01-01",
                    modified="2025-01-01",
                )
            )
        # Create the file so it doesn't also trigger db_file_consistency
        bad_path = vault.root / "notes" / "bad_id.md"
        fm = {"id": "bad_id", "type": "note", "status": "draft", "title": "Bad ID Node"}
        bad_path.write_text(render_frontmatter(fm, ""), encoding="utf-8")
        # Also insert FTS row to avoid schema_integrity issue
        with vault.engine.begin() as conn:
            conn.execute(
                text("INSERT INTO nodes_fts(id, title, body) VALUES (:id, :title, :body)"),
                {"id": "bad_id", "title": "Bad ID Node", "body": ""},
            )

        result = CheckService(vault).check()
        issues = result.data["issues"]
        bad_id = [i for i in issues if "does not match" in i["message"]]
        assert len(bad_id) >= 1
        assert bad_id[0]["category"] == "structural_validation"

    def test_invalid_status_detected(self, vault: Vault) -> None:
        """Status not in valid set → error."""
        with vault.engine.begin() as conn:
            conn.execute(
                insert(nodes).values(
                    id="ztl_badstat0",
                    title="Bad Status",
                    type="note",
                    status="bogus_status",
                    path="notes/ztl_badstat0.md",
                    created="2025-01-01",
                    modified="2025-01-01",
                )
            )
        bad_path = vault.root / "notes" / "ztl_badstat0.md"
        fm = {"id": "ztl_badstat0", "type": "note", "status": "bogus_status", "title": "Bad Status"}
        bad_path.write_text(render_frontmatter(fm, ""), encoding="utf-8")
        with vault.engine.begin() as conn:
            conn.execute(
                text("INSERT INTO nodes_fts(id, title, body) VALUES (:id, :title, :body)"),
                {"id": "ztl_badstat0", "title": "Bad Status", "body": ""},
            )

        result = CheckService(vault).check()
        issues = result.data["issues"]
        bad_status = [i for i in issues if "Invalid status" in i["message"]]
        assert len(bad_status) >= 1

    def test_tag_format_warning(self, vault: Vault) -> None:
        """Tag without domain/scope format → warning."""
        create_note(vault, "Unscoped Tag Note", tags=["noscopeformat"])

        result = CheckService(vault).check()
        issues = result.data["issues"]
        tag_warn = [
            i
            for i in issues
            if i["category"] == "structural_validation" and "domain/scope" in i["message"]
        ]
        assert len(tag_warn) >= 1
        assert tag_warn[0]["severity"] == "warning"


# ---------------------------------------------------------------------------
# fix() — automatic repair
# ---------------------------------------------------------------------------


class TestFix:
    def test_fix_removes_orphan_db_row(self, vault: Vault) -> None:
        """Fix removes DB rows whose files are gone."""
        data = create_note(vault, "To Be Deleted")
        (vault.root / data["path"]).unlink()

        svc = CheckService(vault)
        result = svc.fix()
        assert result.ok
        assert any("Removed orphan DB row" in f for f in result.data["fixes"])

        # Verify node is gone from DB
        with vault.engine.connect() as conn:
            row = conn.execute(select(nodes.c.id).where(nodes.c.id == data["id"])).first()
            assert row is None

    def test_fix_removes_dangling_edges(self, vault: Vault) -> None:
        """Fix removes edges to nonexistent nodes."""
        data = create_note(vault, "Edge Source")
        with vault.engine.begin() as conn:
            conn.execute(text("PRAGMA foreign_keys=OFF"))
            conn.execute(
                text(
                    "INSERT INTO edges (source_id, target_id, edge_type, "
                    "source_layer, weight, created) "
                    "VALUES (:src, :tgt, :etype, :layer, :w, :c)"
                ),
                {
                    "src": data["id"],
                    "tgt": "ztl_gone0000",
                    "etype": "relates",
                    "layer": "body",
                    "w": 1.0,
                    "c": "2025-01-01",
                },
            )
            conn.execute(text("PRAGMA foreign_keys=ON"))

        result = CheckService(vault).fix()
        assert result.ok
        assert any("dangling edge" in f for f in result.data["fixes"])

    def test_fix_reinserts_missing_fts(self, vault: Vault) -> None:
        """Fix re-inserts missing FTS5 rows."""
        data = create_note(vault, "FTS Recovery")
        with vault.engine.begin() as conn:
            conn.execute(
                text("DELETE FROM nodes_fts WHERE id = :id"),
                {"id": data["id"]},
            )

        result = CheckService(vault).fix()
        assert result.ok
        assert any("FTS5" in f for f in result.data["fixes"])

        # Verify FTS is back
        with vault.engine.connect() as conn:
            row = conn.execute(
                text("SELECT id FROM nodes_fts WHERE id = :id"),
                {"id": data["id"]},
            ).first()
            assert row is not None

    def test_fix_resyncs_title_from_file(self, vault: Vault) -> None:
        """Fix updates DB title to match file (files are truth)."""
        data = create_note(vault, "Old Title")
        file_path = vault.root / data["path"]
        fm, body = parse_frontmatter(file_path.read_text(encoding="utf-8"))
        fm["title"] = "New Title"
        file_path.write_text(render_frontmatter(fm, body), encoding="utf-8")

        result = CheckService(vault).fix()
        assert result.ok

        with vault.engine.connect() as conn:
            row = conn.execute(select(nodes.c.title).where(nodes.c.id == data["id"])).one()
            assert row.title == "New Title"

    def test_fix_creates_backup(self, vault: Vault) -> None:
        """Fix creates a DB backup before modifying anything."""
        create_note(vault, "Backup Test")
        CheckService(vault).fix()

        backups = list((vault.root / ".ztlctl" / "backups").glob("ztlctl-*.db"))
        assert len(backups) >= 1

    def test_aggressive_reindexes_edges(self, vault: Vault) -> None:
        """Aggressive fix re-indexes all edges from files."""
        data_a = create_note(vault, "Node A")
        data_b = create_note(vault, "Node B")

        # Create a frontmatter link from A to B in the file
        path_a = vault.root / data_a["path"]
        fm, body = parse_frontmatter(path_a.read_text(encoding="utf-8"))
        fm["links"] = {"relates": [data_b["id"]]}
        path_a.write_text(render_frontmatter(fm, body), encoding="utf-8")

        result = CheckService(vault).fix(level="aggressive")
        assert result.ok
        assert any("Re-indexed" in f for f in result.data["fixes"])

        # Verify edge exists
        with vault.engine.connect() as conn:
            edge = conn.execute(
                select(edges.c.source_id).where(
                    edges.c.source_id == data_a["id"],
                    edges.c.target_id == data_b["id"],
                )
            ).first()
            assert edge is not None


# ---------------------------------------------------------------------------
# rebuild() — full DB reconstruction from files
# ---------------------------------------------------------------------------


class TestRebuild:
    def test_rebuild_recovers_all_nodes(self, vault: Vault) -> None:
        """Rebuild reconstructs DB from files."""
        data_a = create_note(vault, "Rebuild A", tags=["domain/scope"])
        data_b = create_reference(vault, "Rebuild B")

        # Wipe the DB manually (but leave files)
        with vault.engine.begin() as conn:
            conn.execute(text("DELETE FROM nodes_fts"))
            conn.execute(delete(node_tags))
            conn.execute(delete(edges))
            conn.execute(delete(nodes))

        result = CheckService(vault).rebuild()
        assert result.ok
        assert result.data["nodes_indexed"] == 2

        # Verify nodes exist again
        with vault.engine.connect() as conn:
            row_a = conn.execute(select(nodes.c.id).where(nodes.c.id == data_a["id"])).first()
            row_b = conn.execute(select(nodes.c.id).where(nodes.c.id == data_b["id"])).first()
            assert row_a is not None
            assert row_b is not None

    def test_rebuild_recovers_tags(self, vault: Vault) -> None:
        """Rebuild recovers tags from file frontmatter."""
        data = create_note(vault, "Tagged Rebuild", tags=["ai/nlp"])

        with vault.engine.begin() as conn:
            conn.execute(text("DELETE FROM nodes_fts"))
            conn.execute(delete(node_tags))
            conn.execute(delete(edges))
            conn.execute(delete(nodes))

        result = CheckService(vault).rebuild()
        assert result.ok
        assert result.data["tags_found"] >= 1

        with vault.engine.connect() as conn:
            tag_rows = conn.execute(
                select(node_tags.c.tag).where(node_tags.c.node_id == data["id"])
            ).fetchall()
            assert any(r.tag == "ai/nlp" for r in tag_rows)

    def test_rebuild_recovers_edges(self, vault: Vault) -> None:
        """Rebuild recovers frontmatter edges between existing nodes."""
        data_a = create_note(vault, "Edge Source")
        data_b = create_note(vault, "Edge Target")

        # Add a frontmatter link from A -> B
        path_a = vault.root / data_a["path"]
        fm, body = parse_frontmatter(path_a.read_text(encoding="utf-8"))
        fm["links"] = {"relates": [data_b["id"]]}
        path_a.write_text(render_frontmatter(fm, body), encoding="utf-8")

        with vault.engine.begin() as conn:
            conn.execute(text("DELETE FROM nodes_fts"))
            conn.execute(delete(node_tags))
            conn.execute(delete(edges))
            conn.execute(delete(nodes))

        result = CheckService(vault).rebuild()
        assert result.ok
        assert result.data["edges_created"] >= 1

    def test_rebuild_preserves_id_counters(self, vault: Vault) -> None:
        """Rebuild should NOT reset sequential ID counters."""
        from ztlctl.infrastructure.database.schema import id_counters

        # Check current counter value
        with vault.engine.connect() as conn:
            before = conn.execute(
                select(id_counters.c.next_value).where(id_counters.c.type_prefix == "LOG-")
            ).scalar()

        CheckService(vault).rebuild()

        with vault.engine.connect() as conn:
            after = conn.execute(
                select(id_counters.c.next_value).where(id_counters.c.type_prefix == "LOG-")
            ).scalar()

        assert after == before

    def test_rebuild_creates_backup(self, vault: Vault) -> None:
        """Rebuild creates a backup before starting."""
        create_note(vault, "Backup Before Rebuild")
        CheckService(vault).rebuild()

        backups = list((vault.root / ".ztlctl" / "backups").glob("ztlctl-*.db"))
        assert len(backups) >= 1

    def test_rebuild_recovers_fts(self, vault: Vault) -> None:
        """Rebuild re-creates FTS5 entries."""
        data = create_note(vault, "FTS Rebuild Test")

        with vault.engine.begin() as conn:
            conn.execute(text("DELETE FROM nodes_fts"))
            conn.execute(delete(node_tags))
            conn.execute(delete(edges))
            conn.execute(delete(nodes))

        CheckService(vault).rebuild()

        with vault.engine.connect() as conn:
            rows = conn.execute(
                text("SELECT id FROM nodes_fts WHERE title MATCH :q"),
                {"q": "Rebuild"},
            ).fetchall()
            assert any(r[0] == data["id"] for r in rows)

    def test_rebuild_warns_on_bad_file(self, vault: Vault) -> None:
        """Rebuild warns when a file can't be parsed."""
        # Create an unparseable file
        bad_path = vault.root / "notes" / "bad_file.md"
        bad_path.write_text("not valid frontmatter", encoding="utf-8")

        result = CheckService(vault).rebuild()
        assert result.ok
        assert any("missing 'id'" in w or "parse" in w.lower() for w in result.warnings)


# ---------------------------------------------------------------------------
# rollback() — restore from backup
# ---------------------------------------------------------------------------


class TestRollback:
    def test_rollback_no_backups(self, vault: Vault) -> None:
        """Rollback with no backup files → error."""
        result = CheckService(vault).rollback()
        assert not result.ok
        assert result.error is not None
        assert result.error.code == "NO_BACKUPS"

    def test_rollback_restores_backup(self, vault: Vault) -> None:
        """Rollback copies the latest backup over the DB."""
        # Create initial content
        create_note(vault, "Before Backup")

        # Create a backup
        svc = CheckService(vault)
        backup_path = svc._backup_db()
        assert backup_path.exists()

        # Create more content after backup
        create_note(vault, "After Backup")

        # Rollback
        result = svc.rollback()
        assert result.ok
        assert "backup_file" in result.data

    def test_rollback_returns_backup_filename(self, vault: Vault) -> None:
        """Rollback result includes the backup filename."""
        create_note(vault, "Content")
        svc = CheckService(vault)
        svc._backup_db()

        result = svc.rollback()
        assert result.ok
        assert result.data["backup_file"].startswith("ztlctl-")
        assert result.data["backup_file"].endswith(".db")


# ---------------------------------------------------------------------------
# Backup pruning
# ---------------------------------------------------------------------------


class TestBackupPruning:
    def test_prune_exceeding_max_count(self, vault: Vault) -> None:
        """Backups exceeding max_count are pruned (oldest removed)."""
        svc = CheckService(vault)
        backup_dir = vault.root / ".ztlctl" / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)

        # Create more backups than max_count allows
        max_count = vault.settings.check.backup_max_count
        db_path = vault.root / ".ztlctl" / "ztlctl.db"
        for i in range(max_count + 3):
            bp = backup_dir / f"ztlctl-2025010{i:02d}T000000.db"
            bp.write_bytes(db_path.read_bytes())

        svc._prune_backups(backup_dir)
        remaining = list(backup_dir.glob("ztlctl-*.db"))
        assert len(remaining) == max_count
