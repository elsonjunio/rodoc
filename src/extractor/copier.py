import logging
import shutil
from pathlib import Path

logger = logging.getLogger(__name__)


def copy_document(source_file: Path, source_root: Path, output_root: Path) -> Path | None:
    try:
        relative = source_file.relative_to(source_root)
        destination = output_root / "files" / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_file, destination)
        logger.debug("Copied: %s -> %s", source_file, destination)
        return destination
    except Exception:
        logger.exception("Failed to copy %s", source_file)
        return None
