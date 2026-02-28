"""Integration tests for the semantic extra (sqlite-vec + embeddings)."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest
from sqlalchemy import text

from tests.conftest import create_note
from ztlctl.config.settings import ZtlSettings
from ztlctl.infrastructure.vault import Vault
from ztlctl.services.query import QueryService
from ztlctl.services.update import UpdateService
from ztlctl.services.vector import VectorService

if (
    importlib.util.find_spec("sqlite_vec") is None
    or importlib.util.find_spec("sentence_transformers") is None
):
    pytest.skip("semantic extra not installed", allow_module_level=True)


class _FakeEncoder:
    """Deterministic 4D encoder for extras-enabled semantic tests."""

    def encode(self, texts: str | list[str]) -> list[float] | list[list[float]]:
        if isinstance(texts, list):
            return [self._encode_one(text) for text in texts]
        return self._encode_one(texts)

    @staticmethod
    def _encode_one(text: str) -> list[float]:
        lowered = text.lower()
        return [
            1.0 if "python" in lowered else 0.0,
            1.0 if "neural" in lowered else 0.0,
            1.0 if "graph" in lowered else 0.0,
            1.0 if "vector" in lowered or "embedding" in lowered else 0.0,
        ]


@pytest.fixture
def semantic_vault(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Vault:
    config_path = tmp_path / "ztlctl.toml"
    config_path.write_text(
        (
            "[vault]\n"
            'name = "semantic-test"\n'
            'client = "vanilla"\n'
            "\n"
            "[agent]\n"
            'tone = "minimal"\n'
            "\n"
            "[search]\n"
            "semantic_enabled = true\n"
            "embedding_dim = 4\n"
            "semantic_weight = 0.5\n"
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr("ztlctl.infrastructure.embeddings._st_available", True)
    monkeypatch.setattr(
        "ztlctl.infrastructure.embeddings._load_model",
        lambda _name: _FakeEncoder(),
    )
    settings = ZtlSettings.from_cli(vault_root=tmp_path, no_reweave=True)
    vault = Vault(settings)
    try:
        yield vault
    finally:
        vault.close()


class TestSemanticExtra:
    def test_vector_service_real_sqlite_vec_round_trip(self, semantic_vault: Vault) -> None:
        svc = VectorService(semantic_vault)

        assert svc.is_available() is True
        svc.ensure_table()
        svc.index_node("node-python", "Python vector guide")
        svc.index_node("node-graph", "Graph theory notes")

        results = svc.search_similar("Python", limit=2)

        assert len(results) == 2
        assert results[0]["node_id"] == "node-python"

    def test_create_note_auto_indexes_vector_when_semantic_enabled(
        self, semantic_vault: Vault
    ) -> None:
        data = create_note(semantic_vault, "Python Seed")

        with semantic_vault.engine.connect() as conn:
            count = conn.execute(
                text("SELECT COUNT(*) FROM vec_items WHERE node_id = :node_id"),
                {"node_id": data["id"]},
            ).scalar_one()

        assert count == 1

    def test_update_note_reindexes_vector_when_title_or_body_changes(
        self, semantic_vault: Vault
    ) -> None:
        data = create_note(semantic_vault, "Plain Note")

        result = UpdateService(semantic_vault).update(
            data["id"],
            changes={"title": "Neural Note", "body": "Neural vector embeddings"},
        )

        assert result.ok
        similar = VectorService(semantic_vault).search_similar("neural", limit=1)
        assert similar[0]["node_id"] == data["id"]

    def test_query_service_semantic_search_uses_real_vector_backend(
        self, semantic_vault: Vault
    ) -> None:
        python_note = create_note(semantic_vault, "Python Patterns")
        create_note(semantic_vault, "Graph Systems")

        result = QueryService(semantic_vault).search("python", rank_by="semantic")

        assert result.ok
        assert not any("unavailable" in warning.lower() for warning in result.warnings)
        assert result.data["items"][0]["id"] == python_note["id"]

    def test_query_service_hybrid_search_uses_real_vector_backend(
        self, semantic_vault: Vault
    ) -> None:
        create_note(semantic_vault, "Python Patterns")
        graph_note = create_note(semantic_vault, "Graph Primer")

        result = QueryService(semantic_vault).search("graph", rank_by="hybrid")

        assert result.ok
        assert not any("unavailable" in warning.lower() for warning in result.warnings)
        assert result.data["items"][0]["id"] == graph_note["id"]

    def test_vector_reindex_all_succeeds_with_semantic_extra(self, semantic_vault: Vault) -> None:
        create_note(semantic_vault, "Python Note")
        create_note(semantic_vault, "Neural Note")

        result = VectorService(semantic_vault).reindex_all()

        assert result.ok
        assert result.data["indexed_count"] >= 2
