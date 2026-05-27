import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

_CONFIG_FILENAME = "rodoc.json"
_DEFAULT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


@dataclass(frozen=True)
class ServerConfig:
    vectorstore_path: Path
    embedding_model: str


def _find_config_file() -> Path | None:
    # Walk up from CWD (max 5 levels)
    current = Path.cwd()
    for _ in range(5):
        candidate = current / _CONFIG_FILENAME
        if candidate.exists():
            logger.debug("Config file found: %s", candidate)
            return candidate
        if current == current.parent:
            break
        current = current.parent

    # Fallback: ~/.config/rodoc/rodoc.json
    fallback = Path.home() / ".config" / "rodoc" / _CONFIG_FILENAME
    if fallback.exists():
        return fallback

    return None


def load_config() -> ServerConfig:
    # VECTORSTORE_PATH env var takes precedence (set by OpenCode or the user)
    if vs_env := os.environ.get("VECTORSTORE_PATH"):
        model = os.environ.get("EMBEDDING_MODEL", _DEFAULT_MODEL)
        logger.info("Config from env  vectorstore=%s  model=%s", vs_env, model)
        return ServerConfig(vectorstore_path=Path(vs_env), embedding_model=model)

    config_file = _find_config_file()
    if config_file is None:
        raise RuntimeError(
            f"No configuration found. "
            f"Create '{_CONFIG_FILENAME}' in the project root or set the "
            f"VECTORSTORE_PATH environment variable."
        )

    data = json.loads(config_file.read_text(encoding="utf-8"))

    if "vectorstore_path" not in data:
        raise RuntimeError(f"'vectorstore_path' key missing in {config_file}")

    config = ServerConfig(
        vectorstore_path=Path(data["vectorstore_path"]),
        embedding_model=data.get("embedding_model", _DEFAULT_MODEL),
    )
    logger.info(
        "Config loaded from %s  vectorstore=%s  model=%s",
        config_file,
        config.vectorstore_path,
        config.embedding_model,
    )
    return config
