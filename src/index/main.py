import argparse
import logging
import sys
from pathlib import Path

from .chunker import chunk_document
from .embedding import DEFAULT_MODEL, load_embedder
from .faiss_store import add_embeddings, create_index, save_index
from .loader import load_documents
from .metadata import build_metadata
from .writer import write_chunks, write_metadata

logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate FAISS vector index from normalized documents."
    )
    parser.add_argument("--source", required=True, type=Path, help="Normalized documents directory")
    parser.add_argument("--output", required=True, type=Path, help="Vector store output root")
    parser.add_argument("--technology", required=True, help="Technology name (e.g. angular)")
    parser.add_argument("--version", required=True, help="Technology version (e.g. 20)")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Sentence-transformers model name")
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging")
    return parser.parse_args()


def run(
    source: Path,
    output: Path,
    technology: str,
    version: str,
    model_name: str = DEFAULT_MODEL,
) -> int:
    if not source.is_dir():
        logger.error("Source is not a valid directory: %s", source)
        return 1

    logger.info(
        "Starting indexing  technology=%s  version=%s  model=%s",
        technology, version, model_name,
    )

    # ------------------------------------------------------------------ #
    # 1. Load normalized documents
    # ------------------------------------------------------------------ #
    documents = load_documents(source)
    if not documents:
        logger.warning("No documents found in %s", source)
        return 0

    # ------------------------------------------------------------------ #
    # 2. Semantic chunking
    # ------------------------------------------------------------------ #
    all_chunks = []
    failed_docs = 0

    for doc in documents:
        try:
            chunks = chunk_document(doc.content, doc.relative_path, technology, version)
            all_chunks.extend(chunks)
            logger.debug("Chunked %s -> %d chunks", doc.relative_path, len(chunks))
        except Exception:
            logger.exception("Failed to chunk: %s", doc.relative_path)
            failed_docs += 1

    if not all_chunks:
        logger.error("No chunks generated. Aborting.")
        return 1

    logger.info(
        "Chunking complete  documents=%d  chunks=%d  failed=%d",
        len(documents),
        len(all_chunks),
        failed_docs,
    )

    # ------------------------------------------------------------------ #
    # 3. Embed
    # ------------------------------------------------------------------ #
    embedder = load_embedder(model_name)
    texts = [c.content for c in all_chunks]
    embeddings = embedder.embed(texts)

    # ------------------------------------------------------------------ #
    # 4. FAISS index
    # ------------------------------------------------------------------ #
    index = create_index(embedder.dimension)
    add_embeddings(index, embeddings)

    # Assign final FAISS position to each chunk
    for i, chunk in enumerate(all_chunks):
        chunk.embedding_index = i

    # ------------------------------------------------------------------ #
    # 5. Persist
    # ------------------------------------------------------------------ #
    store_path = output / technology / version
    store_path.mkdir(parents=True, exist_ok=True)

    save_index(index, store_path / "faiss.index")
    write_chunks(all_chunks, store_path / "chunks.jsonl")
    write_metadata(
        build_metadata(
            technology=technology,
            version=version,
            model_name=model_name,
            chunk_count=len(all_chunks),
            dimension=embedder.dimension,
            document_count=len(documents),
        ),
        store_path / "metadata.json",
    )

    logger.info(
        "Indexing complete  store=%s  chunks=%d  dimension=%d",
        store_path,
        len(all_chunks),
        embedder.dimension,
    )
    return 0 if failed_docs == 0 else 2


def main() -> None:
    args = parse_args()
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
    sys.exit(run(args.source, args.output, args.technology, args.version, args.model))


if __name__ == "__main__":
    main()
