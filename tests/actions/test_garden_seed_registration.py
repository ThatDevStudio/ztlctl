"""Tests for garden_seed ActionDefinition registration (ARCH-09)."""

from __future__ import annotations


def test_garden_seed_registered() -> None:
    """garden_seed ActionDefinition exists in the registry."""
    import ztlctl.actions  # noqa: F401 — triggers registration

    from ztlctl.actions.registry import get_action_registry

    registry = get_action_registry()
    action = registry.get("garden_seed")
    assert action is not None
    assert action.name == "garden_seed"
    assert action.cli_group == "garden"
    assert action.cli_name == "seed"
    assert action.side_effect == "write"
    assert action.category == "creation"


def test_garden_seed_handler_routes_through_controller() -> None:
    """garden_seed handler calls CreateController, not CreateService directly."""
    from unittest.mock import MagicMock, patch

    import ztlctl.actions  # noqa: F401 — triggers registration

    from ztlctl.actions.registry import get_action_registry

    registry = get_action_registry()
    action = registry.get("garden_seed")
    assert action is not None

    mock_vault = MagicMock()
    mock_vault.plugin_manager = None

    with patch("ztlctl.controllers.create.CreateController.create_note") as mock_create:
        mock_create.return_value = MagicMock(ok=True)
        action.handler(mock_vault, title="Test seed title", tags=["tag1"], topic="test")

    mock_create.assert_called_once()
    call_kwargs = mock_create.call_args
    # maturity="seed" is baked into the handler
    assert call_kwargs.kwargs.get("maturity") == "seed"
