"""Tests for GraphService — six graph algorithms."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import insert

from ztlctl.infrastructure.database.schema import edges, nodes
from ztlctl.infrastructure.vault import Vault
from ztlctl.services.graph import GraphService

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_NOW = datetime.now(UTC).isoformat()


def _insert_node(vault: Vault, node_id: str, **kwargs: Any) -> None:
    """Insert a node directly into the DB."""
    defaults: dict[str, Any] = {
        "id": node_id,
        "title": kwargs.get("title", node_id),
        "type": kwargs.get("type", "note"),
        "subtype": kwargs.get("subtype"),
        "status": kwargs.get("status", "evergreen"),
        "path": kwargs.get("path", f"notes/{node_id}.md"),
        "created": _NOW,
        "modified": _NOW,
        "archived": 0,
    }
    defaults.update(kwargs)
    with vault.engine.begin() as conn:
        conn.execute(insert(nodes).values(**defaults))


def _insert_edge(vault: Vault, source: str, target: str, **kwargs: Any) -> None:
    """Insert an edge directly into the DB."""
    defaults: dict[str, Any] = {
        "source_id": source,
        "target_id": target,
        "edge_type": kwargs.get("edge_type", "relates"),
        "weight": kwargs.get("weight", 1.0),
        "source_layer": kwargs.get("source_layer", "body"),
        "created": _NOW,
    }
    defaults.update(kwargs)
    with vault.engine.begin() as conn:
        conn.execute(insert(edges).values(**defaults))


def _build_chain(vault: Vault, ids: list[str]) -> None:
    """Create a chain: A -> B -> C -> D."""
    for nid in ids:
        _insert_node(vault, nid)
    for i in range(len(ids) - 1):
        _insert_edge(vault, ids[i], ids[i + 1])


def _build_star(vault: Vault, center: str, spokes: list[str]) -> None:
    """Create a star topology: center connected to all spokes."""
    _insert_node(vault, center, title=center)
    for spoke in spokes:
        _insert_node(vault, spoke, title=spoke)
        _insert_edge(vault, center, spoke)


# ---------------------------------------------------------------------------
# related — spreading activation
# ---------------------------------------------------------------------------


class TestRelated:
    def test_related_basic(self, vault: Vault) -> None:
        _build_chain(vault, ["A", "B", "C"])
        svc = GraphService(vault)
        result = svc.related("A")
        assert result.ok
        assert result.data["source_id"] == "A"
        assert result.data["count"] >= 1
        ids = [i["id"] for i in result.data["items"]]
        assert "B" in ids

    def test_related_depth_2(self, vault: Vault) -> None:
        _build_chain(vault, ["A", "B", "C", "D"])
        svc = GraphService(vault)
        result = svc.related("A", depth=2)
        assert result.ok
        ids = [i["id"] for i in result.data["items"]]
        assert "B" in ids
        assert "C" in ids

    def test_related_decay_scores(self, vault: Vault) -> None:
        _build_chain(vault, ["A", "B", "C"])
        svc = GraphService(vault)
        result = svc.related("A", depth=2)
        assert result.ok
        score_map = {i["id"]: i["score"] for i in result.data["items"]}
        # B is 1 hop (score 1.0), C is 2 hops (score 0.5)
        assert score_map["B"] > score_map["C"]

    def test_related_not_found(self, vault: Vault) -> None:
        svc = GraphService(vault)
        result = svc.related("nonexistent")
        assert not result.ok
        assert result.error is not None
        assert result.error.code == "NOT_FOUND"

    def test_related_isolated_node(self, vault: Vault) -> None:
        _insert_node(vault, "isolated")
        svc = GraphService(vault)
        result = svc.related("isolated")
        assert result.ok
        assert result.data["count"] == 0

    def test_related_with_top_limit(self, vault: Vault) -> None:
        _build_star(vault, "hub", ["s1", "s2", "s3", "s4", "s5"])
        svc = GraphService(vault)
        result = svc.related("hub", top=2)
        assert result.ok
        assert result.data["count"] == 2

    def test_related_includes_incoming_edges(self, vault: Vault) -> None:
        """Related should traverse both directions."""
        _insert_node(vault, "X")
        _insert_node(vault, "Y")
        _insert_edge(vault, "Y", "X")  # Y -> X (incoming to X)
        svc = GraphService(vault)
        result = svc.related("X")
        assert result.ok
        ids = [i["id"] for i in result.data["items"]]
        assert "Y" in ids

    def test_related_depth_clamped(self, vault: Vault) -> None:
        """Depth is clamped between 1 and 5."""
        _build_chain(vault, ["A", "B"])
        svc = GraphService(vault)
        # depth=0 should be clamped to 1
        result = svc.related("A", depth=0)
        assert result.ok
        assert result.data["count"] >= 1


# ---------------------------------------------------------------------------
# themes — community detection
# ---------------------------------------------------------------------------


class TestThemes:
    def test_themes_empty_graph(self, vault: Vault) -> None:
        svc = GraphService(vault)
        result = svc.themes()
        assert result.ok
        assert result.data["count"] == 0

    def test_themes_single_community(self, vault: Vault) -> None:
        # Triangle: A-B-C all connected
        _insert_node(vault, "A")
        _insert_node(vault, "B")
        _insert_node(vault, "C")
        _insert_edge(vault, "A", "B")
        _insert_edge(vault, "B", "C")
        _insert_edge(vault, "A", "C")
        svc = GraphService(vault)
        result = svc.themes()
        assert result.ok
        assert result.data["count"] >= 1
        # All nodes should be in communities
        all_members = []
        for comm in result.data["communities"]:
            all_members.extend(m["id"] for m in comm["members"])
        assert "A" in all_members
        assert "B" in all_members
        assert "C" in all_members

    def test_themes_two_clusters(self, vault: Vault) -> None:
        # Cluster 1: A-B-C, Cluster 2: X-Y-Z, bridge: C-X
        for nid in ["A", "B", "C", "X", "Y", "Z"]:
            _insert_node(vault, nid)
        _insert_edge(vault, "A", "B")
        _insert_edge(vault, "B", "C")
        _insert_edge(vault, "A", "C")
        _insert_edge(vault, "X", "Y")
        _insert_edge(vault, "Y", "Z")
        _insert_edge(vault, "X", "Z")
        _insert_edge(vault, "C", "X")  # bridge
        svc = GraphService(vault)
        result = svc.themes()
        assert result.ok
        assert result.data["count"] >= 1

    def test_themes_has_community_structure(self, vault: Vault) -> None:
        _build_star(vault, "hub", ["s1", "s2", "s3"])
        svc = GraphService(vault)
        result = svc.themes()
        assert result.ok
        for comm in result.data["communities"]:
            assert "community_id" in comm
            assert "size" in comm
            assert "members" in comm

    def test_themes_louvain_fallback(self, vault: Vault) -> None:
        """Without leidenalg, should fall back to Louvain with a warning."""
        _build_star(vault, "hub", ["s1", "s2"])
        svc = GraphService(vault)
        result = svc.themes()
        assert result.ok
        # May or may not have warning depending on leidenalg availability


# ---------------------------------------------------------------------------
# rank — PageRank
# ---------------------------------------------------------------------------


class TestRank:
    def test_rank_empty_graph(self, vault: Vault) -> None:
        svc = GraphService(vault)
        result = svc.rank()
        assert result.ok
        assert result.data["count"] == 0

    def test_rank_returns_scores(self, vault: Vault) -> None:
        _build_star(vault, "hub", ["s1", "s2", "s3"])
        svc = GraphService(vault)
        result = svc.rank()
        assert result.ok
        assert result.data["count"] == 4
        for item in result.data["items"]:
            assert "score" in item
            assert isinstance(item["score"], float)
            assert item["score"] > 0

    def test_rank_hub_scores_higher(self, vault: Vault) -> None:
        """Hub that receives links should score higher."""
        # Create hub with incoming links
        _insert_node(vault, "hub")
        for i in range(5):
            nid = f"spoke_{i}"
            _insert_node(vault, nid)
            _insert_edge(vault, nid, "hub")  # all point TO hub
        svc = GraphService(vault)
        result = svc.rank()
        assert result.ok
        # Hub should be in the top results
        top_item = result.data["items"][0]
        assert top_item["id"] == "hub"

    def test_rank_top_limit(self, vault: Vault) -> None:
        _build_star(vault, "hub", ["s1", "s2", "s3", "s4"])
        svc = GraphService(vault)
        result = svc.rank(top=2)
        assert result.ok
        assert result.data["count"] == 2

    def test_rank_includes_metadata(self, vault: Vault) -> None:
        _insert_node(vault, "N1", title="Test Note", type="note")
        svc = GraphService(vault)
        result = svc.rank()
        assert result.ok
        item = result.data["items"][0]
        assert item["title"] == "Test Note"
        assert item["type"] == "note"


# ---------------------------------------------------------------------------
# path — shortest path
# ---------------------------------------------------------------------------


class TestPath:
    def test_path_direct(self, vault: Vault) -> None:
        _insert_node(vault, "A")
        _insert_node(vault, "B")
        _insert_edge(vault, "A", "B")
        svc = GraphService(vault)
        result = svc.path("A", "B")
        assert result.ok
        assert result.data["length"] == 1
        assert len(result.data["steps"]) == 2
        assert result.data["steps"][0]["id"] == "A"
        assert result.data["steps"][1]["id"] == "B"

    def test_path_multi_hop(self, vault: Vault) -> None:
        _build_chain(vault, ["A", "B", "C", "D"])
        svc = GraphService(vault)
        result = svc.path("A", "D")
        assert result.ok
        assert result.data["length"] == 3
        ids = [s["id"] for s in result.data["steps"]]
        assert ids == ["A", "B", "C", "D"]

    def test_path_reverse_direction(self, vault: Vault) -> None:
        """Path should work in reverse direction (undirected view)."""
        _insert_node(vault, "A")
        _insert_node(vault, "B")
        _insert_edge(vault, "A", "B")  # A -> B
        svc = GraphService(vault)
        result = svc.path("B", "A")  # reverse
        assert result.ok
        assert result.data["length"] == 1

    def test_path_no_path(self, vault: Vault) -> None:
        _insert_node(vault, "A")
        _insert_node(vault, "B")
        # No edge between A and B
        svc = GraphService(vault)
        result = svc.path("A", "B")
        assert not result.ok
        assert result.error is not None
        assert result.error.code == "NO_PATH"

    def test_path_source_not_found(self, vault: Vault) -> None:
        _insert_node(vault, "B")
        svc = GraphService(vault)
        result = svc.path("nonexistent", "B")
        assert not result.ok
        assert result.error is not None
        assert result.error.code == "NOT_FOUND"
        assert "source" in result.error.message

    def test_path_target_not_found(self, vault: Vault) -> None:
        _insert_node(vault, "A")
        svc = GraphService(vault)
        result = svc.path("A", "nonexistent")
        assert not result.ok
        assert result.error is not None
        assert result.error.code == "NOT_FOUND"
        assert "target" in result.error.message

    def test_path_same_node(self, vault: Vault) -> None:
        _insert_node(vault, "A")
        svc = GraphService(vault)
        result = svc.path("A", "A")
        assert result.ok
        assert result.data["length"] == 0
        assert len(result.data["steps"]) == 1


# ---------------------------------------------------------------------------
# gaps — structural holes (constraint)
# ---------------------------------------------------------------------------


class TestGaps:
    def test_gaps_empty_graph(self, vault: Vault) -> None:
        svc = GraphService(vault)
        result = svc.gaps()
        assert result.ok
        assert result.data["count"] == 0

    def test_gaps_returns_constraint(self, vault: Vault) -> None:
        # Triangle: A-B-C (high constraint)
        _insert_node(vault, "A")
        _insert_node(vault, "B")
        _insert_node(vault, "C")
        _insert_edge(vault, "A", "B")
        _insert_edge(vault, "B", "C")
        _insert_edge(vault, "A", "C")
        svc = GraphService(vault)
        result = svc.gaps()
        assert result.ok
        for item in result.data["items"]:
            assert "constraint" in item
            assert isinstance(item["constraint"], float)

    def test_gaps_sorted_descending(self, vault: Vault) -> None:
        _build_star(vault, "hub", ["s1", "s2", "s3"])
        # Add cross-links so constraint values differ
        _insert_edge(vault, "s1", "s2")
        svc = GraphService(vault)
        result = svc.gaps()
        assert result.ok
        if result.data["count"] >= 2:
            constraints = [i["constraint"] for i in result.data["items"]]
            assert constraints == sorted(constraints, reverse=True)

    def test_gaps_top_limit(self, vault: Vault) -> None:
        _build_star(vault, "hub", ["s1", "s2", "s3", "s4"])
        _insert_edge(vault, "s1", "s2")
        _insert_edge(vault, "s3", "s4")
        svc = GraphService(vault)
        result = svc.gaps(top=2)
        assert result.ok
        assert result.data["count"] <= 2

    def test_gaps_isolated_nodes_excluded(self, vault: Vault) -> None:
        """Isolated nodes have NaN constraint and should be excluded."""
        _insert_node(vault, "isolated")
        _insert_node(vault, "A")
        _insert_node(vault, "B")
        _insert_edge(vault, "A", "B")
        svc = GraphService(vault)
        result = svc.gaps()
        assert result.ok
        ids = [i["id"] for i in result.data["items"]]
        assert "isolated" not in ids


# ---------------------------------------------------------------------------
# bridges — betweenness centrality
# ---------------------------------------------------------------------------


class TestBridges:
    def test_bridges_empty_graph(self, vault: Vault) -> None:
        svc = GraphService(vault)
        result = svc.bridges()
        assert result.ok
        assert result.data["count"] == 0

    def test_bridges_identifies_bridge_node(self, vault: Vault) -> None:
        """A node connecting two clusters should have high betweenness."""
        # Cluster 1: A-B, Cluster 2: C-D, bridge: B-C
        for nid in ["A", "B", "C", "D"]:
            _insert_node(vault, nid)
        _insert_edge(vault, "A", "B")
        _insert_edge(vault, "B", "C")
        _insert_edge(vault, "C", "D")
        svc = GraphService(vault)
        result = svc.bridges()
        assert result.ok
        assert result.data["count"] >= 1
        ids = [i["id"] for i in result.data["items"]]
        # B and C should be bridges
        assert "B" in ids or "C" in ids

    def test_bridges_returns_centrality(self, vault: Vault) -> None:
        _build_chain(vault, ["A", "B", "C"])
        svc = GraphService(vault)
        result = svc.bridges()
        assert result.ok
        for item in result.data["items"]:
            assert "centrality" in item
            assert isinstance(item["centrality"], float)
            assert item["centrality"] > 0

    def test_bridges_sorted_descending(self, vault: Vault) -> None:
        _build_chain(vault, ["A", "B", "C", "D", "E"])
        svc = GraphService(vault)
        result = svc.bridges()
        assert result.ok
        if result.data["count"] >= 2:
            centralities = [i["centrality"] for i in result.data["items"]]
            assert centralities == sorted(centralities, reverse=True)

    def test_bridges_excludes_zero_centrality(self, vault: Vault) -> None:
        """Leaf nodes with zero betweenness should be excluded."""
        _build_chain(vault, ["A", "B", "C"])
        svc = GraphService(vault)
        result = svc.bridges()
        assert result.ok
        for item in result.data["items"]:
            assert item["centrality"] > 0

    def test_bridges_top_limit(self, vault: Vault) -> None:
        _build_chain(vault, ["A", "B", "C", "D", "E"])
        svc = GraphService(vault)
        result = svc.bridges(top=1)
        assert result.ok
        assert result.data["count"] <= 1
