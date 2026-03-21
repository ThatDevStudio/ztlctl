"""Tests for EmbeddingProvider -- local sentence-transformers wrapper."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from ztlctl.infrastructure.embeddings import DEFAULT_EMBEDDING_DIM, EmbeddingProvider


class TestEmbeddingProvider:
    def test_default_embedding_dim_constant(self) -> None:
        """DEFAULT_EMBEDDING_DIM is the canonical 384 constant."""
        assert DEFAULT_EMBEDDING_DIM == 384

    def test_embed_returns_correct_dimension(self) -> None:
        """embed() returns a list of floats with correct dimension."""
        with patch("ztlctl.infrastructure.embeddings._load_model") as mock_load:
            mock_model = MagicMock()
            mock_model.encode.return_value = [0.1] * DEFAULT_EMBEDDING_DIM
            mock_load.return_value = mock_model

            provider = EmbeddingProvider(model_name="test-model", dim=DEFAULT_EMBEDDING_DIM)
            result = provider.embed("Hello world")
            assert isinstance(result, list)
            assert len(result) == DEFAULT_EMBEDDING_DIM
            assert all(isinstance(x, float) for x in result)

    def test_embed_batch_returns_list_of_vectors(self) -> None:
        """embed_batch() returns a list of vectors."""
        with patch("ztlctl.infrastructure.embeddings._load_model") as mock_load:
            mock_model = MagicMock()
            # Simulate numpy-like return with tolist()
            mock_row1 = MagicMock()
            mock_row1.tolist.return_value = [0.1] * DEFAULT_EMBEDDING_DIM
            mock_row1.__iter__ = lambda self: iter([0.1] * DEFAULT_EMBEDDING_DIM)
            mock_row2 = MagicMock()
            mock_row2.tolist.return_value = [0.2] * DEFAULT_EMBEDDING_DIM
            mock_row2.__iter__ = lambda self: iter([0.2] * DEFAULT_EMBEDDING_DIM)
            mock_model.encode.return_value = [mock_row1, mock_row2]
            mock_load.return_value = mock_model

            provider = EmbeddingProvider(model_name="test-model", dim=DEFAULT_EMBEDDING_DIM)
            result = provider.embed_batch(["Hello", "World"])
            assert len(result) == 2
            assert all(len(v) == DEFAULT_EMBEDDING_DIM for v in result)

    def test_lazy_model_loading(self) -> None:
        """Model is not loaded until first embed() call."""
        with patch("ztlctl.infrastructure.embeddings._load_model") as mock_load:
            provider = EmbeddingProvider(model_name="test-model", dim=DEFAULT_EMBEDDING_DIM)
            mock_load.assert_not_called()

            mock_model = MagicMock()
            mock_model.encode.return_value = [0.1] * DEFAULT_EMBEDDING_DIM
            mock_load.return_value = mock_model

            provider.embed("trigger load")
            mock_load.assert_called_once_with("test-model")

    def test_model_loaded_once(self) -> None:
        """Model is loaded only once across multiple calls."""
        with patch("ztlctl.infrastructure.embeddings._load_model") as mock_load:
            mock_model = MagicMock()
            mock_model.encode.return_value = [0.1] * DEFAULT_EMBEDDING_DIM
            mock_load.return_value = mock_model

            provider = EmbeddingProvider(model_name="test-model", dim=DEFAULT_EMBEDDING_DIM)
            provider.embed("first")
            provider.embed("second")
            mock_load.assert_called_once()

    def test_is_available_returns_bool(self) -> None:
        """is_available() returns a boolean."""
        result = EmbeddingProvider.is_available()
        assert isinstance(result, bool)
        # sentence-transformers is NOT installed in test env
        assert result is False
