"""Tests for contradiction ActionDefinition registrations in ActionRegistry.

Tests cover:
- check_contradictions and confirm_contradiction registered in ActionRegistry
- Both in 'analysis' category
- Correct params, side_effects, and MCP metadata
- CLI names and groups correct
"""

from __future__ import annotations


class TestCheckContradictionsRegistration:
    def test_check_contradictions_registered(self) -> None:
        """check_contradictions is registered in the ActionRegistry."""
        from ztlctl.actions.registry import get_action_registry

        registry = get_action_registry()
        action = registry.get("check_contradictions")
        assert action is not None

    def test_check_contradictions_category_is_analysis(self) -> None:
        """check_contradictions has category='analysis'."""
        from ztlctl.actions.registry import get_action_registry

        registry = get_action_registry()
        action = registry.get("check_contradictions")
        assert action is not None
        assert action.category == "analysis"

    def test_check_contradictions_side_effect_is_read(self) -> None:
        """check_contradictions has side_effect='read'."""
        from ztlctl.actions.registry import get_action_registry

        registry = get_action_registry()
        action = registry.get("check_contradictions")
        assert action is not None
        assert action.side_effect == "read"

    def test_check_contradictions_params(self) -> None:
        """check_contradictions has similarity_threshold and max_pairs params."""
        from ztlctl.actions.registry import get_action_registry

        registry = get_action_registry()
        action = registry.get("check_contradictions")
        assert action is not None

        param_names = {p.name for p in action.params}
        assert "similarity_threshold" in param_names
        assert "max_pairs" in param_names

    def test_check_contradictions_similarity_threshold_param(self) -> None:
        """similarity_threshold param has correct type, default, and required=False."""
        from ztlctl.actions.registry import get_action_registry

        registry = get_action_registry()
        action = registry.get("check_contradictions")
        assert action is not None

        threshold_param = next(p for p in action.params if p.name == "similarity_threshold")
        assert threshold_param.type is float
        assert threshold_param.required is False
        assert threshold_param.default == 0.85

    def test_check_contradictions_max_pairs_param(self) -> None:
        """max_pairs param has correct type, default, and required=False."""
        from ztlctl.actions.registry import get_action_registry

        registry = get_action_registry()
        action = registry.get("check_contradictions")
        assert action is not None

        max_pairs_param = next(p for p in action.params if p.name == "max_pairs")
        assert max_pairs_param.type is int
        assert max_pairs_param.required is False
        assert max_pairs_param.default == 20

    def test_check_contradictions_cli_group_and_name(self) -> None:
        """check_contradictions has cli_group='check' and cli_name='contradictions'."""
        from ztlctl.actions.registry import get_action_registry

        registry = get_action_registry()
        action = registry.get("check_contradictions")
        assert action is not None
        assert action.cli_group == "check"
        assert action.cli_name == "contradictions"

    def test_check_contradictions_mcp_metadata(self) -> None:
        """check_contradictions has non-empty MCP when_to_use and avoid_when."""
        from ztlctl.actions.registry import get_action_registry

        registry = get_action_registry()
        action = registry.get("check_contradictions")
        assert action is not None
        assert action.mcp_when_to_use
        assert action.mcp_avoid_when


class TestConfirmContradictionRegistration:
    def test_confirm_contradiction_registered(self) -> None:
        """confirm_contradiction is registered in the ActionRegistry."""
        from ztlctl.actions.registry import get_action_registry

        registry = get_action_registry()
        action = registry.get("confirm_contradiction")
        assert action is not None

    def test_confirm_contradiction_category_is_analysis(self) -> None:
        """confirm_contradiction has category='analysis'."""
        from ztlctl.actions.registry import get_action_registry

        registry = get_action_registry()
        action = registry.get("confirm_contradiction")
        assert action is not None
        assert action.category == "analysis"

    def test_confirm_contradiction_side_effect_is_write(self) -> None:
        """confirm_contradiction has side_effect='write'."""
        from ztlctl.actions.registry import get_action_registry

        registry = get_action_registry()
        action = registry.get("confirm_contradiction")
        assert action is not None
        assert action.side_effect == "write"

    def test_confirm_contradiction_params(self) -> None:
        """confirm_contradiction has note_a and note_b params."""
        from ztlctl.actions.registry import get_action_registry

        registry = get_action_registry()
        action = registry.get("confirm_contradiction")
        assert action is not None

        param_names = {p.name for p in action.params}
        assert "note_a" in param_names
        assert "note_b" in param_names

    def test_confirm_contradiction_note_a_param(self) -> None:
        """note_a param is required=True, type=str, cli_is_argument=True."""
        from ztlctl.actions.registry import get_action_registry

        registry = get_action_registry()
        action = registry.get("confirm_contradiction")
        assert action is not None

        note_a_param = next(p for p in action.params if p.name == "note_a")
        assert note_a_param.type is str
        assert note_a_param.required is True
        assert note_a_param.cli_is_argument is True

    def test_confirm_contradiction_note_b_param(self) -> None:
        """note_b param is required=True, type=str, cli_is_argument=True."""
        from ztlctl.actions.registry import get_action_registry

        registry = get_action_registry()
        action = registry.get("confirm_contradiction")
        assert action is not None

        note_b_param = next(p for p in action.params if p.name == "note_b")
        assert note_b_param.type is str
        assert note_b_param.required is True
        assert note_b_param.cli_is_argument is True

    def test_confirm_contradiction_cli_group_and_name(self) -> None:
        """confirm_contradiction has cli_group='check' and cli_name='confirm-contradiction'."""
        from ztlctl.actions.registry import get_action_registry

        registry = get_action_registry()
        action = registry.get("confirm_contradiction")
        assert action is not None
        assert action.cli_group == "check"
        assert action.cli_name == "confirm-contradiction"

    def test_confirm_contradiction_mcp_common_errors(self) -> None:
        """confirm_contradiction lists NOT_FOUND in mcp_common_errors."""
        from ztlctl.actions.registry import get_action_registry

        registry = get_action_registry()
        action = registry.get("confirm_contradiction")
        assert action is not None
        assert "NOT_FOUND" in action.mcp_common_errors

    def test_confirm_contradiction_mcp_metadata(self) -> None:
        """confirm_contradiction has non-empty MCP when_to_use and avoid_when."""
        from ztlctl.actions.registry import get_action_registry

        registry = get_action_registry()
        action = registry.get("confirm_contradiction")
        assert action is not None
        assert action.mcp_when_to_use
        assert action.mcp_avoid_when


class TestContradictionHandlersDelegateToController:
    def test_check_contradictions_handler_calls_controller(self) -> None:
        """check_contradictions handler calls ContradictionController.check_contradictions."""
        from unittest.mock import MagicMock, patch

        from ztlctl.actions.registry import get_action_registry

        registry = get_action_registry()
        action = registry.get("check_contradictions")
        assert action is not None

        mock_vault = MagicMock()
        mock_result = MagicMock()

        with patch(
            "ztlctl.controllers.contradiction.ContradictionController.check_contradictions",
            return_value=mock_result,
        ) as mock_method:
            result = action.handler(mock_vault)

        mock_method.assert_called_once()
        assert result is mock_result

    def test_confirm_contradiction_handler_calls_controller(self) -> None:
        """confirm_contradiction handler calls ContradictionController.confirm_contradiction."""
        from unittest.mock import MagicMock, patch

        from ztlctl.actions.registry import get_action_registry

        registry = get_action_registry()
        action = registry.get("confirm_contradiction")
        assert action is not None

        mock_vault = MagicMock()
        mock_result = MagicMock()

        with patch(
            "ztlctl.controllers.contradiction.ContradictionController.confirm_contradiction",
            return_value=mock_result,
        ) as mock_method:
            result = action.handler(mock_vault, note_a="NOTE-0001", note_b="NOTE-0002")

        mock_method.assert_called_once_with(note_a="NOTE-0001", note_b="NOTE-0002")
        assert result is mock_result
