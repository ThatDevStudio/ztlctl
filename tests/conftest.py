"""Shared pytest fixtures for ztlctl tests."""

from pathlib import Path

import pytest
from click.testing import CliRunner
from sqlalchemy.engine import Engine

from ztlctl.config.settings import ZtlSettings
from ztlctl.infrastructure.database.engine import init_database
from ztlctl.infrastructure.vault import Vault


@pytest.fixture
def cli_runner() -> CliRunner:
    """Provide a Click CLI test runner."""
    return CliRunner()


@pytest.fixture
def db_engine(tmp_path: Path) -> Engine:
    """Initialized SQLite engine with all tables created."""
    return init_database(tmp_path)


@pytest.fixture
def vault_root(tmp_path: Path) -> Path:
    """Temporary vault directory with basic structure.

    This is the single source of truth for the vault directory layout.
    All vault-related fixtures (vault, _isolated_vault) build on this.
    """
    (tmp_path / "notes").mkdir()
    (tmp_path / "ops" / "logs").mkdir(parents=True)
    (tmp_path / "ops" / "tasks").mkdir(parents=True)
    return tmp_path


@pytest.fixture
def vault(vault_root: Path) -> Vault:
    """Fully initialized vault on a temp directory.

    Creates the vault directory structure, initializes the database,
    and returns a ready-to-use Vault instance.
    """
    settings = ZtlSettings.from_cli(vault_root=vault_root)
    return Vault(settings)


@pytest.fixture
def _isolated_vault(vault_root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Change CWD to a temp vault root so the CLI creates an isolated vault.

    Use via ``@pytest.mark.usefixtures("_isolated_vault")`` on command test
    classes. Tests that need the path can also request ``tmp_path`` directly
    (pytest deduplicates — it's the same directory).
    """
    monkeypatch.chdir(vault_root)
