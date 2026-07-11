import uuid

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_analysis_service, get_current_user
from app.models.user import User
from app.schemas.analysis import ReviewResponse
from app.services.analysis_service import AnalysisService, ReviewNotFoundError

router = APIRouter(prefix="/reviews")


@router.get("/{review_id}", response_model=ReviewResponse)
def get_review(
    review_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    analysis_service: AnalysisService = Depends(get_analysis_service),
) -> ReviewResponse:
    try:
        return analysis_service.get_review(current_user, review_id)
    except ReviewNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=exc.message,
        ) from exc
