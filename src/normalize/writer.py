import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def write_document(content: str, relative_path: str, output: Path) -> Path | None:
    try:
        destination = output / "files" / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(content, encoding="utf-8")
        logger.debug("Written: %s", destination)
        return destination
    except Exception:
        logger.exception("Failed to write %s", relative_path)
        return None
