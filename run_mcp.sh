#!/usr/bin/env bash
set -euo pipefail

DIR="$(dirname "$(readlink -f "$0")")"
VENV="$DIR/.venv"
PYTHON="$VENV/bin/python"

if [ ! -d "$VENV" ]; then
    echo "venv não encontrado em $VENV" >&2
    echo "Execute: python3 -m venv .venv && .venv/bin/pip install -r requirements.txt" >&2
    exit 1
fi

export PYTHONPATH="$DIR/src${PYTHONPATH:+:$PYTHONPATH}"

cd $DIR

exec "$PYTHON" "$DIR/src/mcp_docs_server" "$@"