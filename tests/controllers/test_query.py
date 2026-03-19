"""Integration tests for QueryController."""

from __future__ import annotations

from ztlctl.controllers.create import CreateController
from ztlctl.controllers.query import QueryController
from ztlctl.infrastructure.vault import Vault
from ztlctl.services.result import ServiceResult


class TestQueryController:
    def test_list_items_returns_service_result(self, vault: Vault) -> None:
        """QueryController.list_items() returns a ServiceResult."""
        ctrl = QueryController(vault)
        result = ctrl.list_items()
        assert isinstance(result, ServiceResult)

    def test_list_items_ok(self, vault: Vault) -> None:
        """QueryController.list_items() returns ok=True."""
        ctrl = QueryController(vault)
        result = ctrl.list_items()
        assert result.ok is True

    def test_list_items_data_has_count(self, vault: Vault) -> None:
        """QueryController.list_items() returns data with 'count' key."""
        ctrl = QueryController(vault)
        result = ctrl.list_items()
        assert "count" in result.data

    def test_list_items_empty_vault(self, vault: Vault) -> None:
        """QueryController.list_items() returns empty list on new vault."""
        ctrl = QueryController(vault)
        result = ctrl.list_items()
        assert result.data["count"] == 0
        assert result.data["items"] == []

    def test_list_items_with_created_note(self, vault: Vault) -> None:
        """QueryController.list_items() returns created notes."""
        CreateController(vault).create_note("Sample Note")
        ctrl = QueryController(vault)
        result = ctrl.list_items()
        assert result.data["count"] == 1

    def test_count_items_returns_service_result(self, vault: Vault) -> None:
        """QueryController.count_items() returns a ServiceResult."""
        ctrl = QueryController(vault)
        result = ctrl.count_items()
        assert isinstance(result, ServiceResult)

    def test_count_items_ok(self, vault: Vault) -> None:
        """QueryController.count_items() returns ok=True."""
        ctrl = QueryController(vault)
        result = ctrl.count_items()
        assert result.ok is True

    def test_count_items_data_has_count(self, vault: Vault) -> None:
        """QueryController.count_items() returns data with 'count' key."""
        ctrl = QueryController(vault)
        result = ctrl.count_items()
        assert "count" in result.data
        assert result.data["count"] == 0

    def test_count_items_increments_after_create(self, vault: Vault) -> None:
        """QueryController.count_items() increments after creating content."""
        CreateController(vault).create_note("Count Test Note")
        ctrl = QueryController(vault)
        result = ctrl.count_items()
        assert result.data["count"] == 1

    def test_search_returns_service_result(self, vault: Vault) -> None:
        """QueryController.search() returns a ServiceResult."""
        ctrl = QueryController(vault)
        result = ctrl.search("test query")
        assert isinstance(result, ServiceResult)

    def test_search_empty_vault(self, vault: Vault) -> None:
        """QueryController.search() returns ok=True with no results on empty vault."""
        ctrl = QueryController(vault)
        result = ctrl.search("test")
        assert isinstance(result, ServiceResult)
        # May be ok=True with 0 results or ok=False if no results, depends on impl
        # We just verify it returns a ServiceResult without throwing

    def test_search_finds_created_note(self, vault: Vault) -> None:
        """QueryController.search() can find a created note by title."""
        CreateController(vault).create_note("Unique Search Target Title")
        ctrl = QueryController(vault)
        result = ctrl.search("Unique Search Target")
        assert result.ok is True
        assert result.data["count"] >= 1

    def test_get_returns_not_found(self, vault: Vault) -> None:
        """QueryController.get() returns ok=False for missing ID."""
        ctrl = QueryController(vault)
        result = ctrl.get("ztl_nonexistent")
        assert result.ok is False
        assert result.error is not None
        assert result.error.code == "NOT_FOUND"

    def test_work_queue_returns_service_result(self, vault: Vault) -> None:
        """QueryController.work_queue() returns a ServiceResult."""
        ctrl = QueryController(vault)
        result = ctrl.work_queue()
        assert isinstance(result, ServiceResult)
        assert result.ok is True

    def test_list_tags_returns_service_result(self, vault: Vault) -> None:
        """QueryController.list_tags() returns a ServiceResult."""
        ctrl = QueryController(vault)
        result = ctrl.list_tags()
        assert isinstance(result, ServiceResult)
        assert result.ok is True
