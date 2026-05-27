import json
import logging
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ExtractedDocument:
    id: str
    repository: str
    relative_path: str
    filename: str
    extension: str
    category: str
    original_sha1: str
    source_path: Path
    content: str


def load_manifest(source: Path) -> dict:
    manifest_path = source / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def load_documents(source: Path) -> list[ExtractedDocument]:
    manifest = load_manifest(source)
    documents: list[ExtractedDocument] = []

    for entry in manifest.get("documents", []):
        relative_path = entry["relative_path"]
        file_path = source / "files" / relative_path

        if not file_path.exists():
            logger.warning("File not found, skipping: %s", file_path)
            continue

        try:
            # utf-8-sig strips BOM if present
            content = file_path.read_text(encoding="utf-8-sig", errors="replace")
            documents.append(ExtractedDocument(
                id=entry["id"],
                repository=entry["repository"],
                relative_path=relative_path,
                filename=entry["filename"],
                extension=entry["extension"],
                category=entry["category"],
                original_sha1=entry["sha1"],
                source_path=file_path,
                content=content,
            ))
        except Exception:
            logger.exception("Failed to load document: %s", file_path)

    logger.info("Loaded %d documents from %s", len(documents), source)
    return documents
