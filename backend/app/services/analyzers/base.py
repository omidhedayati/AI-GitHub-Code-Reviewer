from dataclasses import dataclass
from enum import StrEnum


class IssueCategory(StrEnum):
    BUG = "bug"
    DUPLICATED_CODE = "duplicated_code"
    LONG_METHOD = "long_method"
    BAD_NAMING = "bad_naming"
    SECURITY = "security"
    CODE_SMELL = "code_smell"
    DEAD_CODE = "dead_code"
    COMPLEXITY = "complexity"
    MISSING_DOCUMENTATION = "missing_documentation"
    UNUSED_IMPORT = "unused_import"


class IssueSeverity(StrEnum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass(frozen=True)
class AnalysisIssue:
    file_path: str
    line_start: int
    line_end: int | None
    category: IssueCategory
    severity: IssueSeverity
    confidence: float
    rule_id: str
    title: str
    explanation: str
    suggestion: str

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")
