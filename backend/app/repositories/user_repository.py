import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import GitHubProfile, User


class UserRepository:
    """Data access for user accounts."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def get_by_id(self, user_id: uuid.UUID) -> User | None:
        return self._db.get(User, user_id)

    def get_by_email(self, email: str) -> User | None:
        statement = select(User).where(User.email == email.lower())
        return self._db.scalar(statement)

    def get_by_github_id(self, github_id: int) -> User | None:
        statement = select(User).where(User.github_id == github_id)
        return self._db.scalar(statement)

    def create(
        self,
        *,
        email: str,
        hashed_password: str | None,
        full_name: str | None = None,
        auth_provider: str = "local",
        github_id: int | None = None,
        github_username: str | None = None,
        avatar_url: str | None = None,
    ) -> User:
        user = User(
            email=email.lower(),
            hashed_password=hashed_password,
            full_name=full_name,
            auth_provider=auth_provider,
            github_id=github_id,
            github_username=github_username,
            avatar_url=avatar_url,
        )
        self._db.add(user)
        self._db.commit()
        self._db.refresh(user)
        return user

    def link_github(self, user: User, profile: GitHubProfile) -> User:
        user.github_id = profile.github_id
        user.github_username = profile.username
        user.avatar_url = profile.avatar_url
        if profile.full_name and not user.full_name:
            user.full_name = profile.full_name
        if user.auth_provider == "local":
            user.auth_provider = "github"
        self._db.add(user)
        self._db.commit()
        self._db.refresh(user)
        return user

    def update_github_user(self, user: User, profile: GitHubProfile) -> User:
        user.email = profile.email
        user.github_username = profile.username
        user.avatar_url = profile.avatar_url
        if profile.full_name:
            user.full_name = profile.full_name
        user.auth_provider = "github"
        self._db.add(user)
        self._db.commit()
        self._db.refresh(user)
        return user
