import uuid
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from app.models.review import ReviewType
from app.schemas.analysis import ReviewStatus


class ReviewSearchSort(StrEnum):
    CREATED_DESC = "-created_at"
    CREATED_ASC = "created_at"
    SCORE_DESC = "-overall_score"
    SCORE_ASC = "overall_score"
    ISSUES_DESC = "-issues_count"
    ISSUES_ASC = "issues_count"


class ReviewSearchParams(BaseModel):
    q: str | None = None
    repository_id: uuid.UUID | None = None
    review_type: ReviewType | None = None
    status: ReviewStatus | None = None
    severity: str | None = None
    min_score: float | None = Field(default=None, ge=0)
    max_score: float | None = Field(default=None, ge=0)
    from_date: datetime | None = None
    to_date: datetime | None = None
    sort: ReviewSearchSort = ReviewSearchSort.CREATED_DESC
    offset: int = Field(default=0, ge=0)
    limit: int = Field(default=20, ge=1, le=100)


class ReviewHistoryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    repository_id: uuid.UUID
    repository_name: str
    review_type: ReviewType
    status: ReviewStatus
    overall_score: float
    issues_count: int
    files_analyzed: int
    summary: str | None
    ai_model: str | None = None
    created_at: datetime


class ReviewSearchResponse(BaseModel):
    items: list[ReviewHistoryItem]
    total: int
    offset: int
    limit: int
