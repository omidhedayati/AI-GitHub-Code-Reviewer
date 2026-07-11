from fastapi.testclient import TestClient


def test_register_success(test_client: TestClient) -> None:
    response = test_client.post(
        "/api/v1/auth/register",
        json={
            "email": "newuser@example.com",
            "password": "securepass123",
            "full_name": "New User",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["user"]["email"] == "newuser@example.com"
    assert data["user"]["full_name"] == "New User"
    assert data["tokens"]["access_token"]
    assert data["tokens"]["refresh_token"]
    assert data["tokens"]["token_type"] == "bearer"


def test_register_duplicate_email(
    test_client: TestClient,
    registered_user: dict[str, str],
) -> None:
    response = test_client.post(
        "/api/v1/auth/register",
        json={
            "email": registered_user["email"],
            "password": "anotherpass123",
        },
    )
    assert response.status_code == 409
    assert response.json()["detail"] == "Email already registered"


def test_register_invalid_password(test_client: TestClient) -> None:
    response = test_client.post(
        "/api/v1/auth/register",
        json={
            "email": "shortpass@example.com",
            "password": "short",
        },
    )
    assert response.status_code == 422


def test_login_success(
    test_client: TestClient,
    registered_user: dict[str, str],
) -> None:
    response = test_client.post(
        "/api/v1/auth/login",
        json={
            "email": registered_user["email"],
            "password": "securepass123",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["user"]["email"] == registered_user["email"]
    assert data["tokens"]["access_token"]


def test_login_invalid_credentials(test_client: TestClient) -> None:
    response = test_client.post(
        "/api/v1/auth/login",
        json={
            "email": "missing@example.com",
            "password": "wrongpassword",
        },
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"


def test_get_me(
    test_client: TestClient,
    registered_user: dict[str, str],
) -> None:
    response = test_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {registered_user['access_token']}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == registered_user["email"]
    assert data["is_active"] is True


def test_get_me_unauthorized(test_client: TestClient) -> None:
    response = test_client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_refresh_token(
    test_client: TestClient,
    registered_user: dict[str, str],
) -> None:
    response = test_client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": registered_user["refresh_token"]},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["access_token"]
    assert data["refresh_token"]
    assert data["token_type"] == "bearer"


def test_refresh_token_invalid(test_client: TestClient) -> None:
    response = test_client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": "invalid.token.value"},
    )
    assert response.status_code == 401
