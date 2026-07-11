import uuid
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_git_service
from app.utils.github_url import GitHubRepositoryRef


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


def test_clone_repository_success(
    authed_client: TestClient,
    registered_user: dict[str, str],
) -> None:
    response = authed_client.post(
        "/api/v1/repositories",
        json={"url": "https://github.com/octocat/Hello-World"},
        headers={"Authorization": f"Bearer {registered_user['access_token']}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["owner"] == "octocat"
    assert data["name"] == "Hello-World"
    assert data["status"] == "ready"
    assert data["default_branch"] == "main"


def test_clone_repository_invalid_url(
    authed_client: TestClient,
    registered_user: dict[str, str],
) -> None:
    response = authed_client.post(
        "/api/v1/repositories",
        json={"url": "not-valid"},
        headers={"Authorization": f"Bearer {registered_user['access_token']}"},
    )
    assert response.status_code == 422


def test_clone_repository_duplicate(
    authed_client: TestClient,
    registered_user: dict[str, str],
) -> None:
    headers = {"Authorization": f"Bearer {registered_user['access_token']}"}
    payload = {"url": "octocat/Hello-World"}

    first = authed_client.post("/api/v1/repositories", json=payload, headers=headers)
    assert first.status_code == 201

    second = authed_client.post("/api/v1/repositories", json=payload, headers=headers)
    assert second.status_code == 409


def test_list_repositories(
    authed_client: TestClient,
    registered_user: dict[str, str],
) -> None:
    headers = {"Authorization": f"Bearer {registered_user['access_token']}"}
    authed_client.post(
        "/api/v1/repositories",
        json={"url": "https://github.com/octocat/Hello-World"},
        headers=headers,
    )

    response = authed_client.get("/api/v1/repositories", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1


def test_get_repository(
    authed_client: TestClient,
    registered_user: dict[str, str],
) -> None:
    headers = {"Authorization": f"Bearer {registered_user['access_token']}"}
    created = authed_client.post(
        "/api/v1/repositories",
        json={"url": "https://github.com/octocat/Hello-World"},
        headers=headers,
    ).json()

    response = authed_client.get(
        f"/api/v1/repositories/{created['id']}",
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["id"] == created["id"]


def test_delete_repository(
    authed_client: TestClient,
    registered_user: dict[str, str],
) -> None:
    headers = {"Authorization": f"Bearer {registered_user['access_token']}"}
    created = authed_client.post(
        "/api/v1/repositories",
        json={"url": "https://github.com/octocat/Hello-World"},
        headers=headers,
    ).json()

    delete_response = authed_client.delete(
        f"/api/v1/repositories/{created['id']}",
        headers=headers,
    )
    assert delete_response.status_code == 204

    get_response = authed_client.get(
        f"/api/v1/repositories/{created['id']}",
        headers=headers,
    )
    assert get_response.status_code == 404


def test_repositories_require_auth(test_client: TestClient) -> None:
    response = test_client.get("/api/v1/repositories")
    assert response.status_code == 401
