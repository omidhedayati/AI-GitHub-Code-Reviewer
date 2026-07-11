from fastapi.testclient import TestClient


def test_get_default_settings(
    authed_client: TestClient,
    registered_user: dict[str, str],
) -> None:
    headers = {"Authorization": f"Bearer {registered_user['access_token']}"}
    response = authed_client.get("/api/v1/settings/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["effective"]["ollama_model"] == "qwen2.5"
    assert data["overrides"]["ollama_base_url"] is None


def test_update_settings(
    authed_client: TestClient,
    registered_user: dict[str, str],
) -> None:
    headers = {"Authorization": f"Bearer {registered_user['access_token']}"}
    response = authed_client.put(
        "/api/v1/settings/me",
        json={
            "ollama_base_url": "http://localhost:11434",
            "ollama_model": "llama3.2",
            "ignored_folders": "node_modules,.git,custom_dir",
            "max_file_size_bytes": 524288,
        },
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["effective"]["ollama_model"] == "llama3.2"
    assert "custom_dir" in data["effective"]["ignored_folders"]
    assert data["effective"]["max_file_size_bytes"] == 524288


def test_update_settings_invalid_url(
    authed_client: TestClient,
    registered_user: dict[str, str],
) -> None:
    headers = {"Authorization": f"Bearer {registered_user['access_token']}"}
    response = authed_client.put(
        "/api/v1/settings/me",
        json={"ollama_base_url": "ftp://invalid.example"},
        headers=headers,
    )
    assert response.status_code == 422


def test_user_ollama_health(
    authed_client: TestClient,
    registered_user: dict[str, str],
) -> None:
    headers = {"Authorization": f"Bearer {registered_user['access_token']}"}
    response = authed_client.get("/api/v1/settings/me/ollama-health", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "base_url" in data
