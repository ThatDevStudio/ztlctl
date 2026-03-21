"""Tests for ContradictionController — delegation smoke tests."""

from __future__ import annotations

from unittest.mock import patch

from ztlctl.controllers.contradiction import ContradictionController
from ztlctl.infrastructure.vault import Vault


class TestContradictionController:
    def test_check_contradictions_delegates_to_service(self, vault: Vault) -> None:
        """check_contradictions delegates through _run_action to ContradictionService."""
        with patch(
            "ztlctl.services.vector.VectorService.is_available",
            return_value=False,
        ):
            result = ContradictionController(vault).check_contradictions()

        assert result.ok
        assert result.op == "find_candidates"
        assert "candidates" in result.data
        assert result.data["candidates"] == []

    def test_check_contradictions_passes_parameters(self, vault: Vault) -> None:
        """check_contradictions passes similarity_threshold and max_pairs to service."""
        with patch(
            "ztlctl.services.vector.VectorService.is_available",
            return_value=False,
        ):
            result = ContradictionController(vault).check_contradictions(
                similarity_threshold=0.9,
                max_pairs=5,
            )

        assert result.ok
        assert result.data["count"] == 0

    def test_check_contradictions_default_params(self, vault: Vault) -> None:
        """check_contradictions works with default parameters."""
        with patch(
            "ztlctl.services.vector.VectorService.is_available",
            return_value=False,
        ):
            result = ContradictionController(vault).check_contradictions()

        assert result.ok

    def test_confirm_contradiction_delegates_to_service(self, vault: Vault) -> None:
        """confirm_contradiction delegates through _run_action to ContradictionService."""
        result = ContradictionController(vault).confirm_contradiction(
            note_a="NOTE-0001",
            note_b="NOTE-0002",
        )

        # Stub returns NOT_IMPLEMENTED error
        assert not result.ok
        assert result.error is not None
        assert result.error.code == "NOT_IMPLEMENTED"
        assert result.op == "confirm_contradiction"

    def test_confirm_contradiction_returns_not_implemented(self, vault: Vault) -> None:
        """confirm_contradiction stub always returns NOT_IMPLEMENTED."""
        result = ContradictionController(vault).confirm_contradiction(
            note_a="any-id",
            note_b="other-id",
        )

        assert not result.ok
        assert result.error is not None
        assert result.error.code == "NOT_IMPLEMENTED"
        assert "Plan 02" in result.error.message

    def test_check_contradictions_respects_plugin_rejection(self, vault: Vault) -> None:
        """check_contradictions action can be rejected by plugins via _run_action."""
        from ztlctl.plugins.contracts import ActionRejection

        rejection = ActionRejection(reason="test rejection", detail={})

        with patch.object(
            ContradictionController,
            "_dispatch_pre_action",
            return_value=({"similarity_threshold": 0.85, "max_pairs": 20}, rejection),
        ):
            result = ContradictionController(vault).check_contradictions()

        assert not result.ok
        assert result.error is not None
        assert result.error.code == "ACTION_REJECTED"

    def test_confirm_contradiction_respects_plugin_rejection(self, vault: Vault) -> None:
        """confirm_contradiction action can be rejected by plugins via _run_action."""
        from ztlctl.plugins.contracts import ActionRejection

        rejection = ActionRejection(reason="blocked by policy", detail={})

        with patch.object(
            ContradictionController,
            "_dispatch_pre_action",
            return_value=({"note_a": "x", "note_b": "y"}, rejection),
        ):
            result = ContradictionController(vault).confirm_contradiction(
                note_a="x",
                note_b="y",
            )

        assert not result.ok
        assert result.error is not None
        assert result.error.code == "ACTION_REJECTED"
