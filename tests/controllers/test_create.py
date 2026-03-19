"""Integration tests for CreateController."""

from __future__ import annotations

from ztlctl.controllers.create import CreateController
from ztlctl.infrastructure.vault import Vault
from ztlctl.services.result import ServiceResult


class TestCreateController:
    def test_create_note_returns_service_result(self, vault: Vault) -> None:
        """CreateController.create_note() returns a ServiceResult."""
        ctrl = CreateController(vault)
        result = ctrl.create_note("Test Title")
        assert isinstance(result, ServiceResult)

    def test_create_note_ok(self, vault: Vault) -> None:
        """CreateController.create_note() returns ok=True."""
        ctrl = CreateController(vault)
        result = ctrl.create_note("Test Title")
        assert result.ok is True

    def test_create_note_data_has_id(self, vault: Vault) -> None:
        """CreateController.create_note() returns data with an 'id' field."""
        ctrl = CreateController(vault)
        result = ctrl.create_note("Test Title")
        assert "id" in result.data
        assert result.data["id"].startswith("ztl_")

    def test_create_note_data_has_path(self, vault: Vault) -> None:
        """CreateController.create_note() returns data with a 'path' field."""
        ctrl = CreateController(vault)
        result = ctrl.create_note("Test Title")
        assert "path" in result.data

    def test_create_note_with_tags(self, vault: Vault) -> None:
        """CreateController.create_note() accepts tags."""
        ctrl = CreateController(vault)
        result = ctrl.create_note("Tagged Note", tags=["domain/test"])
        assert result.ok is True
        assert result.data["id"].startswith("ztl_")

    def test_create_task_returns_service_result(self, vault: Vault) -> None:
        """CreateController.create_task() returns a ServiceResult."""
        ctrl = CreateController(vault)
        result = ctrl.create_task("Test Task")
        assert isinstance(result, ServiceResult)

    def test_create_task_ok(self, vault: Vault) -> None:
        """CreateController.create_task() returns ok=True."""
        ctrl = CreateController(vault)
        result = ctrl.create_task("Test Task")
        assert result.ok is True

    def test_create_task_data_has_id(self, vault: Vault) -> None:
        """CreateController.create_task() returns data with a task ID."""
        ctrl = CreateController(vault)
        result = ctrl.create_task("Test Task")
        assert "id" in result.data
        assert result.data["id"].startswith("TASK-")

    def test_create_batch_ok(self, vault: Vault) -> None:
        """CreateController.create_batch() creates multiple items."""
        ctrl = CreateController(vault)
        items = [
            {"type": "note", "title": "Batch Note 1"},
            {"type": "task", "title": "Batch Task 1"},
        ]
        result = ctrl.create_batch(items)
        assert isinstance(result, ServiceResult)
        assert result.ok is True
        assert len(result.data["created"]) == 2

    def test_create_reference_ok(self, vault: Vault) -> None:
        """CreateController.create_reference() returns ok=True."""
        ctrl = CreateController(vault)
        result = ctrl.create_reference("Test Reference")
        assert result.ok is True
        assert result.data["type"] == "reference"
