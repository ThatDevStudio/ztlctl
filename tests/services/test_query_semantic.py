"""Tests for semantic and hybrid search ranking in QueryService."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

from tests.conftest import create_note
from ztlctl.infrastructure.vault import Vault
from ztlctl.services.query import QueryService


class TestSemanticSearch:
    def test_semantic_unavailable_falls_back_to_fts(self, vault: Vault) -> None:
        """When VectorService unavailable, semantic falls back to FTS5 with warning."""
        create_note(vault, "Python Patterns")
        svc = QueryService(vault)

        mock_vec = MagicMock()
        mock_vec.is_available.return_value = False

        with patch.object(svc, "_get_vector_service", return_value=mock_vec):
            result = svc.search("Python", rank_by="semantic")

        assert result.ok
        assert any("unavailable" in w.lower() for w in (result.warnings or []))

    def test_hybrid_unavailable_falls_back_to_fts(self, vault: Vault) -> None:
        """When VectorService unavailable, hybrid uses FTS5 only with warning."""
        create_note(vault, "Design Patterns")
        svc = QueryService(vault)

        mock_vec = MagicMock()
        mock_vec.is_available.return_value = False

        with patch.object(svc, "_get_vector_service", return_value=mock_vec):
            result = svc.search("Design", rank_by="hybrid")

        assert result.ok
        assert any("unavailable" in w.lower() for w in (result.warnings or []))

    def test_semantic_with_available_vector_service(self, vault: Vault) -> None:
        """When VectorService available, semantic uses vector results."""
        data = create_note(vault, "Neural Networks")
        svc = QueryService(vault)

        mock_vec = MagicMock()
        mock_vec.is_available.return_value = True
        mock_vec.search_similar.return_value = [
            {"node_id": data["id"], "distance": 0.2},
        ]

        with patch.object(svc, "_get_vector_service", return_value=mock_vec):
            result = svc.search("neural", rank_by="semantic")

        assert result.ok
        mock_vec.search_similar.assert_called_once()
        # Should have 1 result with similarity score
        assert result.data["count"] == 1
        assert result.data["items"][0]["id"] == data["id"]
        # Cosine similarity: 1 - 0.2/2 = 0.9
        assert result.data["items"][0]["score"] == 0.9


class TestHybridMerge:
    def test_merge_hybrid_scores_weighted(self) -> None:
        """Hybrid merge combines BM25 and cosine with weights."""
        fts_items: list[dict[str, Any]] = [
            {"id": "a", "score": -5.0, "title": "A"},
            {"id": "b", "score": -3.0, "title": "B"},
        ]
        vec_results: list[dict[str, Any]] = [
            {"node_id": "a", "distance": 0.2},
            {"node_id": "b", "distance": 0.8},
        ]
        result = QueryService._merge_hybrid_scores(fts_items, vec_results, 0.5, 10)
        assert len(result) == 2
        # All scores should be between 0 and 1
        for item in result:
            assert 0.0 <= item["score"] <= 1.0

    def test_merge_with_zero_semantic_weight(self) -> None:
        """With semantic_weight=0, result is pure BM25 ranking."""
        fts_items: list[dict[str, Any]] = [
            {"id": "a", "score": -5.0, "title": "Best"},
            {"id": "b", "score": -2.0, "title": "Okay"},
        ]
        vec_results: list[dict[str, Any]] = [
            {"node_id": "b", "distance": 0.1},
            {"node_id": "a", "distance": 0.9},
        ]
        result = QueryService._merge_hybrid_scores(fts_items, vec_results, 0.0, 10)
        # Pure BM25: "a" (score 5.0) should rank above "b" (score 2.0)
        assert result[0]["id"] == "a"

    def test_merge_respects_limit(self) -> None:
        """Merge respects the limit parameter."""
        fts_items: list[dict[str, Any]] = [
            {"id": f"n{i}", "score": float(-i - 1), "title": f"T{i}"} for i in range(10)
        ]
        vec_results: list[dict[str, Any]] = [
            {"node_id": f"n{i}", "distance": i * 0.1} for i in range(10)
        ]
        result = QueryService._merge_hybrid_scores(fts_items, vec_results, 0.5, 3)
        assert len(result) == 3
