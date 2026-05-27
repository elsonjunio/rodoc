import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


def _configure_logging(verbose: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Documentation ingestion pipeline")
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging")

    sub = parser.add_subparsers(dest="command", required=True)

    extract = sub.add_parser("extract", help="Discover and copy markdown documents from a repository")
    extract.add_argument("--source", required=True, type=Path, help="Source repository path")
    extract.add_argument("--output", required=True, type=Path, help="Extraction output path")

    crawl = sub.add_parser("crawl", help="Crawl a documentation website and extract content")
    crawl.add_argument("--url", required=True, help="Starting URL to crawl")
    crawl.add_argument("--technology", required=True, help="Technology name (e.g. angular)")
    crawl.add_argument("--output", required=True, type=Path, help="Extraction output path")
    crawl.add_argument("--max-pages", type=int, default=500, help="Maximum number of pages to crawl")
    crawl.add_argument("--max-depth", type=int, default=10, help="Maximum crawl depth")
    crawl.add_argument("--headless", action="store_true", default=True, help="Run browser in headless mode")
    crawl.add_argument("--no-headless", dest="headless", action="store_false", help="Show browser window")

    normalize = sub.add_parser("normalize", help="Clean and normalize extracted documents")
    normalize.add_argument("--source", required=True, type=Path, help="Extracted documents path")
    normalize.add_argument("--output", required=True, type=Path, help="Normalized output path")

    index = sub.add_parser("index", help="Generate FAISS vector index from normalized documents")
    index.add_argument("--source", required=True, type=Path, help="Normalized documents path")
    index.add_argument("--output", required=True, type=Path, help="Vector store output root")
    index.add_argument("--technology", required=True, help="Technology name (e.g. angular)")
    index.add_argument("--version", required=True, help="Technology version (e.g. 20)")
    index.add_argument("--model", default="sentence-transformers/all-MiniLM-L6-v2", help="Embedding model")

    return parser


def main() -> None:
    args = _build_parser().parse_args()
    _configure_logging(args.verbose)

    if args.command == "extract":
        from extractor.main import run
        sys.exit(run(args.source, args.output))

    if args.command == "crawl":
        import asyncio
        from crawl.crawler import crawl
        count = asyncio.run(crawl(
            url=args.url,
            technology=args.technology,
            output=args.output,
            max_pages=args.max_pages,
            max_depth=args.max_depth,
            headless=args.headless,
        ))
        sys.exit(0 if count > 0 else 1)

    if args.command == "normalize":
        from normalize.main import run
        sys.exit(run(args.source, args.output))

    if args.command == "index":
        from index.main import run
        sys.exit(run(args.source, args.output, args.technology, args.version, args.model))


if __name__ == "__main__":
    main()
