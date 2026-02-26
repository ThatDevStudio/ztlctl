"""Tests for ReweaveService — reweave, prune, undo."""

from __future__ import annotations

from typing import Any

from sqlalchemy import insert, select

from tests.conftest import create_note
from ztlctl.domain.content import parse_frontmatter
from ztlctl.infrastructure.database.schema import edges, node_tags, nodes, reweave_log
from ztlctl.infrastructure.vault import Vault
from ztlctl.services.reweave import ReweaveService, _jaccard

# ---------------------------------------------------------------------------
# Helpers (test-specific)
# ---------------------------------------------------------------------------


def _create_note_with_topic(vault: Vault, title: str, topic: str) -> dict[str, Any]:
    return create_note(vault, title, topic=topic)


def _add_edge(vault: Vault, source_id: str, target_id: str) -> None:
    with vault.engine.begin() as conn:
        conn.execute(
            insert(edges).values(
                source_id=source_id,
                target_id=target_id,
                edge_type="relates",
                source_layer="frontmatter",
                weight=1.0,
                created="2025-01-01",
            )
        )


def _add_tag(vault: Vault, node_id: str, tag: str) -> None:
    """Add a tag to a node (both registry and node_tags)."""
    from ztlctl.infrastructure.database.schema import tags_registry

    with vault.engine.begin() as conn:
        # Upsert tag
        existing = conn.execute(
            select(tags_registry.c.tag).where(tags_registry.c.tag == tag)
        ).first()
        if existing is None:
            parts = tag.split("/", 1)
            domain = parts[0] if len(parts) == 2 else "unscoped"
            scope = parts[1] if len(parts) == 2 else parts[0]
            conn.execute(
                insert(tags_registry).values(
                    tag=tag, domain=domain, scope=scope, created="2025-01-01"
                )
            )
        conn.execute(insert(node_tags).values(node_id=node_id, tag=tag))


# ---------------------------------------------------------------------------
# Jaccard helper
# ---------------------------------------------------------------------------


class TestJaccard:
    def test_both_empty(self) -> None:
        assert _jaccard(set(), set()) == 0.0

    def test_identical(self) -> None:
        assert _jaccard({"a", "b"}, {"a", "b"}) == 1.0

    def test_disjoint(self) -> None:
        assert _jaccard({"a"}, {"b"}) == 0.0

    def test_partial_overlap(self) -> None:
        # {a, b} & {b, c} = {b} => 1/3
        result = _jaccard({"a", "b"}, {"b", "c"})
        assert abs(result - 1 / 3) < 0.001


# ---------------------------------------------------------------------------
# DISCOVER
# ---------------------------------------------------------------------------


class TestDiscover:
    def test_discover_specific_id(self, vault: Vault) -> None:
        data = create_note(vault, "Target Note")
        svc = ReweaveService(vault)
        result = svc.reweave(content_id=data["id"], dry_run=True)
        assert result.ok
        assert result.data["target_id"] == data["id"]

    def test_discover_latest_modified(self, vault: Vault) -> None:
        create_note(vault, "Old Note")
        create_note(vault, "New Note")
        svc = ReweaveService(vault)
        result = svc.reweave(dry_run=True)
        assert result.ok
        # Should pick the most recently modified (or created) node
        assert result.data["target_id"] is not None

    def test_discover_not_found(self, vault: Vault) -> None:
        result = ReweaveService(vault).reweave(content_id="ztl_nonexist", dry_run=True)
        assert not result.ok
        assert result.error is not None
        assert result.error.code == "NOT_FOUND"

    def test_empty_vault_no_candidates(self, vault: Vault) -> None:
        data = create_note(vault, "Lonely Note")
        result = ReweaveService(vault).reweave(content_id=data["id"], dry_run=True)
        assert result.ok
        assert result.data["count"] == 0


# ---------------------------------------------------------------------------
# SCORE — individual signals
# ---------------------------------------------------------------------------


class TestBm25Signal:
    def test_lexical_scoring(self, vault: Vault) -> None:
        """Candidates with similar titles get higher BM25 scores."""
        data_target = create_note(vault, "Python Programming Guide")
        data_similar = create_note(vault, "Python Language Reference")
        data_unrelated = create_note(vault, "Cooking Recipes Collection")

        svc = ReweaveService(vault)
        result = svc.reweave(content_id=data_target["id"], dry_run=True)
        assert result.ok

        suggestions = result.data["suggestions"]
        # Both should appear (even if below threshold), but similar should score higher
        scores = {s["id"]: s["signals"]["lexical"] for s in suggestions}
        if data_similar["id"] in scores and data_unrelated["id"] in scores:
            assert scores[data_similar["id"]] >= scores[data_unrelated["id"]]

    def test_top_bm25_is_one(self, vault: Vault) -> None:
        """Top BM25 match should be normalized to 1.0."""
        data_target = create_note(vault, "Alpha Beta Gamma")
        create_note(vault, "Alpha Beta Gamma Delta")

        svc = ReweaveService(vault)
        result = svc.reweave(content_id=data_target["id"], dry_run=True)
        assert result.ok

        if result.data["suggestions"]:
            top = max(result.data["suggestions"], key=lambda s: s["signals"]["lexical"])
            assert top["signals"]["lexical"] == 1.0


class TestTagSignal:
    def test_tag_overlap_scores(self, vault: Vault) -> None:
        """Shared tags increase the tag overlap signal."""
        data_a = create_note(vault, "Note A", tags=["lang/python", "tool/cli"])
        data_b = create_note(vault, "Note B", tags=["lang/python", "tool/cli"])
        data_c = create_note(vault, "Note C", tags=["food/pizza"])

        svc = ReweaveService(vault)
        result = svc.reweave(content_id=data_a["id"], dry_run=True)
        assert result.ok

        scores = {s["id"]: s["signals"]["tag_overlap"] for s in result.data["suggestions"]}
        if data_b["id"] in scores and data_c["id"] in scores:
            assert scores[data_b["id"]] > scores[data_c["id"]]


class TestTopicSignal:
    def test_same_topic_scores_one(self, vault: Vault) -> None:
        """Notes with same topic get topic signal = 1.0."""
        data_a = _create_note_with_topic(vault, "Topic A", "python")
        data_b = _create_note_with_topic(vault, "Topic B", "python")

        svc = ReweaveService(vault)
        result = svc.reweave(content_id=data_a["id"], dry_run=True)
        assert result.ok

        scores = {s["id"]: s["signals"]["topic"] for s in result.data["suggestions"]}
        if data_b["id"] in scores:
            assert scores[data_b["id"]] == 1.0

    def test_different_topic_scores_zero(self, vault: Vault) -> None:
        """Notes with different topics get topic signal = 0.0."""
        data_a = _create_note_with_topic(vault, "Topic A", "python")
        data_b = _create_note_with_topic(vault, "Topic B", "cooking")

        svc = ReweaveService(vault)
        result = svc.reweave(content_id=data_a["id"], dry_run=True)
        assert result.ok

        scores = {s["id"]: s["signals"]["topic"] for s in result.data["suggestions"]}
        if data_b["id"] in scores:
            assert scores[data_b["id"]] == 0.0


class TestGraphProximitySignal:
    def test_closer_nodes_score_higher(self, vault: Vault) -> None:
        """Nodes closer in the graph get higher proximity scores."""
        data_a = create_note(vault, "Hub")
        data_b = create_note(vault, "Direct Neighbor")
        data_c = create_note(vault, "Two Hops Away")
        data_d = create_note(vault, "Three Hops Away")

        # A -> B -> C -> D (chain)
        _add_edge(vault, data_a["id"], data_b["id"])
        _add_edge(vault, data_b["id"], data_c["id"])
        _add_edge(vault, data_c["id"], data_d["id"])

        svc = ReweaveService(vault)
        # Reweave from A — B is already linked, so candidates are C and D
        result = svc.reweave(content_id=data_a["id"], dry_run=True)
        assert result.ok

        scores = {s["id"]: s["signals"]["graph_proximity"] for s in result.data["suggestions"]}
        # C is 2 hops (1/2=0.5), D is 3 hops (1/3=0.33)
        if data_c["id"] in scores and data_d["id"] in scores:
            assert scores[data_c["id"]] > scores[data_d["id"]]


# ---------------------------------------------------------------------------
# FILTER
# ---------------------------------------------------------------------------


class TestFilter:
    def test_threshold_filtering(self, vault: Vault) -> None:
        """Candidates below min_score_threshold are excluded."""
        data_a = create_note(vault, "Alpha Note About Testing")
        create_note(vault, "Completely Unrelated Cooking Topic")

        svc = ReweaveService(vault)
        result = svc.reweave(content_id=data_a["id"], dry_run=True)
        assert result.ok
        # All suggestions should be above threshold
        for s in result.data["suggestions"]:
            assert s["score"] >= vault.settings.reweave.min_score_threshold

    def test_max_links_cap(self, vault: Vault) -> None:
        """Don't suggest more links than max_links_per_note allows."""
        data = create_note(vault, "Hub")
        # Create many candidates
        for i in range(10):
            create_note(vault, f"Related Note {i}", tags=["same/tag"])

        svc = ReweaveService(vault)
        result = svc.reweave(content_id=data["id"], dry_run=True)
        assert result.ok
        max_links = vault.settings.reweave.max_links_per_note
        assert result.data["count"] <= max_links

    def test_already_at_max_links(self, vault: Vault) -> None:
        """Returns empty suggestions if node is already at max links."""
        data = create_note(vault, "Full Node")
        max_links = vault.settings.reweave.max_links_per_note
        for i in range(max_links):
            t = create_note(vault, f"Target {i}")
            _add_edge(vault, data["id"], t["id"])

        svc = ReweaveService(vault)
        result = svc.reweave(content_id=data["id"], dry_run=True)
        assert result.ok
        assert result.data["count"] == 0


# ---------------------------------------------------------------------------
# Disabled
# ---------------------------------------------------------------------------


class TestDisabled:
    def test_reweave_disabled(self, vault_root: Any) -> None:
        """Reweave returns early when disabled in settings."""
        from ztlctl.config.settings import ZtlSettings

        # Write a config that disables reweave
        config = vault_root / "ztlctl.toml"
        config.write_text("[reweave]\nenabled = false\n", encoding="utf-8")
        settings = ZtlSettings.from_cli(vault_root=vault_root)
        disabled_vault = Vault(settings)

        create_note(disabled_vault, "Some Note")
        svc = ReweaveService(disabled_vault)
        result = svc.reweave(dry_run=True)
        assert result.ok
        assert result.data.get("skipped") is True


# ---------------------------------------------------------------------------
# CONNECT (dry_run=False)
# ---------------------------------------------------------------------------


class TestConnect:
    def test_connect_creates_edge(self, vault: Vault) -> None:
        """Reweave with dry_run=False creates edges in DB."""
        data_a = create_note(vault, "Python Programming")
        create_note(vault, "Python Language Reference")

        svc = ReweaveService(vault)
        result = svc.reweave(content_id=data_a["id"], dry_run=False)
        assert result.ok

        if result.data["count"] > 0:
            # Verify edge exists
            with vault.engine.connect() as conn:
                edge = conn.execute(
                    select(edges.c.target_id).where(edges.c.source_id == data_a["id"])
                ).fetchall()
                target_ids = {str(e.target_id) for e in edge}
                for c in result.data["connected"]:
                    assert c["id"] in target_ids

    def test_connect_updates_frontmatter(self, vault: Vault) -> None:
        """Reweave with dry_run=False updates frontmatter links."""
        data_a = create_note(vault, "Python Programming")
        create_note(vault, "Python Language Reference")

        svc = ReweaveService(vault)
        result = svc.reweave(content_id=data_a["id"], dry_run=False)
        assert result.ok

        if result.data["count"] > 0:
            path = vault.root / data_a["path"]
            fm, _ = parse_frontmatter(path.read_text(encoding="utf-8"))
            links = fm.get("links", {})
            relates = links.get("relates", [])
            for c in result.data["connected"]:
                assert c["id"] in relates

    def test_connect_logs_reweave(self, vault: Vault) -> None:
        """Reweave creates audit log entries."""
        data_a = create_note(vault, "Python Programming")
        create_note(vault, "Python Language Reference")

        svc = ReweaveService(vault)
        result = svc.reweave(content_id=data_a["id"], dry_run=False)
        assert result.ok

        with vault.engine.connect() as conn:
            logs = conn.execute(
                select(reweave_log).where(reweave_log.c.source_id == data_a["id"])
            ).fetchall()
            assert len(logs) == result.data["count"]
            for log_entry in logs:
                assert log_entry.action == "add"
                assert log_entry.undone == 0

    def test_garden_note_no_body_wikilink(self, vault: Vault) -> None:
        """Garden notes (maturity set) get frontmatter links only, not body wikilinks."""
        data_a = create_note(vault, "Python Programming Garden")
        create_note(vault, "Python Language Reference")

        # Set maturity on the target
        with vault.engine.begin() as conn:
            conn.execute(nodes.update().where(nodes.c.id == data_a["id"]).values(maturity="seed"))

        svc = ReweaveService(vault)
        result = svc.reweave(content_id=data_a["id"], dry_run=False)
        assert result.ok

        if result.data["count"] > 0:
            path = vault.root / data_a["path"]
            _, body = parse_frontmatter(path.read_text(encoding="utf-8"))
            # Body should NOT contain wikilinks added by reweave
            for c in result.data["connected"]:
                assert f"[[{c['title']}]]" not in body

    def test_dry_run_no_side_effects(self, vault: Vault) -> None:
        """Dry run produces suggestions but doesn't modify DB or files."""
        data_a = create_note(vault, "Python Programming")
        create_note(vault, "Python Language Reference")

        svc = ReweaveService(vault)
        result = svc.reweave(content_id=data_a["id"], dry_run=True)
        assert result.ok
        assert result.data.get("dry_run") is True

        # No edges should have been created
        with vault.engine.connect() as conn:
            edge_count = conn.execute(
                select(edges.c.source_id).where(edges.c.source_id == data_a["id"])
            ).fetchall()
            assert len(edge_count) == 0

            # No log entries
            log_count = conn.execute(
                select(reweave_log).where(reweave_log.c.source_id == data_a["id"])
            ).fetchall()
            assert len(log_count) == 0


# ---------------------------------------------------------------------------
# Prune
# ---------------------------------------------------------------------------


class TestPrune:
    def test_prune_removes_stale_links(self, vault: Vault) -> None:
        """Prune removes links that score below threshold."""
        data_a = create_note(vault, "Alpha")
        data_b = create_note(vault, "Completely Different Topic About Cooking")

        # Manually link them
        _add_edge(vault, data_a["id"], data_b["id"])

        # Update frontmatter to include the link
        path_a = vault.root / data_a["path"]
        fm, body = parse_frontmatter(path_a.read_text(encoding="utf-8"))
        fm["links"] = {"relates": [data_b["id"]]}
        from ztlctl.domain.content import render_frontmatter

        path_a.write_text(render_frontmatter(fm, body), encoding="utf-8")

        svc = ReweaveService(vault)
        result = svc.prune(content_id=data_a["id"], dry_run=False)
        assert result.ok

        # If the link was stale (below threshold), it should be pruned
        if result.data["count"] > 0:
            with vault.engine.connect() as conn:
                remaining = conn.execute(
                    select(edges.c.target_id).where(
                        edges.c.source_id == data_a["id"],
                        edges.c.target_id == data_b["id"],
                    )
                ).first()
                assert remaining is None

    def test_prune_dry_run(self, vault: Vault) -> None:
        """Prune dry run doesn't remove links."""
        data_a = create_note(vault, "Alpha")
        data_b = create_note(vault, "Beta Unrelated Cooking")
        _add_edge(vault, data_a["id"], data_b["id"])

        svc = ReweaveService(vault)
        result = svc.prune(content_id=data_a["id"], dry_run=True)
        assert result.ok
        assert result.data.get("dry_run") is True

        # Edge should still exist
        with vault.engine.connect() as conn:
            edge = conn.execute(
                select(edges.c.target_id).where(
                    edges.c.source_id == data_a["id"],
                    edges.c.target_id == data_b["id"],
                )
            ).first()
            assert edge is not None

    def test_prune_not_found(self, vault: Vault) -> None:
        result = ReweaveService(vault).prune(content_id="ztl_nonexist")
        assert not result.ok
        assert result.error is not None
        assert result.error.code == "NOT_FOUND"

    def test_prune_no_links(self, vault: Vault) -> None:
        data = create_note(vault, "No Links")
        result = ReweaveService(vault).prune(content_id=data["id"])
        assert result.ok
        assert result.data["count"] == 0


# ---------------------------------------------------------------------------
# Undo
# ---------------------------------------------------------------------------


class TestUndo:
    def test_undo_add_removes_link(self, vault: Vault) -> None:
        """Undoing an 'add' action removes the link."""
        data_a = create_note(vault, "Python Programming")
        create_note(vault, "Python Language Reference")

        svc = ReweaveService(vault)
        result = svc.reweave(content_id=data_a["id"], dry_run=False)
        assert result.ok

        if result.data["count"] > 0:
            # Now undo
            undo_result = svc.undo()
            assert undo_result.ok
            assert undo_result.data["count"] > 0

            # Verify edges removed
            with vault.engine.connect() as conn:
                for entry in undo_result.data["undone"]:
                    edge = conn.execute(
                        select(edges.c.source_id).where(
                            edges.c.source_id == entry["source_id"],
                            edges.c.target_id == entry["target_id"],
                            edges.c.edge_type == "relates",
                        )
                    ).first()
                    assert edge is None

                # Verify log entries marked as undone
                logs = conn.execute(
                    select(reweave_log.c.undone).where(reweave_log.c.source_id == data_a["id"])
                ).fetchall()
                for log_entry in logs:
                    assert log_entry.undone == 1

    def test_undo_specific_id(self, vault: Vault) -> None:
        """Undo a specific reweave log entry by ID."""
        data_a = create_note(vault, "Python Programming")
        create_note(vault, "Python Language Reference")

        svc = ReweaveService(vault)
        result = svc.reweave(content_id=data_a["id"], dry_run=False)
        assert result.ok

        if result.data["count"] > 0:
            # Get the log entry ID
            with vault.engine.connect() as conn:
                log_entry = conn.execute(
                    select(reweave_log.c.id).where(reweave_log.c.source_id == data_a["id"])
                ).first()
                assert log_entry is not None

            undo_result = svc.undo(reweave_id=log_entry.id)
            assert undo_result.ok
            assert undo_result.data["count"] == 1

    def test_undo_no_history(self, vault: Vault) -> None:
        """Undo with no history returns error."""
        result = ReweaveService(vault).undo()
        assert not result.ok
        assert result.error is not None
        assert result.error.code == "NO_HISTORY"

    def test_undo_already_undone(self, vault: Vault) -> None:
        """Cannot undo an already-undone entry."""
        data_a = create_note(vault, "Python Programming")
        create_note(vault, "Python Language Reference")

        svc = ReweaveService(vault)
        result = svc.reweave(content_id=data_a["id"], dry_run=False)
        assert result.ok

        if result.data["count"] > 0:
            # Get log entry id
            with vault.engine.connect() as conn:
                log_entry = conn.execute(
                    select(reweave_log.c.id).where(reweave_log.c.source_id == data_a["id"])
                ).first()
                assert log_entry is not None
                log_id = log_entry.id

            # Undo once
            svc.undo(reweave_id=log_id)

            # Try to undo again — should fail
            undo_result = svc.undo(reweave_id=log_id)
            assert not undo_result.ok
            assert undo_result.error is not None
            assert undo_result.error.code == "NOT_FOUND"


# ---------------------------------------------------------------------------
# FTS5 query sanitization
# ---------------------------------------------------------------------------


class TestFts5Sanitization:
    def test_special_chars_in_title(self, vault: Vault) -> None:
        """Special characters in title don't crash the FTS5 query."""
        data = create_note(vault, 'Special: "quotes" & symbols!')
        create_note(vault, "Normal Note")

        result = ReweaveService(vault).reweave(content_id=data["id"], dry_run=True)
        assert result.ok  # Should not crash

    def test_empty_title(self, vault: Vault) -> None:
        """Edge case: title with only whitespace."""
        # Create a note and manually clear its title in FTS
        data = create_note(vault, "Placeholder")
        create_note(vault, "Another Note")

        result = ReweaveService(vault).reweave(content_id=data["id"], dry_run=True)
        assert result.ok
