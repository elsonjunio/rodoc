import re

_TRAILING_WHITESPACE = re.compile(r"[ \t]+$", re.MULTILINE)
_EXCESSIVE_BLANK_LINES = re.compile(r"\n{3,}")


def normalize_line_endings(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def strip_trailing_whitespace(text: str) -> str:
    return _TRAILING_WHITESPACE.sub("", text)


def collapse_blank_lines(text: str) -> str:
    return _EXCESSIVE_BLANK_LINES.sub("\n\n", text)


def ensure_final_newline(text: str) -> str:
    return text.rstrip("\n") + "\n"


def normalize(text: str) -> str:
    text = normalize_line_endings(text)
    text = strip_trailing_whitespace(text)
    text = collapse_blank_lines(text)
    text = ensure_final_newline(text)
    return text
