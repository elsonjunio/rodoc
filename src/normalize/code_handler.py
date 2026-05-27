import re
from dataclasses import dataclass

# Fenced blocks: ```lang\n...\n``` or ~~~lang\n...\n~~~
# The backreference \1 ensures the closing fence matches the opening one.
_FENCED_BLOCK = re.compile(r"(`{3,})[^\n]*\n.*?\1|~{3,}[^\n]*\n.*?~{3,}", re.DOTALL)

# Indented code blocks: 4-space or tab-indented lines preceded by a blank line
_INDENTED_BLOCK = re.compile(r"(?:(?:^|\n)\n)((?:(?:    |\t)[^\n]*\n)+)")

_PLACEHOLDER_TPL = "\x00CODEBLOCK_{index}\x00"


@dataclass(frozen=True)
class _Protected:
    placeholder: str
    content: str


def protect_code_blocks(text: str) -> tuple[str, list[_Protected]]:
    """Replace code blocks with opaque placeholders so other processors skip them."""
    protected: list[_Protected] = []

    def _replace(match: re.Match) -> str:
        placeholder = _PLACEHOLDER_TPL.format(index=len(protected))
        protected.append(_Protected(placeholder=placeholder, content=match.group(0)))
        return placeholder

    text = _FENCED_BLOCK.sub(_replace, text)
    return text, protected


def restore_code_blocks(text: str, protected: list[_Protected]) -> str:
    """Restore previously protected code blocks from their placeholders."""
    for block in protected:
        text = text.replace(block.placeholder, block.content)
    return text
