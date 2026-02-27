"""EmbeddingProvider -- local sentence-transformers wrapper.

Lazy-loads the model on first embed() call. Guarded import so the
sentence-transformers package is only required when semantic search is enabled.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

_st_available = False
try:
    import sentence_transformers  # type: ignore[import-not-found]  # noqa: F401

    _st_available = True
except ImportError:
    pass


def _load_model(model_name: str) -> Any:
    """Load a sentence-transformers model. Raises if not installed."""
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(model_name)


class EmbeddingProvider:
    """Wraps sentence-transformers for local embedding generation.

    The model is loaded lazily on the first ``embed()`` or ``embed_batch()``
    call to avoid startup cost when semantic search is disabled.
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2", dim: int = 384) -> None:
        self._model_name = model_name
        self._dim = dim
        self._model: Any = None

    def _ensure_model(self) -> Any:
        if self._model is None:
            self._model = _load_model(self._model_name)
        return self._model

    def embed(self, text: str) -> list[float]:
        """Embed a single text string into a float vector."""
        model = self._ensure_model()
        vec = model.encode(text)
        if hasattr(vec, "tolist"):
            return [float(x) for x in vec.tolist()]
        return [float(x) for x in vec]

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed multiple texts into float vectors."""
        model = self._ensure_model()
        vecs = model.encode(texts)
        result: list[list[float]] = []
        for vec in vecs:
            if hasattr(vec, "tolist"):
                result.append([float(x) for x in vec.tolist()])
            else:
                result.append([float(x) for x in vec])
        return result

    @staticmethod
    def is_available() -> bool:
        """Check if sentence-transformers is installed."""
        return _st_available
