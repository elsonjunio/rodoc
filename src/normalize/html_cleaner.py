import re

_HAS_HTML = re.compile(r"<[a-zA-Z/!]")

# Blocks to remove entirely (including their content)
_SCRIPT = re.compile(r"<script[^>]*>.*?</script\s*>", re.DOTALL | re.IGNORECASE)
_STYLE = re.compile(r"<style[^>]*>.*?</style\s*>", re.DOTALL | re.IGNORECASE)
_HTML_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)

# MDX/JSX component tags — PascalCase or dotted (e.g. Tabs.Item)
# Self-closing: <MyComponent prop="x" />
_JSX_SELF_CLOSING = re.compile(
    r"<[A-Z][a-zA-Z0-9]*(?:\.[a-zA-Z0-9]+)*(?:\s[^>]*)?\s*/>",
    re.DOTALL,
)
# Block: <MyComponent>...</MyComponent> — removed entirely (structural wrapper, no text)
_JSX_BLOCK = re.compile(
    r"<([A-Z][a-zA-Z0-9]*(?:\.[a-zA-Z0-9]+)*)(?:\s[^>]*)?>.*?</\1\s*>",
    re.DOTALL,
)

# Tags to unwrap: remove the tag but keep inner text
_UNWRAP_OPEN = re.compile(
    r"<(?:div|span|section|article|header|footer|nav|main|aside|figure|figcaption)"
    r"(?:\s[^>]*)?>",
    re.IGNORECASE,
)
_UNWRAP_CLOSE = re.compile(
    r"</(?:div|span|section|article|header|footer|nav|main|aside|figure|figcaption)>",
    re.IGNORECASE,
)

# <br> -> newline
_BR = re.compile(r"<br\s*/?>", re.IGNORECASE)

# Inline style attributes on preserved tags (e.g. <code style="color:red">)
_INLINE_STYLE = re.compile(r'\s+style="[^"]*"', re.IGNORECASE)
_INLINE_CLASS = re.compile(r'\s+class(?:Name)?="[^"]*"', re.IGNORECASE)


def has_html(text: str) -> bool:
    return bool(_HAS_HTML.search(text))


def clean_html(text: str) -> str:
    if not has_html(text):
        return text

    text = _SCRIPT.sub("", text)
    text = _STYLE.sub("", text)
    text = _HTML_COMMENT.sub("", text)

    # Remove JSX blocks before self-closing (block pattern is greedier)
    text = _JSX_BLOCK.sub("", text)
    text = _JSX_SELF_CLOSING.sub("", text)

    text = _BR.sub("\n", text)
    text = _UNWRAP_OPEN.sub("", text)
    text = _UNWRAP_CLOSE.sub("", text)

    # Strip noisy presentational attributes from preserved semantic tags
    text = _INLINE_STYLE.sub("", text)
    text = _INLINE_CLASS.sub("", text)

    return text
