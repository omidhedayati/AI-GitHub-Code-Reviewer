from __future__ import annotations

from dataclasses import dataclass

from app.config.settings import Settings
from app.models.user_settings import UserSettings


@dataclass(frozen=True)
class AnalysisConfig:
    """Resolved analysis and Ollama settings for a user."""

    ollama_base_url: str
    ollama_model: str
    ollama_timeout_seconds: int
    ai_max_files: int
    ai_max_chars_per_file: int
    ai_temperature: float
    max_file_size_bytes: int
    ignored_folders: str
    ignored_extensions: str

    @property
    def ignored_folders_list(self) -> list[str]:
        return [f.strip() for f in self.ignored_folders.split(",") if f.strip()]

    @property
    def ignored_extensions_list(self) -> list[str]:
        return [e.strip() for e in self.ignored_extensions.split(",") if e.strip()]

    @classmethod
    def from_app_settings(cls, settings: Settings) -> AnalysisConfig:
        return cls(
            ollama_base_url=settings.ollama_base_url,
            ollama_model=settings.ollama_model,
            ollama_timeout_seconds=settings.ollama_timeout_seconds,
            ai_max_files=settings.ai_max_files,
            ai_max_chars_per_file=settings.ai_max_chars_per_file,
            ai_temperature=settings.ai_temperature,
            max_file_size_bytes=settings.max_file_size_bytes,
            ignored_folders=settings.ignored_folders,
            ignored_extensions=settings.ignored_extensions,
        )

    @classmethod
    def merge(cls, app_settings: Settings, user_settings: UserSettings | None) -> AnalysisConfig:
        base = cls.from_app_settings(app_settings)
        if user_settings is None:
            return base
        return cls(
            ollama_base_url=user_settings.ollama_base_url or base.ollama_base_url,
            ollama_model=user_settings.ollama_model or base.ollama_model,
            ollama_timeout_seconds=base.ollama_timeout_seconds,
            ai_max_files=base.ai_max_files,
            ai_max_chars_per_file=base.ai_max_chars_per_file,
            ai_temperature=base.ai_temperature,
            max_file_size_bytes=(
                user_settings.max_file_size_bytes or base.max_file_size_bytes
            ),
            ignored_folders=user_settings.ignored_folders or base.ignored_folders,
            ignored_extensions=(
                user_settings.ignored_extensions or base.ignored_extensions
            ),
        )
