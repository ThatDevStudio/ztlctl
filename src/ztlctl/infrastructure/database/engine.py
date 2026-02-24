"""Database engine setup for SQLite with WAL mode.

SQLite is the persistence layer: WAL mode for concurrent reads,
FTS5 for full-text search, ACID transactions for data integrity.
The DB is stored at {vault_root}/.ztlctl/ztlctl.db.

SQLAlchemy Core (not ORM) is used because ztlctl is a short-lived
CLI process — no benefit from session management or identity maps.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine


def create_db_engine(db_path: Path) -> Engine:
    """Create a SQLite engine with WAL mode and foreign keys enabled."""
    engine = create_engine(f"sqlite:///{db_path}", echo=False)

    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_conn: Any, _: Any) -> None:
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    return engine
