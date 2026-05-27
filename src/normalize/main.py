import argparse
import logging
import sys
from pathlib import Path

from .code_handler import protect_code_blocks, restore_code_blocks
from .html_cleaner import clean_html
from .loader import load_documents
from .manifest import generate_manifest
from .markdown_processor import normalize
from .metadata import extract_metadata
from .writer import write_document

logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Normalize extracted markdown documents for RAG ingestion."
    )
    parser.add_argument("--source", required=True, type=Path, help="Extracted documents directory")
    parser.add_argument("--output", required=True, type=Path, help="Normalized output directory")
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging")
    return parser.parse_args()


def run(source: Path, output: Path) -> int:
    if not source.is_dir():
        logger.error("Source is not a valid directory: %s", source)
        return 1

    output.mkdir(parents=True, exist_ok=True)
    logger.info("Starting normalization  source=%s  output=%s", source, output)

    documents = load_documents(source)
    if not documents:
        logger.warning("No documents found in %s", source)
        return 0

    normalized_docs: list[dict] = []
    failed = 0

    for doc in documents:
        try:
            content = doc.content

            # 1. Protect code blocks so subsequent steps leave them untouched
            content, protected = protect_code_blocks(content)

            # 2. Remove irrelevant HTML (scripts, styles, JSX wrappers)
            content = clean_html(content)

            # 3. Normalize whitespace and line endings
            content = normalize(content)

            # 4. Restore code blocks exactly as found
            content = restore_code_blocks(content, protected)

            # 5. Extract structural metadata from the normalized content
            meta = extract_metadata(content)

            # 6. Write to output, preserving relative path structure
            written_to = write_document(content, doc.relative_path, output)
            if written_to is None:
                failed += 1
                continue

            normalized_docs.append({
                "id": doc.id,
                "repository": doc.repository,
                "relative_path": doc.relative_path,
                "filename": doc.filename,
                "extension": doc.extension,
                "category": doc.category,
                "original_sha1": doc.original_sha1,
                "normalized_path": str(written_to.resolve()),
                "normalized_metadata": meta.to_dict(),
            })

            logger.debug(
                "Normalized: %s  headings=%d  code_blocks=%d  links=%d",
                doc.relative_path,
                meta.heading_count,
                meta.code_block_count,
                meta.link_count,
            )

        except Exception:
            logger.exception("Failed to normalize: %s", doc.relative_path)
            failed += 1

    repository = source.name
    generate_manifest(repository, normalized_docs, output)

    logger.info(
        "Normalization complete  processed=%d  failed=%d  total=%d",
        len(normalized_docs),
        failed,
        len(documents),
    )

    return 0 if failed == 0 else 2


def main() -> None:
    args = parse_args()
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
    sys.exit(run(args.source, args.output))


if __name__ == "__main__":
    main()
