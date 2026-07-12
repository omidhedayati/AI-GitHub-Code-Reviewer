from urllib.parse import urlencode

import httpx

from app.config.settings import Settings
from app.models.user import GitHubProfile


class GitHubOAuthError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class GitHubOAuthService:
    """GitHub OAuth authorization code flow helpers."""

    AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
    TOKEN_URL = "https://github.com/login/oauth/access_token"
    USER_URL = "https://api.github.com/user"
    EMAILS_URL = "https://api.github.com/user/emails"

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    @property
    def is_configured(self) -> bool:
        return bool(
            self._settings.github_client_id and self._settings.github_client_secret
        )

    def build_authorize_url(self, state: str) -> str:
        params = {
            "client_id": self._settings.github_client_id,
            "redirect_uri": self._settings.github_oauth_redirect_uri,
            "scope": self._settings.github_oauth_scopes,
            "state": state,
        }
        return f"{self.AUTHORIZE_URL}?{urlencode(params)}"

    def fetch_profile(self, code: str) -> GitHubProfile:
        access_token = self._exchange_code(code)
        user_payload = self._get_json(
            self.USER_URL,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/vnd.github+json",
            },
        )
        email = self._resolve_primary_email(access_token, user_payload)
        github_id = user_payload.get("id")
        username = user_payload.get("login")
        if not isinstance(github_id, int) or not isinstance(username, str):
            raise GitHubOAuthError("GitHub profile response was incomplete")

        raw_name = user_payload.get("name")
        full_name = raw_name if isinstance(raw_name, str) else None
        raw_avatar = user_payload.get("avatar_url")
        avatar_url = raw_avatar if isinstance(raw_avatar, str) else None

        return GitHubProfile(
            github_id=github_id,
            username=username,
            email=email,
            full_name=full_name,
            avatar_url=avatar_url,
        )

    def _exchange_code(self, code: str) -> str:
        try:
            with httpx.Client(timeout=15.0) as client:
                response = client.post(
                    self.TOKEN_URL,
                    headers={"Accept": "application/json"},
                    json={
                        "client_id": self._settings.github_client_id,
                        "client_secret": self._settings.github_client_secret,
                        "code": code,
                        "redirect_uri": self._settings.github_oauth_redirect_uri,
                    },
                )
                response.raise_for_status()
                payload = response.json()
        except httpx.HTTPError as exc:
            raise GitHubOAuthError(
                "Failed to exchange GitHub authorization code"
            ) from exc

        access_token = payload.get("access_token")
        if not isinstance(access_token, str) or not access_token:
            error = payload.get("error_description") or payload.get("error")
            message = (
                error if isinstance(error, str) else "GitHub token exchange failed"
            )
            raise GitHubOAuthError(message)
        return access_token

    def _resolve_primary_email(
        self,
        access_token: str,
        user_payload: dict[str, object],
    ) -> str:
        public_email = user_payload.get("email")
        if isinstance(public_email, str) and public_email:
            return public_email.lower()

        emails = self._get_json_list(
            self.EMAILS_URL,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/vnd.github+json",
            },
        )

        for entry in emails:
            if not isinstance(entry, dict):
                continue
            if entry.get("primary") and entry.get("verified"):
                email = entry.get("email")
                if isinstance(email, str) and email:
                    return email.lower()
        raise GitHubOAuthError(
            "GitHub account must have a verified primary email address"
        )

    def _get_json(self, url: str, *, headers: dict[str, str]) -> dict[str, object]:
        try:
            with httpx.Client(timeout=15.0) as client:
                response = client.get(url, headers=headers)
                response.raise_for_status()
                payload = response.json()
        except httpx.HTTPError as exc:
            raise GitHubOAuthError("Failed to fetch GitHub profile") from exc

        if not isinstance(payload, dict):
            raise GitHubOAuthError("Unexpected GitHub API response")
        return payload

    def _get_json_list(self, url: str, *, headers: dict[str, str]) -> list[object]:
        try:
            with httpx.Client(timeout=15.0) as client:
                response = client.get(url, headers=headers)
                response.raise_for_status()
                payload = response.json()
        except httpx.HTTPError as exc:
            raise GitHubOAuthError("Failed to fetch GitHub profile") from exc

        if not isinstance(payload, list):
            raise GitHubOAuthError("Unexpected GitHub API response")
        return payload
