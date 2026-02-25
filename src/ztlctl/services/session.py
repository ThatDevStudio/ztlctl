"""SessionService — session lifecycle and context management.

Sessions are first-class organizational containers. Every content
item links to its creation session. (DESIGN.md Section 2, 8)
"""

from __future__ import annotations

from ztlctl.services.base import BaseService
from ztlctl.services.result import ServiceResult


class SessionService(BaseService):
    """Handles session lifecycle and agent context."""

    def start(self, topic: str) -> ServiceResult:
        """Start a new session, returning the LOG-NNNN id."""
        raise NotImplementedError

    def close(self, *, summary: str | None = None) -> ServiceResult:
        """Close the active session with enrichment pipeline."""
        raise NotImplementedError

    def reopen(self, session_id: str) -> ServiceResult:
        """Reopen a previously closed session."""
        raise NotImplementedError

    def log_entry(
        self,
        message: str,
        *,
        pin: bool = False,
        cost: int = 0,
    ) -> ServiceResult:
        """Append a log entry to the active session."""
        raise NotImplementedError

    def cost(self, *, report: int | None = None) -> ServiceResult:
        """Query or report accumulated token cost for the session."""
        raise NotImplementedError

    def context(
        self,
        *,
        topic: str | None = None,
        budget: int = 8000,
    ) -> ServiceResult:
        """Build token-budgeted agent context payload."""
        raise NotImplementedError
