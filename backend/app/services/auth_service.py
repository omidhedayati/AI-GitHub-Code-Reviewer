import uuid

from app.config.settings import Settings
from app.models.user import GitHubProfile, User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import (
    AuthResponse,
    TokenResponse,
    UserCreate,
    UserLogin,
    UserResponse,
)
from app.utils.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


class AuthServiceError(Exception):
    """Base class for authentication service errors."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class DuplicateEmailError(AuthServiceError):
    pass


class InvalidCredentialsError(AuthServiceError):
    pass


class InactiveUserError(AuthServiceError):
    pass


class InvalidTokenError(AuthServiceError):
    pass


class OAuthNotConfiguredError(AuthServiceError):
    pass


class OAuthExchangeError(AuthServiceError):
    pass


class AuthService:
    """Authentication and token management."""

    def __init__(
        self,
        user_repository: UserRepository,
        settings: Settings,
    ) -> None:
        self._users = user_repository
        self._settings = settings

    def register(self, data: UserCreate) -> AuthResponse:
        if self._users.get_by_email(data.email):
            raise DuplicateEmailError("Email already registered")

        user = self._users.create(
            email=data.email,
            hashed_password=hash_password(data.password),
            full_name=data.full_name,
        )
        tokens = self._build_tokens(user.id)
        return AuthResponse(
            user=UserResponse.model_validate(user),
            tokens=tokens,
        )

    def login(self, data: UserLogin) -> AuthResponse:
        user = self._users.get_by_email(data.email)
        if user is None or not verify_password(data.password, user.hashed_password):
            raise InvalidCredentialsError("Invalid email or password")
        if not user.is_active:
            raise InactiveUserError("Account is inactive")

        tokens = self._build_tokens(user.id)
        return AuthResponse(
            user=UserResponse.model_validate(user),
            tokens=tokens,
        )

    def refresh_tokens(self, refresh_token: str) -> TokenResponse:
        try:
            payload = decode_token(refresh_token, self._settings)
        except ValueError as exc:
            raise InvalidTokenError("Invalid refresh token") from exc

        if payload["type"] != "refresh":
            raise InvalidTokenError("Invalid refresh token")

        user_id = uuid.UUID(payload["sub"])
        user = self._users.get_by_id(user_id)
        if user is None or not user.is_active:
            raise InvalidTokenError("Invalid refresh token")

        return self._build_tokens(user.id)

    def get_user_by_id(self, user_id: uuid.UUID) -> User:
        user = self._users.get_by_id(user_id)
        if user is None:
            raise InvalidCredentialsError("User not found")
        if not user.is_active:
            raise InactiveUserError("Account is inactive")
        return user

    def authenticate_github(self, profile: GitHubProfile) -> User:
        existing_github = self._users.get_by_github_id(profile.github_id)
        if existing_github is not None:
            return self._users.update_github_user(existing_github, profile)

        existing_email = self._users.get_by_email(profile.email)
        if existing_email is not None:
            return self._users.link_github(existing_email, profile)

        return self._users.create(
            email=profile.email,
            hashed_password=None,
            full_name=profile.full_name,
            auth_provider="github",
            github_id=profile.github_id,
            github_username=profile.username,
            avatar_url=profile.avatar_url,
        )

    def build_auth_response(self, user: User) -> AuthResponse:
        if not user.is_active:
            raise InactiveUserError("Account is inactive")
        tokens = self._build_tokens(user.id)
        return AuthResponse(
            user=UserResponse.model_validate(user),
            tokens=tokens,
        )

    def exchange_github_code(self, exchange_token: str) -> AuthResponse:
        from app.utils.security import decode_oauth_exchange_token

        try:
            user_id = decode_oauth_exchange_token(exchange_token, self._settings)
        except ValueError as exc:
            raise OAuthExchangeError("Invalid or expired GitHub login") from exc

        user = self.get_user_by_id(user_id)
        return self.build_auth_response(user)

    def _build_tokens(self, user_id: uuid.UUID) -> TokenResponse:
        return TokenResponse(
            access_token=create_access_token(user_id, self._settings),
            refresh_token=create_refresh_token(user_id, self._settings),
        )
