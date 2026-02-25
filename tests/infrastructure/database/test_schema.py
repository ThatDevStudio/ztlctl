"""Tests for database schema definitions."""

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine

from ztlctl.infrastructure.database.schema import FTS5_CREATE_SQL, metadata


def _in_memory_engine() -> Engine:
    """Create an in-memory SQLite engine for testing."""
    engine = create_engine("sqlite:///:memory:")
    metadata.create_all(engine)
    with engine.begin() as conn:
        conn.execute(text(FTS5_CREATE_SQL))
    return engine


class TestSchemaCreation:
    def test_all_tables_created(self) -> None:
        engine = _in_memory_engine()
        inspector = inspect(engine)
        table_names = set(inspector.get_table_names())
        expected = {
            "nodes",
            "edges",
            "tags_registry",
            "node_tags",
            "id_counters",
            "reweave_log",
            "event_wal",
            "session_logs",
            "nodes_fts",
        }
        assert expected.issubset(table_names)

    def test_create_all_is_idempotent(self) -> None:
        """Calling create_all twice should not raise."""
        engine = _in_memory_engine()
        metadata.create_all(engine)
        with engine.begin() as conn:
            conn.execute(text(FTS5_CREATE_SQL))
        inspector = inspect(engine)
        assert "nodes" in inspector.get_table_names()


class TestNodesTable:
    def test_primary_key(self) -> None:
        engine = _in_memory_engine()
        inspector = inspect(engine)
        pk = inspector.get_pk_constraint("nodes")
        assert pk["constrained_columns"] == ["id"]

    def test_unique_path(self) -> None:
        engine = _in_memory_engine()
        inspector = inspect(engine)
        uniques = inspector.get_unique_constraints("nodes")
        path_unique = [u for u in uniques if "path" in u["column_names"]]
        assert len(path_unique) == 1

    def test_required_columns_present(self) -> None:
        engine = _in_memory_engine()
        inspector = inspect(engine)
        columns = {c["name"] for c in inspector.get_columns("nodes")}
        required = {
            "id",
            "title",
            "type",
            "status",
            "path",
            "created",
            "modified",
            "subtype",
            "maturity",
            "topic",
            "aliases",
            "session",
            "archived",
            "degree_in",
            "degree_out",
            "pagerank",
            "cluster_id",
            "betweenness",
        }
        assert required.issubset(columns)


class TestEdgesTable:
    def test_unique_constraint(self) -> None:
        engine = _in_memory_engine()
        inspector = inspect(engine)
        uniques = inspector.get_unique_constraints("edges")
        triple = [
            u for u in uniques if set(u["column_names"]) == {"source_id", "target_id", "edge_type"}
        ]
        assert len(triple) == 1


class TestFTS5:
    def test_fts5_insert_and_search(self) -> None:
        engine = _in_memory_engine()
        with engine.begin() as conn:
            conn.execute(
                text(
                    "INSERT INTO nodes_fts (id, title, body) "
                    "VALUES ('ztl_abc12345', 'Database Architecture', "
                    "'Exploring graph databases and SQL alternatives')"
                )
            )
            rows = conn.execute(
                text("SELECT id FROM nodes_fts WHERE nodes_fts MATCH 'graph'")
            ).fetchall()
            assert len(rows) == 1
            assert rows[0][0] == "ztl_abc12345"

    def test_fts5_no_match(self) -> None:
        engine = _in_memory_engine()
        with engine.begin() as conn:
            conn.execute(
                text(
                    "INSERT INTO nodes_fts (id, title, body) "
                    "VALUES ('ztl_abc12345', 'Test', 'Nothing relevant')"
                )
            )
            rows = conn.execute(
                text("SELECT id FROM nodes_fts WHERE nodes_fts MATCH 'nonexistent'")
            ).fetchall()
            assert len(rows) == 0
