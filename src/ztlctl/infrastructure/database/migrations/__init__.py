"""Alembic migration infrastructure for ztlctl.

Provides programmatic Alembic configuration — no alembic.ini needed.
The migration scripts live alongside this module.
"""

from __future__ import annotations

from pathlib import Path

from alembic.config import Config


def build_config(db_url: str) -> Config:
    """Build an Alembic Config pointing at our migration scripts."""
    cfg = Config()
    cfg.set_main_option("script_location", str(Path(__file__).parent))
    cfg.set_main_option("sqlalchemy.url", db_url)
    return cfg


def stamp_head(vault_root: Path) -> None:
    """Stamp a database as at the current head revision.

    Called during ``ztlctl init`` so freshly created databases start
    at the correct Alembic version without running migrations.
    """
    from alembic import command

    db_path = vault_root / ".ztlctl" / "ztlctl.db"
    cfg = build_config(f"sqlite:///{db_path}")
    command.stamp(cfg, "head")
