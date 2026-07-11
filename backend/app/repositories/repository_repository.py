import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.repository import Repository, RepositoryStatus


class RepositoryRepository:
    """Data access for cloned repositories."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def create(
        self,
        *,
        user_id: uuid.UUID,
        url: str,
        owner: str,
        name: str,
        status: RepositoryStatus = RepositoryStatus.PENDING,
    ) -> Repository:
        repository = Repository(
            user_id=user_id,
            url=url,
            owner=owner,
            name=name,
            status=status.value,
        )
        self._db.add(repository)
        self._db.commit()
        self._db.refresh(repository)
        return repository

    def get_by_id(self, repository_id: uuid.UUID) -> Repository | None:
        return self._db.get(Repository, repository_id)

    def get_by_id_for_user(
        self,
        repository_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> Repository | None:
        statement = select(Repository).where(
            Repository.id == repository_id,
            Repository.user_id == user_id,
        )
        return self._db.scalar(statement)

    def list_by_user(self, user_id: uuid.UUID) -> list[Repository]:
        statement = (
            select(Repository)
            .where(Repository.user_id == user_id)
            .order_by(Repository.created_at.desc())
        )
        return list(self._db.scalars(statement).all())

    def get_by_owner_name_for_user(
        self,
        user_id: uuid.UUID,
        owner: str,
        name: str,
    ) -> Repository | None:
        statement = select(Repository).where(
            Repository.user_id == user_id,
            Repository.owner == owner,
            Repository.name == name,
        )
        return self._db.scalar(statement)

    def update(self, repository: Repository) -> Repository:
        self._db.add(repository)
        self._db.commit()
        self._db.refresh(repository)
        return repository

    def delete(self, repository: Repository) -> None:
        self._db.delete(repository)
        self._db.commit()
