import argparse
import json
import sys
from pathlib import Path

# Permite execução direta: python src/mcp_docs_server/search.py
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_docs_server.config import load_config
from mcp_docs_server.model import load_model
from mcp_docs_server.search_docs import handle_search_docs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Busca na documentação indexada via FAISS."
    )
    parser.add_argument("--technology", "-t", required=True, help="Tecnologia (ex: angular)")
    parser.add_argument("--version",    "-v", required=True, help="Versão (ex: 20, 20.1, 20.1.1)")
    parser.add_argument("--query",      "-q", required=True, help="Consulta em linguagem natural")
    parser.add_argument("--top-k",      "-k", type=int, default=5, help="Número de resultados (padrão: 5)")
    parser.add_argument("--json",       "-j", action="store_true", help="Saída em JSON bruto")
    return parser.parse_args()


def _print_results(result: dict) -> None:
    if "error" in result:
        print(f"Erro: {result['message']}", file=sys.stderr)
        sys.exit(1)

    print(f"technology : {result['technology']}")
    print(f"version    : {result['resolved_version']}")
    print(f"query      : {result['query']}")
    print(f"results    : {result['result_count']}")
    print()

    for i, r in enumerate(result["results"], 1):
        breadcrumb = " > ".join(r["breadcrumb"]) if r["breadcrumb"] else ""
        header = f"{breadcrumb} > {r['section']}" if breadcrumb else r["section"]

        print(f"[{i}] score={r['score']:.4f}  {r['document']}")
        print(f"     {header}")
        print()
        print(r["content"])
        print()
        print("─" * 72)
        print()


def main() -> None:
    args = parse_args()

    config = load_config()
    load_model(config.embedding_model)

    result = handle_search_docs(
        config,
        technology=args.technology,
        version=args.version,
        query=args.query,
        top_k=args.top_k,
    )

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        _print_results(result)


if __name__ == "__main__":
    main()
