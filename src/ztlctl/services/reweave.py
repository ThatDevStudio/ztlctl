"""ReweaveService — graph densification pipeline.

Five-stage: DISCOVER → SCORE → FILTER → PRESENT → CONNECT
(DESIGN.md Section 5)
"""

from __future__ import annotations

from ztlctl.services.base import BaseService
from ztlctl.services.result import ServiceResult


class ReweaveService(BaseService):
    """Handles link suggestion, creation, and pruning."""

    def reweave(
        self,
        *,
        content_id: str | None = None,
        dry_run: bool = False,
    ) -> ServiceResult:
        """Run reweave on a specific item or the latest creation."""
        raise NotImplementedError

    def prune(
        self,
        *,
        content_id: str | None = None,
        dry_run: bool = False,
    ) -> ServiceResult:
        """Remove stale links flagged by previous reweave runs."""
        raise NotImplementedError

    def undo(self, *, reweave_id: int | None = None) -> ServiceResult:
        """Reverse a reweave operation via audit trail."""
        raise NotImplementedError
