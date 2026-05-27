import logging
import re

from bs4 import BeautifulSoup

from .content_detector import detect_main_content
from .markdown_converter import html_to_markdown

logger = logging.getLogger(__name__)

_TITLE_RE = re.compile(r"^#\s+(.+)$", re.MULTILINE)


def extract_page(html: str, url: str, title: str) -> str:
    main_html = detect_main_content(html, url)
    markdown = html_to_markdown(main_html, base_url=url)

    if not markdown.strip():
        logger.warning("Empty content extracted from %s", url)
        return ""

    if title and not _has_h1(markdown):
        markdown = f"# {title}\n\n{markdown}"

    return markdown


def extract_title(html: str, fallback: str = "") -> str:
    soup = BeautifulSoup(html, "lxml")

    og_title = soup.find("meta", property="og:title")
    if og_title and og_title.get("content"):
        return og_title["content"].strip()

    h1 = soup.find("h1")
    if h1:
        return h1.get_text(strip=True)

    title_tag = soup.find("title")
    if title_tag:
        text = title_tag.get_text(strip=True)
        text = re.sub(r"\s*[|\-–—]\s*.*$", "", text).strip()
        if text:
            return text

    return fallback


def _has_h1(markdown: str) -> bool:
    return bool(_TITLE_RE.search(markdown))
