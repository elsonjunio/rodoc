import argparse
import logging
import sys
from pathlib import Path

from .copier import copy_document
from .manifest import generate_manifest
from .metadata import build_metadata
from .scanner import scan

logger = logging.getLogger(__name__)


def configure_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract and structure markdown documentation from a repository.",
    )
    parser.add_argument(
        "--source",
        required=True,
        type=Path,
        help="Path to the source repository",
    )
    parser.add_argument(
        "--output",
        required=True,
        type=Path,
        help="Path to the output directory",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug logging",
    )
    return parser.parse_args()


def run(source: Path, output: Path) -> int:
    if not source.is_dir():
        logger.error("Source is not a valid directory: %s", source)
        return 1

    repository = source.name
    output.mkdir(parents=True, exist_ok=True)

    logger.info("Starting extraction  source=%s  output=%s", source, output)

    discovered = scan(source)
    logger.info("Discovered %d documents", len(discovered))

    metadata_list = []
    failed = 0

    for doc_path in discovered:
        copied_to = copy_document(doc_path, source, output)
        if copied_to is None:
            failed += 1
            continue

        metadata = build_metadata(doc_path, source, repository, copied_to)
        if metadata is None:
            failed += 1
            continue

        metadata_list.append(metadata)

    generate_manifest(repository, metadata_list, output)

    logger.info(
        "Extraction complete  processed=%d  failed=%d  total=%d",
        len(metadata_list),
        failed,
        len(discovered),
    )

    return 0 if failed == 0 else 2


def main() -> None:
    args = parse_args()
    configure_logging(args.verbose)
    sys.exit(run(args.source, args.output))


if __name__ == "__main__":
    main()
