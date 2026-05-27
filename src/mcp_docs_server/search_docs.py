import json
import logging
from pathlib import Path

import faiss

from .cache import IndexCache, LoadedIndex
from .config import ServerConfig
from .faiss_search import search
from .model import embed_query
from .resolver import resolve_index, list_technologies, list_versions

logger = logging.getLogger(__name__)

_cache = IndexCache()


def _load_index(path: Path, technology: str, version: str) -> LoadedIndex | None:
    try:
        faiss_path = path / "faiss.index"
        chunks_path = path / "chunks.jsonl"
        metadata_path = path / "metadata.json"

        missing = [p for p in (faiss_path, chunks_path, metadata_path) if not p.exists()]
        if missing:
            logger.error("Incomplete index at %s, missing: %s", path, missing)
            return None

        faiss_index = faiss.read_index(str(faiss_path))
        chunks = [
            json.loads(line)
            for line in chunks_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))

        logger.info("Index loaded: %s@%s  chunks=%d", technology, version, len(chunks))
        return LoadedIndex(
            technology=technology,
            version=version,
            faiss_index=faiss_index,
            chunks=chunks,
            metadata=metadata,
        )
    except Exception:
        logger.exception("Failed to load index: %s", path)
        return None


def _get_loaded_index(
    config: ServerConfig,
    technology: str,
    version: str,
) -> tuple[str | None, LoadedIndex | None]:
    resolved = resolve_index(config.vectorstore_path, technology, version)
    if resolved is None:
        return None, None

    cached = _cache.get(technology, resolved.resolved_version)
    if cached is not None:
        return resolved.resolved_version, cached

    loaded = _load_index(resolved.path, technology, resolved.resolved_version)
    if loaded is None:
        return None, None

    _cache.set(technology, resolved.resolved_version, loaded)
    return resolved.resolved_version, loaded


def handle_search_docs(
    config: ServerConfig,
    technology: str,
    version: str,
    query: str,
    top_k: int,
) -> dict:
    resolved_version, loaded = _get_loaded_index(config, technology, version)

    if loaded is None:
        available_techs = list_technologies(config.vectorstore_path)
        available_versions = list_versions(config.vectorstore_path, technology)
        return {
            "error": "index_not_found",
            "technology": technology,
            "requested_version": version,
            "message": (
                f"No compatible index found for {technology}@{version}. "
                f"Available versions: {available_versions or 'none'}. "
                f"Available technologies: {available_techs}."
            ),
        }

    query_vec = embed_query(query)
    results = search(loaded.faiss_index, loaded.chunks, query_vec, top_k)

    return {
        "technology": technology,
        "resolved_version": resolved_version,
        "query": query,
        "result_count": len(results),
        "results": [
            {
                "score": r.score,
                "document": r.document,
                "section": r.section,
                "breadcrumb": r.breadcrumb,
                "content": r.content,
                "chunk_id": r.chunk_id,
            }
            for r in results
        ],
    }
