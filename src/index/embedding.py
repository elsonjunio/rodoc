from __future__ import annotations

import logging
from abc import ABC, abstractmethod

import numpy as np

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


class BaseEmbedder(ABC):
    @property
    @abstractmethod
    def dimension(self) -> int: ...

    @property
    @abstractmethod
    def model_name(self) -> str: ...

    @abstractmethod
    def embed(self, texts: list[str]) -> np.ndarray: ...


class SentenceTransformerEmbedder(BaseEmbedder):
    def __init__(self, model_name: str = DEFAULT_MODEL) -> None:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as e:
            raise ImportError(
                "sentence-transformers is required for embedding. "
                "Install it with: pip install sentence-transformers"
            ) from e

        logger.info("Loading embedding model: %s", model_name)
        self._model = SentenceTransformer(model_name)
        self._model_name = model_name
        logger.info("Model loaded. Dimension: %d", self.dimension)

    @property
    def dimension(self) -> int:
        return self._model.get_sentence_embedding_dimension()

    @property
    def model_name(self) -> str:
        return self._model_name

    def embed(self, texts: list[str]) -> np.ndarray:
        logger.info("Generating embeddings for %d texts...", len(texts))
        vectors = self._model.encode(
            texts,
            batch_size=64,
            show_progress_bar=True,
            normalize_embeddings=True,  # cosine similarity via inner product
        )
        return np.array(vectors, dtype=np.float32)


def load_embedder(model_name: str = DEFAULT_MODEL) -> BaseEmbedder:
    return SentenceTransformerEmbedder(model_name)
