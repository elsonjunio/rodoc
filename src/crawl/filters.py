import re
from urllib.parse import urlparse

IGNORED_PATH_PATTERNS: list[re.Pattern] = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"/login",
        r"/logout",
        r"/signin",
        r"/signup",
        r"/register",
        r"/auth/",
        r"/account/",
        r"/search(\?|$|/)",
        r"/404",
        r"/500",
        r"\.(png|jpg|jpeg|gif|svg|webp|ico|pdf|zip|tar|gz|woff|woff2|ttf|eot|mp4|mp3)(\?|$)",
        r"/__/",
        r"/cdn-cgi/",
        r"/static/",
        r"/assets/",
        r"/fonts/",
        r"/images/",
        r"/(facebook|twitter|github|google)\.com",
        r"/analytics",
        r"/telemetry",
    ]
]

IGNORED_EXTENSIONS: frozenset[str] = frozenset({
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".ico",
    ".pdf", ".zip", ".tar", ".gz", ".woff", ".woff2", ".ttf", ".eot",
    ".mp4", ".mp3", ".avi", ".mov", ".css", ".js", ".json", ".xml",
    ".txt", ".csv", ".xlsx", ".docx",
})


def is_valid_url(url: str, base_url: str, base_path: str) -> bool:
    try:
        parsed = urlparse(url)
        base = urlparse(base_url)

        if parsed.scheme not in ("http", "https"):
            return False

        if parsed.netloc != base.netloc:
            return False

        path = parsed.path.rstrip("/") or "/"
        if base_path and base_path != "/" and not path.startswith(base_path):
            return False

        suffix = _path_suffix(parsed.path)
        if suffix in IGNORED_EXTENSIONS:
            return False

        for pattern in IGNORED_PATH_PATTERNS:
            if pattern.search(parsed.path):
                return False

        return True
    except Exception:
        return False


def normalize_url(url: str) -> str:
    parsed = urlparse(url)
    # Drop fragment and normalize path
    normalized = parsed._replace(fragment="", query="")
    path = normalized.path.rstrip("/") or "/"
    return normalized._replace(path=path).geturl()


_HTML_EXTENSIONS = frozenset({".html", ".htm", ".xhtml"})


def url_to_relative_path(url: str, base_url: str) -> str:
    parsed = urlparse(url)
    base = urlparse(base_url)

    path = parsed.path
    base_path = base.path.rstrip("/")

    if base_path and path.startswith(base_path):
        path = path[len(base_path):]

    path = path.strip("/")

    if not path:
        return "index.md"

    parts = [p for p in path.split("/") if p]
    last = parts[-1]
    suffix = _path_suffix(last)
    if suffix in _HTML_EXTENSIONS:
        parts[-1] = last[: -len(suffix)]

    return "/".join(parts) + ".md"


def infer_category(relative_path: str) -> str:
    parts = relative_path.lower().split("/")
    category_map = {
        "guide": "guide",
        "guides": "guide",
        "tutorial": "tutorial",
        "tutorials": "tutorial",
        "api": "api",
        "reference": "api",
        "examples": "examples",
        "example": "examples",
        "docs": "docs",
        "documentation": "docs",
        "learn": "guide",
        "start": "guide",
        "getting-started": "guide",
        "quickstart": "guide",
        "concepts": "docs",
        "overview": "docs",
    }
    for part in parts:
        cat = category_map.get(part)
        if cat:
            return cat
    return "docs"


def _path_suffix(path: str) -> str:
    dot = path.rfind(".")
    slash = path.rfind("/")
    if dot > slash:
        return path[dot:].lower()
    return ""
