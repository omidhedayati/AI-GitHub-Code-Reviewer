from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import get_db_session, get_ollama_service, get_settings_dep
from app.config.settings import Settings
from app.schemas.ai_review import OllamaHealthResponse
from app.schemas.common import HealthResponse, ReadyResponse
from app.services.ollama_service import OllamaService

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    return HealthResponse(status="ok")


@router.get("/ready", response_model=ReadyResponse)
def readiness_check(
    db: Session = Depends(get_db_session),
) -> ReadyResponse:
    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unavailable",
        ) from exc
    return ReadyResponse(status="ready", database="connected")


@router.get("/health/ollama", response_model=OllamaHealthResponse)
def ollama_health_check(
    ollama_service: OllamaService = Depends(get_ollama_service),
    settings: Settings = Depends(get_settings_dep),
) -> OllamaHealthResponse:
    health = ollama_service.check_health()
    return OllamaHealthResponse(
        status="available" if health.available else "unavailable",
        model=settings.ollama_model,
        models_available=health.models_available,
        base_url=health.base_url,
    )
