"""Tests for MCP resource contradictions_review_impl.

Tests cover:
- Returns JSON-serializable dict with candidates array
- Returns empty candidates when VectorService unavailable
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from ztlctl.config.settings import ZtlSettings
from ztlctl.infrastructure.vault import Vault

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def vault_root(tmp_path: Path) -> Path:
    (tmp_path / "notes").mkdir()
    (tmp_path / "ops" / "logs").mkdir(parents=True)
    (tmp_path / "ops" / "tasks").mkdir(parents=True)
    return tmp_path


@pytest.fixture
def vault(vault_root: Path) -> Vault:
    settings = ZtlSettings.from_cli(vault_root=vault_root)
    v = Vault(settings)
    try:
        yield v
    finally:
        v.close()


# ---------------------------------------------------------------------------
# Test 7: contradictions_review_impl returns JSON-serializable dict
# ---------------------------------------------------------------------------


class TestContradictionsReviewImpl:
    def test_returns_dict_with_candidates_array(self, vault: Vault) -> None:
        """contradictions_review_impl returns a dict with 'candidates' and 'count' keys."""
        from ztlctl.mcp.resources import contradictions_review_impl

        mock_candidates = [
            {
                "note_a": "NOTE-0001",
                "note_b": "NOTE-0002",
                "title_a": "Note A",
                "title_b": "Note B",
                "score": 0.72,
                "signals": ["cosine_similarity:0.900"],
            }
        ]

        with patch(
            "ztlctl.services.contradiction.ContradictionService.find_candidates"
        ) as mock_find:
            from ztlctl.services.result import ServiceResult

            mock_find.return_value = ServiceResult(
                ok=True,
                op="find_candidates",
                data={"candidates": mock_candidates, "count": 1},
            )
            result = contradictions_review_impl(vault)

        assert isinstance(result, dict)
        assert "candidates" in result
        assert "count" in result
        assert result["count"] == 1
        assert len(result["candidates"]) == 1

        # Verify JSON-serializable
        import json

        serialized = json.dumps(result)
        parsed = json.loads(serialized)
        assert parsed["count"] == 1

    def test_returns_correct_candidate_structure(self, vault: Vault) -> None:
        """contradictions_review_impl passes through candidate fields from find_candidates."""
        from ztlctl.mcp.resources import contradictions_review_impl

        mock_candidates = [
            {
                "note_a": "NOTE-0010",
                "note_b": "NOTE-0011",
                "title_a": "Architecture A",
                "title_b": "Architecture B",
                "score": 0.85,
                "signals": ["cosine_similarity:0.910"],
            }
        ]

        with patch(
            "ztlctl.services.contradiction.ContradictionService.find_candidates"
        ) as mock_find:
            from ztlctl.services.result import ServiceResult

            mock_find.return_value = ServiceResult(
                ok=True,
                op="find_candidates",
                data={"candidates": mock_candidates, "count": 1},
            )
            result = contradictions_review_impl(vault)

        candidate = result["candidates"][0]
        assert candidate["note_a"] == "NOTE-0010"
        assert candidate["note_b"] == "NOTE-0011"
        assert candidate["title_a"] == "Architecture A"
        assert candidate["score"] == 0.85


# ---------------------------------------------------------------------------
# Test 8: contradictions_review_impl returns empty candidates when unavailable
# ---------------------------------------------------------------------------


class TestContradictionsReviewImplUnavailable:
    def test_returns_empty_when_vector_unavailable(self, vault: Vault) -> None:
        """contradictions_review_impl returns empty candidates when VectorService unavailable."""
        from ztlctl.mcp.resources import contradictions_review_impl

        with patch(
            "ztlctl.services.vector.VectorService.is_available",
            return_value=False,
        ):
            result = contradictions_review_impl(vault)

        assert isinstance(result, dict)
        assert result["candidates"] == []
        assert result["count"] == 0

    def test_returns_empty_when_find_candidates_fails(self, vault: Vault) -> None:
        """contradictions_review_impl returns empty candidates on service failure."""
        from ztlctl.mcp.resources import contradictions_review_impl

        with patch(
            "ztlctl.services.contradiction.ContradictionService.find_candidates"
        ) as mock_find:
            from ztlctl.services.result import ServiceError, ServiceResult

            mock_find.return_value = ServiceResult(
                ok=False,
                op="find_candidates",
                error=ServiceError(code="INTERNAL_ERROR", message="Something failed"),
            )
            result = contradictions_review_impl(vault)

        assert result["candidates"] == []
        assert result["count"] == 0

    def test_resource_catalog_includes_review_contradictions(self, vault: Vault) -> None:
        """_RESOURCE_CATALOG includes ztlctl://review/contradictions entry."""
        from ztlctl.mcp.resources import resource_catalog

        catalog = resource_catalog(vault)
        uris = [entry["uri"] for entry in catalog]
        assert "ztlctl://review/contradictions" in uris

    def test_register_resources_includes_contradictions(self, vault: Vault) -> None:
        """register_resources registers ztlctl://review/contradictions on the server."""
        registered: list[str] = []

        class MockServer:
            def resource(self, uri: str):
                registered.append(uri)

                def decorator(fn: Any) -> Any:
                    return fn

                return decorator

        from ztlctl.mcp.resources import register_resources

        register_resources(MockServer(), vault)
        assert "ztlctl://review/contradictions" in registered
