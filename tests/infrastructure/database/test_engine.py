"""Tests for database engine setup and initialization."""

from pathlib import Path

from sqlalchemy import inspect, select, text
from sqlalchemy.engine import Engine

from ztlctl.infrastructure.database.engine import create_db_engine, init_database
from ztlctl.infrastructure.database.schema import id_counters


class TestCreateDbEngine:
    def test_creates_engine(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.db"
        engine = create_db_engine(db_path)
        assert engine is not None

    def test_wal_mode_enabled(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.db"
        engine = create_db_engine(db_path)
        with engine.connect() as conn:
            result = conn.execute(text("PRAGMA journal_mode")).scalar()
            assert result == "wal"

    def test_foreign_keys_enabled(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.db"
        engine = create_db_engine(db_path)
        with engine.connect() as conn:
            result = conn.execute(text("PRAGMA foreign_keys")).scalar()
            assert result == 1


class TestInitDatabase:
    def test_creates_ztlctl_directory(self, tmp_path: Path) -> None:
        init_database(tmp_path)
        assert (tmp_path / ".ztlctl").is_dir()
        assert (tmp_path / ".ztlctl" / "backups").is_dir()
        assert (tmp_path / ".ztlctl" / "plugins").is_dir()

    def test_creates_db_file(self, tmp_path: Path) -> None:
        init_database(tmp_path)
        assert (tmp_path / ".ztlctl" / "ztlctl.db").exists()

    def test_creates_all_tables(self, tmp_path: Path) -> None:
        engine = init_database(tmp_path)
        inspector = inspect(engine)
        table_names = set(inspector.get_table_names())
        assert "nodes" in table_names
        assert "edges" in table_names
        assert "id_counters" in table_names
        assert "nodes_fts" in table_names

    def test_seeds_log_counter(self, db_engine: Engine) -> None:
        with db_engine.connect() as conn:
            row = conn.execute(
                select(id_counters.c.next_value).where(id_counters.c.type_prefix == "LOG-")
            ).one()
            assert row.next_value == 1

    def test_seeds_task_counter(self, db_engine: Engine) -> None:
        with db_engine.connect() as conn:
            row = conn.execute(
                select(id_counters.c.next_value).where(id_counters.c.type_prefix == "TASK-")
            ).one()
            assert row.next_value == 1

    def test_idempotent(self, tmp_path: Path) -> None:
        """Calling init_database twice should not raise or duplicate data."""
        init_database(tmp_path)
        engine2 = init_database(tmp_path)
        with engine2.connect() as conn:
            rows = conn.execute(select(id_counters)).fetchall()
            assert len(rows) == 2  # LOG- and TASK- only
