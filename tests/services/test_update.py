"""Tests for UpdateService — update, archive, supersede."""

from __future__ import annotations

from typing import Any

from sqlalchemy import insert, select, text

from ztlctl.domain.content import parse_frontmatter
from ztlctl.infrastructure.database.schema import edges, node_tags, nodes
from ztlctl.infrastructure.vault import Vault
from ztlctl.services.create import CreateService
from ztlctl.services.update import UpdateService

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _create_note(vault: Vault, title: str, **kwargs: Any) -> dict[str, Any]:
    result = CreateService(vault).create_note(title, **kwargs)
    assert result.ok, result.error
    return result.data


def _create_reference(vault: Vault, title: str, **kwargs: Any) -> dict[str, Any]:
    result = CreateService(vault).create_reference(title, **kwargs)
    assert result.ok, result.error
    return result.data


def _create_task(vault: Vault, title: str, **kwargs: Any) -> dict[str, Any]:
    result = CreateService(vault).create_task(title, **kwargs)
    assert result.ok, result.error
    return result.data


def _create_decision(vault: Vault, title: str, **kwargs: Any) -> dict[str, Any]:
    result = CreateService(vault).create_note(title, subtype="decision", **kwargs)
    assert result.ok, result.error
    return result.data


# ---------------------------------------------------------------------------
# update() — basic field changes
# ---------------------------------------------------------------------------


class TestUpdateBasic:
    def test_update_title(self, vault: Vault) -> None:
        data = _create_note(vault, "Old Title")
        svc = UpdateService(vault)
        result = svc.update(data["id"], changes={"title": "New Title"})
        assert result.ok
        assert "title" in result.data["fields_changed"]

        # Verify file updated
        path = vault.root / data["path"]
        fm, _ = parse_frontmatter(path.read_text(encoding="utf-8"))
        assert fm["title"] == "New Title"

        # Verify DB updated
        with vault.engine.connect() as conn:
            row = conn.execute(select(nodes.c.title).where(nodes.c.id == data["id"])).one()
            assert row.title == "New Title"

    def test_update_tags(self, vault: Vault) -> None:
        data = _create_note(vault, "Tag Note", tags=["old/tag"])
        svc = UpdateService(vault)
        result = svc.update(data["id"], changes={"tags": ["new/tag", "extra/tag"]})
        assert result.ok

        with vault.engine.connect() as conn:
            tag_rows = conn.execute(
                select(node_tags.c.tag).where(node_tags.c.node_id == data["id"])
            ).fetchall()
            tags = {r.tag for r in tag_rows}
            assert tags == {"new/tag", "extra/tag"}

    def test_update_not_found(self, vault: Vault) -> None:
        result = UpdateService(vault).update("ztl_nonexist", changes={"title": "X"})
        assert not result.ok
        assert result.error is not None
        assert result.error.code == "NOT_FOUND"

    def test_update_bumps_modified(self, vault: Vault) -> None:
        data = _create_note(vault, "Mod Note")
        result = UpdateService(vault).update(data["id"], changes={"title": "Updated"})
        assert result.ok

        with vault.engine.connect() as conn:
            row = conn.execute(select(nodes.c.modified).where(nodes.c.id == data["id"])).one()
            assert row.modified is not None

    def test_immutable_fields_warned(self, vault: Vault) -> None:
        """Attempting to change immutable fields (id, type, created) produces warnings."""
        data = _create_note(vault, "Immutable Test")
        result = UpdateService(vault).update(data["id"], changes={"id": "ztl_new00000"})
        assert result.ok
        assert any("immutable" in w.lower() for w in result.warnings)


# ---------------------------------------------------------------------------
# Status transitions
# ---------------------------------------------------------------------------


class TestUpdateStatus:
    def test_valid_task_transition(self, vault: Vault) -> None:
        data = _create_task(vault, "Status Task")
        result = UpdateService(vault).update(data["id"], changes={"status": "active"})
        assert result.ok
        assert result.data["status"] == "active"

    def test_invalid_task_transition(self, vault: Vault) -> None:
        data = _create_task(vault, "Bad Transition")
        result = UpdateService(vault).update(data["id"], changes={"status": "done"})
        assert not result.ok
        assert result.error is not None
        assert result.error.code == "INVALID_TRANSITION"


# ---------------------------------------------------------------------------
# Decision immutability
# ---------------------------------------------------------------------------


class TestDecisionImmutability:
    def test_accepted_decision_rejects_body(self, vault: Vault) -> None:
        """Accepted decisions are immutable — can't change title."""
        data = _create_decision(vault, "My Decision")
        svc = UpdateService(vault)
        # Accept it first
        svc.update(data["id"], changes={"status": "accepted"})
        # Now try to change title
        result = svc.update(data["id"], changes={"title": "Changed"})
        assert not result.ok
        assert result.error is not None
        assert "Cannot modify accepted decision" in result.error.message

    def test_accepted_decision_allows_supersede(self, vault: Vault) -> None:
        """Accepted decisions CAN be superseded."""
        data = _create_decision(vault, "Old Decision")
        svc = UpdateService(vault)
        svc.update(data["id"], changes={"status": "accepted"})
        result = svc.update(
            data["id"],
            changes={"status": "superseded", "superseded_by": "ztl_new00000"},
        )
        assert result.ok


# ---------------------------------------------------------------------------
# Garden note protection
# ---------------------------------------------------------------------------


class TestGardenProtection:
    def test_body_rejected_for_garden_note(self, vault: Vault) -> None:
        """Notes with maturity set reject body modifications."""
        data = _create_note(vault, "Garden Note")
        svc = UpdateService(vault)
        # Set maturity on the note
        svc.update(data["id"], changes={"maturity": "seed"})
        # Try to change body
        result = svc.update(data["id"], changes={"body": "new body text"})
        assert result.ok  # succeeds but body is not changed
        assert any("Body change rejected" in w for w in result.warnings)

    def test_body_accepted_for_machine_note(self, vault: Vault) -> None:
        """Notes without maturity allow body modifications."""
        data = _create_note(vault, "Machine Note")
        result = UpdateService(vault).update(data["id"], changes={"body": "new body text"})
        assert result.ok
        assert "body" in result.data["fields_changed"]


# ---------------------------------------------------------------------------
# Note status propagation
# ---------------------------------------------------------------------------


class TestNoteStatusPropagation:
    def test_draft_stays_draft_with_no_links(self, vault: Vault) -> None:
        data = _create_note(vault, "Lonely Note")
        result = UpdateService(vault).update(data["id"], changes={"title": "Still Lonely"})
        assert result.ok
        assert result.data["status"] == "draft"

    def test_becomes_linked_with_one_edge(self, vault: Vault) -> None:
        data_a = _create_note(vault, "Source")
        data_b = _create_note(vault, "Target")
        # Add an edge A -> B
        with vault.engine.begin() as conn:
            conn.execute(
                insert(edges).values(
                    source_id=data_a["id"],
                    target_id=data_b["id"],
                    edge_type="relates",
                    source_layer="frontmatter",
                    weight=1.0,
                    created="2025-01-01",
                )
            )
        # Trigger update to recompute status
        result = UpdateService(vault).update(data_a["id"], changes={"title": "Source Updated"})
        assert result.ok
        assert result.data["status"] == "linked"

    def test_becomes_connected_with_three_edges(self, vault: Vault) -> None:
        data_a = _create_note(vault, "Hub Node")
        targets = [_create_note(vault, f"Target {i}") for i in range(3)]
        with vault.engine.begin() as conn:
            for t in targets:
                conn.execute(
                    insert(edges).values(
                        source_id=data_a["id"],
                        target_id=t["id"],
                        edge_type="relates",
                        source_layer="frontmatter",
                        weight=1.0,
                        created="2025-01-01",
                    )
                )
        result = UpdateService(vault).update(data_a["id"], changes={"title": "Hub Updated"})
        assert result.ok
        assert result.data["status"] == "connected"


# ---------------------------------------------------------------------------
# FTS5 reindex
# ---------------------------------------------------------------------------


class TestFtsReindex:
    def test_fts_updated_on_title_change(self, vault: Vault) -> None:
        data = _create_note(vault, "Searchable Original")
        UpdateService(vault).update(data["id"], changes={"title": "Searchable Updated"})

        with vault.engine.connect() as conn:
            rows = conn.execute(
                text("SELECT id FROM nodes_fts WHERE title MATCH :q"),
                {"q": "Updated"},
            ).fetchall()
            assert any(r[0] == data["id"] for r in rows)

            # Old title should not match
            old_rows = conn.execute(
                text("SELECT id FROM nodes_fts WHERE title MATCH :q"),
                {"q": "Original"},
            ).fetchall()
            assert not any(r[0] == data["id"] for r in old_rows)


# ---------------------------------------------------------------------------
# Edge reindex
# ---------------------------------------------------------------------------


class TestEdgeReindex:
    def test_edges_reindexed_on_links_change(self, vault: Vault) -> None:
        data_a = _create_note(vault, "Link Source")
        data_b = _create_note(vault, "Link Target")

        result = UpdateService(vault).update(
            data_a["id"],
            changes={"links": {"relates": [data_b["id"]]}},
        )
        assert result.ok

        with vault.engine.connect() as conn:
            edge = conn.execute(
                select(edges.c.target_id).where(
                    edges.c.source_id == data_a["id"],
                    edges.c.target_id == data_b["id"],
                )
            ).first()
            assert edge is not None


# ---------------------------------------------------------------------------
# archive()
# ---------------------------------------------------------------------------


class TestArchive:
    def test_archive_sets_flag(self, vault: Vault) -> None:
        data = _create_note(vault, "Archive Me")
        result = UpdateService(vault).archive(data["id"])
        assert result.ok

        # Check DB
        with vault.engine.connect() as conn:
            row = conn.execute(select(nodes.c.archived).where(nodes.c.id == data["id"])).one()
            assert row.archived == 1

        # Check file
        path = vault.root / data["path"]
        fm, _ = parse_frontmatter(path.read_text(encoding="utf-8"))
        assert fm["archived"] is True

    def test_archive_preserves_edges(self, vault: Vault) -> None:
        data_a = _create_note(vault, "Archived Node")
        data_b = _create_note(vault, "Connected Node")
        with vault.engine.begin() as conn:
            conn.execute(
                insert(edges).values(
                    source_id=data_a["id"],
                    target_id=data_b["id"],
                    edge_type="relates",
                    source_layer="frontmatter",
                    weight=1.0,
                    created="2025-01-01",
                )
            )

        UpdateService(vault).archive(data_a["id"])

        with vault.engine.connect() as conn:
            edge = conn.execute(
                select(edges.c.source_id).where(edges.c.source_id == data_a["id"])
            ).first()
            assert edge is not None

    def test_archive_not_found(self, vault: Vault) -> None:
        result = UpdateService(vault).archive("ztl_nonexist")
        assert not result.ok
        assert result.error is not None
        assert result.error.code == "NOT_FOUND"


# ---------------------------------------------------------------------------
# supersede()
# ---------------------------------------------------------------------------


class TestSupersede:
    def test_supersede_sets_status_and_link(self, vault: Vault) -> None:
        data_old = _create_decision(vault, "Old Decision")
        data_new = _create_decision(vault, "New Decision")

        svc = UpdateService(vault)
        svc.update(data_old["id"], changes={"status": "accepted"})

        result = svc.supersede(data_old["id"], data_new["id"])
        assert result.ok

        # Check file
        path = vault.root / data_old["path"]
        fm, _ = parse_frontmatter(path.read_text(encoding="utf-8"))
        assert fm["status"] == "superseded"
        assert fm["superseded_by"] == data_new["id"]


# ---------------------------------------------------------------------------
# Alias resolution
# ---------------------------------------------------------------------------


class TestAliasResolution:
    def test_wikilink_resolves_by_alias(self, vault: Vault) -> None:
        """Wikilinks can resolve via node aliases."""
        import json

        data = _create_note(vault, "Python Language")
        # Store aliases in DB
        with vault.engine.begin() as conn:
            conn.execute(
                nodes.update()
                .where(nodes.c.id == data["id"])
                .values(aliases=json.dumps(["py", "python"]))
            )

        # Create another note with a wikilink to the alias
        data_b = _create_note(vault, "Uses Python")
        path_b = vault.root / data_b["path"]
        fm, _ = parse_frontmatter(path_b.read_text(encoding="utf-8"))
        body_with_link = "This references [[py]] language."
        # Update with links in body — use frontmatter links change to trigger reindex
        result = UpdateService(vault).update(
            data_b["id"],
            changes={"links": {}},
        )
        assert result.ok

        # Write body with wikilink directly and re-trigger edge reindex
        from ztlctl.domain.content import render_frontmatter as render_fm

        path_b.write_text(render_fm(fm, body_with_link), encoding="utf-8")
        result = UpdateService(vault).update(data_b["id"], changes={"links": {}})
        assert result.ok

        # Verify edge was created via alias resolution
        with vault.engine.connect() as conn:
            edge = conn.execute(
                select(edges.c.target_id).where(
                    edges.c.source_id == data_b["id"],
                    edges.c.target_id == data["id"],
                )
            ).first()
            assert edge is not None
