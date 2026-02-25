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
