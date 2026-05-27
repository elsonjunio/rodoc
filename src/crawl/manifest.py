import json
import logging
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)


def generate_manifest(
    technology: str,
    documents: list[dict],
    output: Path,
) -> Path:
    payload = {
        "repository": technology,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "document_count": len(documents),
        "documents": documents,
    }

    manifest_path = output / "manifest.json"
    manifest_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    logger.info("Manifest written: %s (%d documents)", manifest_path, len(documents))
    return manifest_path
