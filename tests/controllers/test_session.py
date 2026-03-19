"""Integration tests for SessionController."""

from __future__ import annotations

from ztlctl.controllers.session import SessionController
from ztlctl.infrastructure.vault import Vault
from ztlctl.services.result import ServiceResult


class TestSessionController:
    def test_start_returns_service_result(self, vault: Vault) -> None:
        """SessionController.start() returns a ServiceResult."""
        ctrl = SessionController(vault)
        result = ctrl.start("test topic")
        assert isinstance(result, ServiceResult)

    def test_start_ok(self, vault: Vault) -> None:
        """SessionController.start() returns ok=True."""
        ctrl = SessionController(vault)
        result = ctrl.start("test topic")
        assert result.ok is True

    def test_start_data_has_id(self, vault: Vault) -> None:
        """SessionController.start() returns data with a session ID."""
        ctrl = SessionController(vault)
        result = ctrl.start("test topic")
        assert "id" in result.data
        assert result.data["id"].startswith("LOG-")

    def test_start_data_has_topic(self, vault: Vault) -> None:
        """SessionController.start() returns data with the topic."""
        ctrl = SessionController(vault)
        result = ctrl.start("my topic")
        assert result.data["topic"] == "my topic"

    def test_start_prevents_double_open(self, vault: Vault) -> None:
        """SessionController.start() fails if a session is already open."""
        ctrl = SessionController(vault)
        ctrl.start("first topic")
        second = ctrl.start("second topic")
        assert second.ok is False
        assert second.error is not None
        assert second.error.code == "ACTIVE_SESSION_EXISTS"

    def test_status_returns_service_result(self, vault: Vault) -> None:
        """SessionController.status() returns a ServiceResult."""
        ctrl = SessionController(vault)
        result = ctrl.status()
        assert isinstance(result, ServiceResult)

    def test_status_ok_no_session(self, vault: Vault) -> None:
        """SessionController.status() returns ok=True even with no session."""
        ctrl = SessionController(vault)
        result = ctrl.status()
        assert result.ok is True
        assert result.data["session"] is None

    def test_status_shows_active_session(self, vault: Vault) -> None:
        """SessionController.status() reflects an active session."""
        ctrl = SessionController(vault)
        ctrl.start("active topic")
        result = ctrl.status()
        assert result.ok is True
        assert result.data["session"] is not None
        assert result.data["session"]["status"] == "open"

    def test_close_fails_with_no_session(self, vault: Vault) -> None:
        """SessionController.close() fails if no session is open."""
        ctrl = SessionController(vault)
        result = ctrl.close()
        assert result.ok is False
        assert result.error is not None
        assert result.error.code == "NO_ACTIVE_SESSION"

    def test_close_ok_after_start(self, vault: Vault) -> None:
        """SessionController.close() succeeds after start()."""
        ctrl = SessionController(vault)
        ctrl.start("close test")
        result = ctrl.close()
        assert result.ok is True
        assert result.data["status"] == "closed"
