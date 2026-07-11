import ast
import re
from pathlib import Path

from app.services.analyzers.base import (
    AnalysisIssue,
    IssueCategory,
    IssueSeverity,
)
from app.services.analyzers.common import analyze_common_patterns

MAX_FUNCTION_LINES = 50
MAX_COMPLEXITY = 10
BAD_NAME_PATTERN = re.compile(r"^[a-z]$|^[a-z]{1,2}$")


class PythonAnalyzer:
    language = "python"

    def analyze(
        self, file_path: Path, content: str, relative_path: str
    ) -> list[AnalysisIssue]:
        issues = analyze_common_patterns(file_path, content, relative_path)
        try:
            tree = ast.parse(content, filename=relative_path)
        except SyntaxError as exc:
            issues.append(
                AnalysisIssue(
                    file_path=relative_path,
                    line_start=exc.lineno or 1,
                    line_end=exc.lineno or 1,
                    category=IssueCategory.BUG,
                    severity=IssueSeverity.HIGH,
                    confidence=0.99,
                    rule_id="python-syntax-error",
                    title="Python syntax error",
                    explanation=str(exc.msg or "Invalid Python syntax"),
                    suggestion="Fix the syntax error before running or deploying the code.",
                )
            )
            return issues

        issues.extend(self._analyze_tree(tree, relative_path))
        return issues

    def _analyze_tree(self, tree: ast.AST, relative_path: str) -> list[AnalysisIssue]:
        issues: list[AnalysisIssue] = []

        if isinstance(tree, ast.Module) and not ast.get_docstring(tree):
            issues.append(
                AnalysisIssue(
                    file_path=relative_path,
                    line_start=1,
                    line_end=1,
                    category=IssueCategory.MISSING_DOCUMENTATION,
                    severity=IssueSeverity.LOW,
                    confidence=0.7,
                    rule_id="missing-module-docstring",
                    title="Missing module docstring",
                    explanation="The Python module has no top-level docstring.",
                    suggestion="Add a module docstring describing the file purpose.",
                )
            )

        issues.extend(self._check_imports(tree, relative_path))
        issues.extend(self._check_functions_and_classes(tree, relative_path))
        issues.extend(self._check_security(tree, relative_path))
        return issues

    def _check_imports(self, tree: ast.AST, relative_path: str) -> list[AnalysisIssue]:
        imported: set[str] = set()
        used_names: set[str] = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported.add(alias.asname or alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    if alias.name != "*":
                        imported.add(alias.asname or alias.name)
            elif isinstance(node, ast.Name):
                used_names.add(node.id)

        unused = imported - used_names - {"__future__"}
        issues: list[AnalysisIssue] = []
        for name in sorted(unused):
            issues.append(
                AnalysisIssue(
                    file_path=relative_path,
                    line_start=1,
                    line_end=1,
                    category=IssueCategory.UNUSED_IMPORT,
                    severity=IssueSeverity.LOW,
                    confidence=0.6,
                    rule_id="unused-import",
                    title=f"Potentially unused import: {name}",
                    explanation=f"Import '{name}' may not be referenced in this module.",
                    suggestion="Remove unused imports to keep the module clean.",
                )
            )
        return issues

    def _check_functions_and_classes(
        self,
        tree: ast.AST,
        relative_path: str,
    ) -> list[AnalysisIssue]:
        issues: list[AnalysisIssue] = []

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name.startswith("_") and not node.name.startswith("__"):
                    continue
                if BAD_NAME_PATTERN.match(node.name):
                    issues.append(
                        AnalysisIssue(
                            file_path=relative_path,
                            line_start=node.lineno,
                            line_end=node.end_lineno,
                            category=IssueCategory.BAD_NAMING,
                            severity=IssueSeverity.LOW,
                            confidence=0.65,
                            rule_id="short-function-name",
                            title=f"Function name '{node.name}' is too short",
                            explanation="Very short names reduce code readability.",
                            suggestion="Use descriptive function names that explain intent.",
                        )
                    )

                body_lines = (node.end_lineno or node.lineno) - node.lineno + 1
                if body_lines > MAX_FUNCTION_LINES:
                    issues.append(
                        AnalysisIssue(
                            file_path=relative_path,
                            line_start=node.lineno,
                            line_end=node.end_lineno,
                            category=IssueCategory.LONG_METHOD,
                            severity=IssueSeverity.MEDIUM,
                            confidence=0.9,
                            rule_id="long-function",
                            title=f"Function '{node.name}' is too long",
                            explanation=(
                                f"Function spans approximately {body_lines} lines "
                                f"(threshold: {MAX_FUNCTION_LINES})."
                            ),
                            suggestion="Extract helper functions to reduce complexity.",
                        )
                    )

                if not ast.get_docstring(node) and not node.name.startswith("_"):
                    issues.append(
                        AnalysisIssue(
                            file_path=relative_path,
                            line_start=node.lineno,
                            line_end=node.lineno,
                            category=IssueCategory.MISSING_DOCUMENTATION,
                            severity=IssueSeverity.LOW,
                            confidence=0.75,
                            rule_id="missing-function-docstring",
                            title=f"Function '{node.name}' lacks a docstring",
                            explanation="Public functions should document behavior and parameters.",
                            suggestion="Add a docstring explaining what the function does.",
                        )
                    )

                complexity = self._calculate_complexity(node)
                if complexity > MAX_COMPLEXITY:
                    issues.append(
                        AnalysisIssue(
                            file_path=relative_path,
                            line_start=node.lineno,
                            line_end=node.end_lineno,
                            category=IssueCategory.COMPLEXITY,
                            severity=IssueSeverity.MEDIUM,
                            confidence=0.85,
                            rule_id="high-cyclomatic-complexity",
                            title=f"Function '{node.name}' has high complexity",
                            explanation=(
                                f"Estimated cyclomatic complexity is {complexity} "
                                f"(threshold: {MAX_COMPLEXITY})."
                            ),
                            suggestion="Reduce branching logic or split the function.",
                        )
                    )

            if isinstance(node, ast.ClassDef) and not ast.get_docstring(node):
                issues.append(
                    AnalysisIssue(
                        file_path=relative_path,
                        line_start=node.lineno,
                        line_end=node.lineno,
                        category=IssueCategory.MISSING_DOCUMENTATION,
                        severity=IssueSeverity.LOW,
                        confidence=0.7,
                        rule_id="missing-class-docstring",
                        title=f"Class '{node.name}' lacks a docstring",
                        explanation="Classes should describe their responsibility.",
                        suggestion="Add a class docstring summarizing purpose and usage.",
                    )
                )

        return issues

    def _check_security(self, tree: ast.AST, relative_path: str) -> list[AnalysisIssue]:
        issues: list[AnalysisIssue] = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = self._call_name(node.func)
                if func_name in {"eval", "exec"}:
                    issues.append(
                        AnalysisIssue(
                            file_path=relative_path,
                            line_start=node.lineno,
                            line_end=node.lineno,
                            category=IssueCategory.SECURITY,
                            severity=IssueSeverity.CRITICAL,
                            confidence=0.95,
                            rule_id="python-eval-exec",
                            title=f"Use of {func_name}() detected",
                            explanation=f"{func_name}() can execute arbitrary code.",
                            suggestion="Avoid dynamic code execution; use safe alternatives.",
                        )
                    )
                if func_name in {"subprocess.run", "subprocess.call"}:
                    for keyword in node.keywords:
                        if keyword.arg == "shell" and isinstance(
                            keyword.value, ast.Constant
                        ):
                            if keyword.value.value is True:
                                issues.append(
                                    AnalysisIssue(
                                        file_path=relative_path,
                                        line_start=node.lineno,
                                        line_end=node.lineno,
                                        category=IssueCategory.SECURITY,
                                        severity=IssueSeverity.HIGH,
                                        confidence=0.9,
                                        rule_id="subprocess-shell-true",
                                        title="subprocess invoked with shell=True",
                                        explanation="shell=True increases command injection risk.",
                                        suggestion="Use shell=False and pass arguments as a list.",
                                    )
                                )
        return issues

    def _calculate_complexity(self, node: ast.AST) -> int:
        complexity = 1
        for child in ast.walk(node):
            if isinstance(
                child,
                (
                    ast.If,
                    ast.For,
                    ast.AsyncFor,
                    ast.While,
                    ast.ExceptHandler,
                    ast.With,
                    ast.AsyncWith,
                ),
            ):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += max(len(child.values) - 1, 0)
        return complexity

    def _call_name(self, node: ast.AST) -> str:
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            return f"{self._call_name(node.value)}.{node.attr}"
        return ""
