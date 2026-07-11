import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import (
    get_ai_review_service,
    get_analysis_service,
    get_current_user,
    get_repository_service,
)
from app.models.review import ReviewType
from app.models.user import User
from app.schemas.analysis import ReviewListResponse, ReviewResponse
from app.schemas.repository import (
    RepositoryCreate,
    RepositoryListResponse,
    RepositoryResponse,
)
from app.services.ai_review_service import (
    AIReviewService,
    AIReviewServiceError,
    OllamaNotReadyError,
)
from app.services.ai_review_service import (
    RepositoryNotReadyError as AIRepositoryNotReadyError,
)
from app.services.ai_review_service import (
    ReviewNotFoundError as AIReviewNotFoundError,
)
from app.services.analysis_service import (
    AnalysisService,
    AnalysisServiceError,
    RepositoryNotReadyError,
    ReviewNotFoundError,
)
from app.services.repository_service import (
    DuplicateRepositoryError,
    InvalidRepositoryURLError,
    RepositoryNotFoundError,
    RepositoryService,
)

router = APIRouter(prefix="/repositories")


@router.get("", response_model=RepositoryListResponse)
def list_repositories(
    current_user: User = Depends(get_current_user),
    repository_service: RepositoryService = Depends(get_repository_service),
) -> RepositoryListResponse:
    items = repository_service.list_repositories(current_user)
    return RepositoryListResponse(items=items, total=len(items))


@router.post("", response_model=RepositoryResponse, status_code=status.HTTP_201_CREATED)
def clone_repository(
    data: RepositoryCreate,
    current_user: User = Depends(get_current_user),
    repository_service: RepositoryService = Depends(get_repository_service),
) -> RepositoryResponse:
    try:
        return repository_service.clone_repository(current_user, data)
    except InvalidRepositoryURLError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=exc.message,
        ) from exc
    except DuplicateRepositoryError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=exc.message,
        ) from exc


@router.get("/{repository_id}", response_model=RepositoryResponse)
def get_repository(
    repository_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    repository_service: RepositoryService = Depends(get_repository_service),
) -> RepositoryResponse:
    try:
        return repository_service.get_repository(current_user, repository_id)
    except RepositoryNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=exc.message,
        ) from exc


@router.delete("/{repository_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_repository(
    repository_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    repository_service: RepositoryService = Depends(get_repository_service),
) -> None:
    try:
        repository_service.delete_repository(current_user, repository_id)
    except RepositoryNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=exc.message,
        ) from exc


@router.post(
    "/{repository_id}/analyze",
    response_model=ReviewResponse,
    status_code=status.HTTP_201_CREATED,
)
def analyze_repository(
    repository_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    analysis_service: AnalysisService = Depends(get_analysis_service),
) -> ReviewResponse:
    try:
        return analysis_service.analyze_repository(current_user, repository_id)
    except ReviewNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=exc.message,
        ) from exc
    except RepositoryNotReadyError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=exc.message,
        ) from exc
    except AnalysisServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=exc.message,
        ) from exc


@router.post(
    "/{repository_id}/ai-review",
    response_model=ReviewResponse,
    status_code=status.HTTP_201_CREATED,
)
def run_ai_review(
    repository_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    ai_review_service: AIReviewService = Depends(get_ai_review_service),
) -> ReviewResponse:
    try:
        return ai_review_service.run_ai_review(current_user, repository_id)
    except AIReviewNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=exc.message,
        ) from exc
    except AIRepositoryNotReadyError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=exc.message,
        ) from exc
    except OllamaNotReadyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=exc.message,
        ) from exc
    except AIReviewServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=exc.message,
        ) from exc


@router.get("/{repository_id}/reviews", response_model=ReviewListResponse)
def list_repository_reviews(
    repository_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    analysis_service: AnalysisService = Depends(get_analysis_service),
) -> ReviewListResponse:
    try:
        items = analysis_service.list_reviews(current_user, repository_id)
        return ReviewListResponse(items=items, total=len(items))
    except ReviewNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=exc.message,
        ) from exc


@router.get("/{repository_id}/reviews/latest", response_model=ReviewResponse)
def get_latest_repository_review(
    repository_id: uuid.UUID,
    review_type: ReviewType | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    analysis_service: AnalysisService = Depends(get_analysis_service),
) -> ReviewResponse:
    try:
        review = analysis_service.get_latest_review(
            current_user,
            repository_id,
            review_type=review_type,
        )
    except ReviewNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=exc.message,
        ) from exc
    if review is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No reviews found for this repository",
        )
    return review
