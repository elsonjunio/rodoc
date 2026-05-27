import json
import logging
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class NormalizedDocument:
    id: str
    relative_path: str
    filename: str
    category: str
    source_path: Path
    content: str


def load_documents(source: Path) -> list[NormalizedDocument]:
    manifest_path = source / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    documents: list[NormalizedDocument] = []

    for entry in manifest.get("documents", []):
        file_path = source / "files" / entry["relative_path"]

        if not file_path.exists():
            logger.warning("File not found, skipping: %s", file_path)
            continue

        try:
            content = file_path.read_text(encoding="utf-8")
            documents.append(NormalizedDocument(
                id=entry["id"],
                relative_path=entry["relative_path"],
                filename=entry["filename"],
                category=entry["category"],
                source_path=file_path,
                content=content,
            ))
        except Exception:
            logger.exception("Failed to load: %s", file_path)

    logger.info("Loaded %d documents from %s", len(documents), source)
    return documents
