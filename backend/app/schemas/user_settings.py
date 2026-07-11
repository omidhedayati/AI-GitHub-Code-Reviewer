from pydantic import BaseModel, ConfigDict, Field


class UserSettingsOverrides(BaseModel):
    ollama_base_url: str | None = None
    ollama_model: str | None = Field(default=None, max_length=128)
    ignored_folders: str | None = None
    ignored_extensions: str | None = None
    max_file_size_bytes: int | None = Field(default=None, ge=1024, le=10_485_760)


class UserSettingsUpdate(BaseModel):
    ollama_base_url: str | None = Field(default=None, max_length=512)
    ollama_model: str | None = Field(default=None, max_length=128)
    ignored_folders: str | None = None
    ignored_extensions: str | None = None
    max_file_size_bytes: int | None = Field(default=None, ge=1024, le=10_485_760)


class EffectiveUserSettings(BaseModel):
    ollama_base_url: str
    ollama_model: str
    ignored_folders: str
    ignored_extensions: str
    max_file_size_bytes: int


class UserSettingsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    overrides: UserSettingsOverrides
    effective: EffectiveUserSettings


class OllamaUserHealthResponse(BaseModel):
    status: str
    model: str
    models_available: list[str] = Field(default_factory=list)
    base_url: str
    message: str
