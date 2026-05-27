import logging
from pathlib import Path

import faiss
import numpy as np

logger = logging.getLogger(__name__)


def create_index(dimension: int) -> faiss.IndexFlatIP:
    # IndexFlatIP: exact inner-product search (cosine similarity with normalized vectors)
    return faiss.IndexFlatIP(dimension)


def add_embeddings(index: faiss.IndexFlatIP, embeddings: np.ndarray) -> None:
    if embeddings.dtype != np.float32:
        embeddings = embeddings.astype(np.float32)
    index.add(embeddings)
    logger.info("Added %d vectors to FAISS index (total: %d)", len(embeddings), index.ntotal)


def save_index(index: faiss.IndexFlatIP, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(path))
    logger.info("FAISS index saved: %s (%d vectors)", path, index.ntotal)


def load_index(path: Path) -> faiss.IndexFlatIP:
    if not path.exists():
        raise FileNotFoundError(f"FAISS index not found: {path}")
    index = faiss.read_index(str(path))
    logger.info("FAISS index loaded: %s (%d vectors)", path, index.ntotal)
    return index
