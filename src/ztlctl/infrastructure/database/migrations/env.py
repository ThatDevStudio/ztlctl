"""Alembic environment configuration for ztlctl migrations."""

from __future__ import annotations

from typing import Any

from alembic import context
from sqlalchemy import create_engine, event, pool

from ztlctl.infrastructure.database.schema import metadata

target_metadata = metadata


def _set_sqlite_pragma(dbapi_conn: Any, _: Any) -> None:
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode — emit SQL to stdout."""
    url = context.config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations against a live database connection."""
    url = context.config.get_main_option("sqlalchemy.url")
    assert url is not None, "sqlalchemy.url must be set in Alembic config"

    connectable = create_engine(url, poolclass=pool.NullPool)
    event.listen(connectable, "connect", _set_sqlite_pragma)

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
