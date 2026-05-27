import logging
from dataclasses import dataclass

import faiss
import numpy as np

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SearchResult:
    score: float
    document: str
    section: str
    breadcrumb: list[str]
    content: str
    chunk_id: str


def search(
    faiss_index: faiss.IndexFlatIP,
    chunks: list[dict],
    query_embedding: np.ndarray,
    top_k: int,
) -> list[SearchResult]:
    if query_embedding.ndim == 1:
        query_embedding = query_embedding.reshape(1, -1)

    k = min(top_k, faiss_index.ntotal)
    if k == 0:
        return []

    distances, indices = faiss_index.search(query_embedding.astype(np.float32), k)
    results: list[SearchResult] = []

    for dist, idx in zip(distances[0], indices[0]):
        if idx < 0:
            continue
        chunk = chunks[int(idx)]
        results.append(SearchResult(
            score=round(float(dist), 6),
            document=chunk.get("document", ""),
            section=chunk.get("section", ""),
            breadcrumb=chunk.get("breadcrumb", []),
            content=chunk.get("content", ""),
            chunk_id=chunk.get("chunk_id", ""),
        ))

    return results
