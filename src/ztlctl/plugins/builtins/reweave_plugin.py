"""Built-in reweave plugin for automatic post-create graph densification.

Hooks into post_create to run reweave on newly created content, unless
the --no-reweave flag is set or reweave is disabled in settings.

DESIGN.md Section 4: "Reweave runs unless --no-reweave is passed."
DESIGN.md Section 15: Plugin failures are warnings, never errors.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import pluggy

if TYPE_CHECKING:
    from ztlctl.infrastructure.vault import Vault

hookimpl = pluggy.HookimplMarker("ztlctl")

logger = logging.getLogger(__name__)


class ReweavePlugin:
    """Automatic post-create reweave plugin.

    After content creation, runs the reweave pipeline on the new item
    to discover and create links to existing content. Controlled by:

    - ``--no-reweave`` CLI flag (skips entirely)
    - ``[reweave] enabled`` config (skips if disabled)
    """

    def __init__(self, vault: Vault) -> None:
        self._vault = vault

    @hookimpl
    def post_create(
        self,
        content_type: str,
        content_id: str,
        title: str,
        path: str,
        tags: list[str],
    ) -> None:
        """Run reweave on newly created content."""
        settings = self._vault.settings

        if content_type not in ("note", "reference"):
            logger.debug("Skipping post-create reweave for type=%s", content_type)
            return

        if settings.no_reweave:
            logger.debug("Skipping post-create reweave (--no-reweave)")
            return

        if not settings.reweave.enabled:
            logger.debug("Skipping post-create reweave (reweave disabled)")
            return

        from ztlctl.services.reweave import ReweaveService

        try:
            result = ReweaveService(self._vault).reweave(content_id=content_id)
        except Exception:
            logger.debug("Post-create reweave raised for %s", content_id, exc_info=True)
            return

        if result.ok:
            count = result.data.get("count", 0)
            if count > 0:
                logger.debug(
                    "Post-create reweave for %s: %d links added",
                    content_id,
                    count,
                )
        else:
            logger.debug(
                "Post-create reweave failed for %s: %s",
                content_id,
                result.error,
            )
