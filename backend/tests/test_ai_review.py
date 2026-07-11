import json
import uuid
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_ollama_service
from app.models.repository import Repository, RepositoryStatus

MOCK_AI_RESPONSE = json.dumps(
    {
        "summary": (
            "The repository has security concerns around dynamic code execution."
        ),
        "issues": [
            {
                "file_path": "main.py",
                "line_start": 3,
                "line_end": 3,
                "category": "security",
                "severity": "critical",
                "confidence": 0.95,
                "title": "Unsafe eval usage",
                "explanation": "eval executes arbitrary code and is unsafe.",
                "suggestion": "Replace eval with a safe parser or literal evaluation.",
            }
        ],
    }
)


@pytest.fixture
def mock_ollama_service() -> MagicMock:
    service = MagicMock()
    service.check_health.return_value = MagicMock(
        available=True,
        model="qwen2.5",
        models_available=["qwen2.5"],
        base_url="http://localhost:11434",
        message="Ollama is ready",
    )
    service.generate_json.return_value = MOCK_AI_RESPONSE
    return service


@pytest.fixture
def ai_client(
    authed_client: TestClient,
    mock_ollama_service: MagicMock,
) -> TestClient:
    authed_client.app.dependency_overrides[get_ollama_service] = (
        lambda: mock_ollama_service
    )
    yield authed_client
    authed_client.app.dependency_overrides.pop(get_ollama_service, None)


@pytest.fixture
def ready_repository(
    ai_client: TestClient,
    registered_user: dict[str, str],
    db_session,
    tmp_path: Path,
) -> dict[str, str]:
    headers = {"Authorization": f"Bearer {registered_user['access_token']}"}
    response = ai_client.post(
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

    record = db_session.get(Repository, uuid.UUID(repository["id"]))
    assert record is not None
    record.status = RepositoryStatus.READY.value
    record.local_path = str(repo_dir)
    record.default_branch = "main"
    db_session.add(record)
    db_session.commit()

    return {"id": repository["id"], "headers": headers}


def test_run_ai_review(
    ai_client: TestClient,
    ready_repository: dict[str, str],
    mock_ollama_service: MagicMock,
) -> None:
    response = ai_client.post(
        f"/api/v1/repositories/{ready_repository['id']}/ai-review",
        headers=ready_repository["headers"],
    )
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "completed"
    assert data["review_type"] == "ai"
    assert data["ai_model"] == "qwen2.5"
    assert data["issues_count"] >= 1
    assert len(data["issues"]) >= 1
    assert data["issues"][0]["rule_id"].startswith("ai:")
    mock_ollama_service.generate_json.assert_called_once()


def test_get_latest_ai_review(
    ai_client: TestClient,
    ready_repository: dict[str, str],
) -> None:
    ai_client.post(
        f"/api/v1/repositories/{ready_repository['id']}/ai-review",
        headers=ready_repository["headers"],
    )
    response = ai_client.get(
        f"/api/v1/repositories/{ready_repository['id']}/reviews/latest"
        "?review_type=ai",
        headers=ready_repository["headers"],
    )
    assert response.status_code == 200
    assert response.json()["review_type"] == "ai"


def test_ai_review_ollama_unavailable(
    ai_client: TestClient,
    ready_repository: dict[str, str],
    mock_ollama_service: MagicMock,
) -> None:
    mock_ollama_service.check_health.return_value = MagicMock(
        available=False,
        model="qwen2.5",
        models_available=[],
        base_url="http://localhost:11434",
        message="Ollama is unreachable",
    )
    response = ai_client.post(
        f"/api/v1/repositories/{ready_repository['id']}/ai-review",
        headers=ready_repository["headers"],
    )
    assert response.status_code == 503


def test_ollama_health_endpoint(
    ai_client: TestClient,
    mock_ollama_service: MagicMock,
) -> None:
    response = ai_client.get("/api/v1/health/ollama")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "available"
    assert data["model"] == "qwen2.5"
