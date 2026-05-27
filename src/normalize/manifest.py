import json
import logging
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)


def generate_manifest(
    repository: str,
    documents: list[dict],
    output: Path,
) -> Path:
    stats = {
        "total_headings": sum(d["normalized_metadata"]["heading_count"] for d in documents),
        "total_code_blocks": sum(d["normalized_metadata"]["code_block_count"] for d in documents),
        "total_links": sum(d["normalized_metadata"]["link_count"] for d in documents),
        "total_internal_links": sum(d["normalized_metadata"]["internal_link_count"] for d in documents),
        "total_external_links": sum(d["normalized_metadata"]["external_link_count"] for d in documents),
    }

    payload = {
        "repository": repository,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "document_count": len(documents),
        "statistics": stats,
        "documents": documents,
    }

    manifest_path = output / "manifest.json"
    manifest_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    logger.info(
        "Manifest written: %s (%d documents, %d headings, %d code blocks, %d links)",
        manifest_path,
        len(documents),
        stats["total_headings"],
        stats["total_code_blocks"],
        stats["total_links"],
    )
    return manifest_path
