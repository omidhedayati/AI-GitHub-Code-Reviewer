from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse

from app.api.deps import get_auth_service, get_current_user, get_github_oauth_service
from app.config.settings import Settings, get_settings
from app.models.user import User
from app.schemas.auth import (
    AuthResponse,
    GitHubExchangeRequest,
    TokenRefresh,
    TokenResponse,
    UserCreate,
    UserLogin,
    UserResponse,
)
from app.services.auth_service import (
    AuthService,
    DuplicateEmailError,
    InactiveUserError,
    InvalidCredentialsError,
    InvalidTokenError,
    OAuthExchangeError,
)
from app.services.github_oauth_service import GitHubOAuthError, GitHubOAuthService
from app.utils.security import (
    create_oauth_exchange_token,
    create_oauth_state_token,
    verify_oauth_state_token,
)

router = APIRouter(prefix="/auth")


def _ensure_github_oauth_configured(
    github_oauth: GitHubOAuthService,
) -> None:
    if not github_oauth.is_configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="GitHub OAuth is not configured",
        )


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    data: UserCreate,
    auth_service: AuthService = Depends(get_auth_service),
) -> AuthResponse:
    try:
        return auth_service.register(data)
    except DuplicateEmailError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=exc.message,
        ) from exc


@router.post("/login", response_model=AuthResponse)
def login(
    data: UserLogin,
    auth_service: AuthService = Depends(get_auth_service),
) -> AuthResponse:
    try:
        return auth_service.login(data)
    except InvalidCredentialsError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=exc.message,
        ) from exc
    except InactiveUserError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=exc.message,
        ) from exc


@router.get("/github/login")
def github_login(
    github_oauth: GitHubOAuthService = Depends(get_github_oauth_service),
    settings: Settings = Depends(get_settings),
) -> RedirectResponse:
    _ensure_github_oauth_configured(github_oauth)
    state = create_oauth_state_token(settings)
    return RedirectResponse(github_oauth.build_authorize_url(state), status_code=302)


@router.get("/github/callback")
def github_callback(
    code: str | None = Query(default=None),
    state: str | None = Query(default=None),
    error: str | None = Query(default=None),
    auth_service: AuthService = Depends(get_auth_service),
    github_oauth: GitHubOAuthService = Depends(get_github_oauth_service),
    settings: Settings = Depends(get_settings),
) -> RedirectResponse:
    _ensure_github_oauth_configured(github_oauth)
    frontend_callback = f"{settings.frontend_url.rstrip('/')}/auth/github/callback"

    if error:
        params = urlencode({"error": error})
        return RedirectResponse(f"{frontend_callback}?{params}", status_code=302)

    if not code or not state:
        params = urlencode({"error": "missing_code"})
        return RedirectResponse(f"{frontend_callback}?{params}", status_code=302)

    try:
        verify_oauth_state_token(state, settings)
        profile = github_oauth.fetch_profile(code)
        user = auth_service.authenticate_github(profile)
        exchange_token = create_oauth_exchange_token(user.id, settings)
    except (GitHubOAuthError, ValueError) as exc:
        message = exc.message if isinstance(exc, GitHubOAuthError) else "invalid_state"
        params = urlencode({"error": message})
        return RedirectResponse(f"{frontend_callback}?{params}", status_code=302)

    params = urlencode({"code": exchange_token})
    return RedirectResponse(f"{frontend_callback}?{params}", status_code=302)


@router.post("/github/exchange", response_model=AuthResponse)
def github_exchange(
    data: GitHubExchangeRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> AuthResponse:
    try:
        return auth_service.exchange_github_code(data.code)
    except OAuthExchangeError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=exc.message,
        ) from exc
    except InactiveUserError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=exc.message,
        ) from exc


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(
    data: TokenRefresh,
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    try:
        return auth_service.refresh_tokens(data.refresh_token)
    except InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=exc.message,
        ) from exc


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)) -> User:
    return current_user
