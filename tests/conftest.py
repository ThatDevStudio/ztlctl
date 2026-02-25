"""Shared pytest fixtures for ztlctl tests."""

from pathlib import Path

import pytest
from click.testing import CliRunner
from sqlalchemy.engine import Engine

from ztlctl.infrastructure.database.engine import init_database


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
    """Temporary vault directory with basic structure."""
    (tmp_path / "notes").mkdir()
    (tmp_path / "ops" / "logs").mkdir(parents=True)
    (tmp_path / "ops" / "tasks").mkdir(parents=True)
    return tmp_path
