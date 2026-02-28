"""Tests for QueryService — five read-only query surfaces."""

from __future__ import annotations

from ztlctl.infrastructure.vault import Vault
from ztlctl.services.create import CreateService
from ztlctl.services.query import QueryService

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _seed_notes(vault: Vault) -> CreateService:
    """Create a set of notes/refs/tasks for query tests."""
    svc = CreateService(vault)
    svc.create_note("Alpha Note", tags=["ai/ml"], topic="math")
    svc.create_note("Beta Note", tags=["ai/nlp"])
    svc.create_note("Gamma Decision", subtype="decision", topic="math")
    svc.create_reference("Python Docs", url="https://docs.python.org", tags=["lang/python"])
    svc.create_reference("Rust Guide", tags=["lang/rust"])
    svc.create_task("Fix login bug", priority="high", impact="high", effort="low")
    svc.create_task("Write tests", priority="medium", impact="medium", effort="medium")
    svc.create_task("Refactor auth", priority="low", impact="low", effort="high")
    return svc


# ---------------------------------------------------------------------------
# search
# ---------------------------------------------------------------------------


class TestSearch:
    def test_search_by_title(self, vault: Vault) -> None:
        _seed_notes(vault)
        svc = QueryService(vault)
        result = svc.search("Alpha")
        assert result.ok
        assert result.data["count"] >= 1
        titles = [i["title"] for i in result.data["items"]]
        assert "Alpha Note" in titles

    def test_search_multiple_results(self, vault: Vault) -> None:
        _seed_notes(vault)
        svc = QueryService(vault)
        result = svc.search("Note")
        assert result.ok
        assert result.data["count"] >= 2

    def test_search_filter_by_type(self, vault: Vault) -> None:
        _seed_notes(vault)
        svc = QueryService(vault)
        result = svc.search("Python OR Rust", content_type="reference")
        assert result.ok
        for item in result.data["items"]:
            assert item["type"] == "reference"

    def test_search_filter_by_tag(self, vault: Vault) -> None:
        _seed_notes(vault)
        svc = QueryService(vault)
        result = svc.search("Alpha", tag="ai/ml")
        assert result.ok
        assert result.data["count"] >= 1

    def test_search_no_results(self, vault: Vault) -> None:
        _seed_notes(vault)
        svc = QueryService(vault)
        result = svc.search("xyznonexistent")
        assert result.ok
        assert result.data["count"] == 0

    def test_search_empty_query(self, vault: Vault) -> None:
        svc = QueryService(vault)
        result = svc.search("")
        assert not result.ok
        assert result.error is not None
        assert result.error.code == "EMPTY_QUERY"

    def test_search_rank_by_recency(self, vault: Vault) -> None:
        _seed_notes(vault)
        svc = QueryService(vault)
        result = svc.search("Note", rank_by="recency")
        assert result.ok
        assert result.data["count"] >= 2

    def test_search_with_limit(self, vault: Vault) -> None:
        _seed_notes(vault)
        svc = QueryService(vault)
        result = svc.search("Note", limit=1)
        assert result.ok
        assert result.data["count"] <= 1

    def test_search_returns_score(self, vault: Vault) -> None:
        _seed_notes(vault)
        svc = QueryService(vault)
        result = svc.search("Alpha")
        assert result.ok
        for item in result.data["items"]:
            assert "score" in item


# ---------------------------------------------------------------------------
# get
# ---------------------------------------------------------------------------


class TestGet:
    def test_get_existing_note(self, vault: Vault) -> None:
        cs = CreateService(vault)
        r = cs.create_note("Get Test Note", tags=["test/get"])
        assert r.ok

        svc = QueryService(vault)
        result = svc.get(r.data["id"])
        assert result.ok
        assert result.data["title"] == "Get Test Note"
        assert result.data["tags"] == ["test/get"]
        assert "body" in result.data

    def test_get_includes_links(self, vault: Vault) -> None:
        cs = CreateService(vault)
        r = cs.create_note("Linked Note")
        assert r.ok

        svc = QueryService(vault)
        result = svc.get(r.data["id"])
        assert result.ok
        assert "links_out" in result.data
        assert "links_in" in result.data

    def test_get_not_found(self, vault: Vault) -> None:
        svc = QueryService(vault)
        result = svc.get("nonexistent_id")
        assert not result.ok
        assert result.error is not None
        assert result.error.code == "NOT_FOUND"

    def test_get_reference(self, vault: Vault) -> None:
        cs = CreateService(vault)
        r = cs.create_reference("Ref for Get", url="https://example.com")
        assert r.ok

        svc = QueryService(vault)
        result = svc.get(r.data["id"])
        assert result.ok
        assert result.data["type"] == "reference"

    def test_get_task(self, vault: Vault) -> None:
        cs = CreateService(vault)
        r = cs.create_task("Task for Get")
        assert r.ok

        svc = QueryService(vault)
        result = svc.get(r.data["id"])
        assert result.ok
        assert result.data["type"] == "task"

    def test_get_includes_maturity(self, vault: Vault) -> None:
        cs = CreateService(vault)
        r = cs.create_note("Garden Get", maturity="seed")
        assert r.ok

        result = QueryService(vault).get(r.data["id"])

        assert result.ok
        assert result.data["maturity"] == "seed"


# ---------------------------------------------------------------------------
# list_items
# ---------------------------------------------------------------------------


class TestListItems:
    def test_list_all(self, vault: Vault) -> None:
        _seed_notes(vault)
        svc = QueryService(vault)
        result = svc.list_items()
        assert result.ok
        assert result.data["count"] == 8  # 3 notes + 2 refs + 3 tasks

    def test_list_by_type(self, vault: Vault) -> None:
        _seed_notes(vault)
        svc = QueryService(vault)
        result = svc.list_items(content_type="note")
        assert result.ok
        for item in result.data["items"]:
            assert item["type"] == "note"

    def test_list_by_status(self, vault: Vault) -> None:
        _seed_notes(vault)
        svc = QueryService(vault)
        result = svc.list_items(content_type="task", status="inbox")
        assert result.ok
        for item in result.data["items"]:
            assert item["status"] == "inbox"

    def test_list_by_tag(self, vault: Vault) -> None:
        _seed_notes(vault)
        svc = QueryService(vault)
        result = svc.list_items(tag="ai/ml")
        assert result.ok
        assert result.data["count"] >= 1

    def test_list_by_topic(self, vault: Vault) -> None:
        _seed_notes(vault)
        svc = QueryService(vault)
        result = svc.list_items(topic="math")
        assert result.ok
        assert result.data["count"] >= 1
        for item in result.data["items"]:
            assert item["topic"] == "math"

    def test_list_sort_by_title(self, vault: Vault) -> None:
        _seed_notes(vault)
        svc = QueryService(vault)
        result = svc.list_items(content_type="note", sort="title")
        assert result.ok
        titles = [i["title"] for i in result.data["items"]]
        assert titles == sorted(titles)

    def test_list_sort_by_type(self, vault: Vault) -> None:
        _seed_notes(vault)
        svc = QueryService(vault)
        result = svc.list_items(sort="type")
        assert result.ok
        types = [i["type"] for i in result.data["items"]]
        assert types == sorted(types)

    def test_list_with_limit(self, vault: Vault) -> None:
        _seed_notes(vault)
        svc = QueryService(vault)
        result = svc.list_items(limit=3)
        assert result.ok
        assert result.data["count"] <= 3

    def test_list_empty_vault(self, vault: Vault) -> None:
        svc = QueryService(vault)
        result = svc.list_items()
        assert result.ok
        assert result.data["count"] == 0


# ---------------------------------------------------------------------------
# list_items — extended filters and sort modes
# ---------------------------------------------------------------------------


class TestListItemsExtended:
    """Extended filters and sort modes for list_items."""

    def test_filter_by_subtype(self, vault: Vault) -> None:
        _seed_notes(vault)
        svc = QueryService(vault)
        result = svc.list_items(subtype="decision")
        assert result.ok
        assert result.data["count"] >= 1
        for item in result.data["items"]:
            assert item["subtype"] == "decision"

    def test_filter_by_subtype_no_match(self, vault: Vault) -> None:
        _seed_notes(vault)
        svc = QueryService(vault)
        result = svc.list_items(subtype="article")
        assert result.ok
        assert result.data["count"] == 0

    def test_filter_by_maturity(self, vault: Vault) -> None:
        from ztlctl.services.update import UpdateService

        svc_c = CreateService(vault)
        r = svc_c.create_note("Garden Note", topic="botany")
        assert r.ok
        UpdateService(vault).update(r.data["id"], changes={"maturity": "seed"})

        svc = QueryService(vault)
        result = svc.list_items(maturity="seed")
        assert result.ok
        assert result.data["count"] >= 1
        for item in result.data["items"]:
            assert item["maturity"] == "seed"

    def test_filter_by_maturity_no_match(self, vault: Vault) -> None:
        _seed_notes(vault)
        svc = QueryService(vault)
        result = svc.list_items(maturity="evergreen")
        assert result.ok
        assert result.data["count"] == 0

    def test_maturity_in_result(self, vault: Vault) -> None:
        _seed_notes(vault)
        svc = QueryService(vault)
        result = svc.list_items()
        assert result.ok
        for item in result.data["items"]:
            assert "maturity" in item

    def test_since_today(self, vault: Vault) -> None:
        from datetime import UTC, datetime

        _seed_notes(vault)
        svc = QueryService(vault)
        today = datetime.now(UTC).date().isoformat()
        result = svc.list_items(since=today)
        assert result.ok
        assert result.data["count"] == 8

    def test_since_future(self, vault: Vault) -> None:
        _seed_notes(vault)
        svc = QueryService(vault)
        result = svc.list_items(since="2099-01-01")
        assert result.ok
        assert result.data["count"] == 0

    def test_since_past(self, vault: Vault) -> None:
        _seed_notes(vault)
        svc = QueryService(vault)
        result = svc.list_items(since="2000-01-01")
        assert result.ok
        assert result.data["count"] == 8

    def test_include_archived(self, vault: Vault) -> None:
        from ztlctl.services.update import UpdateService

        _seed_notes(vault)
        svc = QueryService(vault)
        us = UpdateService(vault)

        all_result = svc.list_items()
        first_id = all_result.data["items"][0]["id"]
        us.archive(first_id)

        result = svc.list_items()
        assert result.ok
        assert result.data["count"] == 7

        result = svc.list_items(include_archived=True)
        assert result.ok
        assert result.data["count"] == 8

    def test_include_archived_default(self, vault: Vault) -> None:
        _seed_notes(vault)
        svc = QueryService(vault)
        result = svc.list_items()
        assert result.ok
        assert result.data["count"] == 8

    def test_sort_priority_scores_present(self, vault: Vault) -> None:
        _seed_notes(vault)
        svc = QueryService(vault)
        result = svc.list_items(sort="priority")
        assert result.ok
        for item in result.data["items"]:
            assert "score" in item

    def test_sort_priority_descending(self, vault: Vault) -> None:
        _seed_notes(vault)
        svc = QueryService(vault)
        result = svc.list_items(sort="priority")
        assert result.ok
        scores = [item["score"] for item in result.data["items"]]
        assert scores == sorted(scores, reverse=True)

    def test_sort_priority_tasks_first(self, vault: Vault) -> None:
        _seed_notes(vault)
        svc = QueryService(vault)
        result = svc.list_items(sort="priority")
        assert result.ok
        first = result.data["items"][0]
        assert first["type"] == "task"
        assert first["title"] == "Fix login bug"

    def test_sort_priority_nontasks_zero(self, vault: Vault) -> None:
        _seed_notes(vault)
        svc = QueryService(vault)
        result = svc.list_items(sort="priority")
        assert result.ok
        for item in result.data["items"]:
            if item["type"] != "task":
                assert item["score"] == 0.0

    def test_sort_priority_with_limit(self, vault: Vault) -> None:
        _seed_notes(vault)
        svc = QueryService(vault)
        result = svc.list_items(sort="priority", limit=3)
        assert result.ok
        assert result.data["count"] == 3
        for item in result.data["items"]:
            assert item["type"] == "task"

    def test_combined_filters(self, vault: Vault) -> None:
        _seed_notes(vault)
        svc = QueryService(vault)
        result = svc.list_items(content_type="note", topic="math")
        assert result.ok
        for item in result.data["items"]:
            assert item["type"] == "note"
            assert item["topic"] == "math"


# ---------------------------------------------------------------------------
# work_queue
# ---------------------------------------------------------------------------


class TestWorkQueue:
    def test_work_queue_returns_tasks(self, vault: Vault) -> None:
        _seed_notes(vault)
        svc = QueryService(vault)
        result = svc.work_queue()
        assert result.ok
        assert result.data["count"] == 3

    def test_work_queue_sorted_by_score(self, vault: Vault) -> None:
        _seed_notes(vault)
        svc = QueryService(vault)
        result = svc.work_queue()
        assert result.ok
        scores = [t["score"] for t in result.data["items"]]
        assert scores == sorted(scores, reverse=True)

    def test_work_queue_high_priority_first(self, vault: Vault) -> None:
        _seed_notes(vault)
        svc = QueryService(vault)
        result = svc.work_queue()
        assert result.ok
        # "Fix login bug" (high/high/low) should score highest
        first = result.data["items"][0]
        assert first["title"] == "Fix login bug"

    def test_work_queue_includes_score(self, vault: Vault) -> None:
        _seed_notes(vault)
        svc = QueryService(vault)
        result = svc.work_queue()
        assert result.ok
        for task in result.data["items"]:
            assert "score" in task
            assert isinstance(task["score"], float)

    def test_work_queue_excludes_done(self, vault: Vault) -> None:
        """Done/dropped tasks should not appear in work queue."""
        svc = QueryService(vault)
        result = svc.work_queue()
        assert result.ok
        assert result.data["count"] == 0

    def test_work_queue_empty(self, vault: Vault) -> None:
        svc = QueryService(vault)
        result = svc.work_queue()
        assert result.ok
        assert result.data["count"] == 0


# ---------------------------------------------------------------------------
# decision_support
# ---------------------------------------------------------------------------


class TestDecisionSupport:
    def test_decision_support_all(self, vault: Vault) -> None:
        _seed_notes(vault)
        svc = QueryService(vault)
        result = svc.decision_support()
        assert result.ok
        assert result.data["counts"]["decisions"] >= 1
        assert result.data["counts"]["notes"] >= 1
        assert result.data["counts"]["references"] >= 1

    def test_decision_support_by_topic(self, vault: Vault) -> None:
        _seed_notes(vault)
        svc = QueryService(vault)
        result = svc.decision_support(topic="math")
        assert result.ok
        # Gamma Decision and Alpha Note are in "math"
        assert result.data["counts"]["decisions"] >= 1
        assert result.data["counts"]["notes"] >= 1
        # No references in "math"
        assert result.data["counts"]["references"] == 0

    def test_decision_support_excludes_tasks(self, vault: Vault) -> None:
        _seed_notes(vault)
        svc = QueryService(vault)
        result = svc.decision_support()
        assert result.ok
        all_items = result.data["decisions"] + result.data["notes"] + result.data["references"]
        for item in all_items:
            assert item["type"] != "task"

    def test_decision_support_empty_topic(self, vault: Vault) -> None:
        _seed_notes(vault)
        svc = QueryService(vault)
        result = svc.decision_support(topic="nonexistent")
        assert result.ok
        assert result.data["counts"]["decisions"] == 0
        assert result.data["counts"]["notes"] == 0
        assert result.data["counts"]["references"] == 0

    def test_decision_support_partitions_correctly(self, vault: Vault) -> None:
        _seed_notes(vault)
        svc = QueryService(vault)
        result = svc.decision_support()
        assert result.ok
        for d in result.data["decisions"]:
            assert d["subtype"] == "decision"
        for r in result.data["references"]:
            assert r["type"] == "reference"
        for n in result.data["notes"]:
            assert n["type"] == "note"
            assert n["subtype"] != "decision"


# ---------------------------------------------------------------------------
# space filter
# ---------------------------------------------------------------------------


class TestSpaceFilter:
    """Tests for --space filtering across query methods."""

    def test_search_space_notes(self, vault: Vault) -> None:
        """Notes/refs returned when filtering by notes space."""
        _seed_notes(vault)
        svc = QueryService(vault)
        # "Note" matches Alpha Note, Beta Note — both under notes/
        result = svc.search("Note", space="notes")
        assert result.ok
        assert result.data["count"] >= 2
        for item in result.data["items"]:
            assert item["path"].startswith("notes/")

    def test_search_space_ops(self, vault: Vault) -> None:
        """Tasks returned when filtering by ops space."""
        _seed_notes(vault)
        svc = QueryService(vault)
        # "bug" matches "Fix login bug" task — under ops/
        result = svc.search("bug", space="ops")
        assert result.ok
        assert result.data["count"] >= 1
        for item in result.data["items"]:
            assert item["path"].startswith("ops/")

    def test_search_space_excludes_other(self, vault: Vault) -> None:
        """Notes space excludes tasks."""
        _seed_notes(vault)
        svc = QueryService(vault)
        # "bug" is a task — shouldn't appear in notes space
        result = svc.search("bug", space="notes")
        assert result.ok
        assert result.data["count"] == 0

    def test_list_space_notes(self, vault: Vault) -> None:
        """List with notes space returns only notes/refs."""
        _seed_notes(vault)
        svc = QueryService(vault)
        result = svc.list_items(space="notes")
        assert result.ok
        assert result.data["count"] == 5  # 3 notes + 2 refs
        for item in result.data["items"]:
            assert item["path"].startswith("notes/")

    def test_list_space_ops(self, vault: Vault) -> None:
        """List with ops space returns only tasks."""
        _seed_notes(vault)
        svc = QueryService(vault)
        result = svc.list_items(space="ops")
        assert result.ok
        assert result.data["count"] == 3  # 3 tasks
        for item in result.data["items"]:
            assert item["path"].startswith("ops/")

    def test_work_queue_space_ops(self, vault: Vault) -> None:
        """Work queue with ops space returns tasks (all tasks are under ops)."""
        _seed_notes(vault)
        svc = QueryService(vault)
        result = svc.work_queue(space="ops")
        assert result.ok
        assert result.data["count"] == 3

    def test_work_queue_space_notes(self, vault: Vault) -> None:
        """Work queue with notes space returns 0 (no tasks under notes/)."""
        _seed_notes(vault)
        svc = QueryService(vault)
        result = svc.work_queue(space="notes")
        assert result.ok
        assert result.data["count"] == 0

    def test_decision_support_space_notes(self, vault: Vault) -> None:
        """Decision support with notes space returns decisions/notes/refs."""
        _seed_notes(vault)
        svc = QueryService(vault)
        result = svc.decision_support(space="notes")
        assert result.ok
        total = (
            result.data["counts"]["decisions"]
            + result.data["counts"]["notes"]
            + result.data["counts"]["references"]
        )
        assert total >= 1

    def test_decision_support_space_ops(self, vault: Vault) -> None:
        """Decision support with ops space returns empty (no notes/refs in ops)."""
        _seed_notes(vault)
        svc = QueryService(vault)
        result = svc.decision_support(space="ops")
        assert result.ok
        assert result.data["counts"]["decisions"] == 0
        assert result.data["counts"]["notes"] == 0
        assert result.data["counts"]["references"] == 0


# ---------------------------------------------------------------------------
# search — time-decay ranking
# ---------------------------------------------------------------------------


class TestSearchTimeDecay:
    """Tests for BM25 x time-decay recency ranking."""

    def test_recency_returns_positive_scores(self, vault: Vault) -> None:
        """Recency mode produces positive combined scores (negated BM25 x decay)."""
        _seed_notes(vault)
        svc = QueryService(vault)
        result = svc.search("Note", rank_by="recency")
        assert result.ok
        assert result.data["count"] >= 2
        for item in result.data["items"]:
            assert item["score"] > 0

    def test_recency_recent_note_ranks_higher(self, vault: Vault) -> None:
        """A recently modified note ranks higher than an older one."""
        from datetime import UTC, datetime, timedelta

        from sqlalchemy import text as sa_text

        # Seed corpus for meaningful BM25 IDF
        _seed_notes(vault)

        svc_c = CreateService(vault)
        r1 = svc_c.create_note("Recency Alpha Signal", tags=["test"])
        r2 = svc_c.create_note("Recency Beta Signal", tags=["test"])
        assert r1.ok and r2.ok

        # Push the first note's modified time back by 365 days (>>half-life)
        old_time = (datetime.now(UTC) - timedelta(days=365)).isoformat()
        with vault.engine.begin() as conn:
            conn.execute(
                sa_text("UPDATE nodes SET modified = :ts WHERE id = :id"),
                {"ts": old_time, "id": r1.data["id"]},
            )

        svc = QueryService(vault)
        result = svc.search("Recency Signal", rank_by="recency")
        assert result.ok
        assert result.data["count"] == 2
        ids = [i["id"] for i in result.data["items"]]
        # New note should rank before old note (365-day gap overwhelms BM25 diff)
        assert ids.index(r2.data["id"]) < ids.index(r1.data["id"])

    def test_recency_with_custom_half_life(self, vault: Vault) -> None:
        """Shorter half-life produces more aggressive decay."""
        from datetime import UTC, datetime, timedelta

        from sqlalchemy import text as sa_text

        # Seed corpus for meaningful BM25 IDF
        _seed_notes(vault)

        svc_c = CreateService(vault)
        r = svc_c.create_note("Decay Halflife Measure")
        assert r.ok

        # Push modified back by 30 days (exactly 1 half-life at default 30 days)
        old_time = (datetime.now(UTC) - timedelta(days=30)).isoformat()
        with vault.engine.begin() as conn:
            conn.execute(
                sa_text("UPDATE nodes SET modified = :ts WHERE id = :id"),
                {"ts": old_time, "id": r.data["id"]},
            )

        svc = QueryService(vault)

        # Default half-life (30 days) — 50% decay
        result_default = svc.search("Decay Halflife", rank_by="recency")
        assert result_default.ok
        score_default = result_default.data["items"][0]["score"]
        assert score_default > 0

        # Override half-life to 1 day — much more decay for 30 days old
        original = vault.settings.search.half_life_days
        object.__setattr__(vault.settings.search, "half_life_days", 1.0)
        try:
            result_short = svc.search("Decay Halflife", rank_by="recency")
            assert result_short.ok
            score_short = result_short.data["items"][0]["score"]
            assert score_short < score_default
        finally:
            object.__setattr__(vault.settings.search, "half_life_days", original)

    def test_apply_time_decay_directly(self, vault: Vault) -> None:
        """Unit test for _apply_time_decay with mock items."""
        from datetime import UTC, datetime, timedelta

        svc = QueryService(vault)
        now = datetime.now(UTC)

        items = [
            {"score": -5.0, "modified": now.isoformat()},
            {"score": -5.0, "modified": (now - timedelta(days=30)).isoformat()},
            {"score": -5.0, "modified": (now - timedelta(days=60)).isoformat()},
        ]

        result = svc._apply_time_decay(items, half_life=30.0, limit=10)

        # All scores should be positive
        for item in result:
            assert item["score"] > 0

        # Scores should decrease with age
        assert result[0]["score"] > result[1]["score"] > result[2]["score"]

        # 30-day-old item should have roughly half the score of the fresh one
        ratio = result[1]["score"] / result[0]["score"]
        assert 0.45 <= ratio <= 0.55  # ~0.5 with half-life of 30 days


# ---------------------------------------------------------------------------
# search — graph ranking
# ---------------------------------------------------------------------------


class TestSearchGraphRank:
    """Tests for BM25 x PageRank graph ranking."""

    def test_graph_rank_with_materialized_metrics(self, vault: Vault) -> None:
        """Search with rank_by=graph uses PageRank after materialization."""
        from ztlctl.services.graph import GraphService

        _seed_notes(vault)

        # Materialize graph metrics
        mat_result = GraphService(vault).materialize_metrics()
        assert mat_result.ok

        svc = QueryService(vault)
        result = svc.search("Note", rank_by="graph")
        assert result.ok
        assert result.data["count"] >= 1
        # Scores should be positive (abs(bm25) * pagerank)
        for item in result.data["items"]:
            assert item["score"] >= 0

    def test_graph_rank_without_metrics_warns(self, vault: Vault) -> None:
        """Search without materializing falls back to BM25 with warning."""
        _seed_notes(vault)
        svc = QueryService(vault)
        result = svc.search("Note", rank_by="graph")
        assert result.ok
        assert result.warnings
        assert any("materialize" in w for w in result.warnings)
