import hashlib
import logging
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

_UUID_NAMESPACE = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")

CATEGORY_MAP: dict[str, str] = {
    "docs": "docs",
    "documentation": "docs",
    "guide": "guide",
    "guides": "guide",
    "tutorial": "tutorial",
    "tutorials": "tutorial",
    "api": "api",
    "examples": "examples",
    "src": "src",
    "packages": "packages",
}


@dataclass(frozen=True)
class DocumentMetadata:
    id: str
    repository: str
    relative_path: str
    absolute_path: str
    filename: str
    extension: str
    size_bytes: int
    sha1: str
    category: str
    copied_to: str
    discovered_at: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _compute_sha1(path: Path) -> str:
    h = hashlib.sha1()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _infer_category(relative_path: Path) -> str:
    if relative_path.name.lower() in ("readme.md", "readme.mdx"):
        return "readme"

    for part in relative_path.parts:
        category = CATEGORY_MAP.get(part.lower())
        if category:
            return category

    return "misc"


def _generate_id(repository: str, relative_path: Path) -> str:
    key = f"{repository}:{relative_path.as_posix()}"
    return str(uuid.uuid5(_UUID_NAMESPACE, key))


def build_metadata(
    path: Path,
    source: Path,
    repository: str,
    copied_to: Path,
) -> DocumentMetadata | None:
    try:
        relative = path.relative_to(source)
        return DocumentMetadata(
            id=_generate_id(repository, relative),
            repository=repository,
            relative_path=relative.as_posix(),
            absolute_path=str(path.resolve()),
            filename=path.name,
            extension=path.suffix.lower(),
            size_bytes=path.stat().st_size,
            sha1=_compute_sha1(path),
            category=_infer_category(relative),
            copied_to=str(copied_to.resolve()),
            discovered_at=datetime.now(timezone.utc).isoformat(),
        )
    except Exception:
        logger.exception("Failed to build metadata for %s", path)
        return None
