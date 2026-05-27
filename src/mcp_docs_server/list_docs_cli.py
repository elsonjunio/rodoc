import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_docs_server.config import load_config
from mcp_docs_server.list_docs import handle_list_docs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Lista tecnologias e versões indexadas no vectorstore."
    )
    parser.add_argument("--technology", "-t", default=None, help="Filtrar por tecnologia (ex: angular)")
    parser.add_argument("--page",       "-p", type=int, default=1, help="Página (padrão: 1)")
    parser.add_argument("--page-size",  "-s", type=int, default=10, help="Itens por página (padrão: 10)")
    parser.add_argument("--json",       "-j", action="store_true", help="Saída em JSON bruto")
    return parser.parse_args()


def _print_results(result: dict) -> None:
    if "error" in result:
        print(f"Erro: {result['message']}", file=sys.stderr)
        sys.exit(1)

    techs = result.get("technologies", [])
    total_tech = result.get("total_technologies", len(techs))
    total_ver  = result.get("total_versions", 0)
    page       = result.get("page", 1)
    total_pages = result.get("total_pages", 1)

    print(f"tecnologias : {total_tech}  versões : {total_ver}  (página {page}/{total_pages})")
    print()

    for entry in techs:
        print(f"  {entry['technology']}")
        for v in entry["versions"]:
            chunks = v.get("chunk_count", "?")
            docs   = v.get("document_count", "?")
            date   = v.get("generated_at", "")[:10]
            print(f"    {v['version']:20s}  chunks={chunks}  docs={docs}  {date}")
        print()

    if result.get("has_next"):
        print(f"  (use --page {page + 1} para ver mais)")


def main() -> None:
    args = parse_args()

    config = load_config()
    result = handle_list_docs(config, args.technology, args.page, args.page_size)

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        _print_results(result)


if __name__ == "__main__":
    main()
