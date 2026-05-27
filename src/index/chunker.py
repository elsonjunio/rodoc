import re
import uuid
from dataclasses import dataclass, field

_UUID_NS = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")
_HEADING = re.compile(r"^(#{1,6})\s+(.+?)$", re.MULTILINE)
_FENCED_CODE = re.compile(r"`{3,}[^\n]*\n.*?`{3,}", re.DOTALL)

MAX_CHUNK_CHARS: int = 2000
MIN_CHUNK_CHARS: int = 60


# ---------------------------------------------------------------------------
# Public data model
# ---------------------------------------------------------------------------

@dataclass
class DocumentChunk:
    id: str
    technology: str
    version: str
    document: str
    section: str
    breadcrumb: list[str]
    content: str
    code_blocks: list[str]
    token_estimate: int
    embedding_index: int = -1

    def to_dict(self) -> dict:
        return {
            "chunk_id": self.id,
            "technology": self.technology,
            "version": self.version,
            "document": self.document,
            "section": self.section,
            "breadcrumb": self.breadcrumb,
            "content": self.content,
            "code_blocks": self.code_blocks,
            "token_estimate": self.token_estimate,
            "embedding_index": self.embedding_index,
        }


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

@dataclass
class _Section:
    level: int
    title: str
    body: str
    breadcrumb: list[str] = field(default_factory=list)

    @property
    def heading_line(self) -> str:
        return ("#" * self.level + " " + self.title) if self.level > 0 else ""

    def full_content(self) -> str:
        """Assemble content used for both embedding and the chunk record."""
        parts: list[str] = []
        if self.breadcrumb:
            parts.append(" > ".join(self.breadcrumb))
        if self.heading_line:
            parts.append(self.heading_line)
        if self.body:
            parts.append(self.body)
        return "\n\n".join(p for p in parts if p)


def _protect(text: str) -> tuple[str, dict[str, str]]:
    store: dict[str, str] = {}
    ctr = 0

    def _sub(m: re.Match) -> str:
        nonlocal ctr
        key = f"\x00CB{ctr}\x00"
        store[key] = m.group(0)
        ctr += 1
        return key

    return _FENCED_CODE.sub(_sub, text), store


def _restore(text: str, store: dict[str, str]) -> str:
    for key, block in store.items():
        text = text.replace(key, block)
    return text


def _split_paragraphs(text: str) -> list[str]:
    protected, store = _protect(text)
    parts = re.split(r"\n\n+", protected)
    result: list[str] = []
    for part in parts:
        restored = _restore(part.strip(), store)
        if restored:
            result.append(restored)
    return result


def _estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4)


def _chunk_id(document: str, section: str, idx: int) -> str:
    return str(uuid.uuid5(_UUID_NS, f"{document}:{section}:{idx}"))


def _make_chunk(
    section: _Section,
    content: str,
    document: str,
    technology: str,
    version: str,
    idx: int,
) -> DocumentChunk:
    return DocumentChunk(
        id=_chunk_id(document, section.title, idx),
        technology=technology,
        version=version,
        document=document,
        section=section.title or document,
        breadcrumb=section.breadcrumb,
        content=content,
        code_blocks=_FENCED_CODE.findall(content),
        token_estimate=_estimate_tokens(content),
    )


# ---------------------------------------------------------------------------
# Section extraction
# ---------------------------------------------------------------------------

def _extract_sections(content: str) -> list[_Section]:
    """Split document into sections by headings, protecting code blocks."""
    protected, store = _protect(content)
    matches = list(_HEADING.finditer(protected))

    if not matches:
        return [_Section(level=0, title="", body=content.strip())]

    sections: list[_Section] = []
    active: dict[int, str] = {}

    # Preamble before first heading
    if matches[0].start() > 0:
        preamble_p = protected[: matches[0].start()].strip()
        preamble = _restore(preamble_p, store)
        if preamble:
            sections.append(_Section(level=0, title="", body=preamble))

    for i, match in enumerate(matches):
        level = len(match.group(1))
        title = match.group(2).strip()

        active[level] = title
        for lvl in list(active):
            if lvl > level:
                del active[lvl]

        breadcrumb = [active[lvl] for lvl in sorted(active) if lvl < level]

        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(protected)
        body = _restore(protected[start:end].strip(), store)

        sections.append(_Section(level=level, title=title, body=body, breadcrumb=breadcrumb))

    return sections


# ---------------------------------------------------------------------------
# Large section splitting
# ---------------------------------------------------------------------------

def _split_large(
    section: _Section,
    document: str,
    technology: str,
    version: str,
    base_idx: int,
) -> list[DocumentChunk]:
    """Split a section that exceeds MAX_CHUNK_CHARS by paragraph boundaries."""
    paragraphs = _split_paragraphs(section.body)
    chunks: list[DocumentChunk] = []
    current: list[str] = []
    current_size = 0
    sub = 0

    def _flush() -> None:
        nonlocal current, current_size, sub
        if not current:
            return
        # Re-attach heading context to each sub-chunk
        sub_section = _Section(
            level=section.level,
            title=section.title,
            body="\n\n".join(current),
            breadcrumb=section.breadcrumb,
        )
        chunks.append(_make_chunk(sub_section, sub_section.full_content(), document, technology, version, base_idx + sub))
        current = []
        current_size = 0
        sub += 1

    for para in paragraphs:
        size = len(para)

        if size > MAX_CHUNK_CHARS:
            # Oversized single element (e.g., a huge code block) — own chunk
            _flush()
            oversized = _Section(
                level=section.level,
                title=section.title,
                body=para,
                breadcrumb=section.breadcrumb,
            )
            chunks.append(_make_chunk(oversized, oversized.full_content(), document, technology, version, base_idx + sub))
            sub += 1
        elif current_size + size > MAX_CHUNK_CHARS:
            _flush()
            current.append(para)
            current_size = size
        else:
            current.append(para)
            current_size += size

    _flush()
    return chunks


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def chunk_document(
    content: str,
    document: str,
    technology: str,
    version: str,
) -> list[DocumentChunk]:
    sections = _extract_sections(content)
    chunks: list[DocumentChunk] = []

    for section in sections:
        full = section.full_content()
        if not full or len(full) < MIN_CHUNK_CHARS:
            continue

        if len(full) <= MAX_CHUNK_CHARS:
            chunks.append(_make_chunk(section, full, document, technology, version, len(chunks)))
        else:
            chunks.extend(_split_large(section, document, technology, version, len(chunks)))

    return chunks
