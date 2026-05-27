import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from .metadata import DocumentMetadata

logger = logging.getLogger(__name__)


def generate_manifest(
    repository: str,
    documents: list[DocumentMetadata],
    output: Path,
) -> Path:
    payload = {
        "repository": repository,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "document_count": len(documents),
        "documents": [doc.to_dict() for doc in documents],
    }

    manifest_path = output / "manifest.json"
    manifest_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    logger.info("Manifest written: %s (%d documents)", manifest_path, len(documents))
    return manifest_path
