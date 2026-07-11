import json
from unittest.mock import MagicMock, patch

import httpx
import pytest

from app.config.analysis_config import AnalysisConfig
from app.config.settings import Settings
from app.services.ollama_service import OllamaService, OllamaUnavailableError


def _config() -> AnalysisConfig:
    return AnalysisConfig.from_app_settings(
        Settings(
            OLLAMA_BASE_URL="http://ollama.test",
            OLLAMA_MODEL="qwen2.5",
            OLLAMA_TIMEOUT_SECONDS=5,
        )
    )


def test_generate_json_success() -> None:
    service = OllamaService(_config())

    tags_response = MagicMock()
    tags_response.raise_for_status = MagicMock()
    tags_response.json.return_value = {"models": [{"name": "qwen2.5:latest"}]}

    chat_response = MagicMock()
    chat_response.raise_for_status = MagicMock()
    chat_response.json.return_value = {
        "message": {"content": json.dumps({"summary": "ok", "issues": []})}
    }

    mock_client = MagicMock()
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    mock_client.get.return_value = tags_response
    mock_client.post.return_value = chat_response

    with patch("app.services.ollama_service.httpx.Client", return_value=mock_client):
        result = service.generate_json(
            system_prompt="system",
            user_prompt="review this code",
        )

    assert "summary" in result


def test_check_health_unreachable() -> None:
    service = OllamaService(_config())

    mock_client = MagicMock()
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    mock_client.get.side_effect = httpx.ConnectError("connection refused")

    with patch("app.services.ollama_service.httpx.Client", return_value=mock_client):
        health = service.check_health()

    assert health.available is False


def test_generate_json_unreachable() -> None:
    service = OllamaService(_config())

    mock_client = MagicMock()
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    mock_client.get.side_effect = httpx.ConnectError("connection refused")

    with (
        patch("app.services.ollama_service.httpx.Client", return_value=mock_client),
        pytest.raises(OllamaUnavailableError),
    ):
        service.generate_json(system_prompt="system", user_prompt="user")
