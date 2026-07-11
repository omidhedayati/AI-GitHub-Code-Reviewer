import uuid

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_user, get_repository_service
from app.models.user import User
from app.schemas.repository import (
    RepositoryCreate,
    RepositoryListResponse,
    RepositoryResponse,
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
