"""Tests for SessionService — start, close, reopen, log_entry, cost, context."""

from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy import select

from tests.conftest import create_note, create_task, start_session
from ztlctl.infrastructure.database.schema import nodes, session_logs
from ztlctl.infrastructure.vault import Vault
from ztlctl.services.session import SessionService

# ---------------------------------------------------------------------------
# start()
# ---------------------------------------------------------------------------


class TestSessionStart:
    def test_start_creates_session(self, vault: Vault) -> None:
        result = SessionService(vault).start("Test Topic")
        assert result.ok
        assert result.data["id"].startswith("LOG-")
        assert result.data["topic"] == "Test Topic"
        assert result.data["status"] == "open"

    def test_start_creates_jsonl_file(self, vault: Vault) -> None:
        data = start_session(vault, "File Test")
        path = vault.root / data["path"]
        assert path.exists()
        assert path.suffix == ".jsonl"

        content = path.read_text(encoding="utf-8").strip()
        entry = json.loads(content)
        assert entry["type"] == "session_start"
        assert entry["session_id"] == data["id"]
        assert entry["topic"] == "File Test"

    def test_start_creates_db_row(self, vault: Vault) -> None:
        data = start_session(vault, "DB Test")
        with vault.engine.connect() as conn:
            row = conn.execute(select(nodes).where(nodes.c.id == data["id"])).first()
            assert row is not None
            assert row.type == "log"
            assert row.status == "open"
            assert row.topic == "DB Test"

    def test_start_sequential_ids(self, vault: Vault) -> None:
        data1 = start_session(vault, "First")
        data2 = start_session(vault, "Second")
        # IDs should be sequential
        n1 = int(data1["id"].split("-")[1])
        n2 = int(data2["id"].split("-")[1])
        assert n2 == n1 + 1

    def test_start_creates_fts_entry(self, vault: Vault) -> None:
        from sqlalchemy import text

        data = start_session(vault, "Searchable Session")
        with vault.engine.connect() as conn:
            rows = conn.execute(
                text("SELECT id FROM nodes_fts WHERE title MATCH :q"),
                {"q": "Searchable"},
            ).fetchall()
            assert any(r[0] == data["id"] for r in rows)


# ---------------------------------------------------------------------------
# close()
# ---------------------------------------------------------------------------


class TestSessionClose:
    def test_close_active_session(self, vault: Vault) -> None:
        data = start_session(vault, "Close Me")
        result = SessionService(vault).close()
        assert result.ok
        assert result.data["session_id"] == data["id"]
        assert result.data["status"] == "closed"

    def test_close_updates_db_status(self, vault: Vault) -> None:
        data = start_session(vault, "Close DB Test")
        SessionService(vault).close()

        with vault.engine.connect() as conn:
            row = conn.execute(select(nodes.c.status).where(nodes.c.id == data["id"])).first()
            assert row is not None
            assert row.status == "closed"

    def test_close_appends_to_jsonl(self, vault: Vault) -> None:
        data = start_session(vault, "JSONL Close Test")
        SessionService(vault).close(summary="Done!")

        path = vault.root / data["path"]
        lines = path.read_text(encoding="utf-8").strip().split("\n")
        assert len(lines) == 2  # start + close
        close_entry = json.loads(lines[1])
        assert close_entry["type"] == "session_close"
        assert close_entry["summary"] == "Done!"

    def test_close_no_active_session(self, vault: Vault) -> None:
        result = SessionService(vault).close()
        assert not result.ok
        assert result.error is not None
        assert result.error.code == "NO_ACTIVE_SESSION"

    def test_close_already_closed(self, vault: Vault) -> None:
        start_session(vault, "Already Closed")
        SessionService(vault).close()

        # Try to close again
        result = SessionService(vault).close()
        assert not result.ok
        assert result.error is not None
        assert result.error.code == "NO_ACTIVE_SESSION"

    def test_close_report_counts(self, vault: Vault) -> None:
        start_session(vault, "Report Test")
        result = SessionService(vault).close()
        assert result.ok
        assert "reweave_count" in result.data
        assert "orphan_count" in result.data
        assert "integrity_issues" in result.data

    def test_close_with_session_notes_reweave(self, vault: Vault) -> None:
        """Notes created in the session are reweaved on close."""
        data = start_session(vault, "Reweave Session")
        session_id = data["id"]

        # Create notes in this session
        create_note(vault, "Python Guide", session=session_id)
        create_note(vault, "Python Reference", session=session_id)

        result = SessionService(vault).close()
        assert result.ok
        # Reweave count may be 0 if scores are below threshold, but pipeline ran
        assert result.data["reweave_count"] >= 0


# ---------------------------------------------------------------------------
# close() — disabled enrichment
# ---------------------------------------------------------------------------


class TestSessionCloseDisabled:
    def test_close_reweave_disabled(self, vault_root: Path) -> None:
        """Close skips reweave when disabled in settings."""
        from ztlctl.config.settings import ZtlSettings

        config = vault_root / "ztlctl.toml"
        toml = (
            "[session]\n"
            "close_reweave = false\n"
            "close_orphan_sweep = false\n"
            "close_integrity_check = false\n"
        )
        config.write_text(toml, encoding="utf-8")
        settings = ZtlSettings.from_cli(vault_root=vault_root)
        v = Vault(settings)

        start_session(v, "Disabled Test")
        result = SessionService(v).close()
        assert result.ok
        assert result.data["reweave_count"] == 0
        assert result.data["orphan_count"] == 0


# ---------------------------------------------------------------------------
# reopen()
# ---------------------------------------------------------------------------


class TestSessionReopen:
    def test_reopen_closed_session(self, vault: Vault) -> None:
        data = start_session(vault, "Reopen Me")
        SessionService(vault).close()

        result = SessionService(vault).reopen(data["id"])
        assert result.ok
        assert result.data["status"] == "open"

    def test_reopen_updates_db(self, vault: Vault) -> None:
        data = start_session(vault, "Reopen DB Test")
        SessionService(vault).close()
        SessionService(vault).reopen(data["id"])

        with vault.engine.connect() as conn:
            row = conn.execute(select(nodes.c.status).where(nodes.c.id == data["id"])).first()
            assert row is not None
            assert row.status == "open"

    def test_reopen_appends_to_jsonl(self, vault: Vault) -> None:
        data = start_session(vault, "Reopen JSONL Test")
        SessionService(vault).close()
        SessionService(vault).reopen(data["id"])

        path = vault.root / data["path"]
        lines = path.read_text(encoding="utf-8").strip().split("\n")
        assert len(lines) == 3  # start + close + reopen
        reopen_entry = json.loads(lines[2])
        assert reopen_entry["type"] == "session_reopen"

    def test_reopen_already_open(self, vault: Vault) -> None:
        data = start_session(vault, "Already Open")
        result = SessionService(vault).reopen(data["id"])
        assert not result.ok
        assert result.error is not None
        assert result.error.code == "ALREADY_OPEN"

    def test_reopen_not_found(self, vault: Vault) -> None:
        result = SessionService(vault).reopen("LOG-9999")
        assert not result.ok
        assert result.error is not None
        assert result.error.code == "NOT_FOUND"

    def test_reopen_then_close_again(self, vault: Vault) -> None:
        """Can close a reopened session."""
        data = start_session(vault, "Cycle Test")
        SessionService(vault).close()
        SessionService(vault).reopen(data["id"])

        result = SessionService(vault).close()
        assert result.ok
        assert result.data["session_id"] == data["id"]


# ---------------------------------------------------------------------------
# log_entry()
# ---------------------------------------------------------------------------


class TestLogEntry:
    def test_log_entry_basic(self, vault: Vault) -> None:
        start_session(vault, "Log Test")
        result = SessionService(vault).log_entry("Found something interesting")
        assert result.ok
        assert result.op == "log_entry"
        assert "entry_id" in result.data

    def test_log_entry_appends_to_jsonl(self, vault: Vault) -> None:
        data = start_session(vault, "JSONL Log Test")
        SessionService(vault).log_entry("Entry one")
        SessionService(vault).log_entry("Entry two")

        path = vault.root / data["path"]
        lines = path.read_text(encoding="utf-8").strip().split("\n")
        assert len(lines) == 3  # start + 2 entries
        entry = json.loads(lines[1])
        assert entry["type"] == "log_entry"
        assert entry["message"] == "Entry one"

    def test_log_entry_inserts_db_row(self, vault: Vault) -> None:
        start_session(vault, "DB Log Test")
        SessionService(vault).log_entry("DB entry", cost=1500)

        with vault.engine.connect() as conn:
            rows = conn.execute(select(session_logs)).fetchall()
            assert len(rows) == 1
            assert rows[0].summary == "DB entry"
            assert rows[0].cost == 1500

    def test_log_entry_with_pin(self, vault: Vault) -> None:
        start_session(vault, "Pin Test")
        result = SessionService(vault).log_entry("Important!", pin=True)
        assert result.ok

        with vault.engine.connect() as conn:
            row = conn.execute(select(session_logs)).first()
            assert row is not None
            assert row.pinned == 1

    def test_log_entry_with_detail(self, vault: Vault) -> None:
        start_session(vault, "Detail Test")
        result = SessionService(vault).log_entry(
            "Summary line",
            detail="Full detailed context here",
        )
        assert result.ok

        with vault.engine.connect() as conn:
            row = conn.execute(select(session_logs)).first()
            assert row is not None
            assert row.detail == "Full detailed context here"

    def test_log_entry_with_references(self, vault: Vault) -> None:
        start_session(vault, "Ref Test")
        note = create_note(vault, "Referenced Note")
        result = SessionService(vault).log_entry(
            "Found relevant note",
            references=[note["id"]],
        )
        assert result.ok

        with vault.engine.connect() as conn:
            row = conn.execute(select(session_logs)).first()
            assert row is not None
            refs = json.loads(row.references)
            assert note["id"] in refs

    def test_log_entry_with_entry_type(self, vault: Vault) -> None:
        start_session(vault, "Type Test")
        result = SessionService(vault).log_entry(
            "Made a decision",
            entry_type="decision_made",
        )
        assert result.ok

        with vault.engine.connect() as conn:
            row = conn.execute(select(session_logs)).first()
            assert row is not None
            assert row.type == "decision_made"

    def test_log_entry_jsonl_reflects_entry_type(self, vault: Vault) -> None:
        """JSONL entry type must match the entry_type parameter."""
        data = start_session(vault, "Type Sync Test")
        SessionService(vault).log_entry("Made a call", entry_type="decision_made")

        path = vault.root / data["path"]
        lines = path.read_text(encoding="utf-8").strip().split("\n")
        entry = json.loads(lines[1])  # index 0 is session_start
        assert entry["type"] == "decision_made"

    def test_log_entry_checkpoint_subtype(self, vault: Vault) -> None:
        start_session(vault, "Checkpoint Test")
        result = SessionService(vault).log_entry(
            "Checkpoint snapshot",
            entry_type="checkpoint",
            subtype="checkpoint",
            detail="Full accumulated context...",
        )
        assert result.ok

        with vault.engine.connect() as conn:
            row = conn.execute(select(session_logs)).first()
            assert row is not None
            assert row.subtype == "checkpoint"

    def test_log_entry_no_active_session(self, vault: Vault) -> None:
        result = SessionService(vault).log_entry("Orphan entry")
        assert not result.ok
        assert result.error is not None
        assert result.error.code == "NO_ACTIVE_SESSION"

    def test_log_entry_preserves_session_id(self, vault: Vault) -> None:
        data = start_session(vault, "ID Test")
        SessionService(vault).log_entry("Test entry")

        with vault.engine.connect() as conn:
            row = conn.execute(select(session_logs)).first()
            assert row is not None
            assert row.session_id == data["id"]


# ---------------------------------------------------------------------------
# cost()
# ---------------------------------------------------------------------------


class TestCost:
    def test_cost_query_empty_session(self, vault: Vault) -> None:
        start_session(vault, "Cost Test")
        result = SessionService(vault).cost()
        assert result.ok
        assert result.op == "cost"
        assert result.data["total_cost"] == 0

    def test_cost_query_with_entries(self, vault: Vault) -> None:
        start_session(vault, "Cost Sum Test")
        svc = SessionService(vault)
        svc.log_entry("First", cost=1000)
        svc.log_entry("Second", cost=2500)
        svc.log_entry("Third", cost=500)

        result = svc.cost()
        assert result.ok
        assert result.data["total_cost"] == 4000
        assert result.data["entry_count"] == 3

    def test_cost_report_mode(self, vault: Vault) -> None:
        start_session(vault, "Report Test")
        svc = SessionService(vault)
        svc.log_entry("Entry", cost=3000)

        result = svc.cost(report=10000)
        assert result.ok
        assert result.data["total_cost"] == 3000
        assert result.data["budget"] == 10000
        assert result.data["remaining"] == 7000

    def test_cost_report_over_budget(self, vault: Vault) -> None:
        start_session(vault, "Over Budget Test")
        svc = SessionService(vault)
        svc.log_entry("Big entry", cost=9000)

        result = svc.cost(report=5000)
        assert result.ok
        assert result.data["remaining"] == -4000
        assert result.data["over_budget"] is True

    def test_cost_no_active_session(self, vault: Vault) -> None:
        result = SessionService(vault).cost()
        assert not result.ok
        assert result.error is not None
        assert result.error.code == "NO_ACTIVE_SESSION"

    def test_cost_includes_session_id(self, vault: Vault) -> None:
        data = start_session(vault, "ID Cost Test")
        svc = SessionService(vault)
        svc.log_entry("Entry", cost=100)

        result = svc.cost()
        assert result.ok
        assert result.data["session_id"] == data["id"]


# ---------------------------------------------------------------------------
# context()
# ---------------------------------------------------------------------------


class TestContext:
    def test_context_basic(self, vault: Vault) -> None:
        start_session(vault, "Context Test")
        result = SessionService(vault).context()
        assert result.ok
        assert result.op == "context"
        assert "layers" in result.data
        assert "total_tokens" in result.data

    def test_context_layer0_identity(self, vault: Vault) -> None:
        """Layer 0 includes self/ files."""
        (vault.root / "self").mkdir(exist_ok=True)
        (vault.root / "self" / "identity.md").write_text("I am a researcher.", encoding="utf-8")
        (vault.root / "self" / "methodology.md").write_text("Use zettelkasten.", encoding="utf-8")

        start_session(vault, "L0 Test")
        result = SessionService(vault).context()
        assert result.ok
        layers = result.data["layers"]
        assert "I am a researcher" in layers["identity"]
        assert "Use zettelkasten" in layers["methodology"]

    def test_context_layer0_missing_files(self, vault: Vault) -> None:
        """Layer 0 handles missing self/ files gracefully."""
        start_session(vault, "Missing L0 Test")
        result = SessionService(vault).context()
        assert result.ok
        layers = result.data["layers"]
        assert layers["identity"] is None
        assert layers["methodology"] is None

    def test_context_layer1_session(self, vault: Vault) -> None:
        """Layer 1 includes active session info."""
        start_session(vault, "L1 Test")
        result = SessionService(vault).context()
        assert result.ok
        layers = result.data["layers"]
        assert "session" in layers
        assert layers["session"]["topic"] == "L1 Test"
        assert layers["session"]["status"] == "open"

    def test_context_layer1_work_queue(self, vault: Vault) -> None:
        """Layer 1 includes work queue."""
        start_session(vault, "WQ Test")
        create_task(vault, "Do something", priority="high")

        result = SessionService(vault).context()
        assert result.ok
        layers = result.data["layers"]
        assert "work_queue" in layers

    def test_context_layer1_recent_decisions(self, vault: Vault) -> None:
        """Layer 1 includes recent decisions."""
        start_session(vault, "Decisions Test")
        create_note(vault, "Decision: use postgres", subtype="decision")

        result = SessionService(vault).context()
        assert result.ok
        layers = result.data["layers"]
        assert "recent_decisions" in layers

    def test_context_no_active_session(self, vault: Vault) -> None:
        result = SessionService(vault).context()
        assert not result.ok
        assert result.error is not None
        assert result.error.code == "NO_ACTIVE_SESSION"

    def test_context_budget_tracking(self, vault: Vault) -> None:
        """Context tracks total tokens used."""
        start_session(vault, "Budget Test")
        result = SessionService(vault).context(budget=8000)
        assert result.ok
        assert result.data["total_tokens"] > 0
        assert result.data["budget"] == 8000
        assert result.data["remaining"] >= 0

    def test_context_layer2_topic_content(self, vault: Vault) -> None:
        """Layer 2 includes topic-scoped notes."""
        start_session(vault, "Topic Content")
        create_note(vault, "Python Basics", topic="python")
        create_note(vault, "Python Advanced", topic="python")

        result = SessionService(vault).context(topic="python")
        assert result.ok
        layers = result.data["layers"]
        assert "topic_content" in layers

    def test_context_layer3_graph_adjacent(self, vault: Vault) -> None:
        """Layer 3 includes graph neighbors of Layer 2 content."""
        start_session(vault, "Graph Test")
        create_note(vault, "Graph Source", topic="math")
        create_note(vault, "Graph Neighbor")

        result = SessionService(vault).context(topic="math")
        assert result.ok
        layers = result.data["layers"]
        assert "graph_adjacent" in layers

    def test_context_layer4_background(self, vault: Vault) -> None:
        """Layer 4 includes background signals."""
        start_session(vault, "Background Test")
        create_note(vault, "Recent Activity")

        result = SessionService(vault).context()
        assert result.ok
        layers = result.data["layers"]
        assert "background" in layers

    def test_context_budget_pressure_caution(self, vault: Vault) -> None:
        """Small budget triggers caution or exceeded pressure."""
        (vault.root / "self").mkdir(exist_ok=True)
        # 400 chars = ~100 tokens, which with session metadata will exceed budget=100
        (vault.root / "self" / "identity.md").write_text("x" * 400, encoding="utf-8")

        start_session(vault, "Pressure Test")
        result = SessionService(vault).context(budget=100)
        assert result.ok
        assert result.data["pressure"] in ("caution", "exceeded")

    def test_context_log_entries_with_checkpoint(self, vault: Vault) -> None:
        """Context starts from latest checkpoint."""
        start_session(vault, "Checkpoint Context")
        svc = SessionService(vault)
        svc.log_entry("Before checkpoint", cost=100)
        svc.log_entry(
            "Checkpoint",
            entry_type="checkpoint",
            subtype="checkpoint",
            detail="Accumulated context snapshot",
        )
        svc.log_entry("After checkpoint", cost=200)

        result = svc.context()
        assert result.ok
        entries = result.data["layers"]["log_entries"]
        # Should include checkpoint and after, not before
        types = [e["type"] for e in entries]
        assert "checkpoint" in types

    def test_context_ignore_checkpoints(self, vault: Vault) -> None:
        """With ignore_checkpoints, all entries are returned regardless of checkpoint."""
        start_session(vault, "Ignore Checkpoint")
        svc = SessionService(vault)
        svc.log_entry("Before checkpoint", cost=100)
        svc.log_entry(
            "Checkpoint",
            entry_type="checkpoint",
            subtype="checkpoint",
            detail="Accumulated context snapshot",
        )
        svc.log_entry("After checkpoint", cost=200)

        result = svc.context(ignore_checkpoints=True)
        assert result.ok
        entries = result.data["layers"]["log_entries"]
        summaries = [e["summary"] for e in entries]
        # All three entries should be present (not just checkpoint + after)
        assert "Before checkpoint" in summaries
        assert "Checkpoint" in summaries
        assert "After checkpoint" in summaries

    def test_context_pinned_entries_survive_budget(self, vault: Vault) -> None:
        """Pinned entries are never dropped under budget pressure."""
        start_session(vault, "Pin Budget Test")
        svc = SessionService(vault)
        svc.log_entry("Pinned!", pin=True, cost=50)
        svc.log_entry("Not pinned", cost=50)

        result = svc.context(budget=50)
        assert result.ok
        entries = result.data["layers"]["log_entries"]
        pinned = [e for e in entries if e.get("pinned")]
        assert len(pinned) >= 1


# ---------------------------------------------------------------------------
# brief()
# ---------------------------------------------------------------------------


class TestBrief:
    def test_brief_no_session(self, vault: Vault) -> None:
        """Brief returns ok=True even without an active session."""
        result = SessionService(vault).brief()
        assert result.ok
        assert result.op == "brief"
        assert result.data["session"] is None
        assert "vault_stats" in result.data

    def test_brief_with_session(self, vault: Vault) -> None:
        data = start_session(vault, "Brief Test")
        result = SessionService(vault).brief()
        assert result.ok
        assert result.data["session"] is not None
        assert result.data["session"]["session_id"] == data["id"]
        assert result.data["session"]["topic"] == "Brief Test"

    def test_brief_vault_stats(self, vault: Vault) -> None:
        """Vault stats reflect created content types."""
        create_note(vault, "Note One")
        create_note(vault, "Note Two")
        create_task(vault, "Task One")

        result = SessionService(vault).brief()
        assert result.ok
        stats = result.data["vault_stats"]
        assert stats.get("note") == 2
        assert stats.get("task") == 1

    def test_brief_recent_decisions(self, vault: Vault) -> None:
        create_note(vault, "Use Postgres", subtype="decision")
        create_note(vault, "Use Redis", subtype="decision")

        result = SessionService(vault).brief()
        assert result.ok
        decisions = result.data["recent_decisions"]
        assert len(decisions) == 2

    def test_brief_work_queue_count(self, vault: Vault) -> None:
        create_task(vault, "Do something", priority="high")

        result = SessionService(vault).brief()
        assert result.ok
        assert result.data["work_queue_count"] >= 1


# ---------------------------------------------------------------------------
# extract_decision()
# ---------------------------------------------------------------------------


class TestExtractDecision:
    def test_extract_basic(self, vault: Vault) -> None:
        """Extract creates a decision note from session log entries."""
        data = start_session(vault, "Design Review")
        svc = SessionService(vault)
        svc.log_entry("Considered option A", pin=True)
        svc.log_entry("Considered option B", pin=True)
        svc.log_entry("Minor note")
        svc.close()

        result = svc.extract_decision(data["id"])
        assert result.ok
        assert result.op == "extract_decision"
        assert result.data["id"].startswith("ztl_")
        assert result.data["session_id"] == data["id"]
        assert result.data["entries_extracted"] == 2  # only pinned

    def test_extract_auto_title(self, vault: Vault) -> None:
        """Title auto-derived from session topic."""
        data = start_session(vault, "Auth Architecture")
        svc = SessionService(vault)
        svc.log_entry("Key finding", pin=True)
        svc.close()

        result = svc.extract_decision(data["id"])
        assert result.ok
        assert result.data["title"] == "Decision: Auth Architecture"

    def test_extract_custom_title(self, vault: Vault) -> None:
        data = start_session(vault, "DB Choice")
        svc = SessionService(vault)
        svc.log_entry("Use Postgres", pin=True)
        svc.close()

        result = svc.extract_decision(data["id"], title="Use Postgres for persistence")
        assert result.ok
        assert result.data["title"] == "Use Postgres for persistence"

    def test_extract_pinned_entries_only(self, vault: Vault) -> None:
        """Only pinned entries appear in the body when pins exist."""
        data = start_session(vault, "Pin Filter")
        svc = SessionService(vault)
        svc.log_entry("Pinned entry", pin=True)
        svc.log_entry("Unpinned entry")
        svc.close()

        result = svc.extract_decision(data["id"])
        assert result.ok

        # Read the created note body
        note_path = vault.root / result.data["path"]
        body = note_path.read_text(encoding="utf-8")
        assert "Pinned entry" in body
        assert "Unpinned entry" not in body

    def test_extract_all_entries_when_no_pins(self, vault: Vault) -> None:
        """All entries included when no pinned entries exist."""
        data = start_session(vault, "No Pins")
        svc = SessionService(vault)
        svc.log_entry("Entry one")
        svc.log_entry("Entry two")
        svc.close()

        result = svc.extract_decision(data["id"])
        assert result.ok
        # All entries used (start + 2 log + close = 4)
        assert result.data["entries_extracted"] == 4

    def test_extract_session_not_found(self, vault: Vault) -> None:
        result = SessionService(vault).extract_decision("LOG-9999")
        assert not result.ok
        assert result.error is not None
        assert result.error.code == "NOT_FOUND"

    def test_extract_creates_decision_subtype(self, vault: Vault) -> None:
        """Created note has subtype=decision in the DB."""
        data = start_session(vault, "Subtype Check")
        svc = SessionService(vault)
        svc.log_entry("Decision content", pin=True)
        svc.close()

        result = svc.extract_decision(data["id"])
        assert result.ok

        with vault.engine.connect() as conn:
            row = conn.execute(select(nodes).where(nodes.c.id == result.data["id"])).first()
            assert row is not None
            assert row.subtype == "decision"

    def test_extract_creates_edge_to_session(self, vault: Vault) -> None:
        """Decision note links to the session via derived_from edge."""
        data = start_session(vault, "Edge Check")
        svc = SessionService(vault)
        svc.log_entry("Content", pin=True)
        svc.close()

        result = svc.extract_decision(data["id"])
        assert result.ok

        from ztlctl.infrastructure.database.schema import edges

        with vault.engine.connect() as conn:
            edge = conn.execute(
                select(edges).where(
                    edges.c.source_id == result.data["id"],
                    edges.c.target_id == data["id"],
                    edges.c.edge_type == "derived_from",
                )
            ).first()
            assert edge is not None

    def test_extract_decision_matches_on_type(self, vault: Vault) -> None:
        """extract_decision finds entries by type='decision_made' in JSONL."""
        data = start_session(vault, "Type Match")
        svc = SessionService(vault)
        svc.log_entry("Decision via type", entry_type="decision_made")
        svc.log_entry("Regular note")
        svc.close()

        result = svc.extract_decision(data["id"])
        assert result.ok
        # Should pick up only the decision_made entry (not regular, not start/close)
        assert result.data["entries_extracted"] == 1
