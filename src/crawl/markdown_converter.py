import re

import markdownify
from bs4 import BeautifulSoup

_MULTIPLE_BLANKS = re.compile(r"\n{3,}")
_TRAILING_SPACES = re.compile(r"[ \t]+\n")


class _DocMarkdownConverter(markdownify.MarkdownConverter):
    def convert_pre(self, el, text, parent_tags):
        code = el.find("code")
        lang = ""
        if code:
            classes = code.get("class") or []
            for cls in classes:
                if cls.startswith("language-"):
                    lang = cls[len("language-"):]
                    break
            inner = code.get_text()
        else:
            inner = el.get_text()

        inner = inner.strip("\n")
        return f"\n\n```{lang}\n{inner}\n```\n\n"

    def convert_code(self, el, text, parent_tags):
        if el.parent and el.parent.name == "pre":
            return text
        code = el.get_text()
        return f"`{code}`"

    def convert_table(self, el, text, parent_tags):
        return "\n\n" + text.strip() + "\n\n"


def html_to_markdown(html: str, base_url: str = "") -> str:
    soup = BeautifulSoup(html, "lxml")

    for tag in soup.select("script, style, noscript, iframe"):
        tag.decompose()

    converter = _DocMarkdownConverter(
        heading_style=markdownify.ATX,
        bullets="-",
        strip=["img"],
        autolinks=False,
    )

    md = converter.convert(str(soup))
    md = _clean_markdown(md)
    return md


def _clean_markdown(md: str) -> str:
    md = _TRAILING_SPACES.sub("\n", md)
    md = _MULTIPLE_BLANKS.sub("\n\n", md)
    return md.strip() + "\n"
