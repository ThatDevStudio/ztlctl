"""Shared pytest fixtures and test helpers for ztlctl tests."""

from __future__ import annotations

from pathlib import Path
from typing import Any

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
    engine = init_database(tmp_path)
    try:
        yield engine
    finally:
        engine.dispose()


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
    settings = ZtlSettings.from_cli(vault_root=vault_root, no_reweave=True)
    v = Vault(settings)
    try:
        yield v
    finally:
        v.close()


@pytest.fixture
def _isolated_vault(vault_root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Change CWD to a temp vault root so the CLI creates an isolated vault.

    Use via ``@pytest.mark.usefixtures("_isolated_vault")`` on command test
    classes. Tests that need the path can also request ``tmp_path`` directly
    (pytest deduplicates — it's the same directory).
    """
    monkeypatch.chdir(vault_root)


# ---------------------------------------------------------------------------
# Shared test helpers (used across service test modules)
# ---------------------------------------------------------------------------


def create_note(vault: Vault, title: str, **kwargs: Any) -> dict[str, Any]:
    """Create a note via CreateService, asserting success."""
    from ztlctl.services.create import CreateService

    result = CreateService(vault).create_note(title, **kwargs)
    assert result.ok, result.error
    return result.data


def create_reference(vault: Vault, title: str, **kwargs: Any) -> dict[str, Any]:
    """Create a reference via CreateService, asserting success."""
    from ztlctl.services.create import CreateService

    result = CreateService(vault).create_reference(title, **kwargs)
    assert result.ok, result.error
    return result.data


def create_task(vault: Vault, title: str, **kwargs: Any) -> dict[str, Any]:
    """Create a task via CreateService, asserting success."""
    from ztlctl.services.create import CreateService

    result = CreateService(vault).create_task(title, **kwargs)
    assert result.ok, result.error
    return result.data


def create_decision(vault: Vault, title: str, **kwargs: Any) -> dict[str, Any]:
    """Create a decision note via CreateService, asserting success."""
    from ztlctl.services.create import CreateService

    result = CreateService(vault).create_note(title, subtype="decision", **kwargs)
    assert result.ok, result.error
    return result.data


def start_session(vault: Vault, topic: str) -> dict[str, Any]:
    """Start a session via SessionService, asserting success."""
    from ztlctl.services.session import SessionService

    result = SessionService(vault).start(topic)
    assert result.ok, result.error
    return result.data
