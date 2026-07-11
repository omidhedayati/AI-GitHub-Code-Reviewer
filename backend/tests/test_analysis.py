import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.models.repository import Repository, RepositoryStatus


@pytest.fixture
def ready_repository(
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
    (repo_dir / "main.py").write_text(
        '"""Sample module."""\n\n\ndef hello():\n    return eval("1")\n',
        encoding="utf-8",
    )
    (repo_dir / "app.js").write_text(
        "console.log('debug');\neval('1');\n",
        encoding="utf-8",
    )

    record = db_session.get(Repository, uuid.UUID(repository["id"]))
    assert record is not None
    record.status = RepositoryStatus.READY.value
    record.local_path = str(repo_dir)
    record.default_branch = "main"
    db_session.add(record)
    db_session.commit()

    return {"id": repository["id"], "headers": headers}


def test_analyze_repository(
    authed_client: TestClient,
    ready_repository: dict[str, str],
) -> None:
    response = authed_client.post(
        f"/api/v1/repositories/{ready_repository['id']}/analyze",
        headers=ready_repository["headers"],
    )
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "completed"
    assert data["files_analyzed"] >= 1
    assert data["issues_count"] >= 1
    assert data["overall_score"] >= 0
    assert len(data["issues"]) >= 1


def test_get_latest_review(
    authed_client: TestClient,
    ready_repository: dict[str, str],
) -> None:
    authed_client.post(
        f"/api/v1/repositories/{ready_repository['id']}/analyze",
        headers=ready_repository["headers"],
    )
    response = authed_client.get(
        f"/api/v1/repositories/{ready_repository['id']}/reviews/latest",
        headers=ready_repository["headers"],
    )
    assert response.status_code == 200
    assert response.json()["status"] == "completed"
