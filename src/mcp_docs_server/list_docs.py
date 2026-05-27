import json
import logging
import math
from pathlib import Path

from .config import ServerConfig
from .resolver import list_technologies, list_versions

logger = logging.getLogger(__name__)

_DEFAULT_PAGE_SIZE = 10
_MAX_PAGE_SIZE = 50


def _read_metadata(index_path: Path) -> dict | None:
    metadata_path = index_path / "metadata.json"
    if not metadata_path.exists():
        return None
    try:
        return json.loads(metadata_path.read_text(encoding="utf-8"))
    except Exception:
        logger.warning("Could not read metadata at %s", metadata_path)
        return None


def _build_tech_entry(vectorstore: Path, tech: str) -> dict | None:
    versions = list_versions(vectorstore, tech)
    version_entries: list[dict] = []

    for ver in versions:
        index_path = vectorstore / tech / ver
        if not (index_path / "faiss.index").exists():
            continue

        meta = _read_metadata(index_path)
        entry: dict = {"version": ver}

        if meta:
            entry["document_count"] = meta.get("document_count", 0)
            entry["chunk_count"] = meta.get("chunk_count", 0)
            entry["generated_at"] = meta.get("generated_at", "")

        version_entries.append(entry)

    if not version_entries:
        return None

    return {"technology": tech, "versions": version_entries}


def handle_list_docs(
    config: ServerConfig,
    technology: str | None,
    page: int = 1,
    page_size: int = _DEFAULT_PAGE_SIZE,
) -> dict:
    vectorstore = config.vectorstore_path

    if not vectorstore.is_dir():
        return {
            "error": "vectorstore_not_found",
            "message": f"Vectorstore path does not exist: {vectorstore}",
            "technologies": [],
        }

    page_size = min(max(1, page_size), _MAX_PAGE_SIZE)
    page = max(1, page)

    if technology:
        entry = _build_tech_entry(vectorstore, technology)
        if entry is None:
            all_techs = list_technologies(vectorstore)
            return {
                "error": "technology_not_found",
                "technology": technology,
                "message": f"No indexed versions found for '{technology}'. Available: {all_techs or 'none'}.",
                "technologies": [],
            }
        return {
            "technologies": [entry],
            "total_technologies": 1,
            "total_versions": len(entry["versions"]),
            "page": 1,
            "page_size": page_size,
            "total_pages": 1,
            "has_next": False,
        }

    all_techs = list_technologies(vectorstore)
    all_entries: list[dict] = []
    total_versions = 0

    for tech in all_techs:
        entry = _build_tech_entry(vectorstore, tech)
        if entry is not None:
            all_entries.append(entry)
            total_versions += len(entry["versions"])

    total_technologies = len(all_entries)
    total_pages = max(1, math.ceil(total_technologies / page_size))
    page = min(page, total_pages)

    start = (page - 1) * page_size
    end = start + page_size
    page_entries = all_entries[start:end]

    return {
        "technologies": page_entries,
        "total_technologies": total_technologies,
        "total_versions": total_versions,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "has_next": page < total_pages,
    }
