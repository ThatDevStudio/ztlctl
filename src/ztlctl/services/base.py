"""BaseService — abstract foundation for all ztlctl services.

Every service receives a :class:`Vault` at construction time. The Vault
provides transactional access to the database, filesystem, and graph.
Services own their transaction boundaries via ``self._vault.transaction()``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ztlctl.infrastructure.vault import Vault


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

    @property
    def vault(self) -> Vault:
        """The vault this service operates on."""
        return self._vault
