"""Tests for infrastructure query repository read models."""

from __future__ import annotations

from tests.conftest import create_note, create_task

from ztlctl.infrastructure.repositories import QueryRepository
from ztlctl.infrastructure.vault import Vault
from ztlctl.services.update import UpdateService


class TestQueryRepository:
    def test_count_items_respects_archived_flag(self, vault: Vault) -> None:
        keep = create_note(vault, "Keep")
        archived = create_note(vault, "Archive")
        result = UpdateService(vault).archive(archived["id"])
        assert result.ok

        repo = QueryRepository(vault.engine)
        assert repo.count_items() == 1
        assert repo.count_items(include_archived=True) == 2

        # ensure kept note is still queryable
        row = repo.get_node(keep["id"])
        assert row is not None
        assert row["title"] == "Keep"

    def test_search_fts_rows_returns_ranked_matches(self, vault: Vault) -> None:
        create_note(vault, "Repository Search Target")
        create_note(vault, "Unrelated")

        rows = QueryRepository(vault.engine).search_fts_rows("Repository")
        assert rows
        assert any(row["title"] == "Repository Search Target" for row in rows)
        assert "score" in rows[0]

    def test_links_and_tags_are_retrievable(self, vault: Vault) -> None:
        source = create_note(vault, "Source", tags=["arch/layered"])
        target = create_note(vault, "Target")
        updated = UpdateService(vault).update(
            source["id"],
            changes={"links": {"relates": [target["id"]]}},
        )
        assert updated.ok

        repo = QueryRepository(vault.engine)
        tags = repo.get_node_tags(source["id"])
        outgoing = repo.get_outgoing_links(source["id"])
        incoming = repo.get_incoming_links(target["id"])

        assert "arch/layered" in tags
        assert any(link["id"] == target["id"] for link in outgoing)
        assert any(link["id"] == source["id"] for link in incoming)

    def test_work_queue_rows_only_actionable_statuses(self, vault: Vault) -> None:
        active = create_task(vault, "Active Task")
        done = create_task(vault, "Done Task")

        activated = UpdateService(vault).update(done["id"], changes={"status": "active"})
        assert activated.ok
        completed = UpdateService(vault).update(done["id"], changes={"status": "done"})
        assert completed.ok

        rows = QueryRepository(vault.engine).work_queue_rows()
        ids = {row["id"] for row in rows}
        assert active["id"] in ids
        assert done["id"] not in ids
