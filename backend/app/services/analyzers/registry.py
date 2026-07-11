from pathlib import Path
from typing import Protocol

from app.services.analyzers.base import AnalysisIssue
from app.services.analyzers.python_analyzer import PythonAnalyzer
from app.services.analyzers.regex_analyzer import (
    CppAnalyzer,
    CSharpAnalyzer,
    GoAnalyzer,
    JavaAnalyzer,
    JavaScriptAnalyzer,
    RustAnalyzer,
    TypeScriptAnalyzer,
)
from app.utils.file_walker import detect_language


class LanguageAnalyzer(Protocol):
    language: str

    def analyze(
        self,
        file_path: Path,
        content: str,
        relative_path: str,
    ) -> list[AnalysisIssue]: ...


_ANALYZERS: dict[str, LanguageAnalyzer] = {
    "python": PythonAnalyzer(),
    "javascript": JavaScriptAnalyzer(),
    "typescript": TypeScriptAnalyzer(),
    "java": JavaAnalyzer(),
    "go": GoAnalyzer(),
    "rust": RustAnalyzer(),
    "csharp": CSharpAnalyzer(),
    "cpp": CppAnalyzer(),
}


def get_analyzer_for_file(file_path: Path) -> LanguageAnalyzer | None:
    language = detect_language(file_path)
    if language is None:
        return None
    return _ANALYZERS.get(language)


def analyze_file(
    file_path: Path,
    content: str,
    relative_path: str,
) -> list[AnalysisIssue]:
    analyzer = get_analyzer_for_file(file_path)
    if analyzer is None:
        return []
    return analyzer.analyze(file_path, content, relative_path)
