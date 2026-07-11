from pathlib import Path

from app.config.settings import Settings

SUPPORTED_EXTENSIONS: dict[str, str] = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".java": "java",
    ".go": "go",
    ".rs": "rust",
    ".cs": "csharp",
    ".cpp": "cpp",
    ".cc": "cpp",
    ".cxx": "cpp",
    ".hpp": "cpp",
    ".h": "cpp",
    ".c": "cpp",
}


def detect_language(file_path: Path) -> str | None:
    return SUPPORTED_EXTENSIONS.get(file_path.suffix.lower())


def should_analyze_file(
    file_path: Path,
    repository_root: Path,
    settings: Settings,
) -> bool:
    if not file_path.is_file():
        return False

    try:
        relative = file_path.relative_to(repository_root)
    except ValueError:
        return False

    if any(part in settings.ignored_folders_list for part in relative.parts):
        return False

    suffix = file_path.suffix.lower()
    if suffix in {ext.lower() for ext in settings.ignored_extensions_list}:
        return False

    if detect_language(file_path) is None:
        return False

    try:
        if file_path.stat().st_size > settings.max_file_size_bytes:
            return False
    except OSError:
        return False

    return True


def iter_analyzable_files(
    repository_root: Path,
    settings: Settings,
) -> list[Path]:
    files: list[Path] = []
    for path in repository_root.rglob("*"):
        if should_analyze_file(path, repository_root, settings):
            files.append(path)
    return sorted(files)
