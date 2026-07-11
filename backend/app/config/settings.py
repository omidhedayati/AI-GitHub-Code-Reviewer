from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = Field(default="AI GitHub Code Reviewer", alias="APP_NAME")
    debug: bool = Field(default=False, alias="DEBUG")
    api_v1_prefix: str = Field(default="/api/v1", alias="API_V1_PREFIX")

    database_url: str = Field(
        default="postgresql+psycopg://reviewer:reviewer@localhost:5432/reviewer",
        alias="DATABASE_URL",
    )

    jwt_secret: str = Field(default="change-me-in-production", alias="JWT_SECRET")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(
        default=30,
        alias="ACCESS_TOKEN_EXPIRE_MINUTES",
    )
    refresh_token_expire_days: int = Field(
        default=7,
        alias="REFRESH_TOKEN_EXPIRE_DAYS",
    )

    ollama_base_url: str = Field(
        default="http://localhost:11434",
        alias="OLLAMA_BASE_URL",
    )
    ollama_model: str = Field(default="qwen2.5", alias="OLLAMA_MODEL")
    ollama_timeout_seconds: int = Field(
        default=120,
        alias="OLLAMA_TIMEOUT_SECONDS",
    )
    ai_max_files: int = Field(default=10, alias="AI_MAX_FILES")
    ai_max_chars_per_file: int = Field(
        default=4000,
        alias="AI_MAX_CHARS_PER_FILE",
    )
    ai_temperature: float = Field(default=0.2, alias="AI_TEMPERATURE")

    cors_origins: str = Field(
        default="http://localhost:5173,http://127.0.0.1:5173",
        alias="CORS_ORIGINS",
    )

    max_file_size_bytes: int = Field(
        default=1_048_576,
        alias="MAX_FILE_SIZE_BYTES",
    )
    ignored_folders: str = Field(
        default="node_modules,.git,__pycache__,dist,build,.venv,venv",
        alias="IGNORED_FOLDERS",
    )
    ignored_extensions: str = Field(
        default=".min.js,.map,.lock,.png,.jpg,.jpeg,.gif,.svg,.ico,.woff,.woff2",
        alias="IGNORED_EXTENSIONS",
    )

    repos_workspace_root: str = Field(
        default="./.repos",
        alias="REPOS_WORKSPACE_ROOT",
    )
    git_clone_depth: int = Field(default=1, alias="GIT_CLONE_DEPTH")
    git_clone_timeout_seconds: int = Field(
        default=300,
        alias="GIT_CLONE_TIMEOUT_SECONDS",
    )

    @property
    def cors_origins_list(self) -> list[str]:
        return [
            origin.strip() for origin in self.cors_origins.split(",") if origin.strip()
        ]

    @property
    def ignored_folders_list(self) -> list[str]:
        return [f.strip() for f in self.ignored_folders.split(",") if f.strip()]

    @property
    def ignored_extensions_list(self) -> list[str]:
        return [e.strip() for e in self.ignored_extensions.split(",") if e.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
