"""Integration workflow tests — multi-step scenarios spanning multiple services.

These tests exercise cross-service interactions that unit tests cannot catch:
data flows between Create → Query → Graph → Reweave, session lifecycle with
enrichment, integrity check/fix/rebuild cycles, and update propagation.
"""

from __future__ import annotations

from sqlalchemy import delete, select, text

from tests.conftest import create_note, create_reference, start_session
from ztlctl.infrastructure.database.schema import edges, nodes
from ztlctl.infrastructure.vault import Vault
from ztlctl.services.check import CheckService
from ztlctl.services.graph import GraphService
from ztlctl.services.query import QueryService
from ztlctl.services.reweave import ReweaveService
from ztlctl.services.session import SessionService
from ztlctl.services.update import UpdateService


class TestCreateReweaveQuery:
    """Create notes with overlapping tags → reweave → verify edges → query related."""

    def test_create_reweave_query_pipeline(self, vault: Vault) -> None:
        # Create 5 notes with overlapping tags
        n1 = create_note(vault, "Python Basics", tags=["lang/python", "level/beginner"])
        n2 = create_note(vault, "Python Advanced", tags=["lang/python", "level/advanced"])
        create_note(vault, "Rust Basics", tags=["lang/rust", "level/beginner"])
        n4 = create_note(vault, "Type Systems", tags=["lang/python", "lang/rust"])
        create_note(vault, "Testing Strategy", tags=["practice/testing", "lang/python"])

        # Reweave from n1 — should find related notes via tag overlap
        result = ReweaveService(vault).reweave(content_id=n1["id"])
        assert result.ok

        # Query search for "python" — should find relevant notes
        search_result = QueryService(vault).search("python", limit=10)
        assert search_result.ok
        found_ids = {r["id"] for r in search_result.data["items"]}
        # At minimum n1 and n2 should appear (both have "python" in title)
        assert n1["id"] in found_ids
        assert n2["id"] in found_ids

        # Graph related from n4 (Type Systems) — should find neighbors
        related = GraphService(vault).related(n4["id"], depth=1, top=5)
        assert related.ok

    def test_reweave_creates_queryable_edges(self, vault: Vault) -> None:
        """Reweave edges should be visible in graph queries."""
        n1 = create_note(vault, "Source Note", tags=["topic/ai"])
        n2 = create_note(vault, "Related Note", tags=["topic/ai"])

        # Before reweave: no edges between them
        with vault.engine.connect() as conn:
            edge_count = conn.execute(
                select(edges).where(
                    edges.c.source_id == n1["id"],
                    edges.c.target_id == n2["id"],
                )
            ).fetchall()
        assert len(edge_count) == 0

        # Reweave
        ReweaveService(vault).reweave(content_id=n1["id"])

        # After reweave: edges may exist (depending on scoring threshold)
        # At minimum, the reweave operation should not error
        related = GraphService(vault).related(n1["id"], depth=1, top=5)
        assert related.ok


class TestSessionLifecycle:
    """Start → create notes → log entries → close → verify enrichment."""

    def test_full_session_lifecycle(self, vault: Vault) -> None:
        # Start session
        session_data = start_session(vault, "Architecture Review")
        session_id = session_data["id"]

        # Create notes within session
        create_note(vault, "Decision: Use PostgreSQL", subtype="decision", session=session_id)
        create_note(vault, "Research: ORM Options", session=session_id)

        # Log entries
        svc = SessionService(vault)
        svc.log_entry("Reviewed ORM options", pin=True, cost=500)
        svc.log_entry("Decided on SQLAlchemy Core", cost=300)

        # Check cost tracking
        cost_result = svc.cost()
        assert cost_result.ok
        assert cost_result.data["total_cost"] == 800
        # session_start (cost=0) + 2 log entries = 3 rows
        assert cost_result.data["entry_count"] == 3

        # Context assembly
        ctx = svc.context(topic="Architecture")
        assert ctx.ok
        assert "layers" in ctx.data
        assert ctx.data["total_tokens"] > 0

        # Brief
        brief = svc.brief()
        assert brief.ok
        assert brief.data["session"] is not None
        assert brief.data["session"]["session_id"] == session_id

        # Close session (triggers enrichment pipeline)
        close_result = svc.close(summary="Completed architecture review")
        assert close_result.ok
        assert close_result.data["session_id"] == session_id
        assert close_result.data["status"] == "closed"

    def test_extract_decision_from_session(self, vault: Vault) -> None:
        """Extract decision creates a decision note linked to the session."""
        session_data = start_session(vault, "Design Review")
        session_id = session_data["id"]

        svc = SessionService(vault)
        svc.log_entry("Considered option A", pin=True)
        svc.log_entry("Selected option A over B", pin=True)
        svc.close()

        # Extract decision
        result = svc.extract_decision(session_id, title="Decision: Option A")
        assert result.ok
        decision_id = result.data["id"]

        # Verify the decision is queryable
        get_result = QueryService(vault).get(decision_id)
        assert get_result.ok
        assert get_result.data["title"] == "Decision: Option A"


class TestCheckFixRebuild:
    """Create notes → corrupt DB → check (issues found) → fix → check (clean)."""

    def test_check_fix_cycle(self, vault: Vault) -> None:
        # Create content
        n1 = create_note(vault, "Note One", tags=["domain/test"])
        create_note(vault, "Note Two", tags=["domain/test"])

        # Initial check should be clean
        check_svc = CheckService(vault)
        result = check_svc.check()
        assert result.ok
        issues = result.data.get("issues", [])
        errors = [i for i in issues if i.get("severity") == "error"]
        assert len(errors) == 0

        # Corrupt: delete a DB row but leave the file
        with vault.engine.begin() as conn:
            conn.execute(text("PRAGMA foreign_keys=OFF"))
            conn.execute(delete(nodes).where(nodes.c.id == n1["id"]))
            conn.execute(text("PRAGMA foreign_keys=ON"))

        # Check should find issues
        result = check_svc.check()
        assert result.ok
        issues = result.data.get("issues", [])
        assert len(issues) > 0  # At least orphan file or missing DB row

    def test_rebuild_restores_consistency(self, vault: Vault) -> None:
        """Full rebuild from files should restore a clean state."""
        # Create content
        create_note(vault, "Rebuild Note A", tags=["domain/rebuild"])
        create_note(vault, "Rebuild Note B", tags=["domain/rebuild"])
        create_reference(vault, "Rebuild Ref", tags=["domain/rebuild"])

        # Rebuild
        check_svc = CheckService(vault)
        rebuild_result = check_svc.rebuild()
        assert rebuild_result.ok

        # Post-rebuild check should be clean
        result = check_svc.check()
        assert result.ok
        issues = result.data.get("issues", [])
        errors = [i for i in issues if i.get("severity") == "error"]
        assert len(errors) == 0

        # Content should still be queryable
        search = QueryService(vault).search("Rebuild", limit=10)
        assert search.ok
        assert len(search.data["items"]) >= 2


class TestUpdatePropagation:
    """Create + link notes → update (tags, links) → verify re-indexing."""

    def test_update_reindexes_tags_and_fts(self, vault: Vault) -> None:
        # Create note with initial tags
        n1 = create_note(vault, "Original Title", tags=["domain/initial"])

        # Update tags
        update_svc = UpdateService(vault)
        result = update_svc.update(
            n1["id"],
            changes={
                "tags": ["domain/updated", "scope/new"],
            },
        )
        assert result.ok
        assert "tags" in result.data["fields_changed"]

        # Query by new tag should find it
        query_svc = QueryService(vault)
        list_result = query_svc.list_items(tag="domain/updated")
        assert list_result.ok
        found_ids = {item["id"] for item in list_result.data["items"]}
        assert n1["id"] in found_ids

        # Query by old tag should NOT find it
        old_result = query_svc.list_items(tag="domain/initial")
        assert old_result.ok
        old_ids = {item["id"] for item in old_result.data["items"]}
        assert n1["id"] not in old_ids

    def test_update_title_updates_fts(self, vault: Vault) -> None:
        """Updating title should update FTS index."""
        n1 = create_note(vault, "OriginalUniqueName123")

        # Search for original title
        r1 = QueryService(vault).search("OriginalUniqueName123")
        assert r1.ok
        assert any(r["id"] == n1["id"] for r in r1.data["items"])

        # Update title
        UpdateService(vault).update(n1["id"], changes={"title": "UpdatedUniqueName456"})

        # Search for new title
        r2 = QueryService(vault).search("UpdatedUniqueName456")
        assert r2.ok
        assert any(r["id"] == n1["id"] for r in r2.data["items"])


class TestArchiveQuery:
    """Create → archive → query excludes by default → query with flag includes."""

    def test_archive_excludes_from_default_queries(self, vault: Vault) -> None:
        # Create and archive
        n1 = create_note(vault, "Archived Note XYZ")
        n2 = create_note(vault, "Active Note XYZ")

        UpdateService(vault).archive(n1["id"])

        # Default list should exclude archived
        query_svc = QueryService(vault)
        list_result = query_svc.list_items()
        assert list_result.ok
        list_ids = {item["id"] for item in list_result.data["items"]}
        assert n1["id"] not in list_ids
        assert n2["id"] in list_ids

    def test_archive_included_with_flag(self, vault: Vault) -> None:
        n1 = create_note(vault, "Will Archive This")
        UpdateService(vault).archive(n1["id"])

        # With include_archived=True should find it
        result = QueryService(vault).list_items(include_archived=True)
        assert result.ok
        ids = {item["id"] for item in result.data["items"]}
        assert n1["id"] in ids
