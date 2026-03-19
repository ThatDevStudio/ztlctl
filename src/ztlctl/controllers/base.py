"""BaseController — abstract foundation for all ztlctl controllers.

Every controller receives a :class:`Vault` at construction time.
Controllers delegate to the corresponding service layer, acting as
the single interface for the registry layer.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, cast

if TYPE_CHECKING:
    from ztlctl.infrastructure.vault import Vault

logger = logging.getLogger(__name__)


class BaseController:
    """Abstract base for all controller-layer classes.

    INVARIANT: All controller methods return ServiceResult.
    INVARIANT: Plugin failures are warnings, never errors.
    """

    def __init__(self, vault: Vault) -> None:
        self._vault = vault

    def _dispatch_event(
        self,
        hook_name: str,
        payload: dict[str, Any],
        warnings: list[str],
        *,
        session_id: str | None = None,
    ) -> int | None:
        """Dispatch a lifecycle event. No-op if event bus not initialized."""
        bus = self._vault.event_bus
        if bus is None:
            return None
        try:
            return cast(int, bus.dispatch(hook_name, payload, session_id=session_id))
        except Exception:
            logger.debug("Event dispatch failed for %s", hook_name, exc_info=True)
            warnings.append(f"Event dispatch failed for {hook_name}")
            return None
