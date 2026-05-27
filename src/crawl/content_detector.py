import logging

from bs4 import BeautifulSoup, Tag

logger = logging.getLogger(__name__)

MAIN_SELECTORS = [
    "main",
    "article",
    '[role="main"]',
    ".main-content",
    ".content-main",
    "#main-content",
    "#content",
    ".documentation",
    ".doc-content",
    ".docs-content",
    ".page-content",
    ".markdown-body",
    ".prose",
]

NOISE_SELECTORS = [
    "nav",
    "header",
    "footer",
    "aside",
    ".sidebar",
    ".nav",
    ".navbar",
    ".navigation",
    ".menu",
    ".toc",
    ".table-of-contents",
    ".breadcrumb",
    ".breadcrumbs",
    ".cookie-banner",
    ".announcement",
    ".banner",
    ".ad",
    ".advertisement",
    '[aria-label="breadcrumb"]',
    '[role="navigation"]',
    '[role="banner"]',
    '[role="complementary"]',
    "script",
    "style",
    "noscript",
    "iframe",
    "svg",
]


def detect_main_content(html: str, url: str = "") -> str:
    try:
        return _readability_extract(html)
    except Exception as exc:
        logger.debug("readability failed for %s: %s", url, exc)

    return _beautifulsoup_extract(html)


def _readability_extract(html: str) -> str:
    from readability import Document

    # Pre-clean noise before readability scoring
    soup = BeautifulSoup(html, "lxml")
    for selector in NOISE_SELECTORS:
        for el in soup.select(selector):
            el.decompose()

    doc = Document(str(soup))
    return doc.summary(html_partial=True)


def _beautifulsoup_extract(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")

    for selector in NOISE_SELECTORS:
        for el in soup.select(selector):
            el.decompose()

    for selector in MAIN_SELECTORS:
        el = soup.select_one(selector)
        if el and _has_enough_text(el):
            return str(el)

    body = soup.find("body")
    if body:
        return str(body)

    return str(soup)


def _has_enough_text(el: Tag) -> bool:
    return len(el.get_text(strip=True)) > 100
