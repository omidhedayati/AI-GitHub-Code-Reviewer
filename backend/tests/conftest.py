import os
import uuid
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import get_db_session, get_git_service
from app.db.base import Base
from app.main import create_app
from app.models.repository import Repository  # noqa: F401
from app.models.review import FileAnalysisResult, Review, ReviewIssue  # noqa: F401
from app.models.user import User  # noqa: F401
from app.models.user_settings import UserSettings  # noqa: F401
from app.utils.github_url import GitHubRepositoryRef


@pytest.fixture
def test_client() -> TestClient:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session_local = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = testing_session_local()
        try:
            yield db
        finally:
            db.close()

    os.environ.setdefault("JWT_SECRET", "test-secret")
    app = create_app()
    app.dependency_overrides[get_db_session] = override_get_db

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture
def registered_user(test_client: TestClient) -> dict[str, str]:
    response = test_client.post(
        "/api/v1/auth/register",
        json={
            "email": "reviewer@example.com",
            "password": "securepass123",
            "full_name": "Test Reviewer",
        },
    )
    assert response.status_code == 201
    payload = response.json()
    return {
        "id": payload["user"]["id"],
        "email": payload["user"]["email"],
        "access_token": payload["tokens"]["access_token"],
        "refresh_token": payload["tokens"]["refresh_token"],
    }


@pytest.fixture
def db_session(test_client: TestClient) -> Session:
    override_get_db = test_client.app.dependency_overrides[get_db_session]
    generator = override_get_db()
    session = next(generator)
    yield session
    session.close()
    try:
        next(generator)
    except StopIteration:
        pass


@pytest.fixture
def mock_git_service(tmp_path: Path) -> MagicMock:
    service = MagicMock()
    workspace = tmp_path / "repos"
    workspace.mkdir()

    def resolve_clone_directory(
        user_id: uuid.UUID,
        repository_id: uuid.UUID,
    ) -> Path:
        return workspace / str(user_id) / str(repository_id)

    def clone_repository(
        repo_ref: GitHubRepositoryRef,
        destination: Path,
        *,
        branch: str | None = None,
    ) -> str:
        destination.mkdir(parents=True, exist_ok=True)
        (destination / "README.md").write_text("# test", encoding="utf-8")
        return branch or "main"

    service.resolve_clone_directory.side_effect = resolve_clone_directory
    service.clone_repository.side_effect = clone_repository
    service.remove_repository.side_effect = lambda path: None
    return service


@pytest.fixture
def authed_client(
    test_client: TestClient,
    mock_git_service: MagicMock,
) -> TestClient:
    test_client.app.dependency_overrides[get_git_service] = lambda: mock_git_service
    yield test_client
    test_client.app.dependency_overrides.pop(get_git_service, None)
