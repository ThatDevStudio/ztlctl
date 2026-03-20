"""DocsController — wraps _docs_search_impl for the action registry.

Does NOT access vault.engine, vault.db, or any vault method.
Vault is accepted only to satisfy the ActionDefinition handler contract.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from ztlctl.controllers.base import BaseController

if TYPE_CHECKING:
    from ztlctl.infrastructure.vault import Vault


class DocsController(BaseController):
    """Controller for documentation search operations."""

    def __init__(self, vault: Vault) -> None:
        super().__init__(vault)

    def search(
        self,
        query: str,
        limit: int = 5,
        docs_path: Path | None = None,
    ) -> dict[str, Any]:
        """Search the ztlctl documentation corpus.

        Returns a dict with a ``results`` key containing a list of
        ``DocResult`` dicts (title, path, score, excerpt), or a list
        with a single ``DocError`` dict if the docs path cannot be resolved.

        Does not access self._vault — vault arg is present only to
        satisfy the ActionDefinition handler lambda contract.
        """
        from ztlctl.services.docs import _docs_search_impl

        results = _docs_search_impl(query, limit=limit, docs_path=docs_path)
        return {"results": results}
