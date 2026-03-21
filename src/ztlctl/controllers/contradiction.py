"""ContradictionController — orchestration wrapper for ContradictionService."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ztlctl.controllers.base import BaseController

if TYPE_CHECKING:
    from ztlctl.services.result import ServiceResult


class ContradictionController(BaseController):
    """Thin wrapper over ContradictionService. All methods return ServiceResult."""

    def check_contradictions(
        self,
        *,
        similarity_threshold: float = 0.85,
        max_pairs: int = 20,
    ) -> ServiceResult:
        """Find candidate note pairs that may contain contradictory claims."""
        from ztlctl.services.contradiction import ContradictionService

        kwargs: dict[str, Any] = {
            "similarity_threshold": similarity_threshold,
            "max_pairs": max_pairs,
        }

        def _invoke(kw: dict[str, Any]) -> ServiceResult:
            return ContradictionService(self._vault).find_candidates(
                similarity_threshold=kw["similarity_threshold"],
                max_pairs=kw["max_pairs"],
            )

        return self._run_action("check_contradictions", kwargs, _invoke)

    def confirm_contradiction(self, *, note_a: str, note_b: str) -> ServiceResult:
        """Record a confirmed contradiction edge between two notes in the graph."""
        from ztlctl.services.contradiction import ContradictionService

        kwargs: dict[str, Any] = {"note_a": note_a, "note_b": note_b}

        def _invoke(kw: dict[str, Any]) -> ServiceResult:
            return ContradictionService(self._vault).confirm_contradiction(
                note_a=kw["note_a"],
                note_b=kw["note_b"],
            )

        return self._run_action("confirm_contradiction", kwargs, _invoke)
