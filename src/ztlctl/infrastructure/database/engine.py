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

from sqlalchemy import create_engine, event, insert, select, text
from sqlalchemy.engine import Engine

from ztlctl.infrastructure.database.schema import FTS5_CREATE_SQL, id_counters, metadata


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


def init_database(vault_root: Path) -> Engine:
    """Initialize the ztlctl database at ``{vault_root}/.ztlctl/ztlctl.db``.

    Creates the ``.ztlctl/`` directory structure, all tables from
    :data:`schema.metadata`, the FTS5 virtual table, and seeds the
    ``id_counters`` table with initial values for sequential types.

    Idempotent — safe to call on an existing vault.

    Returns the engine ready for use.
    """
    ztlctl_dir = vault_root / ".ztlctl"
    ztlctl_dir.mkdir(parents=True, exist_ok=True)
    (ztlctl_dir / "backups").mkdir(exist_ok=True)
    (ztlctl_dir / "plugins").mkdir(exist_ok=True)

    db_path = ztlctl_dir / "ztlctl.db"
    engine = create_db_engine(db_path)

    metadata.create_all(engine)

    with engine.begin() as conn:
        conn.execute(text(FTS5_CREATE_SQL))

    _seed_counters(engine)
    return engine


def _seed_counters(engine: Engine) -> None:
    """Insert initial counter rows for LOG and TASK if they don't exist."""
    with engine.begin() as conn:
        for prefix in ("LOG-", "TASK-"):
            row = conn.execute(
                select(id_counters.c.type_prefix).where(id_counters.c.type_prefix == prefix)
            ).first()
            if row is None:
                conn.execute(insert(id_counters).values(type_prefix=prefix, next_value=1))
