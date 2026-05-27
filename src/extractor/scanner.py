import logging
from pathlib import Path

from .filters import is_ignored_directory, is_valid_document

logger = logging.getLogger(__name__)


def scan(source: Path) -> list[Path]:
    documents: list[Path] = []
    _walk(source, documents)
    logger.info("Scan complete: %d documents found in %s", len(documents), source)
    return documents


def _walk(directory: Path, documents: list[Path]) -> None:
    try:
        entries = sorted(directory.iterdir())
    except PermissionError:
        logger.warning("Permission denied, skipping: %s", directory)
        return

    for entry in entries:
        if entry.is_symlink():
            logger.debug("Skipped symlink: %s", entry)
            continue

        if entry.is_dir():
            if not is_ignored_directory(entry):
                _walk(entry, documents)
            else:
                logger.debug("Skipped ignored directory: %s", entry)
        elif entry.is_file():
            if is_valid_document(entry):
                documents.append(entry)
            else:
                logger.debug("Skipped: %s", entry)
