import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user_settings import UserSettings


class UserSettingsRepository:
    """Data access for per-user settings."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def get_by_user_id(self, user_id: uuid.UUID) -> UserSettings | None:
        statement = select(UserSettings).where(UserSettings.user_id == user_id)
        return self._db.scalar(statement)

    def upsert(
        self,
        user_id: uuid.UUID,
        *,
        ollama_base_url: str | None = None,
        ollama_model: str | None = None,
        ignored_folders: str | None = None,
        ignored_extensions: str | None = None,
        max_file_size_bytes: int | None = None,
        clear_ollama_base_url: bool = False,
        clear_ollama_model: bool = False,
        clear_ignored_folders: bool = False,
        clear_ignored_extensions: bool = False,
        clear_max_file_size_bytes: bool = False,
    ) -> UserSettings:
        record = self.get_by_user_id(user_id)
        if record is None:
            record = UserSettings(user_id=user_id)
            self._db.add(record)

        if clear_ollama_base_url:
            record.ollama_base_url = None
        elif ollama_base_url is not None:
            record.ollama_base_url = ollama_base_url or None

        if clear_ollama_model:
            record.ollama_model = None
        elif ollama_model is not None:
            record.ollama_model = ollama_model or None

        if clear_ignored_folders:
            record.ignored_folders = None
        elif ignored_folders is not None:
            record.ignored_folders = ignored_folders or None

        if clear_ignored_extensions:
            record.ignored_extensions = None
        elif ignored_extensions is not None:
            record.ignored_extensions = ignored_extensions or None

        if clear_max_file_size_bytes:
            record.max_file_size_bytes = None
        elif max_file_size_bytes is not None:
            record.max_file_size_bytes = max_file_size_bytes

        self._db.commit()
        self._db.refresh(record)
        return record
