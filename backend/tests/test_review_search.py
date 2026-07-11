import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.models.repository import Repository, RepositoryStatus


@pytest.fixture
def ready_repository_with_review(
    authed_client: TestClient,
    registered_user: dict[str, str],
    db_session,
    tmp_path: Path,
) -> dict[str, str]:
    headers = {"Authorization": f"Bearer {registered_user['access_token']}"}
    response = authed_client.post(
        "/api/v1/repositories",
        json={"url": "https://github.com/octocat/Hello-World"},
        headers=headers,
    )
    repository = response.json()

    repo_dir = tmp_path / "repos" / registered_user["id"] / repository["id"]
    repo_dir.mkdir(parents=True, exist_ok=True)
    (repo_dir / "main.py").write_text("password = 'secret123'\n", encoding="utf-8")

    record = db_session.get(Repository, uuid.UUID(repository["id"]))
    assert record is not None
    record.status = RepositoryStatus.READY.value
    record.local_path = str(repo_dir)
    record.default_branch = "main"
    db_session.add(record)
    db_session.commit()

    analyze_response = authed_client.post(
        f"/api/v1/repositories/{repository['id']}/analyze",
        headers=headers,
    )
    review = analyze_response.json()

    return {
        "repository_id": repository["id"],
        "review_id": review["id"],
        "headers": headers,
    }


def test_search_reviews(
    authed_client: TestClient,
    ready_repository_with_review: dict[str, str],
) -> None:
    response = authed_client.get(
        "/api/v1/reviews?q=secret",
        headers=ready_repository_with_review["headers"],
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert data["items"][0]["repository_name"] == "octocat/Hello-World"


def test_search_reviews_by_type(
    authed_client: TestClient,
    ready_repository_with_review: dict[str, str],
) -> None:
    response = authed_client.get(
        "/api/v1/reviews?review_type=static",
        headers=ready_repository_with_review["headers"],
    )
    assert response.status_code == 200
    assert all(item["review_type"] == "static" for item in response.json()["items"])


def test_get_review_report_markdown(
    authed_client: TestClient,
    ready_repository_with_review: dict[str, str],
) -> None:
    review_id = ready_repository_with_review["review_id"]
    response = authed_client.get(
        f"/api/v1/reviews/{review_id}/report?format=markdown",
        headers=ready_repository_with_review["headers"],
    )
    assert response.status_code == 200
    assert "Code Review Report" in response.text


def test_get_review_report_json(
    authed_client: TestClient,
    ready_repository_with_review: dict[str, str],
) -> None:
    review_id = ready_repository_with_review["review_id"]
    response = authed_client.get(
        f"/api/v1/reviews/{review_id}/report?format=json",
        headers=ready_repository_with_review["headers"],
    )
    assert response.status_code == 200
    data = response.json()
    assert "review" in data
    assert "issues" in data
