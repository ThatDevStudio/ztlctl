"""GraphEngine — lazy-built NetworkX graph from SQLite edges.

Rebuilt per invocation, no cross-invocation cache.
At vault scale (< 10K nodes), full rebuild takes < 10ms.
Commands that don't need graph operations never build it.
(DESIGN.md Section 3)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import networkx as nx

if TYPE_CHECKING:
    from sqlalchemy.engine import Engine

# Node and edge types are loosely typed until the schema is finalized.
_Graph = nx.DiGraph[str]


class GraphEngine:
    """Lazy-loading graph engine backed by SQLite edge data."""

    def __init__(self, db: Engine) -> None:
        self._db = db
        self._graph: _Graph | None = None

    @property
    def graph(self) -> _Graph:
        """Return the graph, building from DB on first access."""
        if self._graph is None:
            self._graph = self._build_from_db()
        return self._graph

    def invalidate(self) -> None:
        """Clear the cached graph, forcing rebuild on next access."""
        self._graph = None

    def _build_from_db(self) -> _Graph:
        """Build a NetworkX DiGraph from the edges table."""
        from sqlalchemy import select

        from ztlctl.infrastructure.database.schema import edges

        g: _Graph = nx.DiGraph()
        with self._db.connect() as conn:
            for row in conn.execute(select(edges)):
                g.add_edge(
                    row.source_id,
                    row.target_id,
                    edge_type=row.edge_type,
                    weight=row.weight,
                    source_layer=row.source_layer,
                )
        return g
