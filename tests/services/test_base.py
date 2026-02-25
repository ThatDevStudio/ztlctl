"""Tests for BaseService."""

from pathlib import Path

from ztlctl.config.settings import ZtlSettings
from ztlctl.infrastructure.vault import Vault
from ztlctl.services.base import BaseService


class TestBaseService:
    def test_vault_property(self, tmp_path: Path) -> None:
        settings = ZtlSettings.from_cli(vault_root=tmp_path)
        vault = Vault(settings)
        service = BaseService(vault)
        assert service.vault is vault

    def test_subclass_pattern(self, tmp_path: Path) -> None:
        """Verify the intended subclass usage pattern works."""

        class MyService(BaseService):
            def do_thing(self) -> str:
                return f"vault at {self._vault.root}"

        settings = ZtlSettings.from_cli(vault_root=tmp_path)
        vault = Vault(settings)
        svc = MyService(vault)
        assert str(tmp_path) in svc.do_thing()
