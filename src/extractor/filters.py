from pathlib import Path

IGNORED_DIRS: frozenset[str] = frozenset({
    "node_modules", "dist", "build", "coverage", "vendor",
    ".git", ".next", ".cache", "target", "out",
})

IGNORED_FILES: frozenset[str] = frozenset({
    "package-lock.json", "yarn.lock", "pnpm-lock.yaml",
})

SUPPORTED_EXTENSIONS: frozenset[str] = frozenset({".md", ".mdx", ".txt"})


def is_ignored_directory(path: Path) -> bool:
    return path.name in IGNORED_DIRS


def is_ignored_file(path: Path) -> bool:
    return path.name in IGNORED_FILES


def has_supported_extension(path: Path) -> bool:
    return path.suffix.lower() in SUPPORTED_EXTENSIONS


def is_binary_file(path: Path) -> bool:
    try:
        with path.open("rb") as f:
            return b"\x00" in f.read(8192)
    except OSError:
        return True


def is_valid_document(path: Path) -> bool:
    return (
        has_supported_extension(path)
        and not is_ignored_file(path)
        and not is_binary_file(path)
    )
