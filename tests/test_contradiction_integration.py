"""Integration tests for CheckService CAT_SEMANTIC and ContradictionService.confirm_contradiction.

Tests cover:
- CAT_SEMANTIC integration in CheckService.check()
- _check_semantic graceful skip when VectorService unavailable
- _check_semantic returns CheckIssue entries for each candidate pair
- confirm_contradiction records bidirectional 'contradicts' edges
- confirm_contradiction returns error for unknown notes
- confirm_contradiction skips duplicate edges
"""

from __future__ import annotations

from typing import Any
from unittest.mock import patch

from ztlctl.infrastructure.vault import Vault

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _create_note(vault: Vault, title: str, tags: list[str] | None = None) -> dict[str, Any]:
    from ztlctl.services.create import CreateService

    kwargs: dict[str, Any] = {}
    if tags:
        kwargs["tags"] = tags
    result = CreateService(vault).create_note(title, **kwargs)
    assert result.ok, result.error
    return result.data


def _get_contradicts_edges(vault: Vault, note_a: str, note_b: str) -> list[Any]:
    """Return all 'contradicts' edges between note_a and note_b."""
    from sqlalchemy import select

    from ztlctl.infrastructure.database.schema import edges

    with vault.engine.connect() as conn:
        rows = conn.execute(
            select(edges).where(
                edges.c.edge_type == "contradicts",
                edges.c.source_id.in_([note_a, note_b]),
                edges.c.target_id.in_([note_a, note_b]),
            )
        ).fetchall()
    return rows


# ---------------------------------------------------------------------------
# Test 1: check() with min_severity="info" includes CAT_SEMANTIC issues
# ---------------------------------------------------------------------------


class TestCheckSemanticIntegration:
    def test_check_includes_cat_semantic_when_candidates_found(self, vault: Vault) -> None:
        """check() with min_severity='info' includes CAT_SEMANTIC issues when contradictions found."""  # noqa: E501
        from ztlctl.services.check import CAT_SEMANTIC, CheckService

        note_a = _create_note(vault, "Note A Semantic", ["arch"])
        note_b = _create_note(vault, "Note B Semantic", ["arch"])

        mock_candidates = [
            {
                "note_a": note_a["id"],
                "note_b": note_b["id"],
                "title_a": "Note A Semantic",
                "title_b": "Note B Semantic",
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
            result = CheckService(vault).check(min_severity="info")

        assert result.ok
        issues = result.data.get("issues", [])
        semantic_issues = [i for i in issues if i.get("category") == CAT_SEMANTIC]
        assert len(semantic_issues) == 1
        assert "Note A Semantic" in semantic_issues[0]["message"]
        assert "Note B Semantic" in semantic_issues[0]["message"]

    def test_check_excludes_semantic_at_warning_severity(self, vault: Vault) -> None:
        """check() with default min_severity='warning' excludes info-level semantic issues."""
        from ztlctl.services.check import CAT_SEMANTIC, CheckService

        note_a = _create_note(vault, "Note Warn A", ["arch"])
        note_b = _create_note(vault, "Note Warn B", ["arch"])

        mock_candidates = [
            {
                "note_a": note_a["id"],
                "note_b": note_b["id"],
                "title_a": "Note Warn A",
                "title_b": "Note Warn B",
                "score": 0.72,
                "signals": [],
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
            result = CheckService(vault).check(min_severity="warning")

        assert result.ok
        issues = result.data.get("issues", [])
        semantic_issues = [i for i in issues if i.get("category") == CAT_SEMANTIC]
        assert len(semantic_issues) == 0


# ---------------------------------------------------------------------------
# Test 2: _check_semantic returns empty list when VectorService unavailable
# ---------------------------------------------------------------------------


class TestCheckSemanticVectorUnavailable:
    def test_semantic_check_skips_gracefully_when_vector_unavailable(self, vault: Vault) -> None:
        """_check_semantic returns empty list when VectorService unavailable (graceful skip)."""
        from ztlctl.services.check import CAT_SEMANTIC, CheckService

        with patch(
            "ztlctl.services.vector.VectorService.is_available",
            return_value=False,
        ):
            result = CheckService(vault).check(min_severity="info")

        assert result.ok
        issues = result.data.get("issues", [])
        semantic_issues = [i for i in issues if i.get("category") == CAT_SEMANTIC]
        assert len(semantic_issues) == 0


# ---------------------------------------------------------------------------
# Test 3: _check_semantic returns CheckIssue entries with severity="info"
# ---------------------------------------------------------------------------


class TestCheckSemanticIssueShape:
    def test_semantic_issue_has_correct_shape(self, vault: Vault) -> None:
        """_check_semantic produces CheckIssue with severity='info' and required fields."""
        from ztlctl.services.check import CAT_SEMANTIC, SEVERITY_INFO, CheckService

        note_a = _create_note(vault, "Arch Monolith Note", ["system"])
        note_b = _create_note(vault, "Arch Microservice Note", ["system"])

        mock_candidates = [
            {
                "note_a": note_a["id"],
                "note_b": note_b["id"],
                "title_a": "Arch Monolith Note",
                "title_b": "Arch Microservice Note",
                "score": 0.65,
                "signals": ["cosine_similarity:0.910", "negation_density:3_keywords"],
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
            result = CheckService(vault).check(min_severity="info")

        assert result.ok
        issues = result.data.get("issues", [])
        semantic_issues = [i for i in issues if i.get("category") == CAT_SEMANTIC]
        assert len(semantic_issues) == 1

        issue = semantic_issues[0]
        assert issue["severity"] == SEVERITY_INFO
        assert issue["category"] == CAT_SEMANTIC
        assert "message" in issue
        assert "Arch Monolith Note" in issue["message"]
        assert "Arch Microservice Note" in issue["message"]
        assert "score" in issue
        assert issue["note_a"] == note_a["id"]
        assert issue["note_b"] == note_b["id"]


# ---------------------------------------------------------------------------
# Test 4: confirm_contradiction records bidirectional edges
# ---------------------------------------------------------------------------


class TestConfirmContradictionEdges:
    def test_confirm_creates_bidirectional_contradicts_edges(self, vault: Vault) -> None:
        """confirm_contradiction records two edges: A->B and B->A with edge_type='contradicts'."""
        from ztlctl.services.contradiction import ContradictionService

        note_a = _create_note(vault, "Edge Note A", ["policy"])
        note_b = _create_note(vault, "Edge Note B", ["policy"])

        result = ContradictionService(vault).confirm_contradiction(
            note_a=note_a["id"], note_b=note_b["id"]
        )

        assert result.ok, result.error
        assert result.op == "confirm_contradiction"
        assert result.data["note_a"] == note_a["id"]
        assert result.data["note_b"] == note_b["id"]
        assert result.data["edges_created"] == 2

        edges_rows = _get_contradicts_edges(vault, note_a["id"], note_b["id"])
        assert len(edges_rows) == 2

        # Check that both directions are present
        directions = {(str(r.source_id), str(r.target_id)) for r in edges_rows}
        assert (note_a["id"], note_b["id"]) in directions
        assert (note_b["id"], note_a["id"]) in directions

    def test_confirm_edges_have_correct_edge_type_and_layer(self, vault: Vault) -> None:
        """Inserted edges have edge_type='contradicts' and source_layer='user'."""
        from sqlalchemy import select

        from ztlctl.infrastructure.database.schema import edges
        from ztlctl.services.contradiction import ContradictionService

        note_a = _create_note(vault, "Layer Note A", ["test"])
        note_b = _create_note(vault, "Layer Note B", ["test"])

        ContradictionService(vault).confirm_contradiction(note_a=note_a["id"], note_b=note_b["id"])

        with vault.engine.connect() as conn:
            rows = conn.execute(select(edges).where(edges.c.edge_type == "contradicts")).fetchall()

        assert len(rows) == 2
        for row in rows:
            assert row.edge_type == "contradicts"
            assert row.source_layer == "user"


# ---------------------------------------------------------------------------
# Test 5: confirm_contradiction returns error for unknown notes
# ---------------------------------------------------------------------------


class TestConfirmContradictionNotFound:
    def test_returns_error_when_note_a_not_found(self, vault: Vault) -> None:
        """confirm_contradiction returns error when note_a does not exist."""
        from ztlctl.services.contradiction import ContradictionService

        note_b = _create_note(vault, "Existing Note B", ["x"])

        result = ContradictionService(vault).confirm_contradiction(
            note_a="FAKE-9999", note_b=note_b["id"]
        )

        assert not result.ok
        assert result.error is not None
        assert result.error.code in ("NOT_FOUND", "VALIDATION_ERROR")

    def test_returns_error_when_note_b_not_found(self, vault: Vault) -> None:
        """confirm_contradiction returns error when note_b does not exist."""
        from ztlctl.services.contradiction import ContradictionService

        note_a = _create_note(vault, "Existing Note A", ["x"])

        result = ContradictionService(vault).confirm_contradiction(
            note_a=note_a["id"], note_b="FAKE-9999"
        )

        assert not result.ok
        assert result.error is not None
        assert result.error.code in ("NOT_FOUND", "VALIDATION_ERROR")


# ---------------------------------------------------------------------------
# Test 6: confirm_contradiction skips duplicate edges
# ---------------------------------------------------------------------------


class TestConfirmContradictionDuplicates:
    def test_duplicate_call_does_not_create_extra_edges(self, vault: Vault) -> None:
        """confirm_contradiction does not insert duplicate edges on repeat call."""
        from ztlctl.services.contradiction import ContradictionService

        note_a = _create_note(vault, "Dup Note A", ["dup"])
        note_b = _create_note(vault, "Dup Note B", ["dup"])

        svc = ContradictionService(vault)
        result1 = svc.confirm_contradiction(note_a=note_a["id"], note_b=note_b["id"])
        result2 = svc.confirm_contradiction(note_a=note_a["id"], note_b=note_b["id"])

        assert result1.ok
        assert result2.ok

        # Second call should create 0 edges (duplicates skipped)
        assert result2.data["edges_created"] == 0

        # Total edges should still be 2
        edges_rows = _get_contradicts_edges(vault, note_a["id"], note_b["id"])
        assert len(edges_rows) == 2
