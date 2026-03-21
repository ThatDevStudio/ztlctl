"""Built-in reweave plugin for automatic post-create graph densification.

Hooks into post_action to run reweave on newly created notes and references,
unless the --no-reweave flag is set or reweave is disabled in settings.

DESIGN.md Section 4: "Reweave runs unless --no-reweave is passed."
DESIGN.md Section 15: Plugin failures are warnings, never errors.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

import pluggy
from sqlalchemy import select

if TYPE_CHECKING:
    from ztlctl.infrastructure.vault import Vault

from ztlctl.infrastructure.database.schema import nodes

hookimpl = pluggy.HookimplMarker("ztlctl")

logger = logging.getLogger(__name__)


class ReweavePlugin:
    """Automatic post-create reweave plugin.

    After content creation, runs the reweave pipeline on the new item
    to discover and create links to existing content. Controlled by:

    - ``--no-reweave`` CLI flag (skips entirely)
    - ``[reweave] enabled`` config (skips if disabled)

    Implements the stable post_action hookspec (PLUG-02). The per-event
    post_create hookimpl has been removed; routing is done inside post_action
    via action_name filtering.
    """

    PLUGIN_API_VERSION = 1

    def __init__(self, vault: Vault) -> None:
        self._vault = vault

    @hookimpl
    def declare_capabilities(self) -> set[str]:
        """Declare that this plugin uses database and filesystem operations."""
        return {"database", "filesystem"}

    @hookimpl
    def post_action(
        self,
        action_name: str,
        kwargs: dict[str, Any],
        result: Any,
    ) -> None:
        """Run reweave on newly created notes or references.

        Only acts when action_name is "create_note" or "create_reference".
        ``result=None`` (EventBus bridge path) is treated as a pass-through.
        An explicit ``result.ok=False`` skips reweave.
        """
        if action_name not in {"create_note", "create_reference"}:
            logger.debug("Skipping post-action reweave for action=%s", action_name)
            return

        # Guard: skip if result indicates failure. None = pass-through.
        # Result may be a ServiceResult object or a dict (from ActionEvent serialization).
        if result is not None:
            ok = result.get("ok") if isinstance(result, dict) else getattr(result, "ok", True)
            if not ok:
                return

        settings = self._vault.settings

        # Extract content_id from kwargs. ActionEvent payloads use "id" (from
        # ServiceResult.data), legacy controller kwargs used "content_id".
        content_id: str = kwargs.get("content_id", "") or kwargs.get("id", "")

        if not content_id:
            logger.debug("Skipping post-action reweave: no content_id in kwargs")
            return

        # Decision notes have a stricter lifecycle and should not be
        # auto-mutated by asynchronous post-create reweave.
        try:
            with self._vault.engine.connect() as conn:
                subtype = conn.execute(
                    select(nodes.c.subtype).where(nodes.c.id == content_id)
                ).scalar_one_or_none()
            if subtype == "decision":
                logger.debug("Skipping post-action reweave for decision note %s", content_id)
                return
        except Exception:
            logger.debug(
                "Subtype lookup failed for %s; continuing with reweave",
                content_id,
                exc_info=True,
            )

        if settings.no_reweave:
            logger.debug("Skipping post-action reweave (--no-reweave)")
            return

        if not settings.reweave.enabled:
            logger.debug("Skipping post-action reweave (reweave disabled)")
            return

        from ztlctl.services.reweave import ReweaveService

        try:
            reweave_result = ReweaveService(self._vault).reweave(content_id=content_id)
        except Exception:
            logger.debug("Post-action reweave raised for %s", content_id, exc_info=True)
            return

        if reweave_result.ok:
            count = reweave_result.data.get("count", 0)
            if count > 0:
                logger.debug(
                    "Post-action reweave for %s: %d links added",
                    content_id,
                    count,
                )
        else:
            logger.debug(
                "Post-action reweave failed for %s: %s",
                content_id,
                reweave_result.error,
            )
