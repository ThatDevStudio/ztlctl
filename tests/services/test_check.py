"""Tests for CheckService — integrity checking, fix, rebuild, rollback."""

from __future__ import annotations

from sqlalchemy import delete, insert, select, text

from tests.conftest import create_note, create_reference, start_session
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
        assert result.data["error_count"] == 0
        assert result.data["warning_count"] == 0
        assert result.data["healthy"] is True
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

    def test_errors_only_filter_hides_warning_only_issues(self, vault: Vault) -> None:
        create_note(vault, "Warning Note", tags=["unscoped"])

        result = CheckService(vault).check(min_severity="error")

        assert result.ok
        assert result.data["count"] == 0
        assert result.data["error_count"] == 0
        assert result.data["warning_count"] == 0
        assert result.data["healthy"] is True
        assert result.data["issues"] == []

    def test_warning_only_vault_reports_healthy(self, vault: Vault) -> None:
        create_note(vault, "Warning Note", tags=["unscoped"])

        result = CheckService(vault).check()

        assert result.ok
        assert result.data["count"] > 0
        assert result.data["error_count"] == 0
        assert result.data["warning_count"] == result.data["count"]
        assert result.data["healthy"] is True

    def test_mixed_warning_and_error_vault_reports_unhealthy(self, vault: Vault) -> None:
        create_note(vault, "Warning Note", tags=["unscoped"])
        broken = create_note(vault, "Broken Note", tags=["domain/scope"])
        (vault.root / broken["path"]).unlink()

        result = CheckService(vault).check()

        assert result.ok
        assert result.data["count"] >= 2
        assert result.data["error_count"] >= 1
        assert result.data["warning_count"] >= 1
        assert result.data["healthy"] is False


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

    def test_session_log_skipped_in_consistency_check(self, vault: Vault) -> None:
        """Session log nodes (DB-only) are skipped in file consistency checks."""
        data = start_session(vault, "Clean Session")

        result = CheckService(vault).check()

        issues = [
            issue
            for issue in result.data["issues"]
            if issue["node_id"] == data["id"] and issue["category"] == "db_file_consistency"
        ]
        assert len(issues) == 0

    def test_closed_session_log_skipped_in_consistency_check(self, vault: Vault) -> None:
        """Closed session log nodes are also skipped (DB-only)."""
        data = start_session(vault, "Closed Session")
        from ztlctl.services.session import SessionService

        SessionService(vault).close()
        result = CheckService(vault).check()

        issues = [
            issue
            for issue in result.data["issues"]
            if issue["node_id"] == data["id"] and issue["category"] == "db_file_consistency"
        ]
        assert len(issues) == 0

    def test_fix_skips_log_nodes_in_resync(self, vault: Vault) -> None:
        """fix() does NOT modify log-type nodes (they're skipped in resync)."""
        data = start_session(vault, "Repair Session")
        with vault.engine.begin() as conn:
            conn.execute(
                nodes.update()
                .where(nodes.c.id == data["id"])
                .values(title="Wrong Title", status="closed", topic="wrong-topic")
            )

        result = CheckService(vault).fix()

        assert result.ok
        # Log nodes are skipped — no fix should reference this session
        assert not any(data["id"] in fix for fix in result.data["fixes"])
        # DB row remains as-is (not resynced from file)
        with vault.engine.connect() as conn:
            row = conn.execute(
                select(nodes.c.title, nodes.c.status, nodes.c.topic).where(nodes.c.id == data["id"])
            ).first()
        assert row is not None
        assert row.title == "Wrong Title"
        assert row.status == "closed"
        assert row.topic == "wrong-topic"


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


class TestCheckGardenHealth:
    def test_aging_seed_detected(self, vault: Vault) -> None:
        """Seed note older than seed_age_warning_days → warning."""
        data = create_note(vault, "Old Seed")
        # Set maturity to seed and backdate the created field
        with vault.engine.begin() as conn:
            conn.execute(
                nodes.update()
                .where(nodes.c.id == data["id"])
                .values(maturity="seed", created="2025-01-01")
            )

        result = CheckService(vault).check()
        issues = result.data["issues"]
        aging = [i for i in issues if "Aging seed" in i["message"]]
        assert len(aging) == 1
        assert aging[0]["category"] == "garden_health"
        assert aging[0]["severity"] == "warning"

    def test_fresh_seed_not_reported(self, vault: Vault) -> None:
        """Seed created today → no aging warning."""
        from datetime import UTC, datetime

        data = create_note(vault, "Fresh Seed")
        today = datetime.now(UTC).strftime("%Y-%m-%d")
        with vault.engine.begin() as conn:
            conn.execute(
                nodes.update()
                .where(nodes.c.id == data["id"])
                .values(maturity="seed", created=today)
            )

        result = CheckService(vault).check()
        issues = result.data["issues"]
        aging = [i for i in issues if "Aging seed" in i["message"]]
        assert len(aging) == 0

    def test_evergreen_ready_candidate_reported(self, vault: Vault) -> None:
        """Budding note meeting both thresholds → advisory warning."""
        data_a = create_note(vault, "Candidate Note")
        # Create enough bidirectional links (default threshold = 3)
        targets = []
        for i in range(3):
            td = create_note(vault, f"Linked Note {i}")
            targets.append(td)
        # Set maturity and create bidirectional edges
        with vault.engine.begin() as conn:
            conn.execute(
                nodes.update().where(nodes.c.id == data_a["id"]).values(maturity="budding")
            )
            for td in targets:
                conn.execute(
                    insert(edges).values(
                        source_id=data_a["id"],
                        target_id=td["id"],
                        edge_type="relates",
                        source_layer="body",
                        weight=1.0,
                        created="2025-01-01",
                    )
                )
                conn.execute(
                    insert(edges).values(
                        source_id=td["id"],
                        target_id=data_a["id"],
                        edge_type="relates",
                        source_layer="body",
                        weight=1.0,
                        created="2025-01-01",
                    )
                )
        # Add enough key_points to frontmatter (default threshold = 5)
        file_path = vault.root / data_a["path"]
        fm, body = parse_frontmatter(file_path.read_text(encoding="utf-8"))
        fm["key_points"] = ["point1", "point2", "point3", "point4", "point5"]
        file_path.write_text(render_frontmatter(fm, body), encoding="utf-8")

        result = CheckService(vault).check()
        issues = result.data["issues"]
        evergreen = [i for i in issues if "Evergreen candidate" in i["message"]]
        assert len(evergreen) == 1
        assert evergreen[0]["category"] == "garden_health"

    def test_insufficient_key_points_not_reported(self, vault: Vault) -> None:
        """Enough links but too few key_points → no advisory."""
        data_a = create_note(vault, "Few Points Note")
        targets = []
        for i in range(3):
            td = create_note(vault, f"Link Target {i}")
            targets.append(td)
        with vault.engine.begin() as conn:
            conn.execute(
                nodes.update().where(nodes.c.id == data_a["id"]).values(maturity="budding")
            )
            for td in targets:
                conn.execute(
                    insert(edges).values(
                        source_id=data_a["id"],
                        target_id=td["id"],
                        edge_type="relates",
                        source_layer="body",
                        weight=1.0,
                        created="2025-01-01",
                    )
                )
                conn.execute(
                    insert(edges).values(
                        source_id=td["id"],
                        target_id=data_a["id"],
                        edge_type="relates",
                        source_layer="body",
                        weight=1.0,
                        created="2025-01-01",
                    )
                )
        # Only 2 key_points (threshold is 5)
        file_path = vault.root / data_a["path"]
        fm, body = parse_frontmatter(file_path.read_text(encoding="utf-8"))
        fm["key_points"] = ["point1", "point2"]
        file_path.write_text(render_frontmatter(fm, body), encoding="utf-8")

        result = CheckService(vault).check()
        issues = result.data["issues"]
        evergreen = [i for i in issues if "Evergreen candidate" in i["message"]]
        assert len(evergreen) == 0

    def test_insufficient_links_not_reported(self, vault: Vault) -> None:
        """Enough key_points but too few bidirectional links → no advisory."""
        data_a = create_note(vault, "Few Links Note")
        # Only 1 bidirectional link (threshold is 3)
        td = create_note(vault, "Single Link Target")
        with vault.engine.begin() as conn:
            conn.execute(nodes.update().where(nodes.c.id == data_a["id"]).values(maturity="seed"))
            conn.execute(
                insert(edges).values(
                    source_id=data_a["id"],
                    target_id=td["id"],
                    edge_type="relates",
                    source_layer="body",
                    weight=1.0,
                    created="2025-01-01",
                )
            )
            conn.execute(
                insert(edges).values(
                    source_id=td["id"],
                    target_id=data_a["id"],
                    edge_type="relates",
                    source_layer="body",
                    weight=1.0,
                    created="2025-01-01",
                )
            )
        file_path = vault.root / data_a["path"]
        fm, body = parse_frontmatter(file_path.read_text(encoding="utf-8"))
        fm["key_points"] = ["p1", "p2", "p3", "p4", "p5"]
        file_path.write_text(render_frontmatter(fm, body), encoding="utf-8")

        result = CheckService(vault).check()
        issues = result.data["issues"]
        evergreen = [i for i in issues if "Evergreen candidate" in i["message"]]
        assert len(evergreen) == 0

    def test_archived_note_excluded(self, vault: Vault) -> None:
        """Archived seed → no aging warning."""
        data = create_note(vault, "Archived Seed")
        with vault.engine.begin() as conn:
            conn.execute(
                nodes.update()
                .where(nodes.c.id == data["id"])
                .values(maturity="seed", created="2025-01-01", archived=1)
            )

        result = CheckService(vault).check()
        issues = result.data["issues"]
        aging = [i for i in issues if "Aging seed" in i["message"] and i["node_id"] == data["id"]]
        assert len(aging) == 0


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

    def test_backup_retention_days_prunes_old_backups(self, vault: Vault) -> None:
        """Backups older than retention_days are pruned when max_count is not the binding limit."""
        import time

        svc = CheckService(vault)
        backup_dir = vault.root / ".ztlctl" / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        db_path = vault.root / ".ztlctl" / "ztlctl.db"

        # Create a backup that appears very old (mtime far in the past)
        old_backup = backup_dir / "ztlctl-20200101T000000.db"
        old_backup.write_bytes(db_path.read_bytes())
        # Set mtime to 400 days ago to ensure it's beyond any retention window
        old_mtime = time.time() - (400 * 86400)
        import os

        os.utime(old_backup, (old_mtime, old_mtime))

        # Create a recent backup
        new_backup = backup_dir / "ztlctl-20260101T000000.db"
        new_backup.write_bytes(db_path.read_bytes())

        # Prune — old backup should be removed, new backup kept
        svc._prune_backups(backup_dir)
        remaining = list(backup_dir.glob("ztlctl-*.db"))
        remaining_names = [r.name for r in remaining]

        # Old backup should be pruned (400 days old)
        assert "ztlctl-20200101T000000.db" not in remaining_names
        # New backup should remain
        assert "ztlctl-20260101T000000.db" in remaining_names


class TestDeadLetterCheckReporting:
    """Tests for dead-letter event reporting in CheckService."""

    def test_check_reports_dead_letter_events(self, vault: Vault) -> None:
        """CheckService reports dead-letter WAL rows as info-severity structural issue."""
        from ztlctl.infrastructure.database.schema import event_wal

        # Insert dead_letter WAL rows
        with vault.engine.begin() as conn:
            conn.execute(
                __import__("sqlalchemy", fromlist=["insert"])
                .insert(event_wal)
                .values(
                    hook_name="post_create",
                    payload="{}",
                    status="dead_letter",
                    retries=3,
                    session_id=None,
                    created="2026-01-01T00:00:00+00:00",
                )
            )
            conn.execute(
                __import__("sqlalchemy", fromlist=["insert"])
                .insert(event_wal)
                .values(
                    hook_name="post_update",
                    payload="{}",
                    status="dead_letter",
                    retries=3,
                    session_id=None,
                    created="2026-01-01T00:00:00+00:00",
                )
            )
            conn.execute(
                __import__("sqlalchemy", fromlist=["insert"])
                .insert(event_wal)
                .values(
                    hook_name="post_check",
                    payload="{}",
                    status="dead_letter",
                    retries=3,
                    session_id=None,
                    created="2026-01-01T00:00:00+00:00",
                )
            )

        svc = CheckService(vault)
        # Use min_severity="info" so info issues are included
        result = svc.check(min_severity="info")

        assert result.ok
        dead_letter_issues = [
            i for i in result.data["issues"] if "dead-letter" in i.get("message", "")
        ]
        assert len(dead_letter_issues) == 1
        issue = dead_letter_issues[0]
        assert issue["category"] == "structural_validation"
        assert issue["severity"] == "info"
        assert "3 dead-letter" in issue["message"]
        assert (
            "event purge" in issue["message"].lower()
            or "event_purge" in issue["message"]
            or "ztlctl event purge" in issue["message"].lower()
        )

    def test_check_no_dead_letter_issue_when_none_exist(self, vault: Vault) -> None:
        """CheckService does not report dead-letter issue when WAL has no dead_letter rows."""
        svc = CheckService(vault)
        result = svc.check(min_severity="info")

        assert result.ok
        dead_letter_issues = [
            i for i in result.data["issues"] if "dead-letter" in i.get("message", "")
        ]
        assert len(dead_letter_issues) == 0

    def test_check_dead_letter_filtered_out_at_warning_severity(self, vault: Vault) -> None:
        """Dead-letter info issue is hidden when min_severity='warning'."""
        from ztlctl.infrastructure.database.schema import event_wal

        with vault.engine.begin() as conn:
            conn.execute(
                __import__("sqlalchemy", fromlist=["insert"])
                .insert(event_wal)
                .values(
                    hook_name="post_create",
                    payload="{}",
                    status="dead_letter",
                    retries=3,
                    session_id=None,
                    created="2026-01-01T00:00:00+00:00",
                )
            )

        svc = CheckService(vault)
        result = svc.check(min_severity="warning")

        dead_letter_issues = [
            i for i in result.data["issues"] if "dead-letter" in i.get("message", "")
        ]
        assert len(dead_letter_issues) == 0


class TestRebuildCompleteness:
    """Additional named rebuild tests for plan acceptance criteria."""

    def test_rebuild_completes_with_content(self, vault: Vault) -> None:
        """rebuild() completes successfully and returns correct counts when content exists."""
        # Create several notes and a reference
        data_a = create_note(vault, "Rebuild Content A", tags=["domain/topic"])
        data_b = create_note(vault, "Rebuild Content B", tags=["domain/topic"])
        create_reference(vault, "Rebuild Reference C")

        # Wipe the DB to force rebuild
        with vault.engine.begin() as conn:
            conn.execute(text("DELETE FROM nodes_fts"))
            conn.execute(delete(node_tags))
            conn.execute(delete(edges))
            conn.execute(delete(nodes))

        result = CheckService(vault).rebuild()

        assert result.ok
        assert result.data["nodes_indexed"] == 3

        # Verify all nodes recovered
        with vault.engine.connect() as conn:
            recovered_a = conn.execute(select(nodes.c.id).where(nodes.c.id == data_a["id"])).first()
            recovered_b = conn.execute(select(nodes.c.id).where(nodes.c.id == data_b["id"])).first()
        assert recovered_a is not None
        assert recovered_b is not None


# ---------------------------------------------------------------------------
# Title quality checks (METH-01)
# ---------------------------------------------------------------------------


class TestTitleQualityCheck:
    """Title quality advisory (info severity) under CAT_STRUCTURAL."""

    def test_single_word_title_flagged_at_info(self, vault: Vault) -> None:
        """A 1-word title like 'Notes' is flagged at info severity."""
        create_note(vault, "Notes")
        result = CheckService(vault).check(min_severity="info")
        assert result.ok
        title_issues = [
            i
            for i in result.data["issues"]
            if i.get("category") == "structural_validation"
            and i.get("severity") == "info"
            and "Title quality" in str(i.get("message", ""))
        ]
        assert len(title_issues) >= 1

    def test_two_word_title_flagged_at_info(self, vault: Vault) -> None:
        """A 2-word title like 'My Notes' is flagged at info severity."""
        create_note(vault, "My Notes")
        result = CheckService(vault).check(min_severity="info")
        assert result.ok
        title_issues = [
            i
            for i in result.data["issues"]
            if i.get("category") == "structural_validation"
            and i.get("severity") == "info"
            and "Title quality" in str(i.get("message", ""))
            and "My Notes" in str(i.get("message", ""))
        ]
        assert len(title_issues) == 1

    def test_three_word_title_flagged_at_info(self, vault: Vault) -> None:
        """A 3-word title like 'Notes on X' is flagged at info severity."""
        create_note(vault, "Notes on X")
        result = CheckService(vault).check(min_severity="info")
        assert result.ok
        title_issues = [
            i
            for i in result.data["issues"]
            if i.get("category") == "structural_validation"
            and i.get("severity") == "info"
            and "Title quality" in str(i.get("message", ""))
            and "Notes on X" in str(i.get("message", ""))
        ]
        assert len(title_issues) == 1

    def test_generic_title_untitled_flagged(self, vault: Vault) -> None:
        """Generic title 'Untitled' is flagged at info severity."""
        create_note(vault, "Untitled")
        result = CheckService(vault).check(min_severity="info")
        assert result.ok
        title_issues = [
            i
            for i in result.data["issues"]
            if i.get("category") == "structural_validation"
            and i.get("severity") == "info"
            and "Title quality" in str(i.get("message", ""))
            and "Untitled" in str(i.get("message", ""))
        ]
        assert len(title_issues) == 1

    def test_generic_title_new_note_flagged(self, vault: Vault) -> None:
        """Generic title 'New Note' is flagged at info severity."""
        create_note(vault, "New Note")
        result = CheckService(vault).check(min_severity="info")
        assert result.ok
        title_issues = [
            i
            for i in result.data["issues"]
            if i.get("category") == "structural_validation"
            and i.get("severity") == "info"
            and "Title quality" in str(i.get("message", ""))
            and "New Note" in str(i.get("message", ""))
        ]
        assert len(title_issues) == 1

    def test_descriptive_title_not_flagged(self, vault: Vault) -> None:
        """A descriptive 4+ word title is NOT flagged."""
        create_note(vault, "JWT authentication with refresh token rotation")
        result = CheckService(vault).check(min_severity="info")
        assert result.ok
        title_issues = [
            i
            for i in result.data["issues"]
            if i.get("category") == "structural_validation"
            and i.get("severity") == "info"
            and "Title quality" in str(i.get("message", ""))
            and "JWT authentication with refresh token rotation" in str(i.get("message", ""))
        ]
        assert len(title_issues) == 0

    def test_title_issues_hidden_at_warning_severity(self, vault: Vault) -> None:
        """Title quality issues (info) are NOT visible at default min_severity='warning'."""
        create_note(vault, "Notes")
        result_warning = CheckService(vault).check(min_severity="warning")
        result_info = CheckService(vault).check(min_severity="info")
        assert result_warning.ok
        assert result_info.ok

        warning_title_issues = [
            i
            for i in result_warning.data["issues"]
            if "Title quality" in str(i.get("message", ""))
        ]
        info_title_issues = [
            i for i in result_info.data["issues"] if "Title quality" in str(i.get("message", ""))
        ]
        assert len(warning_title_issues) == 0
        assert len(info_title_issues) >= 1

    def test_title_issue_category_and_severity(self, vault: Vault) -> None:
        """Title quality issues have correct category and severity."""
        from ztlctl.services.check import CAT_STRUCTURAL, SEVERITY_INFO

        create_note(vault, "Draft")
        result = CheckService(vault).check(min_severity="info")
        assert result.ok
        title_issues = [
            i
            for i in result.data["issues"]
            if "Title quality" in str(i.get("message", ""))
            and "Draft" in str(i.get("message", ""))
        ]
        assert len(title_issues) == 1
        assert title_issues[0]["category"] == CAT_STRUCTURAL
        assert title_issues[0]["severity"] == SEVERITY_INFO
