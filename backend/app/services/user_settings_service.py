import re
import uuid

from app.config.analysis_config import AnalysisConfig
from app.config.settings import Settings
from app.models.user import User
from app.models.user_settings import UserSettings
from app.repositories.user_settings_repository import UserSettingsRepository
from app.schemas.user_settings import (
    EffectiveUserSettings,
    OllamaUserHealthResponse,
    UserSettingsOverrides,
    UserSettingsResponse,
    UserSettingsUpdate,
)
from app.services.ollama_service import OllamaService

_URL_PATTERN = re.compile(r"^https?://", re.IGNORECASE)


class UserSettingsServiceError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class InvalidSettingsError(UserSettingsServiceError):
    pass


class UserSettingsService:
    """Manage per-user analysis and Ollama preferences."""

    def __init__(
        self,
        repository: UserSettingsRepository,
        app_settings: Settings,
    ) -> None:
        self._repository = repository
        self._app_settings = app_settings

    def get_settings(self, user: User) -> UserSettingsResponse:
        record = self._repository.get_by_user_id(user.id)
        effective = self.get_analysis_config(user.id)
        return UserSettingsResponse(
            overrides=self._to_overrides(record),
            effective=EffectiveUserSettings(
                ollama_base_url=effective.ollama_base_url,
                ollama_model=effective.ollama_model,
                ignored_folders=effective.ignored_folders,
                ignored_extensions=effective.ignored_extensions,
                max_file_size_bytes=effective.max_file_size_bytes,
            ),
        )

    def update_settings(self, user: User, data: UserSettingsUpdate) -> UserSettingsResponse:
        self._validate_update(data)
        payload = data.model_dump(exclude_unset=True)
        record = self._repository.upsert(
            user.id,
            ollama_base_url=payload.get("ollama_base_url"),
            ollama_model=payload.get("ollama_model"),
            ignored_folders=payload.get("ignored_folders"),
            ignored_extensions=payload.get("ignored_extensions"),
            max_file_size_bytes=payload.get("max_file_size_bytes"),
            clear_ollama_base_url="ollama_base_url" in payload
            and payload["ollama_base_url"] in (None, ""),
            clear_ollama_model="ollama_model" in payload
            and payload["ollama_model"] in (None, ""),
            clear_ignored_folders="ignored_folders" in payload
            and payload["ignored_folders"] in (None, ""),
            clear_ignored_extensions="ignored_extensions" in payload
            and payload["ignored_extensions"] in (None, ""),
            clear_max_file_size_bytes="max_file_size_bytes" in payload
            and payload["max_file_size_bytes"] is None,
        )
        effective = self.get_analysis_config(user.id)
        return UserSettingsResponse(
            overrides=self._to_overrides(record),
            effective=EffectiveUserSettings(
                ollama_base_url=effective.ollama_base_url,
                ollama_model=effective.ollama_model,
                ignored_folders=effective.ignored_folders,
                ignored_extensions=effective.ignored_extensions,
                max_file_size_bytes=effective.max_file_size_bytes,
            ),
        )

    def get_analysis_config(self, user_id: uuid.UUID) -> AnalysisConfig:
        record = self._repository.get_by_user_id(user_id)
        return AnalysisConfig.merge(self._app_settings, record)

    def check_ollama_health(self, user: User) -> OllamaUserHealthResponse:
        config = self.get_analysis_config(user.id)
        health = OllamaService(config).check_health()
        return OllamaUserHealthResponse(
            status="available" if health.available else "unavailable",
            model=health.model,
            models_available=health.models_available,
            base_url=health.base_url,
            message=health.message,
        )

    def _to_overrides(self, record: UserSettings | None) -> UserSettingsOverrides:
        if record is None:
            return UserSettingsOverrides()
        return UserSettingsOverrides(
            ollama_base_url=record.ollama_base_url,
            ollama_model=record.ollama_model,
            ignored_folders=record.ignored_folders,
            ignored_extensions=record.ignored_extensions,
            max_file_size_bytes=record.max_file_size_bytes,
        )

    def _validate_update(self, data: UserSettingsUpdate) -> None:
        if data.ollama_base_url and not _URL_PATTERN.match(data.ollama_base_url.strip()):
            raise InvalidSettingsError("Ollama base URL must start with http:// or https://")
        if data.ollama_model is not None and data.ollama_model.strip() == "":
            return
        if data.ollama_model is not None and not data.ollama_model.strip():
            raise InvalidSettingsError("Ollama model cannot be blank")
