import logging
import sys
import threading

from mcp.server.fastmcp import FastMCP

from .config import ServerConfig, load_config
from .list_docs import handle_list_docs
from .model import load_model
from .search_docs import handle_search_docs

logger = logging.getLogger(__name__)

mcp = FastMCP(
    "local-docs",
    instructions=(
        "Search indexed technical documentation by technology and version. "
        "First call list_docs (page=1) to discover available technologies and versions. "
        "Then call search_docs with the exact technology name and version. "
        "Version resolution is semantic: '20' matches '20.x.y', '20.1' matches '20.1.x'. "
        "Cross-major fallback never happens. "
        "If list_docs returns has_next=true, paginate with page=2, 3, … to see all technologies."
    ),
)

_config: ServerConfig | None = None
_init_lock = threading.Lock()


def _get_config() -> ServerConfig:
    global _config
    if _config is not None:
        return _config
    with _init_lock:
        if _config is None:
            cfg = load_config()
            load_model(cfg.embedding_model)
            _config = cfg
    return _config


@mcp.tool()
def list_docs(
    technology: str | None = None,
    page: int = 1,
    page_size: int = 10,
) -> dict:
    """List all indexed technologies and their available versions.

    Use this to discover what documentation is available before calling search_docs.
    Results are paginated — if has_next is true, call again with page+1.

    Args:
        technology: Optional filter. When provided, returns only that technology's versions.
        page: Page number, 1-indexed (default 1).
        page_size: Technologies per page, 1–50 (default 10).
    """
    try:
        config = _get_config()
        return handle_list_docs(config, technology, page, page_size)
    except Exception as e:
        logger.exception("list_docs error")
        return {"error": "internal_error", "message": str(e)}


@mcp.tool()
def search_docs(technology: str, version: str, query: str, top_k: int = 5) -> dict:
    """Search indexed technical documentation for a specific technology and version.

    Args:
        technology: Technology name, e.g. 'angular', 'react', 'vue', 'nextjs'
        version: Version string — supports partial versions: '20', '20.1', '20.1.1'.
                 Resolves to the closest compatible version within the same major.
        query: Natural language search query describing the feature or concept
        top_k: Number of results to return (1–20, default 5)
    """
    top_k = min(max(1, top_k), 20)
    try:
        config = _get_config()
        return handle_search_docs(config, technology, version, query, top_k)
    except Exception as e:
        logger.exception("search_docs error")
        return {"error": "internal_error", "message": str(e)}


def main() -> None:
    # MCP uses stdout for protocol messages; all logs must go to stderr
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        stream=sys.stderr,
    )
    mcp.run()
