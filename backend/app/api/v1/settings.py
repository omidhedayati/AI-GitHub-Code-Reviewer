from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_user, get_user_settings_service
from app.models.user import User
from app.schemas.user_settings import (
    OllamaUserHealthResponse,
    UserSettingsResponse,
    UserSettingsUpdate,
)
from app.services.user_settings_service import (
    InvalidSettingsError,
    UserSettingsService,
)

router = APIRouter(prefix="/settings")


@router.get("/me", response_model=UserSettingsResponse)
def get_my_settings(
    current_user: User = Depends(get_current_user),
    settings_service: UserSettingsService = Depends(get_user_settings_service),
) -> UserSettingsResponse:
    return settings_service.get_settings(current_user)


@router.put("/me", response_model=UserSettingsResponse)
def update_my_settings(
    data: UserSettingsUpdate,
    current_user: User = Depends(get_current_user),
    settings_service: UserSettingsService = Depends(get_user_settings_service),
) -> UserSettingsResponse:
    try:
        return settings_service.update_settings(current_user, data)
    except InvalidSettingsError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=exc.message,
        ) from exc


@router.get("/me/ollama-health", response_model=OllamaUserHealthResponse)
def get_my_ollama_health(
    current_user: User = Depends(get_current_user),
    settings_service: UserSettingsService = Depends(get_user_settings_service),
) -> OllamaUserHealthResponse:
    return settings_service.check_ollama_health(current_user)
