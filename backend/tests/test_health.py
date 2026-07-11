from fastapi.testclient import TestClient


def test_health_check(test_client: TestClient) -> None:
    response = test_client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readiness_check(test_client: TestClient) -> None:
    response = test_client.get("/api/v1/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert data["database"] == "connected"
