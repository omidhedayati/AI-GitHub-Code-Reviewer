import uuid
from datetime import UTC, datetime

from app.models.repository import RepositoryStatus
from app.models.user import User
from app.repositories.repository_repository import RepositoryRepository
from app.schemas.repository import RepositoryCreate, RepositoryResponse
from app.services.git_service import GitCloneError, GitService
from app.utils.github_url import InvalidGitHubURLError, parse_github_repository


class RepositoryServiceError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class DuplicateRepositoryError(RepositoryServiceError):
    pass


class RepositoryNotFoundError(RepositoryServiceError):
    pass


class InvalidRepositoryURLError(RepositoryServiceError):
    pass


class RepositoryService:
    """Orchestrates GitHub repository validation, cloning, and persistence."""

    def __init__(
        self,
        repository_repository: RepositoryRepository,
        git_service: GitService,
    ) -> None:
        self._repositories = repository_repository
        self._git = git_service

    def list_repositories(self, user: User) -> list[RepositoryResponse]:
        records = self._repositories.list_by_user(user.id)
        return [RepositoryResponse.model_validate(record) for record in records]

    def get_repository(
        self,
        user: User,
        repository_id: uuid.UUID,
    ) -> RepositoryResponse:
        record = self._repositories.get_by_id_for_user(repository_id, user.id)
        if record is None:
            raise RepositoryNotFoundError("Repository not found")
        return RepositoryResponse.model_validate(record)

    def clone_repository(
        self,
        user: User,
        data: RepositoryCreate,
    ) -> RepositoryResponse:
        try:
            repo_ref = parse_github_repository(data.url)
        except InvalidGitHubURLError as exc:
            raise InvalidRepositoryURLError(str(exc)) from exc

        existing = self._repositories.get_by_owner_name_for_user(
            user.id,
            repo_ref.owner,
            repo_ref.name,
        )
        if existing is not None:
            raise DuplicateRepositoryError("Repository already added for this account")

        record = self._repositories.create(
            user_id=user.id,
            url=repo_ref.html_url,
            owner=repo_ref.owner,
            name=repo_ref.name,
            status=RepositoryStatus.CLONING,
        )

        destination = self._git.resolve_clone_directory(user.id, record.id)

        try:
            default_branch = self._git.clone_repository(
                repo_ref,
                destination,
                branch=data.branch,
            )
            record.status = RepositoryStatus.READY.value
            record.local_path = str(destination)
            record.default_branch = default_branch
            record.cloned_at = datetime.now(UTC)
            record.error_message = None
        except GitCloneError as exc:
            record.status = RepositoryStatus.FAILED.value
            record.error_message = exc.message
            self._git.remove_repository(destination)
        except ValueError as exc:
            record.status = RepositoryStatus.FAILED.value
            record.error_message = str(exc)
        except Exception:
            record.status = RepositoryStatus.FAILED.value
            record.error_message = "Unexpected error during clone"
            self._git.remove_repository(destination)

        updated = self._repositories.update(record)
        return RepositoryResponse.model_validate(updated)

    def delete_repository(self, user: User, repository_id: uuid.UUID) -> None:
        record = self._repositories.get_by_id_for_user(repository_id, user.id)
        if record is None:
            raise RepositoryNotFoundError("Repository not found")

        if record.local_path:
            self._git.remove_repository(record.local_path)

        parent_dir = self._git.resolve_clone_directory(user.id, record.id).parent
        if parent_dir.exists() and not any(parent_dir.iterdir()):
            parent_dir.rmdir()

        self._repositories.delete(record)
