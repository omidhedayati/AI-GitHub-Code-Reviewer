import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response

from app.api.deps import get_current_user, get_review_service
from app.models.review import ReviewType
from app.models.user import User
from app.schemas.analysis import ReviewResponse, ReviewStatus
from app.schemas.review_search import (
    ReviewSearchParams,
    ReviewSearchResponse,
    ReviewSearchSort,
)
from app.services.report_service import ReportFormat
from app.services.review_service import ReviewNotFoundError, ReviewService

router = APIRouter(prefix="/reviews")


@router.get("", response_model=ReviewSearchResponse)
def search_reviews(
    q: str | None = Query(default=None, min_length=1, max_length=200),
    repository_id: uuid.UUID | None = Query(default=None),
    review_type: ReviewType | None = Query(default=None),
    status: ReviewStatus | None = Query(default=None),
    severity: str | None = Query(default=None),
    min_score: float | None = Query(default=None, ge=0),
    max_score: float | None = Query(default=None, ge=0),
    from_date: str | None = Query(default=None, alias="from"),
    to_date: str | None = Query(default=None, alias="to"),
    sort: ReviewSearchSort = Query(default=ReviewSearchSort.CREATED_DESC),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    review_service: ReviewService = Depends(get_review_service),
) -> ReviewSearchResponse:
    from datetime import datetime

    parsed_from = datetime.fromisoformat(from_date) if from_date else None
    parsed_to = datetime.fromisoformat(to_date) if to_date else None
    params = ReviewSearchParams(
        q=q,
        repository_id=repository_id,
        review_type=review_type,
        status=status,
        severity=severity,
        min_score=min_score,
        max_score=max_score,
        from_date=parsed_from,
        to_date=parsed_to,
        sort=sort,
        offset=offset,
        limit=limit,
    )
    return review_service.search_reviews(current_user, params)


@router.get("/{review_id}/report")
def get_review_report(
    review_id: uuid.UUID,
    fmt: ReportFormat = Query(default=ReportFormat.MARKDOWN, alias="format"),
    download: bool = Query(default=False),
    current_user: User = Depends(get_current_user),
    review_service: ReviewService = Depends(get_review_service),
) -> Response:
    try:
        report = review_service.get_report(current_user, review_id, fmt)
    except ReviewNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=exc.message,
        ) from exc

    headers: dict[str, str] = {}
    if download:
        headers["Content-Disposition"] = f'attachment; filename="{report.filename}"'

    return Response(content=report.body, media_type=report.media_type, headers=headers)


@router.get("/{review_id}", response_model=ReviewResponse)
def get_review(
    review_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    review_service: ReviewService = Depends(get_review_service),
) -> ReviewResponse:
    try:
        return review_service.get_review(current_user, review_id)
    except ReviewNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=exc.message,
        ) from exc
