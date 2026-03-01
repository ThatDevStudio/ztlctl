"""Tests for MCP tool _impl functions (no mcp package needed)."""

from __future__ import annotations

from pathlib import Path

import pytest

from ztlctl.config.settings import ZtlSettings
from ztlctl.infrastructure.vault import Vault
from ztlctl.mcp.tools import (
    agent_context_impl,
    close_content_impl,
    create_log_impl,
    create_note_impl,
    create_reference_impl,
    create_task_impl,
    decision_support_impl,
    discover_tools_impl,
    garden_seed_impl,
    get_document_impl,
    get_related_impl,
    graph_gaps_impl,
    graph_path_impl,
    graph_rank_impl,
    graph_themes_impl,
    list_items_impl,
    register_tools,
    reweave_impl,
    search_impl,
    session_close_impl,
    update_content_impl,
    work_queue_impl,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def vault_root(tmp_path: Path) -> Path:
    """Vault directory structure."""
    (tmp_path / "notes").mkdir()
    (tmp_path / "ops" / "logs").mkdir(parents=True)
    (tmp_path / "ops" / "tasks").mkdir(parents=True)
    return tmp_path


@pytest.fixture
def vault(vault_root: Path) -> Vault:
    """Vault for MCP tool tests."""
    settings = ZtlSettings.from_cli(vault_root=vault_root)
    return Vault(settings)


# ---------------------------------------------------------------------------
# Tests — Creation tools
# ---------------------------------------------------------------------------


class TestCreateTools:
    """Tests for creation _impl functions."""

    def test_create_note_returns_ok(self, vault: Vault):
        resp = create_note_impl(vault, "Test Note")
        assert resp["ok"] is True
        assert resp["op"] == "create_note"
        assert "id" in resp["data"]

    def test_create_reference_returns_ok(self, vault: Vault):
        resp = create_reference_impl(vault, "Test Ref", url="https://example.com")
        assert resp["ok"] is True
        assert resp["op"] == "create_reference"

    def test_create_task_returns_ok(self, vault: Vault):
        resp = create_task_impl(vault, "Test Task", priority="high")
        assert resp["ok"] is True
        assert resp["op"] == "create_task"

    def test_create_log_starts_session(self, vault: Vault):
        resp = create_log_impl(vault, "research")
        assert resp["ok"] is True
        assert resp["op"] == "session_start"
        assert resp["data"]["topic"] == "research"

    def test_create_note_with_tags(self, vault: Vault):
        resp = create_note_impl(vault, "Tagged", tags=["test/alpha"])
        assert resp["ok"] is True
        assert "id" in resp["data"]

    def test_create_note_with_topic(self, vault: Vault):
        resp = create_note_impl(vault, "Topic Note", topic="math")
        assert resp["ok"] is True

    def test_garden_seed_returns_ok(self, vault: Vault):
        resp = garden_seed_impl(vault, "Quick idea")
        assert resp["ok"] is True
        assert resp["op"] == "create_note"
        assert "id" in resp["data"]

    def test_garden_seed_with_tags(self, vault: Vault):
        resp = garden_seed_impl(vault, "Tagged seed", tags=["research/ai"])
        assert resp["ok"] is True


# ---------------------------------------------------------------------------
# Tests — Discovery tools
# ---------------------------------------------------------------------------


class TestDiscoveryTools:
    """Tests for discovery _impl and registration."""

    def test_discover_tools_returns_grouped_catalog(self, vault: Vault):
        resp = discover_tools_impl(vault)
        assert resp["ok"] is True
        assert resp["op"] == "discover_tools"
        assert resp["data"]["count"] >= 21
        categories = {entry["name"] for entry in resp["data"]["categories"]}
        assert "discovery" in categories
        assert "creation" in categories
        assert "query" in categories
        assert "graph" in categories
        assert "analysis" in categories

    def test_discover_tools_filters_by_category(self, vault: Vault):
        resp = discover_tools_impl(vault, category="creation")
        assert resp["ok"] is True
        assert resp["data"]["count"] == 5
        categories = resp["data"]["categories"]
        assert len(categories) == 1
        assert categories[0]["name"] == "creation"
        names = {tool["name"] for tool in categories[0]["tools"]}
        assert "create_note" in names
        assert "create_reference" in names

    def test_register_tools_includes_discover_tools(self, vault: Vault):
        class DummyServer:
            def __init__(self) -> None:
                self.tools: list[str] = []

            def tool(self):
                def decorator(fn):
                    self.tools.append(fn.__name__)
                    return fn

                return decorator

        server = DummyServer()
        register_tools(server, vault)
        assert "discover_tools" in server.tools


# ---------------------------------------------------------------------------
# Tests — Lifecycle tools
# ---------------------------------------------------------------------------


class TestLifecycleTools:
    """Tests for lifecycle _impl functions."""

    def test_update_content(self, vault: Vault):
        create_resp = create_note_impl(vault, "To Update")
        content_id = create_resp["data"]["id"]

        resp = update_content_impl(vault, content_id, changes={"title": "Updated"})
        assert resp["ok"] is True
        assert resp["op"] == "update"

    def test_close_content(self, vault: Vault):
        create_resp = create_note_impl(vault, "To Close")
        content_id = create_resp["data"]["id"]

        resp = close_content_impl(vault, content_id)
        assert resp["ok"] is True
        assert resp["op"] == "archive"

    def test_reweave_dry_run(self, vault: Vault):
        create_note_impl(vault, "Reweave Target")
        resp = reweave_impl(vault, dry_run=True)
        assert resp["ok"] is True

    def test_update_nonexistent_fails(self, vault: Vault):
        resp = update_content_impl(vault, "NONEXISTENT", changes={"title": "X"})
        assert resp["ok"] is False
        assert "error" in resp


# ---------------------------------------------------------------------------
# Tests — Query tools
# ---------------------------------------------------------------------------


class TestQueryTools:
    """Tests for query _impl functions."""

    def test_search_returns_results(self, vault: Vault):
        create_note_impl(vault, "Searchable Note")
        resp = search_impl(vault, "Searchable")
        assert resp["ok"] is True
        assert resp["op"] == "search"

    def test_get_document(self, vault: Vault):
        create_resp = create_note_impl(vault, "Get Me")
        content_id = create_resp["data"]["id"]

        resp = get_document_impl(vault, content_id)
        assert resp["ok"] is True
        assert resp["data"]["id"] == content_id

    def test_get_document_not_found(self, vault: Vault):
        resp = get_document_impl(vault, "NONEXISTENT")
        assert resp["ok"] is False

    def test_get_related(self, vault: Vault):
        create_resp = create_note_impl(vault, "Related Test")
        content_id = create_resp["data"]["id"]

        resp = get_related_impl(vault, content_id)
        assert resp["ok"] is True

    def test_agent_context_returns_data(self, vault: Vault):
        create_note_impl(vault, "Context Note")
        resp = agent_context_impl(vault)
        assert resp["ok"] is True
        assert "data" in resp

    def test_agent_context_with_query(self, vault: Vault):
        create_note_impl(vault, "Context Search")
        resp = agent_context_impl(vault, query="Context")
        assert resp["ok"] is True

    def test_agent_context_fallback_total_items(self, vault: Vault):
        create_note_impl(vault, "Fallback Count")
        create_task_impl(vault, "Fallback Task")

        resp = agent_context_impl(vault)
        assert resp["ok"] is True
        assert resp["data"]["total_items"] >= 2

    def test_agent_context_fallback_search_results(self, vault: Vault):
        created = create_note_impl(vault, "Fallback Search Item")

        resp = agent_context_impl(vault, query="Fallback")
        assert resp["ok"] is True
        items = resp["data"].get("search_results", [])
        assert items
        ids = {item["id"] for item in items}
        assert created["data"]["id"] in ids


# ---------------------------------------------------------------------------
# Tests — List/Work-queue/Decision-support tools
# ---------------------------------------------------------------------------


class TestListQueryTools:
    """Tests for list_items, work_queue, decision_support _impl functions."""

    def test_list_items_returns_ok(self, vault: Vault):
        create_note_impl(vault, "List Item A")
        create_note_impl(vault, "List Item B")
        resp = list_items_impl(vault)
        assert resp["ok"] is True
        assert resp["op"] == "list_items"
        assert resp["data"]["count"] >= 2

    def test_list_items_filter_by_type(self, vault: Vault):
        create_note_impl(vault, "Note for filter")
        create_task_impl(vault, "Task for filter")
        resp = list_items_impl(vault, content_type="note")
        assert resp["ok"] is True
        for item in resp["data"]["items"]:
            assert item["type"] == "note"

    def test_list_items_with_limit(self, vault: Vault):
        for i in range(5):
            create_note_impl(vault, f"Limit note {i}")
        resp = list_items_impl(vault, limit=3)
        assert resp["ok"] is True
        assert len(resp["data"]["items"]) <= 3

    def test_work_queue_returns_ok(self, vault: Vault):
        create_task_impl(vault, "Queued task", priority="high")
        resp = work_queue_impl(vault)
        assert resp["ok"] is True
        assert resp["op"] == "work_queue"

    def test_work_queue_includes_tasks(self, vault: Vault):
        create_task_impl(vault, "Priority task", priority="critical")
        resp = work_queue_impl(vault)
        assert resp["ok"] is True
        assert resp["data"]["count"] >= 1

    def test_decision_support_returns_ok(self, vault: Vault):
        create_note_impl(vault, "Decision note", topic="architecture")
        resp = decision_support_impl(vault, topic="architecture")
        assert resp["ok"] is True
        assert resp["op"] == "decision_support"

    def test_decision_support_has_counts(self, vault: Vault):
        resp = decision_support_impl(vault)
        assert resp["ok"] is True
        assert "counts" in resp["data"]


# ---------------------------------------------------------------------------
# Tests — Graph tools
# ---------------------------------------------------------------------------


class TestGraphTools:
    """Tests for graph_themes, graph_rank, graph_path, graph_gaps _impl functions."""

    def test_graph_themes_empty_vault(self, vault: Vault):
        resp = graph_themes_impl(vault)
        assert resp["ok"] is True
        assert resp["op"] == "themes"
        assert resp["data"]["count"] == 0

    def test_graph_rank_empty_vault(self, vault: Vault):
        resp = graph_rank_impl(vault)
        assert resp["ok"] is True
        assert resp["op"] == "rank"
        assert resp["data"]["count"] == 0

    def test_graph_rank_with_top(self, vault: Vault):
        resp = graph_rank_impl(vault, top=5)
        assert resp["ok"] is True

    def test_graph_path_not_found(self, vault: Vault):
        resp = graph_path_impl(vault, "NONEXISTENT_A", "NONEXISTENT_B")
        assert resp["ok"] is False
        assert "error" in resp

    def test_graph_gaps_empty_vault(self, vault: Vault):
        resp = graph_gaps_impl(vault)
        assert resp["ok"] is True
        assert resp["op"] == "gaps"
        assert resp["data"]["count"] == 0

    def test_graph_gaps_with_top(self, vault: Vault):
        resp = graph_gaps_impl(vault, top=10)
        assert resp["ok"] is True


# ---------------------------------------------------------------------------
# Tests — Session tools
# ---------------------------------------------------------------------------


class TestSessionTools:
    """Tests for session _impl functions."""

    def test_session_close(self, vault: Vault):
        create_log_impl(vault, "close-test")
        resp = session_close_impl(vault, summary="done")
        assert resp["ok"] is True
        assert resp["op"] == "session_close"

    def test_session_close_no_active(self, vault: Vault):
        resp = session_close_impl(vault)
        assert resp["ok"] is False


# ---------------------------------------------------------------------------
# Tests — MCP response format
# ---------------------------------------------------------------------------


class TestMcpResponse:
    """Tests for _to_mcp_response helper."""

    def test_success_response_format(self, vault: Vault):
        resp = create_note_impl(vault, "Format Test")
        assert "ok" in resp
        assert "op" in resp
        assert "data" in resp

    def test_error_response_format(self, vault: Vault):
        resp = update_content_impl(vault, "NONE", changes={})
        assert resp["ok"] is False
        assert "error" in resp
        assert "code" in resp["error"]
        assert "message" in resp["error"]
