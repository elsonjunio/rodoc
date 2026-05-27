import asyncio
import hashlib
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from crawlee import Glob
from crawlee.crawlers import PlaywrightCrawler, PlaywrightCrawlingContext

from .extractor import extract_page, extract_title
from .filters import infer_category, is_valid_url, normalize_url, url_to_relative_path
from .manifest import generate_manifest
from .models import CrawledDocument
from .writer import write_document

logger = logging.getLogger(__name__)

_UUID_NS = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")


def _doc_id(technology: str, relative_path: str) -> str:
    return str(uuid.uuid5(_UUID_NS, f"{technology}:{relative_path}"))


def _sha1(content: str) -> str:
    return hashlib.sha1(content.encode("utf-8")).hexdigest()


async def crawl(
    url: str,
    technology: str,
    output: Path,
    max_pages: int = 500,
    max_depth: int = 10,
    headless: bool = True,
) -> int:
    output.mkdir(parents=True, exist_ok=True)

    parsed_base = urlparse(url)
    base_path = parsed_base.path.rstrip("/")

    # Glob pattern to stay within the base domain + path
    base_origin = f"{parsed_base.scheme}://{parsed_base.netloc}"
    include_glob = f"{base_origin}{base_path}/**"

    collected: list[dict] = []
    seen_paths: set[str] = set()
    lock = asyncio.Lock()

    crawler = PlaywrightCrawler(
        max_requests_per_crawl=max_pages,
        max_crawl_depth=max_depth,
        headless=headless,
        max_request_retries=2,
        browser_launch_options={
            "args": [
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
            ]
        },
    )

    @crawler.router.default_handler
    async def handler(context: PlaywrightCrawlingContext) -> None:
        page_url = context.request.url
        normalized = normalize_url(page_url)

        if not is_valid_url(normalized, url, base_path):
            logger.debug("Filtered out: %s", page_url)
            return

        try:
            await context.page.wait_for_load_state("networkidle", timeout=15000)
        except Exception:
            pass

        html = await context.page.content()
        raw_title = await context.page.title()
        title = extract_title(html, fallback=raw_title)

        relative_path = url_to_relative_path(normalized, url)
        category = infer_category(relative_path)

        async with lock:
            if relative_path in seen_paths:
                logger.debug("Duplicate path, skipping: %s -> %s", page_url, relative_path)
                return
            seen_paths.add(relative_path)

        content = extract_page(html, page_url, title)

        if not content.strip():
            logger.warning("No content extracted from %s", page_url)
            return

        doc_id = _doc_id(technology, relative_path)
        content_hash = _sha1(content)
        discovered_at = datetime.now(timezone.utc).isoformat()

        written = write_document(content, relative_path, output)
        if written is None:
            return

        doc = CrawledDocument(
            id=doc_id,
            url=normalized,
            title=title,
            technology=technology,
            category=category,
            discovered_at=discovered_at,
            content_hash=content_hash,
            relative_path=relative_path,
            output_path=str(written.resolve()),
        )

        entry = doc.to_manifest_entry(technology, sha1=content_hash)
        entry["size_bytes"] = len(content.encode("utf-8"))

        async with lock:
            collected.append(entry)

        logger.info("[%d] %s -> %s", len(collected), page_url, relative_path)

        await context.enqueue_links(
            strategy="same-hostname",
            include=[Glob(include_glob)],
        )

    await crawler.run([url])

    generate_manifest(technology, collected, output)

    logger.info(
        "Crawl complete: technology=%s pages=%d output=%s",
        technology,
        len(collected),
        output,
    )

    return len(collected)
