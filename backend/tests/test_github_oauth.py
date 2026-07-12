from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_github_oauth_service
from app.config.settings import get_settings
from app.models.user import GitHubProfile
from app.services.github_oauth_service import GitHubOAuthService
from app.utils.security import create_oauth_state_token


@pytest.fixture
def github_profile() -> GitHubProfile:
    return GitHubProfile(
        github_id=424242,
        username="octocat",
        email="octocat@users.noreply.github.com",
        full_name="The Octocat",
        avatar_url="https://avatars.githubusercontent.com/u/424242",
    )


@pytest.fixture
def github_oauth_client(
    test_client: TestClient,
    github_profile: GitHubProfile,
) -> tuple[TestClient, MagicMock]:
    mock_service = MagicMock(spec=GitHubOAuthService)
    mock_service.is_configured = True
    mock_service.build_authorize_url.side_effect = (
        lambda state: f"https://github.com/login/oauth/authorize?state={state}"
    )
    mock_service.fetch_profile.return_value = github_profile

    test_client.app.dependency_overrides[get_github_oauth_service] = (
        lambda: mock_service
    )
    yield test_client, mock_service
    test_client.app.dependency_overrides.pop(get_github_oauth_service, None)


def test_github_login_not_configured(test_client: TestClient) -> None:
    response = test_client.get("/api/v1/auth/github/login", follow_redirects=False)
    assert response.status_code == 503


def test_github_login_redirects(
    github_oauth_client: tuple[TestClient, MagicMock],
) -> None:
    client, mock_service = github_oauth_client
    response = client.get("/api/v1/auth/github/login", follow_redirects=False)
    assert response.status_code == 302
    location = response.headers["location"]
    assert location.startswith("https://github.com/login/oauth/authorize")
    assert "state=" in location
    mock_service.build_authorize_url.assert_called_once()


def test_github_callback_redirects_to_frontend_with_exchange_code(
    github_oauth_client: tuple[TestClient, MagicMock],
) -> None:
    client, mock_service = github_oauth_client
    settings = get_settings()
    state = create_oauth_state_token(settings)

    response = client.get(
        "/api/v1/auth/github/callback",
        params={"code": "github-auth-code", "state": state},
        follow_redirects=False,
    )

    assert response.status_code == 302
    location = response.headers["location"]
    frontend_callback = f"{settings.frontend_url.rstrip('/')}/auth/github/callback?"
    assert location.startswith(frontend_callback)
    assert "code=" in location
    mock_service.fetch_profile.assert_called_once_with("github-auth-code")


def test_github_callback_rejects_invalid_state(
    github_oauth_client: tuple[TestClient, MagicMock],
) -> None:
    client, _mock_service = github_oauth_client
    settings = get_settings()

    response = client.get(
        "/api/v1/auth/github/callback",
        params={"code": "github-auth-code", "state": "invalid-state"},
        follow_redirects=False,
    )

    assert response.status_code == 302
    location = response.headers["location"]
    frontend_callback = f"{settings.frontend_url.rstrip('/')}/auth/github/callback?"
    assert location.startswith(frontend_callback)
    assert "error=invalid_state" in location or "error=Invalid" in location


def test_github_exchange_returns_auth_response(
    github_oauth_client: tuple[TestClient, MagicMock],
) -> None:
    client, _mock_service = github_oauth_client
    settings = get_settings()
    state = create_oauth_state_token(settings)

    callback_response = client.get(
        "/api/v1/auth/github/callback",
        params={"code": "github-auth-code", "state": state},
        follow_redirects=False,
    )
    redirect_url = callback_response.headers["location"]
    exchange_code = redirect_url.split("code=", 1)[1]

    response = client.post(
        "/api/v1/auth/github/exchange",
        json={"code": exchange_code},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["user"]["email"] == "octocat@users.noreply.github.com"
    assert data["user"]["github_username"] == "octocat"
    assert data["user"]["auth_provider"] == "github"
    assert data["tokens"]["access_token"]
    assert data["tokens"]["refresh_token"]


def test_github_exchange_links_existing_email_account(
    github_oauth_client: tuple[TestClient, MagicMock],
    registered_user: dict[str, str],
) -> None:
    client, mock_service = github_oauth_client
    settings = get_settings()
    mock_service.fetch_profile.return_value = GitHubProfile(
        github_id=999001,
        username="linked-user",
        email=registered_user["email"],
        full_name="Linked User",
        avatar_url="https://avatars.githubusercontent.com/u/999001",
    )
    state = create_oauth_state_token(settings)

    callback_response = client.get(
        "/api/v1/auth/github/callback",
        params={"code": "github-auth-code", "state": state},
        follow_redirects=False,
    )
    exchange_code = callback_response.headers["location"].split("code=", 1)[1]

    response = client.post(
        "/api/v1/auth/github/exchange",
        json={"code": exchange_code},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["user"]["id"] == registered_user["id"]
    assert data["user"]["github_username"] == "linked-user"
    assert data["user"]["auth_provider"] == "github"


def test_github_exchange_invalid_code(test_client: TestClient) -> None:
    response = test_client.post(
        "/api/v1/auth/github/exchange",
        json={"code": "not-a-valid-exchange-token"},
    )
    assert response.status_code == 401


def test_login_rejects_oauth_only_user(
    test_client: TestClient,
    github_oauth_client: tuple[TestClient, MagicMock],
) -> None:
    client, _mock_service = github_oauth_client
    settings = get_settings()
    state = create_oauth_state_token(settings)

    callback_response = client.get(
        "/api/v1/auth/github/callback",
        params={"code": "github-auth-code", "state": state},
        follow_redirects=False,
    )
    exchange_code = callback_response.headers["location"].split("code=", 1)[1]
    exchange_response = client.post(
        "/api/v1/auth/github/exchange",
        json={"code": exchange_code},
    )
    email = exchange_response.json()["user"]["email"]

    login_response = test_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "any-password"},
    )
    assert login_response.status_code == 401
    assert login_response.json()["detail"] == "Invalid email or password"
