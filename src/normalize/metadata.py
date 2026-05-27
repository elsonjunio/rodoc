import hashlib
import logging
from dataclasses import asdict, dataclass
from datetime import datetime, timezone

from markdown_it import MarkdownIt

logger = logging.getLogger(__name__)

_md = MarkdownIt()


@dataclass(frozen=True)
class NormalizedMetadata:
    heading_count: int
    code_block_count: int
    link_count: int
    internal_link_count: int
    external_link_count: int
    content_length: int
    sha1: str
    normalized_at: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _compute_sha1(content: str) -> str:
    return hashlib.sha1(content.encode("utf-8")).hexdigest()


def _href_is_external(href: str) -> bool:
    return href.startswith(("http://", "https://", "mailto:"))


def extract_metadata(content: str) -> NormalizedMetadata:
    try:
        tokens = _md.parse(content)
    except Exception:
        logger.warning("markdown-it failed to parse document, falling back to empty metadata")
        tokens = []

    heading_count = 0
    code_block_count = 0
    link_count = 0
    internal_link_count = 0
    external_link_count = 0

    for token in tokens:
        if token.type == "heading_open":
            heading_count += 1
        elif token.type in ("fence", "code_block"):
            code_block_count += 1
        elif token.type == "inline" and token.children:
            for child in token.children:
                if child.type == "link_open":
                    link_count += 1
                    href = (child.attrs or {}).get("href", "")
                    if _href_is_external(href):
                        external_link_count += 1
                    else:
                        internal_link_count += 1

    return NormalizedMetadata(
        heading_count=heading_count,
        code_block_count=code_block_count,
        link_count=link_count,
        internal_link_count=internal_link_count,
        external_link_count=external_link_count,
        content_length=len(content),
        sha1=_compute_sha1(content),
        normalized_at=datetime.now(timezone.utc).isoformat(),
    )
