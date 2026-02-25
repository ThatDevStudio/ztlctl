"""Tests for BaseService and service inheritance."""

from pathlib import Path

import pytest

from ztlctl.config.settings import ZtlSettings
from ztlctl.infrastructure.vault import Vault
from ztlctl.services.base import BaseService
from ztlctl.services.check import CheckService
from ztlctl.services.create import CreateService
from ztlctl.services.graph import GraphService
from ztlctl.services.query import QueryService
from ztlctl.services.reweave import ReweaveService
from ztlctl.services.session import SessionService


class TestBaseService:
    def test_vault_stored(self, tmp_path: Path) -> None:
        settings = ZtlSettings.from_cli(vault_root=tmp_path)
        vault = Vault(settings)
        service = BaseService(vault)
        assert service._vault is vault

    def test_subclass_pattern(self, tmp_path: Path) -> None:
        """Verify the intended subclass usage pattern works."""

        class MyService(BaseService):
            def do_thing(self) -> str:
                return f"vault at {self._vault.root}"

        settings = ZtlSettings.from_cli(vault_root=tmp_path)
        vault = Vault(settings)
        svc = MyService(vault)
        assert str(tmp_path) in svc.do_thing()


# ---------------------------------------------------------------------------
# Service inheritance — all 6 services extend BaseService
# ---------------------------------------------------------------------------

ALL_SERVICES = [
    CreateService,
    QueryService,
    GraphService,
    SessionService,
    ReweaveService,
    CheckService,
]


class TestServiceInheritance:
    @pytest.mark.parametrize("service_cls", ALL_SERVICES, ids=lambda c: c.__name__)
    def test_inherits_base_service(self, service_cls: type) -> None:
        assert issubclass(service_cls, BaseService)

    @pytest.mark.parametrize("service_cls", ALL_SERVICES, ids=lambda c: c.__name__)
    def test_vault_injection(self, service_cls: type, vault: Vault) -> None:
        """Each service accepts a Vault and stores it as _vault."""
        svc = service_cls(vault)
        assert svc._vault is vault

    @pytest.mark.parametrize("service_cls", ALL_SERVICES, ids=lambda c: c.__name__)
    def test_protected_vault_access(self, service_cls: type, vault: Vault) -> None:
        """Subclasses access vault via self._vault (protected attribute)."""
        svc = service_cls(vault)
        assert svc._vault is vault
