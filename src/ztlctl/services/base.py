"""BaseService — abstract foundation for all ztlctl services.

Every service receives a :class:`Vault` at construction time. The Vault
provides transactional access to the database, filesystem, and graph.
Services own their transaction boundaries via ``self._vault.transaction()``.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, cast

if TYPE_CHECKING:
    from ztlctl.infrastructure.vault import Vault

logger = logging.getLogger(__name__)


class BaseService:
    """Abstract base for all service-layer classes.

    Subclasses implement domain-specific operations (create, query, graph,
    session, reweave, check) using the vault for all data access.

    Usage::

        class CreateService(BaseService):
            def create_note(self, title: str, ...) -> ServiceResult:
                with self._vault.transaction() as txn:
                    ...
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
        """Dispatch a lifecycle event. No-op if event bus not initialized.

        INVARIANT: Plugin failures are warnings, never errors.
        """
        bus = self._vault.event_bus
        if bus is None:
            return None
        try:
            return cast(int, bus.dispatch(hook_name, payload, session_id=session_id))
        except Exception:
            logger.debug("Event dispatch failed for %s", hook_name, exc_info=True)
            warnings.append(f"Event dispatch failed for {hook_name}")
            return None

    def _dispatch_post_action_event(
        self,
        action_name: str,
        payload: dict[str, Any],
        warnings: list[str],
        result: Any = None,
        *,
        session_id: str | None = None,
    ) -> int | None:
        """Emit a canonical post_action event via the WAL.

        Called by services after a successful write commit.
        The ActionEvent is serialized and stored in the WAL payload column (D-15).
        """
        from ztlctl.domain.events import ActionEvent

        bus = self._vault.event_bus
        if bus is None:
            return None
        try:
            event = ActionEvent(
                action_name=action_name,
                side_effect="write",
                payload=payload,
                warnings=warnings,
                result=result,
            )
            return cast(
                int,
                bus.dispatch(
                    "post_action",
                    event.model_dump(),
                    session_id=session_id,
                ),
            )
        except Exception:
            logger.debug("post_action dispatch failed for %s", action_name, exc_info=True)
            warnings.append(f"post_action dispatch failed for {action_name}")
            return None
