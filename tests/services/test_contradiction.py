"""Tests for ContradictionService — candidate pair discovery and heuristic scoring."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import patch

from ztlctl.infrastructure.vault import Vault

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_note(vault_root: Path, subdir: str, filename: str, content: str) -> Path:
    """Write a note file to a vault subdirectory."""
    path = vault_root / subdir / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def _create_note_with_tags(
    vault: Vault,
    title: str,
    tags: list[str],
    body: str = "",
    key_points: list[str] | None = None,
    subtype: str | None = None,
) -> dict[str, Any]:
    """Create a note via CreateService and return its data."""
    from ztlctl.services.create import CreateService

    kwargs: dict[str, Any] = {"tags": tags}
    if subtype:
        kwargs["subtype"] = subtype
    result = CreateService(vault).create_note(title, **kwargs)
    assert result.ok, result.error

    # If body or key_points provided, overwrite the file with custom content
    if body or key_points:
        node_id = result.data["id"]
        from sqlalchemy import select

        from ztlctl.infrastructure.database.schema import nodes

        with vault.engine.connect() as conn:
            row = conn.execute(select(nodes.c.path).where(nodes.c.id == node_id)).first()
        assert row is not None
        note_path = Path(row.path)

        fm = note_path.read_text(encoding="utf-8")
        # Replace file with frontmatter that includes key_points
        from ztlctl.domain.content import parse_frontmatter, render_frontmatter

        existing_fm, _ = parse_frontmatter(fm)
        if key_points:
            existing_fm["key_points"] = key_points
        note_path.write_text(render_frontmatter(existing_fm, body or ""), encoding="utf-8")

    return result.data


# ---------------------------------------------------------------------------
# Test: find_candidates returns empty when vector search unavailable
# ---------------------------------------------------------------------------


class TestFindCandidatesVectorUnavailable:
    def test_returns_empty_when_vector_unavailable(self, vault: Vault) -> None:
        """find_candidates returns empty list when VectorService is unavailable."""
        from ztlctl.services.contradiction import ContradictionService

        with patch(
            "ztlctl.services.vector.VectorService.is_available",
            return_value=False,
        ):
            result = ContradictionService(vault).find_candidates()

        assert result.ok
        assert result.op == "find_candidates"
        assert result.data["candidates"] == []
        assert result.data["count"] == 0
        assert len(result.warnings) > 0


# ---------------------------------------------------------------------------
# Test: find_candidates returns empty when no notes share tags
# ---------------------------------------------------------------------------


class TestFindCandidatesNoSharedTags:
    def test_no_shared_tags_returns_empty(self, vault: Vault) -> None:
        """find_candidates returns empty when notes don't share tags."""
        from ztlctl.services.contradiction import ContradictionService

        _create_note_with_tags(vault, "Note A", ["alpha"])
        _create_note_with_tags(vault, "Note B", ["beta"])

        mock_similar = [{"node_id": "fake-id", "distance": 0.1}]

        with (
            patch(
                "ztlctl.services.vector.VectorService.is_available",
                return_value=True,
            ),
            patch(
                "ztlctl.services.vector.VectorService.search_similar",
                return_value=mock_similar,
            ),
        ):
            result = ContradictionService(vault).find_candidates()

        assert result.ok
        assert result.data["candidates"] == []
        assert result.data["count"] == 0


# ---------------------------------------------------------------------------
# Test: find_candidates returns scored pairs for notes with shared tags
# and high cosine similarity
# ---------------------------------------------------------------------------


class TestFindCandidatesWithSharedTags:
    def test_returns_scored_pairs_for_shared_tags_and_high_similarity(self, vault: Vault) -> None:
        """find_candidates returns scored pairs when notes share tags and similarity >= 0.85."""
        from ztlctl.services.contradiction import ContradictionService

        note_a = _create_note_with_tags(vault, "Note A", ["architecture"])
        note_b = _create_note_with_tags(vault, "Note B", ["architecture"])
        note_a_id = note_a["id"]
        note_b_id = note_b["id"]

        # similarity = 1 - distance; 0.1 distance => 0.9 similarity (above 0.85 threshold)
        def mock_search(query_text: str, *, limit: int = 20) -> list[dict[str, Any]]:
            # Return the other note as highly similar for each call
            if note_a_id in query_text or "Note A" in query_text:
                return [{"node_id": note_b_id, "distance": 0.1}]
            return [{"node_id": note_a_id, "distance": 0.1}]

        with (
            patch(
                "ztlctl.services.vector.VectorService.is_available",
                return_value=True,
            ),
            patch(
                "ztlctl.services.vector.VectorService.search_similar",
                side_effect=mock_search,
            ),
        ):
            result = ContradictionService(vault).find_candidates()

        assert result.ok
        assert result.data["count"] >= 1
        candidates = result.data["candidates"]
        assert len(candidates) >= 1

        # Check candidate structure
        c = candidates[0]
        assert "note_a" in c
        assert "note_b" in c
        assert "title_a" in c
        assert "title_b" in c
        assert "score" in c
        assert "signals" in c
        assert isinstance(c["score"], float)
        assert c["score"] > 0


# ---------------------------------------------------------------------------
# Test: _score_pair weighted scoring
# ---------------------------------------------------------------------------


class TestScorePair:
    def test_score_uses_cosine_weight_40_percent(self, vault: Vault) -> None:
        """_score_pair applies cosine_weight=0.4 correctly."""
        from ztlctl.services.contradiction import ContradictionService

        svc = ContradictionService(vault)
        # Pure cosine contribution: 1.0 * 0.4 = 0.4
        # No negation keywords, no key_points => negation=0, kp=0
        score, _signals = svc._score_pair(
            note_a_content="The system should use microservices.",
            note_b_content="The system should use monolith.",
            cosine_sim=1.0,
            key_points_a=[],
            key_points_b=[],
        )
        # cosine contribution = 1.0 * 0.4 = 0.4
        assert abs(score - 0.4) < 0.01

    def test_score_negation_density_detected(self, vault: Vault) -> None:
        """_score_pair detects negation keywords in body text."""
        from ztlctl.services.contradiction import ContradictionService

        svc = ContradictionService(vault)
        # 5 negation keywords => negation_score = 1.0 * 0.3 = 0.3
        body_with_negations = "however but instead on the contrary not"
        score, _signals = svc._score_pair(
            note_a_content=body_with_negations,
            note_b_content="plain text",
            cosine_sim=0.0,
            key_points_a=[],
            key_points_b=[],
        )
        # negation_score = min(5,5)/5 * 0.3 = 0.3
        assert abs(score - 0.3) < 0.01

    def test_score_negation_all_keywords_detected(self, vault: Vault) -> None:
        """_score_pair detects all negation keywords including compound ones."""
        from ztlctl.services.contradiction import ContradictionService

        svc = ContradictionService(vault)
        # All 8 keywords present => capped at 1.0 * 0.3
        body = "however but instead on the contrary disagree not shouldn't won't"
        score, _signals = svc._score_pair(
            note_a_content=body,
            note_b_content="",
            cosine_sim=0.0,
            key_points_a=[],
            key_points_b=[],
        )
        # 8 keywords > 5, capped: negation_score = 1.0 * 0.3 = 0.3
        assert abs(score - 0.3) < 0.01

    def test_score_keypoints_divergence_detected(self, vault: Vault) -> None:
        """_score_pair detects divergent key_points with overlapping topics."""
        from ztlctl.services.contradiction import ContradictionService

        svc = ContradictionService(vault)
        # Overlapping topic "caching" but different conclusions
        kp_a = ["use Redis for caching all requests"]
        kp_b = ["avoid caching to ensure consistency"]
        score, _signals = svc._score_pair(
            note_a_content="",
            note_b_content="",
            cosine_sim=0.0,
            key_points_a=kp_a,
            key_points_b=kp_b,
        )
        # kp divergence detected: 0.3
        assert abs(score - 0.3) < 0.01

    def test_score_no_keypoints_overlap_no_contribution(self, vault: Vault) -> None:
        """_score_pair gives 0 key_points contribution when no topic overlap."""
        from ztlctl.services.contradiction import ContradictionService

        svc = ContradictionService(vault)
        kp_a = ["databases are important for persistence"]
        kp_b = ["networking protocols matter for communication"]
        score, _signals = svc._score_pair(
            note_a_content="",
            note_b_content="",
            cosine_sim=0.0,
            key_points_a=kp_a,
            key_points_b=kp_b,
        )
        # No shared topic words => kp contribution = 0
        assert abs(score - 0.0) < 0.01

    def test_score_combined_all_signals(self, vault: Vault) -> None:
        """_score_pair returns correct combined score for all three signals."""
        from ztlctl.services.contradiction import ContradictionService

        svc = ContradictionService(vault)
        # cosine=1.0 => 0.4
        # 5 negations => 0.3
        # divergent kp => 0.3
        # total = 1.0
        body = "however but instead not on the contrary"
        kp_a = ["use caching always"]
        kp_b = ["avoid caching in production"]
        score, signals = svc._score_pair(
            note_a_content=body,
            note_b_content="",
            cosine_sim=1.0,
            key_points_a=kp_a,
            key_points_b=kp_b,
        )
        assert abs(score - 1.0) < 0.01
        assert len(signals) >= 1

    def test_signals_list_describes_contributions(self, vault: Vault) -> None:
        """_score_pair returns a non-empty signals list when there are contributions."""
        from ztlctl.services.contradiction import ContradictionService

        svc = ContradictionService(vault)
        body = "however but not"
        _, signals = svc._score_pair(
            note_a_content=body,
            note_b_content="",
            cosine_sim=0.9,
            key_points_a=[],
            key_points_b=[],
        )
        assert isinstance(signals, list)
        assert len(signals) >= 1


# ---------------------------------------------------------------------------
# Test: results capped at 20 pairs sorted by score desc
# ---------------------------------------------------------------------------


class TestFindCandidatesCap:
    def test_candidates_capped_at_max_pairs(self, vault: Vault) -> None:
        """find_candidates returns at most max_pairs candidates."""
        from ztlctl.services.contradiction import ContradictionService

        # Create many notes all sharing the same tag
        shared_tag = ["shared"]
        note_ids = []
        for i in range(6):
            note = _create_note_with_tags(vault, f"Note {i}", shared_tag)
            note_ids.append(note["id"])

        def mock_search(query_text: str, *, limit: int = 20) -> list[dict[str, Any]]:
            # Every note is similar to every other note
            return [{"node_id": nid, "distance": 0.1} for nid in note_ids]

        with (
            patch(
                "ztlctl.services.vector.VectorService.is_available",
                return_value=True,
            ),
            patch(
                "ztlctl.services.vector.VectorService.search_similar",
                side_effect=mock_search,
            ),
        ):
            result = ContradictionService(vault).find_candidates(max_pairs=2)

        assert result.ok
        assert len(result.data["candidates"]) <= 2

    def test_candidates_sorted_by_score_desc(self, vault: Vault) -> None:
        """find_candidates returns candidates sorted by score descending."""
        from ztlctl.services.contradiction import ContradictionService

        shared_tag = ["shared"]
        note_a = _create_note_with_tags(vault, "Note A", shared_tag)
        note_b = _create_note_with_tags(vault, "Note B", shared_tag)
        _ = note_a["id"]
        note_b_id = note_b["id"]

        call_count = [0]

        def mock_search(query_text: str, *, limit: int = 20) -> list[dict[str, Any]]:
            call_count[0] += 1
            return [{"node_id": note_b_id, "distance": 0.1}]

        with (
            patch(
                "ztlctl.services.vector.VectorService.is_available",
                return_value=True,
            ),
            patch(
                "ztlctl.services.vector.VectorService.search_similar",
                side_effect=mock_search,
            ),
        ):
            result = ContradictionService(vault).find_candidates()

        assert result.ok
        candidates = result.data["candidates"]
        if len(candidates) >= 2:
            for i in range(len(candidates) - 1):
                assert candidates[i]["score"] >= candidates[i + 1]["score"]


# ---------------------------------------------------------------------------
# Test: graceful empty when vault has no decision notes
# ---------------------------------------------------------------------------


class TestFindCandidatesEmptyVault:
    def test_empty_vault_returns_empty(self, vault: Vault) -> None:
        """find_candidates returns empty when vault has no notes."""
        from ztlctl.services.contradiction import ContradictionService

        with patch(
            "ztlctl.services.vector.VectorService.is_available",
            return_value=True,
        ):
            result = ContradictionService(vault).find_candidates()

        assert result.ok
        assert result.data["candidates"] == []
        assert result.data["count"] == 0
