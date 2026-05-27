import logging
from dataclasses import dataclass
from pathlib import Path

from .semver_resolver import resolve

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ResolvedIndex:
    technology: str
    resolved_version: str
    path: Path


def list_technologies(vectorstore: Path) -> list[str]:
    if not vectorstore.is_dir():
        return []
    return sorted(d.name for d in vectorstore.iterdir() if d.is_dir())


def list_versions(vectorstore: Path, technology: str) -> list[str]:
    tech_path = vectorstore / technology
    if not tech_path.is_dir():
        return []
    return sorted(d.name for d in tech_path.iterdir() if d.is_dir())


def resolve_index(vectorstore: Path, technology: str, version: str) -> ResolvedIndex | None:
    available = list_versions(vectorstore, technology)

    if not available:
        logger.warning("Technology not found or has no versions: %s", technology)
        return None

    resolved_version = resolve(version, available)
    if resolved_version is None:
        logger.warning(
            "No compatible version for %s@%s  (available: %s)",
            technology, version, available,
        )
        return None

    index_path = vectorstore / technology / resolved_version
    if not (index_path / "faiss.index").exists():
        logger.error("Index directory incomplete: %s", index_path)
        return None

    if resolved_version != version:
        logger.info("Version resolved: %s@%s → %s", technology, version, resolved_version)

    return ResolvedIndex(
        technology=technology,
        resolved_version=resolved_version,
        path=index_path,
    )
