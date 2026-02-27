"""SQLAlchemy Core table definitions for the ztlctl database.

All tables from DESIGN.md Section 9. The FTS5 virtual table is created
via raw DDL in the initialization function since SQLAlchemy cannot
express SQLite virtual tables natively.
"""

from __future__ import annotations

from sqlalchemy import (
    REAL,
    Column,
    ForeignKey,
    Index,
    Integer,
    MetaData,
    Table,
    Text,
    UniqueConstraint,
)

metadata = MetaData()

nodes = Table(
    "nodes",
    metadata,
    Column("id", Text, primary_key=True),
    Column("title", Text, nullable=False),
    Column("type", Text, nullable=False),
    Column("subtype", Text),
    Column("status", Text, nullable=False),
    Column("maturity", Text),
    Column("topic", Text),
    Column("path", Text, nullable=False, unique=True),
    Column("aliases", Text),  # JSON array
    Column("session", Text),  # LOG-NNNN
    Column("archived", Integer, default=0, server_default="0"),
    Column("created", Text, nullable=False),
    Column("modified", Text, nullable=False),
    Column("created_at", Text),  # high-resolution timestamp (DB-only)
    Column("modified_at", Text),  # high-resolution timestamp (DB-only)
    # Materialized graph metrics (recomputed by graph service)
    Column("degree_in", Integer, default=0, server_default="0"),
    Column("degree_out", Integer, default=0, server_default="0"),
    Column("pagerank", REAL, default=0.0, server_default="0.0"),
    Column("cluster_id", Integer),
    Column("betweenness", REAL, default=0.0, server_default="0.0"),
)

edges = Table(
    "edges",
    metadata,
    Column("source_id", Text, ForeignKey("nodes.id"), nullable=False),
    Column("target_id", Text, ForeignKey("nodes.id"), nullable=False),
    Column("edge_type", Text, default="relates", server_default="relates"),
    Column("source_layer", Text),  # frontmatter | body
    Column("weight", REAL, default=1.0, server_default="1.0"),
    Column("bidirectional", Integer),  # Reserved — not yet maintained by services
    Column("created", Text, nullable=False),
    UniqueConstraint("source_id", "target_id", "edge_type"),
)

tags_registry = Table(
    "tags_registry",
    metadata,
    Column("tag", Text, primary_key=True),
    Column("domain", Text, nullable=False),
    Column("scope", Text, nullable=False),
    Column("created", Text, nullable=False),
    Column("description", Text),
)

node_tags = Table(
    "node_tags",
    metadata,
    Column("node_id", Text, ForeignKey("nodes.id"), nullable=False),
    Column("tag", Text, nullable=False),
    UniqueConstraint("node_id", "tag"),
)

# ---------------------------------------------------------------------------
# Indexes for frequently filtered columns
# ---------------------------------------------------------------------------

Index("ix_nodes_type", nodes.c.type)
Index("ix_nodes_status", nodes.c.status)
Index("ix_nodes_archived", nodes.c.archived)
Index("ix_nodes_topic", nodes.c.topic)
Index("ix_edges_source", edges.c.source_id)
Index("ix_edges_target", edges.c.target_id)
Index("ix_node_tags_tag", node_tags.c.tag)

id_counters = Table(
    "id_counters",
    metadata,
    Column("type_prefix", Text, primary_key=True),
    Column("next_value", Integer, nullable=False, default=1, server_default="1"),
)

reweave_log = Table(
    "reweave_log",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("source_id", Text, nullable=False),
    Column("target_id", Text, nullable=False),
    Column("action", Text, nullable=False),
    Column("direction", Text),
    Column("timestamp", Text, nullable=False),
    Column("undone", Integer, default=0, server_default="0"),
)

event_wal = Table(
    "event_wal",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("hook_name", Text, nullable=False),
    Column("payload", Text, nullable=False),  # JSON
    Column("status", Text, nullable=False),
    Column("error", Text),
    Column("retries", Integer, default=0, server_default="0"),
    Column("session_id", Text),
    Column("created", Text, nullable=False),
    Column("completed", Text),
)

session_logs = Table(
    "session_logs",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("session_id", Text, nullable=False),
    Column("timestamp", Text, nullable=False),
    Column("type", Text, nullable=False),
    Column("subtype", Text),
    Column("summary", Text, nullable=False),
    Column("detail", Text),
    Column("cost", Integer, default=0, server_default="0"),
    Column("pinned", Integer, default=0, server_default="0"),
    Column("references", Text),  # JSON array
    Column("metadata", Text),  # JSON object
)

# FTS5 virtual table DDL — standalone (no content= clause).
# The service layer manages inserts/deletes explicitly alongside node ops.
# id is UNINDEXED: stored for joins but not searched.
FTS5_CREATE_SQL = (
    "CREATE VIRTUAL TABLE IF NOT EXISTS nodes_fts USING fts5(id UNINDEXED, title, body)"
)

# sqlite-vec virtual table DDL — created when semantic search is enabled.
# node_id maps to nodes.id; embedding dimension must match SearchConfig.embedding_dim.
VEC_CREATE_SQL = (
    "CREATE VIRTUAL TABLE IF NOT EXISTS vec_items USING vec0("
    "node_id TEXT PRIMARY KEY, embedding FLOAT[384])"
)
