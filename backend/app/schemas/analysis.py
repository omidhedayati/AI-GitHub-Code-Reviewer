import uuid
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class ReviewStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


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


class ReviewIssueResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    file_path: str
    line_start: int
    line_end: int | None
    category: IssueCategory
    severity: IssueSeverity
    confidence: float = Field(ge=0.0, le=1.0)
    rule_id: str
    title: str
    explanation: str
    suggestion: str


class FileAnalysisResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    file_path: str
    language: str
    line_count: int
    issues_count: int
    file_score: float


class ReviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    repository_id: uuid.UUID
    user_id: uuid.UUID
    status: ReviewStatus
    files_analyzed: int
    issues_count: int
    overall_score: float
    summary: str | None
    error_message: str | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    issues: list[ReviewIssueResponse] = Field(default_factory=list)
    file_results: list[FileAnalysisResponse] = Field(default_factory=list)


class ReviewListResponse(BaseModel):
    items: list[ReviewResponse]
    total: int
