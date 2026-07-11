import hashlib
import re
from collections import defaultdict
from pathlib import Path

from app.services.analyzers.base import (
    AnalysisIssue,
    IssueCategory,
    IssueSeverity,
)

SECRET_PATTERNS: list[tuple[str, re.Pattern[str], IssueSeverity, str]] = [
    (
        "hardcoded-api-key",
        re.compile(
            r"(?i)(api[_-]?key|secret|password|token)\s*[:=]\s*['\"][^'\"]{8,}['\"]"
        ),
        IssueSeverity.HIGH,
        "Possible hardcoded secret",
    ),
    (
        "aws-access-key",
        re.compile(r"AKIA[0-9A-Z]{16}"),
        IssueSeverity.CRITICAL,
        "Possible AWS access key",
    ),
]

TODO_PATTERN = re.compile(r"\b(TODO|FIXME|HACK|XXX)\b")
LONG_LINE_THRESHOLD = 120


def analyze_common_patterns(
    file_path: Path,
    content: str,
    relative_path: str,
) -> list[AnalysisIssue]:
    issues: list[AnalysisIssue] = []
    lines = content.splitlines()

    for index, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        if len(line) > LONG_LINE_THRESHOLD:
            issues.append(
                AnalysisIssue(
                    file_path=relative_path,
                    line_start=index,
                    line_end=index,
                    category=IssueCategory.CODE_SMELL,
                    severity=IssueSeverity.LOW,
                    confidence=0.9,
                    rule_id="long-line",
                    title="Line exceeds recommended length",
                    explanation=(
                        f"Line {index} has {len(line)} characters "
                        f"(threshold: {LONG_LINE_THRESHOLD})."
                    ),
                    suggestion="Break the line into smaller, readable segments.",
                )
            )

        if TODO_PATTERN.search(line):
            issues.append(
                AnalysisIssue(
                    file_path=relative_path,
                    line_start=index,
                    line_end=index,
                    category=IssueCategory.CODE_SMELL,
                    severity=IssueSeverity.INFO,
                    confidence=0.95,
                    rule_id="todo-comment",
                    title="Unresolved TODO marker",
                    explanation=f"Line {index} contains a TODO/FIXME marker.",
                    suggestion="Resolve or track the TODO in your issue tracker.",
                )
            )

        for rule_id, pattern, severity, title in SECRET_PATTERNS:
            if pattern.search(line):
                issues.append(
                    AnalysisIssue(
                        file_path=relative_path,
                        line_start=index,
                        line_end=index,
                        category=IssueCategory.SECURITY,
                        severity=severity,
                        confidence=0.85,
                        rule_id=rule_id,
                        title=title,
                        explanation=(
                            "Potential secret detected in source code. "
                            "Secrets in repositories can be exposed publicly."
                        ),
                        suggestion=(
                            "Move secrets to environment variables or a secret manager."
                        ),
                    )
                )

    if len(lines) > 500:
        issues.append(
            AnalysisIssue(
                file_path=relative_path,
                line_start=1,
                line_end=len(lines),
                category=IssueCategory.COMPLEXITY,
                severity=IssueSeverity.MEDIUM,
                confidence=0.8,
                rule_id="large-file",
                title="File is very large",
                explanation=f"File contains {len(lines)} lines.",
                suggestion="Split the file into smaller modules or components.",
            )
        )

    return issues


def detect_duplicated_blocks(
    file_contents: dict[str, str],
    *,
    min_lines: int = 4,
) -> list[AnalysisIssue]:
    block_map: dict[str, list[tuple[str, int]]] = defaultdict(list)
    issues: list[AnalysisIssue] = []

    for relative_path, content in file_contents.items():
        lines = [line.strip() for line in content.splitlines()]
        for start in range(len(lines) - min_lines + 1):
            block = lines[start : start + min_lines]
            if not any(block):
                continue
            if all(
                not line or line.startswith("//") or line.startswith("#")
                for line in block
            ):
                continue
            digest = hashlib.sha256("\n".join(block).encode("utf-8")).hexdigest()
            block_map[digest].append((relative_path, start + 1))

    for locations in block_map.values():
        if len(locations) < 2:
            continue
        first_path, first_line = locations[0]
        duplicate_paths = [
            loc for loc in locations[1:] if loc[0] != first_path or loc[1] != first_line
        ]
        if not duplicate_paths:
            continue
        other_path, other_line = duplicate_paths[0]
        issues.append(
            AnalysisIssue(
                file_path=first_path,
                line_start=first_line,
                line_end=first_line + min_lines - 1,
                category=IssueCategory.DUPLICATED_CODE,
                severity=IssueSeverity.MEDIUM,
                confidence=0.75,
                rule_id="duplicated-block",
                title="Duplicated code block detected",
                explanation=(
                    f"Similar {min_lines}-line block found in {other_path} "
                    f"starting at line {other_line}."
                ),
                suggestion="Extract shared logic into a reusable function or module.",
            )
        )

    return issues
