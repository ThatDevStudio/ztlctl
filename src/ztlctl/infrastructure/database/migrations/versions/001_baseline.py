"""Baseline schema — matches schema.py at Phase 6 completion.

Revision ID: 001_baseline
Revises: None
Create Date: 2026-02-25

This is the initial migration that captures the full ztlctl schema.
Existing databases get stamped at this revision without running it;
fresh databases created after this migration was added get it applied
during ``ztlctl upgrade``.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "001_baseline"
down_revision: str | None = None
branch_labels: tuple[str, ...] | None = None
depends_on: tuple[str, ...] | None = None


def upgrade() -> None:
    # nodes
    op.create_table(
        "nodes",
        sa.Column("id", sa.Text, primary_key=True),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("type", sa.Text, nullable=False),
        sa.Column("subtype", sa.Text),
        sa.Column("status", sa.Text, nullable=False),
        sa.Column("maturity", sa.Text),
        sa.Column("topic", sa.Text),
        sa.Column("path", sa.Text, nullable=False, unique=True),
        sa.Column("aliases", sa.Text),
        sa.Column("session", sa.Text),
        sa.Column("archived", sa.Integer, server_default="0"),
        sa.Column("created", sa.Text, nullable=False),
        sa.Column("modified", sa.Text, nullable=False),
        sa.Column("degree_in", sa.Integer, server_default="0"),
        sa.Column("degree_out", sa.Integer, server_default="0"),
        sa.Column("pagerank", sa.REAL, server_default="0.0"),
        sa.Column("cluster_id", sa.Integer),
        sa.Column("betweenness", sa.REAL, server_default="0.0"),
    )
    op.create_index("ix_nodes_type", "nodes", ["type"])
    op.create_index("ix_nodes_status", "nodes", ["status"])
    op.create_index("ix_nodes_archived", "nodes", ["archived"])
    op.create_index("ix_nodes_topic", "nodes", ["topic"])

    # edges
    op.create_table(
        "edges",
        sa.Column("source_id", sa.Text, sa.ForeignKey("nodes.id"), nullable=False),
        sa.Column("target_id", sa.Text, sa.ForeignKey("nodes.id"), nullable=False),
        sa.Column("edge_type", sa.Text, server_default="relates"),
        sa.Column("source_layer", sa.Text),
        sa.Column("weight", sa.REAL, server_default="1.0"),
        sa.Column("bidirectional", sa.Integer),
        sa.Column("created", sa.Text, nullable=False),
        sa.UniqueConstraint("source_id", "target_id", "edge_type"),
    )
    op.create_index("ix_edges_source", "edges", ["source_id"])
    op.create_index("ix_edges_target", "edges", ["target_id"])

    # tags_registry
    op.create_table(
        "tags_registry",
        sa.Column("tag", sa.Text, primary_key=True),
        sa.Column("domain", sa.Text, nullable=False),
        sa.Column("scope", sa.Text, nullable=False),
        sa.Column("created", sa.Text, nullable=False),
        sa.Column("description", sa.Text),
    )

    # node_tags
    op.create_table(
        "node_tags",
        sa.Column("node_id", sa.Text, sa.ForeignKey("nodes.id"), nullable=False),
        sa.Column("tag", sa.Text, nullable=False),
        sa.UniqueConstraint("node_id", "tag"),
    )
    op.create_index("ix_node_tags_tag", "node_tags", ["tag"])

    # id_counters
    op.create_table(
        "id_counters",
        sa.Column("type_prefix", sa.Text, primary_key=True),
        sa.Column("next_value", sa.Integer, nullable=False, server_default="1"),
    )

    # reweave_log
    op.create_table(
        "reweave_log",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("source_id", sa.Text, nullable=False),
        sa.Column("target_id", sa.Text, nullable=False),
        sa.Column("action", sa.Text, nullable=False),
        sa.Column("direction", sa.Text),
        sa.Column("timestamp", sa.Text, nullable=False),
        sa.Column("undone", sa.Integer, server_default="0"),
    )

    # event_wal
    op.create_table(
        "event_wal",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("hook_name", sa.Text, nullable=False),
        sa.Column("payload", sa.Text, nullable=False),
        sa.Column("status", sa.Text, nullable=False),
        sa.Column("error", sa.Text),
        sa.Column("retries", sa.Integer, server_default="0"),
        sa.Column("session_id", sa.Text),
        sa.Column("created", sa.Text, nullable=False),
        sa.Column("completed", sa.Text),
    )

    # session_logs
    op.create_table(
        "session_logs",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("session_id", sa.Text, nullable=False),
        sa.Column("timestamp", sa.Text, nullable=False),
        sa.Column("type", sa.Text, nullable=False),
        sa.Column("subtype", sa.Text),
        sa.Column("summary", sa.Text, nullable=False),
        sa.Column("detail", sa.Text),
        sa.Column("cost", sa.Integer, server_default="0"),
        sa.Column("pinned", sa.Integer, server_default="0"),
        sa.Column("references", sa.Text),
        sa.Column("metadata", sa.Text),
    )

    # FTS5 virtual table (raw SQL — Alembic can't express virtual tables)
    op.execute("CREATE VIRTUAL TABLE IF NOT EXISTS nodes_fts USING fts5(id UNINDEXED, title, body)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS nodes_fts")
    op.drop_table("session_logs")
    op.drop_table("event_wal")
    op.drop_table("reweave_log")
    op.drop_table("id_counters")
    op.drop_table("node_tags")
    op.drop_table("tags_registry")
    op.drop_table("edges")
    op.drop_table("nodes")
