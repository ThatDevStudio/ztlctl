"""ContradictionService — semantic integrity analysis using vector similarity.

Identifies candidate pairs of notes that may contain contradictory claims,
using a three-signal heuristic: cosine similarity, negation density, and
key_points divergence.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from sqlalchemy import select

from ztlctl.infrastructure.database.schema import node_tags, nodes
from ztlctl.services.base import BaseService
from ztlctl.services.result import ServiceResult
from ztlctl.services.telemetry import trace_span, traced

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_COSINE_WEIGHT = 0.4
_NEGATION_WEIGHT = 0.3
_KEYPOINTS_WEIGHT = 0.3
_NEGATION_CAP = 5  # keyword count at which negation score saturates to 1.0

# Order matters: multi-word phrases before single-word tokens so they are
# matched first in the combined body text.
_NEGATION_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\bon the contrary\b", re.IGNORECASE),
    re.compile(r"\bshouldn't\b", re.IGNORECASE),
    re.compile(r"\bwon't\b", re.IGNORECASE),
    re.compile(r"\bhowever\b", re.IGNORECASE),
    re.compile(r"\binstead\b", re.IGNORECASE),
    re.compile(r"\bdisagree\b", re.IGNORECASE),
    re.compile(r"\bbut\b", re.IGNORECASE),
    re.compile(r"\bnot\b", re.IGNORECASE),
]

# Common stop-words to exclude from topic-word extraction for key_points comparison
_STOP_WORDS: frozenset[str] = frozenset(
    {
        "a",
        "an",
        "the",
        "and",
        "or",
        "of",
        "for",
        "in",
        "on",
        "at",
        "to",
        "is",
        "are",
        "was",
        "were",
        "be",
        "been",
        "have",
        "has",
        "had",
        "with",
        "by",
        "from",
        "that",
        "this",
        "it",
        "as",
        "use",
        "using",
        "all",
        "any",
        "can",
        "will",
        "should",
        "would",
        "could",
        "may",
        "must",
        "do",
        "does",
        "did",
        "not",
        "no",
        "so",
        "if",
        "then",
        "when",
        "where",
        "which",
        "who",
        "how",
        "also",
        "its",
        "their",
        "our",
        "your",
        "my",
        "we",
        "they",
        "he",
        "she",
        "i",
        "you",
        "avoid",
        "ensure",
        "always",
        "never",
    }
)


class ContradictionService(BaseService):
    """Identify candidate note pairs with potentially contradictory claims."""

    @traced
    def find_candidates(
        self,
        *,
        similarity_threshold: float = 0.85,
        max_pairs: int = 20,
    ) -> ServiceResult:
        """Find candidate pairs of notes that may contradict each other.

        Candidate discovery uses three filters in sequence:
        1. Only considers non-archived notes.
        2. Requires cosine similarity >= *similarity_threshold* (via VectorService).
        3. Requires at least one shared tag between the note pair.

        Each qualifying pair is scored by :meth:`_score_pair` combining cosine
        similarity (40%), negation density (30%), and key_points divergence (30%).

        Args:
            similarity_threshold: Minimum cosine similarity (0-1) to include a pair.
                                   Default 0.85.
            max_pairs: Maximum number of candidate pairs to return. Default 20.

        Returns:
            ServiceResult with data={"candidates": [...], "count": N}.
            Each candidate dict has keys:
              note_a, note_b, title_a, title_b, score, signals.
        """
        op = "find_candidates"
        warnings: list[str] = []

        # Lazy import to match cross-service import pattern
        from ztlctl.services.vector import VectorService

        vec = VectorService(self._vault)
        if not vec.is_available():
            warnings.append("VectorService unavailable — skipping contradiction analysis")
            return ServiceResult(
                ok=True,
                op=op,
                data={"candidates": [], "count": 0},
                warnings=warnings,
            )

        with self._vault.engine.connect() as conn:
            with trace_span("load_notes"):
                # Fetch all non-archived notes
                note_rows = conn.execute(
                    select(
                        nodes.c.id,
                        nodes.c.title,
                        nodes.c.path,
                    ).where(nodes.c.archived == 0, nodes.c.type.in_(["note", "reference"]))
                ).fetchall()

            if not note_rows:
                return ServiceResult(
                    ok=True,
                    op=op,
                    data={"candidates": [], "count": 0},
                    warnings=warnings,
                )

            # Build lookup dicts
            node_by_id: dict[str, Any] = {str(r.id): r for r in note_rows}
            node_path_by_id: dict[str, str] = {str(r.id): str(r.path) for r in note_rows}
            node_title_by_id: dict[str, str] = {str(r.id): str(r.title) for r in note_rows}

            # Load tags for all notes (tag overlap check)
            with trace_span("tag_overlap"):
                all_ids = list(node_by_id.keys())
                tag_rows = conn.execute(
                    select(node_tags.c.node_id, node_tags.c.tag).where(
                        node_tags.c.node_id.in_(all_ids)
                    )
                ).fetchall()

            tags_by_id: dict[str, set[str]] = {nid: set() for nid in all_ids}
            for tr in tag_rows:
                tags_by_id[str(tr.node_id)].add(str(tr.tag))

        # Candidate discovery: for each note, search for similar notes
        seen_pairs: set[frozenset[str]] = set()
        candidates: list[dict[str, Any]] = []

        with trace_span("scoring"):
            for node_id, row in node_by_id.items():
                body, key_points = self._extract_note_content(node_path_by_id[node_id])
                query_text = f"{node_title_by_id[node_id]} {body}".strip()

                similar = vec.search_similar(query_text, limit=20)

                for hit in similar:
                    peer_id = str(hit["node_id"])
                    distance = float(hit["distance"])

                    # Skip self-match
                    if peer_id == node_id:
                        continue

                    # Skip unknown nodes
                    if peer_id not in node_by_id:
                        continue

                    # Convert cosine distance to similarity
                    cosine_sim = 1.0 - distance
                    if cosine_sim < similarity_threshold:
                        continue

                    # Require shared tags
                    shared = tags_by_id.get(node_id, set()) & tags_by_id.get(peer_id, set())
                    if not shared:
                        continue

                    # Deduplicate pairs (A,B) == (B,A)
                    pair_key = frozenset({node_id, peer_id})
                    if pair_key in seen_pairs:
                        continue
                    seen_pairs.add(pair_key)

                    # Score the pair
                    peer_body, peer_kp = self._extract_note_content(node_path_by_id[peer_id])
                    score, signals = self._score_pair(
                        note_a_content=body,
                        note_b_content=peer_body,
                        cosine_sim=cosine_sim,
                        key_points_a=key_points,
                        key_points_b=peer_kp,
                    )

                    candidates.append(
                        {
                            "note_a": node_id,
                            "note_b": peer_id,
                            "title_a": node_title_by_id[node_id],
                            "title_b": node_title_by_id[peer_id],
                            "score": round(score, 4),
                            "signals": signals,
                        }
                    )

        # Sort by score desc and cap at max_pairs
        candidates.sort(key=lambda c: c["score"], reverse=True)
        candidates = candidates[:max_pairs]

        return ServiceResult(
            ok=True,
            op=op,
            data={"candidates": candidates, "count": len(candidates)},
            warnings=warnings,
        )

    @traced
    def confirm_contradiction(
        self,
        *,
        note_a: str,
        note_b: str,
    ) -> ServiceResult:
        """Confirm a contradiction between two notes by recording bidirectional graph edges.

        Inserts two edges (A->B and B->A) with edge_type='contradicts' and
        source_layer='user'. Duplicate edges are silently skipped.

        Args:
            note_a: ID of the first note in the contradiction pair.
            note_b: ID of the second note in the contradiction pair.

        Returns:
            ServiceResult with data={"note_a": str, "note_b": str, "edges_created": int}.
        """
        from ztlctl.services._helpers import today_iso
        from ztlctl.services.result import ServiceError

        op = "confirm_contradiction"

        # Validate both notes exist
        with self._vault.engine.connect() as conn:
            row_a = conn.execute(select(nodes.c.id).where(nodes.c.id == note_a)).first()
            row_b = conn.execute(select(nodes.c.id).where(nodes.c.id == note_b)).first()

        if row_a is None:
            return ServiceResult(
                ok=False,
                op=op,
                error=ServiceError(
                    code="NOT_FOUND",
                    message=f"Note not found: {note_a}",
                ),
            )
        if row_b is None:
            return ServiceResult(
                ok=False,
                op=op,
                error=ServiceError(
                    code="NOT_FOUND",
                    message=f"Note not found: {note_b}",
                ),
            )

        today = today_iso()
        edges_created = 0

        with self._vault.transaction() as txn:
            inserted_ab = txn.insert_edge(
                note_a,
                note_b,
                "contradicts",
                "user",
                today,
                check_duplicate=True,
                check_target_exists=True,
            )
            if inserted_ab:
                edges_created += 1

            inserted_ba = txn.insert_edge(
                note_b,
                note_a,
                "contradicts",
                "user",
                today,
                check_duplicate=True,
                check_target_exists=True,
            )
            if inserted_ba:
                edges_created += 1

        result = ServiceResult(
            ok=True,
            op=op,
            data={"note_a": note_a, "note_b": note_b, "edges_created": edges_created},
        )
        warnings: list[str] = []
        self._dispatch_post_action_event(
            action_name=op,
            payload=result.data,
            warnings=warnings,
            result=result,
        )
        return result

    # ---------------------------------------------------------------------------
    # Scoring helpers
    # ---------------------------------------------------------------------------

    def _score_pair(
        self,
        note_a_content: str,
        note_b_content: str,
        cosine_sim: float,
        key_points_a: list[str],
        key_points_b: list[str],
    ) -> tuple[float, list[str]]:
        """Compute a contradiction likelihood score for a note pair.

        Weights:
          - Cosine similarity:    40%
          - Negation density:     30%
          - Key_points divergence: 30%

        Args:
            note_a_content: Body text of the first note.
            note_b_content: Body text of the second note.
            cosine_sim: Pre-computed cosine similarity in [0, 1].
            key_points_a: Extracted key_points from the first note's frontmatter.
            key_points_b: Extracted key_points from the second note's frontmatter.

        Returns:
            A ``(total_score, signals)`` tuple where *signals* describes what
            contributed to the score.
        """
        signals: list[str] = []

        # --- Cosine component (40%) ---
        cosine_score = cosine_sim * _COSINE_WEIGHT

        # --- Negation component (30%) ---
        combined_body = f"{note_a_content} {note_b_content}"
        negation_count = sum(len(pattern.findall(combined_body)) for pattern in _NEGATION_PATTERNS)
        negation_normalized = min(negation_count, _NEGATION_CAP) / _NEGATION_CAP
        negation_score = negation_normalized * _NEGATION_WEIGHT
        if negation_score > 0:
            signals.append(f"negation_density:{negation_count}_keywords")

        # --- Key_points divergence component (30%) ---
        kp_score = 0.0
        if key_points_a and key_points_b:
            topic_words_a = self._extract_topic_words(key_points_a)
            topic_words_b = self._extract_topic_words(key_points_b)
            overlap = topic_words_a & topic_words_b
            if overlap:
                # Check if conclusions differ: look for shared topic words that
                # appear in different contexts (substring match fails when the
                # surrounding conclusion text diverges).
                conclusions_differ = not any(
                    kp_a.lower() in kp_b.lower() or kp_b.lower() in kp_a.lower()
                    for kp_a in key_points_a
                    for kp_b in key_points_b
                )
                if conclusions_differ:
                    kp_score = _KEYPOINTS_WEIGHT
                    signals.append(f"key_points_divergence:overlap={sorted(overlap)}")

        if cosine_score > 0:
            signals.append(f"cosine_similarity:{cosine_sim:.3f}")

        total = cosine_score + negation_score + kp_score
        return round(total, 4), signals

    # ---------------------------------------------------------------------------
    # Private helpers
    # ---------------------------------------------------------------------------

    def _extract_note_content(self, node_path: str) -> tuple[str, list[str]]:
        """Read a note file and return (body_text, key_points).

        Falls back to empty strings/lists if the file cannot be read or parsed.
        """
        from ztlctl.domain.content import parse_frontmatter

        try:
            raw = Path(node_path).read_text(encoding="utf-8")
            fm, body = parse_frontmatter(raw)
        except Exception:
            return "", []

        key_points = fm.get("key_points", [])
        if not isinstance(key_points, list):
            key_points = []

        return body, key_points

    @staticmethod
    def _extract_topic_words(key_points: list[str]) -> set[str]:
        """Extract meaningful topic words from a list of key_points strings.

        Splits on whitespace/punctuation and filters out stop-words and
        short tokens (< 4 characters).
        """
        words: set[str] = set()
        for kp in key_points:
            tokens = re.split(r"[\s\W]+", kp.lower())
            for token in tokens:
                if token and len(token) >= 4 and token not in _STOP_WORDS:
                    words.add(token)
        return words
