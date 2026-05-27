from datetime import datetime, timezone


def build_metadata(
    technology: str,
    version: str,
    model_name: str,
    chunk_count: int,
    dimension: int,
    document_count: int,
) -> dict:
    return {
        "technology": technology,
        "version": version,
        "embedding_model": model_name,
        "chunk_count": chunk_count,
        "document_count": document_count,
        "dimension": dimension,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
