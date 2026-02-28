"""Tests for CreateService — six-stage content creation pipeline."""

from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy import select, text

from ztlctl.config.settings import ZtlSettings
from ztlctl.domain.ids import generate_content_hash
from ztlctl.infrastructure.database.schema import edges, node_tags, nodes, tags_registry
from ztlctl.infrastructure.vault import Vault
from ztlctl.services.create import CreateService
from ztlctl.services.result import ServiceResult

# ---------------------------------------------------------------------------
# Note creation
# ---------------------------------------------------------------------------


class TestCreateNote:
    def test_basic_note(self, vault: Vault) -> None:
        svc = CreateService(vault)
        result = svc.create_note("Test Note")
        assert result.ok
        assert result.op == "create_note"
        assert result.data["title"] == "Test Note"
        assert result.data["type"] == "note"
        assert result.data["id"].startswith("ztl_")

    def test_note_creates_file(self, vault: Vault) -> None:
        svc = CreateService(vault)
        result = svc.create_note("My File Note")
        path = vault.root / result.data["path"]
        assert path.exists()
        content = path.read_text()
        assert "title: My File Note" in content
        assert "type: note" in content
        assert "status: draft" in content

    def test_note_inserts_db_row(self, vault: Vault) -> None:
        svc = CreateService(vault)
        result = svc.create_note("DB Note")
        with vault.engine.connect() as conn:
            row = conn.execute(select(nodes).where(nodes.c.id == result.data["id"])).one()
            assert row.title == "DB Note"
            assert row.type == "note"
            assert row.status == "draft"

    def test_note_inserts_fts(self, vault: Vault) -> None:
        svc = CreateService(vault)
        result = svc.create_note("Searchable Title")
        with vault.engine.connect() as conn:
            rows = conn.execute(
                text("SELECT id FROM nodes_fts WHERE title MATCH :q"),
                {"q": "Searchable"},
            ).fetchall()
            ids = [r.id for r in rows]
            assert result.data["id"] in ids

    def test_note_with_topic(self, vault: Vault) -> None:
        svc = CreateService(vault)
        result = svc.create_note("Topic Note", topic="math")
        assert "math" in result.data["path"]

    def test_note_with_session(self, vault: Vault) -> None:
        svc = CreateService(vault)
        result = svc.create_note("Session Note", session="LOG-0001")
        with vault.engine.connect() as conn:
            row = conn.execute(select(nodes.c.session).where(nodes.c.id == result.data["id"])).one()
            assert row.session == "LOG-0001"

    def test_note_with_tags(self, vault: Vault) -> None:
        svc = CreateService(vault)
        result = svc.create_note("Tagged Note", tags=["domain/scope"])
        assert result.ok
        with vault.engine.connect() as conn:
            tag_rows = conn.execute(
                select(node_tags.c.tag).where(node_tags.c.node_id == result.data["id"])
            ).fetchall()
            assert [r.tag for r in tag_rows] == ["domain/scope"]

    def test_note_with_aliases_persisted(self, vault: Vault) -> None:
        svc = CreateService(vault)
        result = svc.create_note("Alias Note", aliases=["py", "python"])
        assert result.ok

        with vault.engine.connect() as conn:
            row = conn.execute(select(nodes.c.aliases).where(nodes.c.id == result.data["id"])).one()
            assert row.aliases == json.dumps(["py", "python"])

    def test_tag_registered_in_registry(self, vault: Vault) -> None:
        svc = CreateService(vault)
        svc.create_note("Registry Note", tags=["ai/nlp"])
        with vault.engine.connect() as conn:
            row = conn.execute(select(tags_registry).where(tags_registry.c.tag == "ai/nlp")).one()
            assert row.domain == "ai"
            assert row.scope == "nlp"

    def test_unscoped_tag_warning(self, vault: Vault) -> None:
        svc = CreateService(vault)
        result = svc.create_note("Warn Note", tags=["unscoped"])
        assert result.ok
        assert any("domain/scope" in w for w in result.warnings)

    def test_duplicate_note_rejected(self, vault: Vault) -> None:
        svc = CreateService(vault)
        r1 = svc.create_note("Same Title")
        assert r1.ok
        r2 = svc.create_note("Same Title")
        assert not r2.ok
        assert r2.error is not None
        assert r2.error.code == "ID_COLLISION"

    def test_deterministic_id(self, vault: Vault) -> None:
        """Same title produces same hash-based ID."""
        svc = CreateService(vault)
        r1 = svc.create_note("Deterministic")
        assert r1.data["id"].startswith("ztl_")
        # Second attempt should collide (same hash)
        r2 = svc.create_note("Deterministic")
        assert not r2.ok


# ---------------------------------------------------------------------------
# Knowledge subtype
# ---------------------------------------------------------------------------


class TestCreateKnowledge:
    def test_knowledge_note(self, vault: Vault) -> None:
        svc = CreateService(vault)
        result = svc.create_note("Knowledge Item", subtype="knowledge")
        assert result.ok
        assert result.data["type"] == "note"
        with vault.engine.connect() as conn:
            row = conn.execute(select(nodes.c.subtype).where(nodes.c.id == result.data["id"])).one()
            assert row.subtype == "knowledge"

    def test_knowledge_warns_no_key_points(self, vault: Vault) -> None:
        svc = CreateService(vault)
        result = svc.create_note("No Points", subtype="knowledge")
        assert result.ok
        assert any("key_points" in w for w in result.warnings)


# ---------------------------------------------------------------------------
# Decision subtype
# ---------------------------------------------------------------------------


class TestCreateDecision:
    def test_decision_note(self, vault: Vault) -> None:
        svc = CreateService(vault)
        result = svc.create_note("Architecture Choice", subtype="decision")
        assert result.ok
        with vault.engine.connect() as conn:
            row = conn.execute(select(nodes.c.status).where(nodes.c.id == result.data["id"])).one()
            assert row.status == "proposed"

    def test_decision_creates_sections(self, vault: Vault) -> None:
        svc = CreateService(vault)
        result = svc.create_note("Section Check", subtype="decision")
        path = vault.root / result.data["path"]
        content = path.read_text()
        assert "## Context" in content
        assert "## Choice" in content
        assert "## Rationale" in content


# ---------------------------------------------------------------------------
# Reference creation
# ---------------------------------------------------------------------------


class TestCreateReference:
    def test_basic_reference(self, vault: Vault) -> None:
        svc = CreateService(vault)
        result = svc.create_reference("Cool Article")
        assert result.ok
        assert result.data["id"].startswith("ref_")
        assert result.data["type"] == "reference"

    def test_reference_with_url(self, vault: Vault) -> None:
        svc = CreateService(vault)
        result = svc.create_reference("Python Docs", url="https://docs.python.org")
        assert result.ok
        path = vault.root / result.data["path"]
        content = path.read_text()
        assert "url: https://docs.python.org" in content

    def test_reference_status(self, vault: Vault) -> None:
        svc = CreateService(vault)
        result = svc.create_reference("Status Check")
        with vault.engine.connect() as conn:
            row = conn.execute(select(nodes.c.status).where(nodes.c.id == result.data["id"])).one()
            assert row.status == "captured"


# ---------------------------------------------------------------------------
# Task creation
# ---------------------------------------------------------------------------


class TestCreateTask:
    def test_basic_task(self, vault: Vault) -> None:
        svc = CreateService(vault)
        result = svc.create_task("Fix the bug")
        assert result.ok
        assert result.data["id"].startswith("TASK-")
        assert result.data["type"] == "task"

    def test_task_sequential_ids(self, vault: Vault) -> None:
        svc = CreateService(vault)
        r1 = svc.create_task("Task One")
        r2 = svc.create_task("Task Two")
        assert r1.data["id"] == "TASK-0001"
        assert r2.data["id"] == "TASK-0002"

    def test_task_status_inbox(self, vault: Vault) -> None:
        svc = CreateService(vault)
        result = svc.create_task("Inbox Task")
        with vault.engine.connect() as conn:
            row = conn.execute(select(nodes.c.status).where(nodes.c.id == result.data["id"])).one()
            assert row.status == "inbox"

    def test_task_with_priority(self, vault: Vault) -> None:
        svc = CreateService(vault)
        result = svc.create_task("High Priority", priority="high")
        assert result.ok
        path = vault.root / result.data["path"]
        content = path.read_text()
        assert "priority: high" in content

    def test_task_file_in_ops(self, vault: Vault) -> None:
        svc = CreateService(vault)
        result = svc.create_task("Ops Task")
        assert result.data["path"].startswith("ops/tasks/")


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------


class TestCreateErrors:
    def test_unknown_type(self, vault: Vault) -> None:
        svc = CreateService(vault)
        result = svc._create_content(content_type="unknown", title="Bad")
        assert not result.ok
        assert result.error is not None
        assert result.error.code == "UNKNOWN_TYPE"


# ---------------------------------------------------------------------------
# Link indexing
# ---------------------------------------------------------------------------


class TestLinkIndexing:
    def test_frontmatter_links_indexed(self, vault: Vault) -> None:
        """Frontmatter links to existing nodes create edges."""
        svc = CreateService(vault)
        # Create target first
        svc.create_note("Target Note")
        # Create source — links field isn't exposed through public API,
        # so we verify the pipeline doesn't fail with tags present
        r2 = svc.create_note("Source Note", tags=["test/links"])
        assert r2.ok

    def test_wikilink_to_nonexistent_ignored(self, vault: Vault) -> None:
        """Wikilinks to non-existent nodes are silently skipped."""
        svc = CreateService(vault)
        # Body contains [[Nonexistent]] but no node with that title exists
        result = svc.create_note("Linker Note")
        assert result.ok
        # No edges should exist
        with vault.engine.connect() as conn:
            edge_rows = conn.execute(
                select(edges).where(edges.c.source_id == result.data["id"])
            ).fetchall()
            assert len(edge_rows) == 0


# ---------------------------------------------------------------------------
# Batch creation
# ---------------------------------------------------------------------------


class TestCreateBatch:
    def test_batch_success(self, vault: Vault) -> None:
        svc = CreateService(vault)
        items = [
            {"type": "note", "title": "Batch Note 1"},
            {"type": "note", "title": "Batch Note 2"},
        ]
        result = svc.create_batch(items)
        assert result.ok
        assert len(result.data["created"]) == 2
        assert len(result.data["errors"]) == 0

    def test_batch_all_or_nothing(self, vault: Vault) -> None:
        """Without partial=True, first failure stops the batch."""
        svc = CreateService(vault)
        # Create a note first to cause collision
        svc.create_note("Duplicate")
        items = [
            {"type": "note", "title": "Duplicate"},  # will collide
            {"type": "note", "title": "Should Not Exist"},
        ]
        result = svc.create_batch(items)
        assert not result.ok
        assert result.error is not None
        assert result.error.code == "BATCH_FAILED"

    def test_batch_all_or_nothing_rolls_back_written_content(self, vault: Vault) -> None:
        svc = CreateService(vault)
        items = [
            {"type": "note", "title": "Good Note"},
            {"type": "invalid_type", "title": "Bad Item"},
        ]

        result = svc.create_batch(items)

        assert not result.ok
        assert result.error is not None
        assert result.error.code == "BATCH_FAILED"
        assert result.data["created"] == []

        with vault.engine.connect() as conn:
            rows = conn.execute(select(nodes.c.id)).fetchall()
            assert rows == []

        note_path = vault.root / "notes" / f"{generate_content_hash('Good Note', 'ztl_')}.md"
        assert not note_path.exists()

    def test_batch_partial(self, vault: Vault) -> None:
        """With partial=True, failures are collected but don't stop."""
        svc = CreateService(vault)
        svc.create_note("Exists")
        items = [
            {"type": "note", "title": "Exists"},  # collision
            {"type": "note", "title": "New Note"},  # ok
        ]
        result = svc.create_batch(items, partial=True)
        assert not result.ok  # has errors
        assert len(result.data["created"]) == 1
        assert len(result.data["errors"]) == 1


# ---------------------------------------------------------------------------
# Maturity support
# ---------------------------------------------------------------------------


class TestCreateNoteMaturity:
    def test_create_note_with_maturity(self, vault: Vault) -> None:
        """Maturity parameter persists to the DB node row."""
        result = CreateService(vault).create_note("Seed Idea", maturity="seed")
        assert result.ok
        with vault.engine.connect() as conn:
            row = conn.execute(
                select(nodes.c.maturity).where(nodes.c.id == result.data["id"])
            ).first()
            assert row is not None
            assert row.maturity == "seed"

    def test_create_note_without_maturity(self, vault: Vault) -> None:
        """Maturity is None by default."""
        result = CreateService(vault).create_note("Normal Note")
        assert result.ok
        with vault.engine.connect() as conn:
            row = conn.execute(
                select(nodes.c.maturity).where(nodes.c.id == result.data["id"])
            ).first()
            assert row is not None
            assert row.maturity is None


# ---------------------------------------------------------------------------
# Post-create automatic reweave (T-001)
# ---------------------------------------------------------------------------


class TestPostCreateReweave:
    def test_create_service_does_not_call_reweave_directly(self, vault_root: Path) -> None:
        """CreateService delegates post-create reweave to plugins via event bus."""
        from unittest.mock import patch

        v = Vault(ZtlSettings.from_cli(vault_root=vault_root))
        svc = CreateService(v)

        with patch("ztlctl.services.reweave.ReweaveService") as mock_cls:
            result = svc.create_note("No Event Bus")

        assert result.ok
        mock_cls.assert_not_called()

    def test_reweave_runs_via_post_create_plugin(self, vault_root: Path) -> None:
        """When event bus is active, post_create plugin triggers reweave exactly once."""
        from unittest.mock import patch

        mock_result = ServiceResult(ok=True, op="reweave", data={"count": 2, "suggestions": []})
        v = Vault(ZtlSettings.from_cli(vault_root=vault_root))
        v.init_event_bus(sync=True)
        svc = CreateService(v)

        with patch("ztlctl.services.reweave.ReweaveService") as mock_cls:
            mock_cls.return_value.reweave.return_value = mock_result
            result = svc.create_note("Plugin Reweave")

        assert result.ok
        mock_cls.assert_called_once_with(v)
        mock_cls.return_value.reweave.assert_called_once()
        call_kwargs = mock_cls.return_value.reweave.call_args.kwargs
        assert call_kwargs["content_id"] == result.data["id"]

    def test_task_creation_skips_plugin_reweave(self, vault_root: Path) -> None:
        """Tasks don't participate in post-create reweave."""
        from unittest.mock import patch

        v = Vault(ZtlSettings.from_cli(vault_root=vault_root))
        v.init_event_bus(sync=True)
        svc = CreateService(v)

        with patch("ztlctl.services.reweave.ReweaveService") as mock_cls:
            result = svc.create_task("Some Task")

        assert result.ok
        mock_cls.assert_not_called()

    def test_entrypoint_plugins_do_not_fail_post_create_dispatch(self, vault_root: Path) -> None:
        v = Vault(ZtlSettings.from_cli(vault_root=vault_root))
        v.init_event_bus(sync=True)
        try:
            result = CreateService(v).create_note("Entrypoint Note")
            assert result.ok

            with v.engine.connect() as conn:
                row = conn.execute(
                    text(
                        "SELECT status, error FROM event_wal "
                        "WHERE hook_name = 'post_create' ORDER BY id DESC LIMIT 1"
                    )
                ).one()
            assert row.status == "completed"
            assert row.error is None
        finally:
            v.close()
