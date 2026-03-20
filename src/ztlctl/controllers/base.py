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
    from ztlctl.plugins.contracts import ActionRejection

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

    def _dispatch_pre_action(
        self,
        action_name: str,
        kwargs: dict[str, Any],
    ) -> tuple[dict[str, Any], ActionRejection | None]:
        """Invoke the ``pre_action`` hook before executing an action.

        Returns a ``(kwargs, rejection)`` tuple:
        - If a plugin returns an :class:`~ztlctl.plugins.contracts.ActionRejection`,
          ``(original_kwargs, rejection)`` is returned so the caller can abort.
        - If a plugin returns a modified kwargs dict, ``(modified_kwargs, None)``
          is returned and the action proceeds with the new arguments.
        - If no plugin intercepts (``None`` result), ``(original_kwargs, None)``
          is returned unchanged.
        - On any exception the original kwargs are returned with ``None`` rejection
          and the error is logged at DEBUG level (plugin failures are warnings).
        """
        from ztlctl.plugins.contracts import ActionRejection

        pm = self._vault.plugin_manager
        if pm is None:
            return kwargs, None

        try:
            result = pm.hook.pre_action(action_name=action_name, kwargs=kwargs)
        except Exception:
            logger.debug("pre_action dispatch failed for %s", action_name, exc_info=True)
            return kwargs, None

        if isinstance(result, ActionRejection):
            return kwargs, result
        if isinstance(result, dict):
            return result, None
        return kwargs, None

    def _dispatch_post_action(
        self,
        action_name: str,
        kwargs: dict[str, Any],
        result: Any,
    ) -> None:
        """Invoke the ``post_action`` hook after executing an action.

        All registered plugins receive this call. Exceptions are caught,
        logged at DEBUG level, and ignored — plugin failures are warnings.
        """
        pm = self._vault.plugin_manager
        if pm is None:
            return

        try:
            pm.hook.post_action(action_name=action_name, kwargs=kwargs, result=result)
        except Exception:
            logger.debug("post_action dispatch failed for %s", action_name, exc_info=True)
