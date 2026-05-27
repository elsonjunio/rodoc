import sys
from pathlib import Path

# Ensure src/ is on sys.path so sibling packages (extractor, index, etc.) are importable
_src = str(Path(__file__).parent.parent)
if _src not in sys.path:
    sys.path.insert(0, _src)

from mcp_docs_server.server import main

main()
