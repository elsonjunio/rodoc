import json
import logging
from pathlib import Path

from .chunker import DocumentChunk

logger = logging.getLogger(__name__)


def write_chunks(chunks: list[DocumentChunk], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for chunk in chunks:
            f.write(json.dumps(chunk.to_dict(), ensure_ascii=False) + "\n")
    logger.info("Chunks written: %s (%d records)", path, len(chunks))


def write_metadata(metadata: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info("Metadata written: %s", path)
