import uuid
from collections.abc import Generator

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.config.settings import Settings, get_settings
from app.db.session import get_db
from app.models.user import User
from app.repositories.repository_repository import RepositoryRepository
from app.repositories.review_repository import ReviewRepository
from app.repositories.user_repository import UserRepository
from app.repositories.user_settings_repository import UserSettingsRepository
from app.services.ai_review_service import AIReviewService
from app.services.analysis_service import AnalysisService
from app.services.auth_service import AuthService, AuthServiceError
from app.services.git_service import GitService
from app.services.ollama_service import OllamaService
from app.services.repository_service import RepositoryService
from app.services.review_service import ReviewService
from app.services.user_settings_service import UserSettingsService
from app.utils.security import decode_token

security_scheme = HTTPBearer(auto_error=False)


def get_settings_dep() -> Settings:
    return get_settings()


def get_db_session() -> Generator[Session, None, None]:
    yield from get_db()


def get_user_repository(
    db: Session = Depends(get_db_session),
) -> UserRepository:
    return UserRepository(db)


def get_auth_service(
    user_repository: UserRepository = Depends(get_user_repository),
    settings: Settings = Depends(get_settings_dep),
) -> AuthService:
    return AuthService(user_repository, settings)


def get_repository_repository(
    db: Session = Depends(get_db_session),
) -> RepositoryRepository:
    return RepositoryRepository(db)


def get_git_service(settings: Settings = Depends(get_settings_dep)) -> GitService:
    return GitService(settings)


def get_repository_service(
    repository_repository: RepositoryRepository = Depends(get_repository_repository),
    git_service: GitService = Depends(get_git_service),
) -> RepositoryService:
    return RepositoryService(repository_repository, git_service)


def get_review_repository(
    db: Session = Depends(get_db_session),
) -> ReviewRepository:
    return ReviewRepository(db)


def get_user_settings_repository(
    db: Session = Depends(get_db_session),
) -> UserSettingsRepository:
    return UserSettingsRepository(db)


def get_user_settings_service(
    repository: UserSettingsRepository = Depends(get_user_settings_repository),
    settings: Settings = Depends(get_settings_dep),
) -> UserSettingsService:
    return UserSettingsService(repository, settings)


def get_analysis_service(
    repository_repository: RepositoryRepository = Depends(get_repository_repository),
    review_repository: ReviewRepository = Depends(get_review_repository),
    user_settings_service: UserSettingsService = Depends(get_user_settings_service),
) -> AnalysisService:
    return AnalysisService(
        repository_repository,
        review_repository,
        get_settings(),
        user_settings_service,
    )


def get_ollama_service(settings: Settings = Depends(get_settings_dep)) -> OllamaService:
    from app.config.analysis_config import AnalysisConfig

    return OllamaService(AnalysisConfig.from_app_settings(settings))


def get_ai_review_service(
    repository_repository: RepositoryRepository = Depends(get_repository_repository),
    review_repository: ReviewRepository = Depends(get_review_repository),
    user_settings_service: UserSettingsService = Depends(get_user_settings_service),
    settings: Settings = Depends(get_settings_dep),
) -> AIReviewService:
    return AIReviewService(
        repository_repository,
        review_repository,
        user_settings_service,
        settings,
    )


def get_review_service(
    review_repository: ReviewRepository = Depends(get_review_repository),
    repository_repository: RepositoryRepository = Depends(get_repository_repository),
) -> ReviewService:
    return ReviewService(review_repository, repository_repository)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security_scheme),
    auth_service: AuthService = Depends(get_auth_service),
    settings: Settings = Depends(get_settings_dep),
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = decode_token(credentials.credentials, settings)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    if payload["type"] != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_id = uuid.UUID(payload["sub"])
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    try:
        return auth_service.get_user_by_id(user_id)
    except AuthServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=exc.message,
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


SettingsDep = Depends(get_settings_dep)
DbSessionDep = Depends(get_db_session)
