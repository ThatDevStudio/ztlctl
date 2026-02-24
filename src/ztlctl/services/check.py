"""CheckService — integrity and reconciliation.

Single command following the linter pattern.
Four categories: DB-file consistency, schema integrity,
graph health, structural validation. (DESIGN.md Section 14)
"""

from __future__ import annotations

from ztlctl.services.result import ServiceResult


class CheckService:
    """Handles vault integrity checking and repair."""

    def check(self) -> ServiceResult:
        """Report integrity issues without modifying anything."""
        raise NotImplementedError

    def fix(self, *, level: str = "safe") -> ServiceResult:
        """Automatically repair issues. Level: 'safe' or 'aggressive'."""
        raise NotImplementedError

    def rebuild(self) -> ServiceResult:
        """Full DB rebuild from filesystem (files are truth)."""
        raise NotImplementedError

    def rollback(self) -> ServiceResult:
        """Restore DB from latest backup."""
        raise NotImplementedError
