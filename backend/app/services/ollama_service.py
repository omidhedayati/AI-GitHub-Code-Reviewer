import json
from dataclasses import dataclass

import httpx

from app.config.settings import Settings


class OllamaServiceError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class OllamaUnavailableError(OllamaServiceError):
    pass


class OllamaModelNotFoundError(OllamaServiceError):
    pass


class OllamaResponseError(OllamaServiceError):
    pass


@dataclass(frozen=True)
class OllamaHealthStatus:
    available: bool
    model: str
    models_available: list[str]
    base_url: str
    message: str


class OllamaService:
    """HTTP client for the local Ollama API."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._base_url = settings.ollama_base_url.rstrip("/")
        self._timeout = settings.ollama_timeout_seconds

    def check_health(self) -> OllamaHealthStatus:
        model = self._settings.ollama_model
        try:
            with httpx.Client(timeout=self._timeout) as client:
                response = client.get(f"{self._base_url}/api/tags")
                response.raise_for_status()
                payload = response.json()
        except httpx.HTTPError:
            return OllamaHealthStatus(
                available=False,
                model=model,
                models_available=[],
                base_url=self._base_url,
                message=f"Ollama is unreachable at {self._base_url}",
            )

        models = [item.get("name", "") for item in payload.get("models", [])]
        model_names = [name.split(":")[0] for name in models if name]
        configured = model.split(":")[0]
        model_ready = any(
            name == configured or name.startswith(f"{configured}:")
            for name in models
        )
        if not model_ready:
            return OllamaHealthStatus(
                available=False,
                model=model,
                models_available=model_names,
                base_url=self._base_url,
                message=(
                    f"Model '{model}' is not available. "
                    f"Run: ollama pull {model}"
                ),
            )

        return OllamaHealthStatus(
            available=True,
            model=model,
            models_available=model_names,
            base_url=self._base_url,
            message="Ollama is ready",
        )

    def generate_json(self, *, system_prompt: str, user_prompt: str) -> str:
        health = self.check_health()
        if not health.available:
            if health.models_available:
                raise OllamaModelNotFoundError(health.message)
            raise OllamaUnavailableError(health.message)

        body = {
            "model": self._settings.ollama_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "format": "json",
            "stream": False,
            "options": {"temperature": self._settings.ai_temperature},
        }

        try:
            with httpx.Client(timeout=self._timeout) as client:
                response = client.post(f"{self._base_url}/api/chat", json=body)
                response.raise_for_status()
                payload = response.json()
        except httpx.HTTPError as exc:
            raise OllamaUnavailableError(
                f"Ollama request failed: {exc}"
            ) from exc

        message = payload.get("message", {})
        content = message.get("content")
        if not isinstance(content, str) or not content.strip():
            raise OllamaResponseError("Ollama returned an empty response")

        try:
            json.loads(content)
        except json.JSONDecodeError as exc:
            raise OllamaResponseError(
                "Ollama returned invalid JSON"
            ) from exc

        return content
