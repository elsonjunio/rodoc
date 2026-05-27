import logging
import threading

import numpy as np

logger = logging.getLogger(__name__)

_lock = threading.Lock()
_embedder = None


class _SentenceTransformerEmbedder:
    def __init__(self, model_name: str) -> None:
        from sentence_transformers import SentenceTransformer
        self._model = SentenceTransformer(model_name)
        self._model_name = model_name

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def dimension(self) -> int:
        return self._model.get_sentence_embedding_dimension()

    def embed(self, text: str) -> np.ndarray:
        vec = self._model.encode([text], normalize_embeddings=True, show_progress_bar=False)
        return vec.astype(np.float32)


def load_model(model_name: str) -> None:
    global _embedder
    with _lock:
        if _embedder is not None and _embedder.model_name == model_name:
            return
        try:
            logger.info("Loading embedding model: %s", model_name)
            _embedder = _SentenceTransformerEmbedder(model_name)
            logger.info("Model ready  dim=%d", _embedder.dimension)
        except ImportError as e:
            raise RuntimeError(
                "sentence-transformers is required. "
                "Install with: pip install sentence-transformers"
            ) from e


def embed_query(text: str) -> np.ndarray:
    if _embedder is None:
        raise RuntimeError("Embedding model not loaded. Call load_model() first.")
    return _embedder.embed(text)
