"""Tests for atomic sequential ID generation."""

import pytest
from sqlalchemy.engine import Engine

from ztlctl.infrastructure.database.counters import next_sequential_id


class TestNextSequentialId:
    def test_first_log_id(self, db_engine: Engine) -> None:
        with db_engine.begin() as conn:
            result = next_sequential_id(conn, "LOG-")
        assert result == "LOG-0001"

    def test_first_task_id(self, db_engine: Engine) -> None:
        with db_engine.begin() as conn:
            result = next_sequential_id(conn, "TASK-")
        assert result == "TASK-0001"

    def test_sequential_increment(self, db_engine: Engine) -> None:
        with db_engine.begin() as conn:
            ids = [next_sequential_id(conn, "LOG-") for _ in range(5)]
        assert ids == [
            "LOG-0001",
            "LOG-0002",
            "LOG-0003",
            "LOG-0004",
            "LOG-0005",
        ]

    def test_independent_counters(self, db_engine: Engine) -> None:
        """LOG and TASK counters are independent."""
        with db_engine.begin() as conn:
            log1 = next_sequential_id(conn, "LOG-")
            task1 = next_sequential_id(conn, "TASK-")
            log2 = next_sequential_id(conn, "LOG-")
        assert log1 == "LOG-0001"
        assert task1 == "TASK-0001"
        assert log2 == "LOG-0002"

    def test_minimum_four_digits(self, db_engine: Engine) -> None:
        with db_engine.begin() as conn:
            result = next_sequential_id(conn, "LOG-")
        assert len(result.split("-")[1]) == 4

    def test_invalid_prefix_raises(self, db_engine: Engine) -> None:
        with db_engine.begin() as conn:
            with pytest.raises(ValueError, match="Unknown sequential type prefix"):
                next_sequential_id(conn, "INVALID-")

    def test_note_prefix_rejected(self, db_engine: Engine) -> None:
        """Content-hash types should not use sequential generation."""
        with db_engine.begin() as conn:
            with pytest.raises(ValueError):
                next_sequential_id(conn, "ztl_")
