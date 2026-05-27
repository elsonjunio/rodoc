import logging
from dataclasses import dataclass
from threading import Lock

import faiss

logger = logging.getLogger(__name__)


@dataclass
class LoadedIndex:
    technology: str
    version: str
    faiss_index: faiss.IndexFlatIP
    chunks: list[dict]
    metadata: dict


class IndexCache:
    """Thread-safe in-memory cache for loaded FAISS indices."""

    def __init__(self) -> None:
        self._store: dict[str, LoadedIndex] = {}
        self._lock = Lock()

    def _key(self, technology: str, version: str) -> str:
        return f"{technology}/{version}"

    def get(self, technology: str, version: str) -> LoadedIndex | None:
        return self._store.get(self._key(technology, version))

    def set(self, technology: str, version: str, index: LoadedIndex) -> None:
        key = self._key(technology, version)
        with self._lock:
            self._store[key] = index
        logger.debug("Cached index: %s (%d chunks)", key, len(index.chunks))

    def evict(self, technology: str, version: str) -> None:
        key = self._key(technology, version)
        with self._lock:
            self._store.pop(key, None)

    def clear(self) -> None:
        with self._lock:
            self._store.clear()
